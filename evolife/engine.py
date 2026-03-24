"""
Движок клеточного автомата для эволюционной симуляции 'Жизнь'.

Содержит основную логику симуляции, правила обновления клеток и генетические операции.
"""

import random
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from .genetics import Genome, GeneticsEngine, Species


class LifeEngine:
    """Основной движок симуляции 'Жизнь' с генетикой."""
    
    def __init__(self, 
                 width: int, 
                 height: int, 
                 seed: Optional[int] = None,
                 default_rule: str = "B3/S23",
                 mutation_rate_multiplier: float = 1.0,
                 max_mutations_per_birth: int = 2,
                 species_hamming_threshold: int = 2,
                 age_max_default: int = 64,
                 catastrophe_probability: float = 0.0):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.tick = 0
        
        # Генетическая система
        self.genetics = GeneticsEngine(
            mutation_rate_multiplier=mutation_rate_multiplier,
            max_mutations_per_birth=max_mutations_per_birth
        )
        self.species = Species(hamming_threshold=species_hamming_threshold)
        
        # Состояние клеток
        self.cells = np.zeros((height, width), dtype=bool)
        self.genomes: Dict[Tuple[int, int], Genome] = {}
        self.ages: Dict[Tuple[int, int], int] = {}
        self.age_maxs: Dict[Tuple[int, int], int] = {}
        
        # Параметры
        self.default_rule = default_rule
        self.age_max_default = age_max_default
        self.catastrophe_probability = catastrophe_probability
        
        # Парсинг правила по умолчанию
        self.default_birth_mask, self.default_survive_mask = self._parse_rule(default_rule)

    def _parse_rule(self, rule: str) -> Tuple[int, int]:
        """Парсит правило в формате B3/S23 в маски."""
        birth_mask = 0
        survive_mask = 0
        
        if "/" in rule:
            birth_part, survive_part = rule.split("/", 1)
        else:
            birth_part = rule
            survive_part = ""
        
        # Парсинг B3
        if birth_part.startswith("B"):
            for digit in birth_part[1:]:
                if digit.isdigit():
                    birth_mask |= (1 << int(digit))
        
        # Парсинг S23
        if survive_part.startswith("S"):
            for digit in survive_part[1:]:
                if digit.isdigit():
                    survive_mask |= (1 << int(digit))
        
        return birth_mask, survive_mask

    def initialize_random(self, density: float = 0.15) -> None:
        """Инициализирует случайное начальное состояние."""
        for y in range(self.height):
            for x in range(self.width):
                if self.rng.random() < density:
                    self._add_cell(x, y, Genome.default())

    def initialize_pattern(self, pattern: List[Tuple[int, int]], offset_x: int = 0, offset_y: int = 0) -> None:
        """Инициализирует паттерн в указанной позиции."""
        for px, py in pattern:
            x, y = px + offset_x, py + offset_y
            if 0 <= x < self.width and 0 <= y < self.height:
                self._add_cell(x, y, Genome.default())

    def _add_cell(self, x: int, y: int, genome: Genome) -> None:
        """Добавляет клетку в указанной позиции."""
        self.cells[y, x] = True
        self.genomes[(x, y)] = genome
        self.ages[(x, y)] = 0
        self.age_maxs[(x, y)] = genome.age_max

    def _remove_cell(self, x: int, y: int) -> None:
        """Удаляет клетку из указанной позиции."""
        self.cells[y, x] = False
        if (x, y) in self.genomes:
            del self.genomes[(x, y)]
        if (x, y) in self.ages:
            del self.ages[(x, y)]
        if (x, y) in self.age_maxs:
            del self.age_maxs[(x, y)]

    def step(self) -> None:
        """Выполняет один шаг симуляции."""
        # Создаем копии для обновления
        new_cells = self.cells.copy()
        new_genomes = self.genomes.copy()
        new_ages = self.ages.copy()
        new_age_maxs = self.age_maxs.copy()
        
        # Подсчитываем соседей для всех клеток
        neighbor_counts = self._count_neighbors()
        
        # Обновляем существующие клетки
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y, x]:
                    # Проверяем выживание
                    if self._should_survive(x, y, neighbor_counts[y, x]):
                        # Увеличиваем возраст
                        new_ages[(x, y)] = self.ages.get((x, y), 0) + 1
                        # Проверяем возрастной лимит
                        if new_ages[(x, y)] > self.age_maxs.get((x, y), self.age_max_default):
                            new_cells[y, x] = False
                            if (x, y) in new_genomes:
                                del new_genomes[(x, y)]
                            if (x, y) in new_ages:
                                del new_ages[(x, y)]
                            if (x, y) in new_age_maxs:
                                del new_age_maxs[(x, y)]
                    else:
                        # Клетка умирает
                        new_cells[y, x] = False
                        if (x, y) in new_genomes:
                            del new_genomes[(x, y)]
                        if (x, y) in new_ages:
                            del new_ages[(x, y)]
                        if (x, y) in new_age_maxs:
                            del new_age_maxs[(x, y)]
        
        # Рождение новых клеток
        for y in range(self.height):
            for x in range(self.width):
                if not self.cells[y, x] and neighbor_counts[y, x] > 0:
                    if self._should_birth(x, y, neighbor_counts[y, x]):
                        # Находим родителей среди соседей
                        parents = self._find_parents(x, y)
                        if parents:
                            # Создаем потомка
                            child_genome = self.genetics.crossover(parents[0], parents[1], self.rng)
                            child_genome = self.genetics.mutate(child_genome, self.rng)
                            
                            new_cells[y, x] = True
                            new_genomes[(x, y)] = child_genome
                            new_ages[(x, y)] = 0
                            new_age_maxs[(x, y)] = child_genome.age_max
        
        # Применяем катастрофы
        if self.catastrophe_probability > 0:
            self._apply_catastrophes(new_cells, new_genomes, new_ages, new_age_maxs)
        
        # Обновляем состояние
        self.cells = new_cells
        self.genomes = new_genomes
        self.ages = new_ages
        self.age_maxs = new_age_maxs
        
        # Обновляем статистику видов
        self._update_species_stats()
        
        self.tick += 1

    def _count_neighbors(self) -> np.ndarray:
        """Подсчитывает количество живых соседей для каждой клетки."""
        counts = np.zeros((self.height, self.width), dtype=int)
        
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                # Сдвигаем массив с учетом тороидальной топологии
                shifted = np.roll(np.roll(self.cells, dy, axis=0), dx, axis=1)
                counts += shifted.astype(int)
        
        return counts

    def _should_survive(self, x: int, y: int, neighbor_count: int) -> bool:
        """Проверяет, должна ли клетка выжить."""
        if (x, y) in self.genomes:
            genome = self.genomes[(x, y)]
            return bool(genome.survive_mask & (1 << neighbor_count))
        else:
            # Используем правило по умолчанию
            return bool(self.default_survive_mask & (1 << neighbor_count))

    def _should_birth(self, x: int, y: int, neighbor_count: int) -> bool:
        """Проверяет, должна ли родиться новая клетка."""
        # Находим геномы соседей для определения правила рождения
        neighbor_genomes = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                if (nx, ny) in self.genomes:
                    neighbor_genomes.append(self.genomes[(nx, ny)])
        
        if neighbor_genomes:
            # Голосование соседей за правило рождения
            birth_votes = [genome.birth_mask for genome in neighbor_genomes]
            # Простое большинство
            birth_mask = max(set(birth_votes), key=birth_votes.count)
            return bool(birth_mask & (1 << neighbor_count))
        else:
            # Используем правило по умолчанию
            return bool(self.default_birth_mask & (1 << neighbor_count))

    def _find_parents(self, x: int, y: int) -> List[Genome]:
        """Находит двух родителей среди соседей."""
        neighbors = []
        
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                if (nx, ny) in self.genomes:
                    neighbors.append(self.genomes[(nx, ny)])
        
        if len(neighbors) < 2:
            if len(neighbors) == 1:
                return [neighbors[0], neighbors[0]]  # Дублируем одного родителя
            else:
                return []
        
        # Турнирный отбор
        parent1 = self.rng.choice(neighbors)
        parent2 = self.rng.choice(neighbors)
        return [parent1, parent2]

    def _apply_catastrophes(self, cells: np.ndarray, genomes: Dict, ages: Dict, age_maxs: Dict) -> None:
        """Применяет катастрофы среды."""
        for y in range(self.height):
            for x in range(self.width):
                if cells[y, x] and self.rng.random() < self.catastrophe_probability:
                    cells[y, x] = False
                    if (x, y) in genomes:
                        del genomes[(x, y)]
                    if (x, y) in ages:
                        del ages[(x, y)]
                    if (x, y) in age_maxs:
                        del age_maxs[(x, y)]

    def _update_species_stats(self) -> None:
        """Обновляет статистику видов."""
        # Сбрасываем счетчики
        for species_id in self.species.species_counts:
            self.species.species_counts[species_id] = 0
        
        # Подсчитываем текущие виды
        for (x, y), genome in self.genomes.items():
            species_id = self.species.get_species_id(genome.birth_mask, genome.survive_mask)
            self.species.update_count(species_id, 1)

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику симуляции."""
        alive_count = np.sum(self.cells)
        species_count = self.species.get_species_count()
        top_species = self.species.get_top_species(3)
        
        return {
            "tick": self.tick,
            "alive": int(alive_count),
            "species": species_count,
            "top_species": top_species
        }

    def get_cell_info(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о клетке в позиции (x, y)."""
        if not self.cells[y, x]:
            return None
        
        genome = self.genomes.get((x, y))
        age = self.ages.get((x, y), 0)
        
        if genome:
            species_id = self.species.get_species_id(genome.birth_mask, genome.survive_mask)
            return {
                "genome": genome,
                "age": age,
                "species_id": species_id,
                "glyph": self.genetics.get_glyph(genome.glyph_id),
                "color": self.genetics.get_color_code(genome.color_id)
            }
        
        return None

    def clear(self) -> None:
        """Очищает все клетки."""
        self.cells.fill(False)
        self.genomes.clear()
        self.ages.clear()
        self.age_maxs.clear()
        self.tick = 0
        self.species = Species(self.species.hamming_threshold)
