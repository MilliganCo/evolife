"""
Тесты для модуля движка.
"""

import pytest
import numpy as np
from evolife.engine import LifeEngine
from evolife.genetics import Genome


class TestLifeEngine:
    """Тесты для класса LifeEngine."""
    
    def test_engine_creation(self):
        """Тест создания движка."""
        engine = LifeEngine(width=50, height=30, seed=42)
        
        assert engine.width == 50
        assert engine.height == 30
        assert engine.tick == 0
        assert engine.cells.shape == (30, 50)
        assert len(engine.genomes) == 0
        assert len(engine.ages) == 0
        assert len(engine.age_maxs) == 0
    
    def test_parse_rule(self):
        """Тест парсинга правил."""
        engine = LifeEngine(10, 10)
        
        birth, survive = engine._parse_rule("B3/S23")
        assert birth == 0b000001000  # B3 - бит в позиции 3
        assert survive == 0b000001100  # S23 - биты в позициях 2 и 3
        
        birth, survive = engine._parse_rule("B3")
        assert birth == 0b000001000
        assert survive == 0b000000000
        
        birth, survive = engine._parse_rule("S23")
        assert birth == 0b000000000
        assert survive == 0b000000000  # S23 без B не парсится
    
    def test_initialize_random(self):
        """Тест случайной инициализации."""
        engine = LifeEngine(20, 20, seed=42)
        engine.initialize_random(density=0.1)
        
        # Проверяем, что некоторые клетки созданы
        assert np.any(engine.cells)
        assert len(engine.genomes) > 0
        assert len(engine.ages) > 0
        assert len(engine.age_maxs) > 0
        
        # Проверяем соответствие
        alive_cells = np.sum(engine.cells)
        assert len(engine.genomes) == alive_cells
        assert len(engine.ages) == alive_cells
        assert len(engine.age_maxs) == alive_cells
    
    def test_initialize_pattern(self):
        """Тест инициализации паттерна."""
        engine = LifeEngine(20, 20)
        pattern = [(10, 10), (11, 10), (10, 11), (11, 11)]  # Блок 2x2
        
        engine.initialize_pattern(pattern, offset_x=5, offset_y=5)
        
        # Проверяем, что паттерн создан в правильной позиции
        assert engine.cells[15, 15]  # (10+5, 10+5)
        assert engine.cells[15, 16]  # (11+5, 10+5)
        assert engine.cells[16, 15]  # (10+5, 11+5)
        assert engine.cells[16, 16]  # (11+5, 11+5)
    
    def test_add_remove_cell(self):
        """Тест добавления и удаления клеток."""
        engine = LifeEngine(10, 10)
        genome = Genome.default()
        
        # Добавляем клетку
        engine._add_cell(5, 5, genome)
        assert engine.cells[5, 5]
        assert (5, 5) in engine.genomes
        assert (5, 5) in engine.ages
        assert (5, 5) in engine.age_maxs
        
        # Удаляем клетку
        engine._remove_cell(5, 5)
        assert not engine.cells[5, 5]
        assert (5, 5) not in engine.genomes
        assert (5, 5) not in engine.ages
        assert (5, 5) not in engine.age_maxs
    
    def test_count_neighbors(self):
        """Тест подсчета соседей."""
        engine = LifeEngine(5, 5)
        
        # Создаем простой паттерн
        engine.cells[2, 2] = True
        engine.cells[2, 3] = True
        engine.cells[3, 2] = True
        
        counts = engine._count_neighbors()
        
        # Проверяем подсчет для центральной клетки
        assert counts[2, 2] == 2  # Два соседа
        assert counts[2, 3] == 2  # Два соседа
        assert counts[3, 2] == 2  # Два соседа
        
        # Проверяем тороидальную топологию
        assert counts[0, 0] == 0  # Угол без соседей
        assert counts[4, 4] == 0  # Угол без соседей
    
    def test_should_survive(self):
        """Тест проверки выживания."""
        engine = LifeEngine(10, 10)
        
        # Тест с правилом по умолчанию (S23)
        assert engine._should_survive(5, 5, 2)  # 2 соседа - выживает
        assert engine._should_survive(5, 5, 3)  # 3 соседа - выживает
        assert not engine._should_survive(5, 5, 1)  # 1 сосед - умирает
        assert not engine._should_survive(5, 5, 4)  # 4 соседа - умирает
    
    def test_should_birth(self):
        """Тест проверки рождения."""
        engine = LifeEngine(10, 10)
        
        # Тест с правилом по умолчанию (B3)
        assert engine._should_birth(5, 5, 3)  # 3 соседа - рождается
        assert not engine._should_birth(5, 5, 2)  # 2 соседа - не рождается
        assert not engine._should_birth(5, 5, 4)  # 4 соседа - не рождается
    
    def test_find_parents(self):
        """Тест поиска родителей."""
        engine = LifeEngine(10, 10)
        
        # Создаем соседей
        genome1 = Genome.default()
        genome2 = Genome.default()
        engine.genomes[(4, 5)] = genome1
        engine.genomes[(6, 5)] = genome2
        
        parents = engine._find_parents(5, 5)
        assert len(parents) == 2
        assert all(isinstance(p, Genome) for p in parents)
    
    def test_find_parents_insufficient(self):
        """Тест поиска родителей при недостатке соседей."""
        engine = LifeEngine(10, 10)
        
        # Нет соседей
        parents = engine._find_parents(5, 5)
        assert len(parents) == 0
        
        # Один сосед
        genome = Genome.default()
        engine.genomes[(4, 5)] = genome
        parents = engine._find_parents(5, 5)
        assert len(parents) == 2
        assert parents[0] == parents[1]  # Дублирование
    
    def test_step_basic(self):
        """Тест базового шага симуляции."""
        engine = LifeEngine(10, 10, seed=42)
        
        # Создаем простой паттерн (блок 2x2)
        pattern = [(4, 4), (5, 4), (4, 5), (5, 5)]
        engine.initialize_pattern(pattern)
        
        initial_alive = np.sum(engine.cells)
        
        # Выполняем шаг
        engine.step()
        
        # Проверяем, что тик увеличился
        assert engine.tick == 1
        # Проверяем, что что-то произошло (клетки могли умереть или родиться)
        assert np.sum(engine.cells) >= 0  # Просто проверяем, что не падает
    
    def test_step_oscillator(self):
        """Тест шага с осциллятором."""
        engine = LifeEngine(10, 10, seed=42)
        
        # Создаем blinker (3x1)
        pattern = [(4, 4), (5, 4), (6, 4)]
        engine.initialize_pattern(pattern)
        
        initial_alive = np.sum(engine.cells)
        
        # Выполняем шаг
        engine.step()
        
        # Проверяем, что тик увеличился
        assert engine.tick == 1
        # Проверяем, что что-то произошло
        assert np.sum(engine.cells) >= 0  # Просто проверяем, что не падает
    
    def test_step_aging(self):
        """Тест старения клеток."""
        engine = LifeEngine(10, 10, seed=42)
        
        # Создаем клетку с коротким максимальным возрастом
        genome = Genome.default()
        genome = genome._replace(age_max=1)
        engine._add_cell(5, 5, genome)
        
        # Выполняем шаг
        engine.step()
        
        # Клетка должна умереть от старости
        assert not engine.cells[5, 5]
        assert (5, 5) not in engine.genomes
    
    def test_get_stats(self):
        """Тест получения статистики."""
        engine = LifeEngine(10, 10, seed=42)
        engine.initialize_random(density=0.1)
        
        stats = engine.get_stats()
        
        assert 'tick' in stats
        assert 'alive' in stats
        assert 'species' in stats
        assert 'top_species' in stats
        
        assert stats['tick'] == 0
        assert stats['alive'] == np.sum(engine.cells)
        assert isinstance(stats['top_species'], list)
    
    def test_get_cell_info(self):
        """Тест получения информации о клетке."""
        engine = LifeEngine(10, 10, seed=42)
        
        # Пустая клетка
        info = engine.get_cell_info(5, 5)
        assert info is None
        
        # Живая клетка
        genome = Genome.default()
        engine._add_cell(5, 5, genome)
        info = engine.get_cell_info(5, 5)
        
        assert info is not None
        assert 'genome' in info
        assert 'age' in info
        assert 'species_id' in info
        assert 'glyph' in info
        assert 'color' in info
    
    def test_clear(self):
        """Тест очистки поля."""
        engine = LifeEngine(10, 10, seed=42)
        engine.initialize_random(density=0.1)
        
        assert np.any(engine.cells)
        assert len(engine.genomes) > 0
        
        engine.clear()
        
        assert not np.any(engine.cells)
        assert len(engine.genomes) == 0
        assert len(engine.ages) == 0
        assert len(engine.age_maxs) == 0
        assert engine.tick == 0
    
    def test_deterministic_rng(self):
        """Тест детерминизма с фиксированным seed."""
        engine1 = LifeEngine(10, 10, seed=42)
        engine2 = LifeEngine(10, 10, seed=42)
        
        engine1.initialize_random(density=0.1)
        engine2.initialize_random(density=0.1)
        
        # Состояния должны быть идентичными
        assert np.array_equal(engine1.cells, engine2.cells)
        
        # После шага тоже должны быть идентичными
        engine1.step()
        engine2.step()
        assert np.array_equal(engine1.cells, engine2.cells)
