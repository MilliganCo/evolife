"""
Модуль генетики для эволюционной симуляции 'Жизнь'.

Содержит классы для генома клеток, мутаций, кроссовера и определения видов.
"""

import random
from typing import List, Tuple, Dict, NamedTuple


class Genome(NamedTuple):
    """Геном клетки с генетической информацией."""
    birth_mask: int  # 9 бит - условия рождения
    survive_mask: int  # 9 бит - условия выживания
    mut_bits: int  # 8 бит - квантованная частота мутаций
    glyph_id: int  # 0..K-1 - индекс ASCII символа
    color_id: int  # 0..15 - индекс ANSI цвета
    age_max: int  # 1..255 - максимальный возраст

    @property
    def mutation_rate(self) -> float:
        """Возвращает частоту мутаций как float в [0, 1]."""
        return self.mut_bits / 255.0

    @classmethod
    def random(cls, rng: random.Random, glyph_count: int = 14) -> "Genome":
        """Создает случайный геном."""
        return cls(
            birth_mask=rng.randint(0, 511),  # 9 бит
            survive_mask=rng.randint(0, 511),  # 9 бит
            mut_bits=rng.randint(0, 255),  # 8 бит
            glyph_id=rng.randint(0, glyph_count - 1),
            color_id=rng.randint(0, 15),
            age_max=rng.randint(1, 255)
        )

    @classmethod
    def default(cls, glyph_count: int = 14) -> "Genome":
        """Создает геном по умолчанию (B3/S23)."""
        return cls(
            birth_mask=0b000100000,  # B3 - рождение при 3 соседях
            survive_mask=0b000110000,  # S23 - выживание при 2 или 3 соседях
            mut_bits=5,  # Низкая частота мутаций по умолчанию
            glyph_id=0,
            color_id=0,
            age_max=64
        )


class Species:
    """Класс для определения и кластеризации видов."""
    
    def __init__(self, hamming_threshold: int = 2):
        self.hamming_threshold = hamming_threshold
        self.species_map: Dict[Tuple[int, int], int] = {}  # (birth, survive) -> species_id
        self.species_counts: Dict[int, int] = {}  # species_id -> count
        self.next_species_id = 0

    def get_species_id(self, birth_mask: int, survive_mask: int) -> int:
        """Возвращает ID вида для данной пары масок."""
        # Ищем существующий вид в пределах порога Хэмминга
        for (existing_birth, existing_survive), species_id in self.species_map.items():
            if (self._hamming_distance(birth_mask, existing_birth) <= self.hamming_threshold and
                self._hamming_distance(survive_mask, existing_survive) <= self.hamming_threshold):
                return species_id
        
        # Создаем новый вид
        species_id = self.next_species_id
        self.next_species_id += 1
        self.species_map[(birth_mask, survive_mask)] = species_id
        self.species_counts[species_id] = 0
        return species_id

    def update_count(self, species_id: int, delta: int) -> None:
        """Обновляет счетчик особей вида."""
        if species_id in self.species_counts:
            self.species_counts[species_id] += delta
            if self.species_counts[species_id] <= 0:
                del self.species_counts[species_id]

    def get_top_species(self, n: int = 3) -> List[Tuple[int, int]]:
        """Возвращает топ-N видов по количеству особей."""
        return sorted(self.species_counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_species_count(self) -> int:
        """Возвращает общее количество видов."""
        return len(self.species_counts)

    @staticmethod
    def _hamming_distance(a: int, b: int) -> int:
        """Вычисляет расстояние Хэмминга между двумя числами."""
        return bin(a ^ b).count('1')


class GeneticsEngine:
    """Движок генетики для кроссовера и мутаций."""
    
    def __init__(self, 
                 mutation_rate_multiplier: float = 1.0,
                 max_mutations_per_birth: int = 2,
                 glyph_count: int = 14):
        self.mutation_rate_multiplier = mutation_rate_multiplier
        self.max_mutations_per_birth = max_mutations_per_birth
        self.glyph_count = glyph_count
        self.glyph_palette = [".", "`", "'", "^", "*", "+", "o", "x", "O", "X", "#", "@", "%", "&"]
        
        # Цветовая палитра ANSI
        self.color_palette = [
            "30", "31", "32", "33", "34", "35", "36", "37",  # Обычные цвета
            "90", "91", "92", "93", "94", "95", "96", "97"   # Яркие цвета
        ]

    def crossover(self, parent1: Genome, parent2: Genome, rng: random.Random) -> Genome:
        """Выполняет кроссовер между двумя родителями."""
        # Однородный кроссовер для масок (50/50)
        birth_mask = self._uniform_crossover(parent1.birth_mask, parent2.birth_mask, rng)
        survive_mask = self._uniform_crossover(parent1.survive_mask, parent2.survive_mask, rng)
        
        # Случайный выбор родителя для скалярных генов
        glyph_id = rng.choice([parent1.glyph_id, parent2.glyph_id])
        color_id = rng.choice([parent1.color_id, parent2.color_id])
        age_max = rng.choice([parent1.age_max, parent2.age_max])
        
        # Частота мутаций - среднее арифметическое
        mut_bits = (parent1.mut_bits + parent2.mut_bits) // 2
        
        return Genome(birth_mask, survive_mask, mut_bits, glyph_id, color_id, age_max)

    def mutate(self, genome: Genome, rng: random.Random) -> Genome:
        """Применяет мутации к геному."""
        mutations = 0
        max_mutations = min(self.max_mutations_per_birth, 6)  # Максимум 6 генов
        
        birth_mask = genome.birth_mask
        survive_mask = genome.survive_mask
        mut_bits = genome.mut_bits
        glyph_id = genome.glyph_id
        color_id = genome.color_id
        age_max = genome.age_max
        
        # Мутации для масок
        if rng.random() < genome.mutation_rate * self.mutation_rate_multiplier and mutations < max_mutations:
            if rng.choice([True, False]):
                birth_mask = self._flip_random_bit(birth_mask, 9, rng)
            else:
                survive_mask = self._flip_random_bit(survive_mask, 9, rng)
            mutations += 1
        
        # Мутация частоты мутаций
        if rng.random() < genome.mutation_rate * self.mutation_rate_multiplier and mutations < max_mutations:
            mut_bits = self._mutate_mut_bits(mut_bits, rng)
            mutations += 1
        
        # Мутация глифа
        if rng.random() < genome.mutation_rate * self.mutation_rate_multiplier and mutations < max_mutations:
            glyph_id = self._mutate_glyph(glyph_id, rng)
            mutations += 1
        
        # Мутация цвета
        if rng.random() < genome.mutation_rate * self.mutation_rate_multiplier and mutations < max_mutations:
            color_id = self._mutate_color(color_id, rng)
            mutations += 1
        
        # Мутация максимального возраста
        if rng.random() < genome.mutation_rate * self.mutation_rate_multiplier and mutations < max_mutations:
            age_max = self._mutate_age_max(age_max, rng)
            mutations += 1
        
        return Genome(birth_mask, survive_mask, mut_bits, glyph_id, color_id, age_max)

    def _uniform_crossover(self, parent1: int, parent2: int, rng: random.Random) -> int:
        """Однородный кроссовер для масок."""
        result = 0
        for i in range(max(parent1.bit_length(), parent2.bit_length())):
            if rng.choice([True, False]):
                result |= (parent1 & (1 << i))
            else:
                result |= (parent2 & (1 << i))
        return result

    def _flip_random_bit(self, value: int, bit_count: int, rng: random.Random) -> int:
        """Инвертирует случайный бит в числе."""
        bit_pos = rng.randint(0, bit_count - 1)
        return value ^ (1 << bit_pos)

    def _mutate_mut_bits(self, mut_bits: int, rng: random.Random) -> int:
        """Мутирует частоту мутаций сдвигом на ±1."""
        delta = rng.choice([-1, 1])
        return max(0, min(255, mut_bits + delta))

    def _mutate_glyph(self, glyph_id: int, rng: random.Random) -> int:
        """Мутирует глиф на соседнее значение."""
        if rng.choice([True, False]) and glyph_id > 0:
            return glyph_id - 1
        elif glyph_id < self.glyph_count - 1:
            return glyph_id + 1
        else:
            return rng.randint(0, self.glyph_count - 1)

    def _mutate_color(self, color_id: int, rng: random.Random) -> int:
        """Мутирует цвет на соседнее значение по цветовому кругу."""
        if rng.choice([True, False]) and color_id > 0:
            return color_id - 1
        elif color_id < 15:
            return color_id + 1
        else:
            return rng.randint(0, 15)

    def _mutate_age_max(self, age_max: int, rng: random.Random) -> int:
        """Мутирует максимальный возраст на ±5."""
        delta = rng.randint(-5, 5)
        return max(1, min(255, age_max + delta))

    def get_glyph(self, glyph_id: int) -> str:
        """Возвращает символ по ID глифа."""
        return self.glyph_palette[glyph_id % len(self.glyph_palette)]

    def get_color_code(self, color_id: int) -> str:
        """Возвращает ANSI код цвета."""
        return self.color_palette[color_id % len(self.color_palette)]
