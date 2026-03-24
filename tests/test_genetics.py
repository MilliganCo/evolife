"""
Тесты для модуля генетики.
"""

import pytest
import random
from evolife.genetics import Genome, Species, GeneticsEngine


class TestGenome:
    """Тесты для класса Genome."""
    
    def test_genome_creation(self):
        """Тест создания генома."""
        genome = Genome(
            birth_mask=0b000100000,
            survive_mask=0b000110000,
            mut_bits=5,
            glyph_id=0,
            color_id=0,
            age_max=64
        )
        
        assert genome.birth_mask == 0b000100000
        assert genome.survive_mask == 0b000110000
        assert genome.mut_bits == 5
        assert genome.glyph_id == 0
        assert genome.color_id == 0
        assert genome.age_max == 64
    
    def test_mutation_rate_property(self):
        """Тест свойства mutation_rate."""
        genome = Genome(0, 0, 128, 0, 0, 64)
        assert genome.mutation_rate == 128 / 255.0
        
        genome = Genome(0, 0, 0, 0, 0, 64)
        assert genome.mutation_rate == 0.0
        
        genome = Genome(0, 0, 255, 0, 0, 64)
        assert genome.mutation_rate == 1.0
    
    def test_random_genome(self):
        """Тест создания случайного генома."""
        rng = random.Random(42)
        genome = Genome.random(rng, glyph_count=10)
        
        assert 0 <= genome.birth_mask <= 511
        assert 0 <= genome.survive_mask <= 511
        assert 0 <= genome.mut_bits <= 255
        assert 0 <= genome.glyph_id < 10
        assert 0 <= genome.color_id <= 15
        assert 1 <= genome.age_max <= 255
    
    def test_default_genome(self):
        """Тест создания генома по умолчанию."""
        genome = Genome.default()
        
        assert genome.birth_mask == 0b000100000  # B3
        assert genome.survive_mask == 0b000110000  # S23
        assert genome.mut_bits == 5
        assert genome.glyph_id == 0
        assert genome.color_id == 0
        assert genome.age_max == 64


class TestSpecies:
    """Тесты для класса Species."""
    
    def test_species_creation(self):
        """Тест создания системы видов."""
        species = Species(hamming_threshold=2)
        assert species.hamming_threshold == 2
        assert len(species.species_map) == 0
        assert len(species.species_counts) == 0
        assert species.next_species_id == 0
    
    def test_get_species_id_new(self):
        """Тест получения ID нового вида."""
        species = Species(hamming_threshold=2)
        species_id = species.get_species_id(0b000100000, 0b000110000)
        
        assert species_id == 0
        assert (0b000100000, 0b000110000) in species.species_map
        assert species.species_map[(0b000100000, 0b000110000)] == 0
        assert species.next_species_id == 1
    
    def test_get_species_id_existing(self):
        """Тест получения ID существующего вида."""
        species = Species(hamming_threshold=2)
        species_id1 = species.get_species_id(0b000100000, 0b000110000)
        species_id2 = species.get_species_id(0b000100000, 0b000110000)
        
        assert species_id1 == species_id2
    
    def test_hamming_distance_clustering(self):
        """Тест кластеризации по расстоянию Хэмминга."""
        species = Species(hamming_threshold=2)
        
        # Создаем первый вид
        species_id1 = species.get_species_id(0b000100000, 0b000110000)
        
        # Создаем похожий вид (расстояние Хэмминга = 1)
        species_id2 = species.get_species_id(0b000100001, 0b000110000)
        
        assert species_id1 == species_id2  # Должны быть в одном кластере
    
    def test_update_count(self):
        """Тест обновления счетчика видов."""
        species = Species(hamming_threshold=2)
        species_id = species.get_species_id(0b000100000, 0b000110000)
        
        species.update_count(species_id, 5)
        assert species.species_counts[species_id] == 5
        
        species.update_count(species_id, -2)
        assert species.species_counts[species_id] == 3
        
        species.update_count(species_id, -3)
        assert species_id not in species.species_counts  # Вид исчез
    
    def test_get_top_species(self):
        """Тест получения топ видов."""
        species = Species(hamming_threshold=0)  # Отключаем кластеризацию
        
        species_id1 = species.get_species_id(0b000100000, 0b000110000)
        species_id2 = species.get_species_id(0b000100001, 0b000110001)
        
        species.update_count(species_id1, 10)
        species.update_count(species_id2, 5)
        
        top = species.get_top_species(2)
        assert len(top) == 2
        assert top[0] == (species_id1, 10)
        assert top[1] == (species_id2, 5)
    
    def test_hamming_distance_calculation(self):
        """Тест вычисления расстояния Хэмминга."""
        assert Species._hamming_distance(0b0000, 0b0000) == 0
        assert Species._hamming_distance(0b0000, 0b0001) == 1
        assert Species._hamming_distance(0b0000, 0b0011) == 2
        assert Species._hamming_distance(0b1111, 0b0000) == 4


class TestGeneticsEngine:
    """Тесты для класса GeneticsEngine."""
    
    def test_genetics_engine_creation(self):
        """Тест создания движка генетики."""
        genetics = GeneticsEngine(
            mutation_rate_multiplier=1.0,
            max_mutations_per_birth=2,
            glyph_count=10
        )
        
        assert genetics.mutation_rate_multiplier == 1.0
        assert genetics.max_mutations_per_birth == 2
        assert genetics.glyph_count == 10
        assert len(genetics.glyph_palette) == 14
        assert len(genetics.color_palette) == 16
    
    def test_crossover(self):
        """Тест кроссовера."""
        genetics = GeneticsEngine()
        rng = random.Random(42)
        
        parent1 = Genome(0b000100000, 0b000110000, 5, 0, 0, 64)
        parent2 = Genome(0b000010000, 0b000101000, 10, 1, 1, 32)
        
        child = genetics.crossover(parent1, parent2, rng)
        
        # Проверяем, что ребенок имеет признаки обоих родителей
        assert isinstance(child, Genome)
        assert 0 <= child.birth_mask <= 511
        assert 0 <= child.survive_mask <= 511
        assert 0 <= child.mut_bits <= 255
        assert child.glyph_id in [0, 1]
        assert child.color_id in [0, 1]
        assert child.age_max in [32, 64]
    
    def test_mutate(self):
        """Тест мутаций."""
        genetics = GeneticsEngine(mutation_rate_multiplier=1.0)
        rng = random.Random(42)
        
        genome = Genome(0b000100000, 0b000110000, 5, 0, 0, 64)
        mutated = genetics.mutate(genome, rng)
        
        assert isinstance(mutated, Genome)
        # Мутации могут изменить любые гены
        assert 0 <= mutated.birth_mask <= 511
        assert 0 <= mutated.survive_mask <= 511
        assert 0 <= mutated.mut_bits <= 255
        assert 0 <= mutated.glyph_id < 14
        assert 0 <= mutated.color_id <= 15
        assert 1 <= mutated.age_max <= 255
    
    def test_get_glyph(self):
        """Тест получения глифа."""
        genetics = GeneticsEngine()
        
        assert genetics.get_glyph(0) == "."
        assert genetics.get_glyph(1) == "`"
        assert genetics.get_glyph(13) == "&"
        assert genetics.get_glyph(20) == "o"  # Циклический доступ
    
    def test_get_color_code(self):
        """Тест получения кода цвета."""
        genetics = GeneticsEngine()
        
        assert genetics.get_color_code(0) == "30"
        assert genetics.get_color_code(1) == "31"
        assert genetics.get_color_code(15) == "97"
        assert genetics.get_color_code(20) == "34"  # Циклический доступ
    
    def test_uniform_crossover(self):
        """Тест однородного кроссовера."""
        genetics = GeneticsEngine()
        rng = random.Random(42)
        
        result = genetics._uniform_crossover(0b1010, 0b0101, rng)
        assert 0 <= result <= 15  # 4 бита
    
    def test_flip_random_bit(self):
        """Тест инверсии случайного бита."""
        genetics = GeneticsEngine()
        rng = random.Random(42)
        
        original = 0b1010
        flipped = genetics._flip_random_bit(original, 4, rng)
        assert flipped != original
        assert Species._hamming_distance(original, flipped) == 1
    
    def test_mutate_mut_bits(self):
        """Тест мутации частоты мутаций."""
        genetics = GeneticsEngine()
        rng = random.Random(42)
        
        # Тест сдвига вверх
        result = genetics._mutate_mut_bits(5, rng)
        assert result in [4, 6]
        
        # Тест границ
        result = genetics._mutate_mut_bits(0, rng)
        assert result >= 0
        
        result = genetics._mutate_mut_bits(255, rng)
        assert result <= 255
    
    def test_mutate_glyph(self):
        """Тест мутации глифа."""
        genetics = GeneticsEngine(glyph_count=5)
        rng = random.Random(42)
        
        # Тест сдвига
        result = genetics._mutate_glyph(2, rng)
        assert 0 <= result < 5
        
        # Тест границ
        result = genetics._mutate_glyph(0, rng)
        assert 0 <= result < 5
        
        result = genetics._mutate_glyph(4, rng)
        assert 0 <= result < 5
    
    def test_mutate_color(self):
        """Тест мутации цвета."""
        genetics = GeneticsEngine()
        rng = random.Random(42)
        
        result = genetics._mutate_color(5, rng)
        assert 0 <= result <= 15
        
        # Тест границ
        result = genetics._mutate_color(0, rng)
        assert 0 <= result <= 15
        
        result = genetics._mutate_color(15, rng)
        assert 0 <= result <= 15
    
    def test_mutate_age_max(self):
        """Тест мутации максимального возраста."""
        genetics = GeneticsEngine()
        rng = random.Random(42)
        
        result = genetics._mutate_age_max(50, rng)
        assert 1 <= result <= 255
        assert abs(result - 50) <= 5
        
        # Тест границ
        result = genetics._mutate_age_max(1, rng)
        assert 1 <= result <= 255
        
        result = genetics._mutate_age_max(255, rng)
        assert 1 <= result <= 255
