"""
Тесты для модуля рендеринга.
"""

import pytest
import numpy as np
from evolife.render import Renderer, RenderMode
from evolife.genetics import GeneticsEngine, Genome


class TestRenderer:
    """Тесты для класса Renderer."""
    
    def test_renderer_creation(self):
        """Тест создания рендерера."""
        genetics = GeneticsEngine()
        renderer = Renderer(50, 30, genetics, color_enabled=False, empty_dot=False, fps=30)
        
        assert renderer.width == 50
        assert renderer.height == 30
        assert renderer.genetics == genetics
        assert not renderer.color_enabled
        assert not renderer.empty_dot
        assert renderer.fps == 30
        assert renderer.mode == RenderMode.NORMAL
    
    def test_set_mode(self):
        """Тест установки режима отображения."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        renderer.set_mode(RenderMode.AGE)
        assert renderer.mode == RenderMode.AGE
        
        renderer.set_mode(RenderMode.SPECIES)
        assert renderer.mode == RenderMode.SPECIES
    
    def test_get_cell_char_normal(self):
        """Тест получения символа в обычном режиме."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        # Пустая клетка
        char = renderer._get_cell_char(5, 5, np.zeros((10, 10), dtype=bool), {}, {})
        assert char == " " or char == "."
        
        # Живая клетка
        cells = np.zeros((10, 10), dtype=bool)
        cells[5, 5] = True
        genomes = {(5, 5): Genome.default()}
        
        char = renderer._get_cell_char(5, 5, cells, genomes, {})
        assert char == "."  # Глиф из генома
    
    def test_get_cell_char_age(self):
        """Тест получения символа в режиме возраста."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        renderer.set_mode(RenderMode.AGE)
        
        cells = np.zeros((10, 10), dtype=bool)
        cells[5, 5] = True
        ages = {(5, 5): 8}  # Возраст 8
        
        char = renderer._get_cell_char(5, 5, cells, {}, ages)
        assert char in renderer.age_palette
    
    def test_get_cell_char_species(self):
        """Тест получения символа в режиме видов."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        renderer.set_mode(RenderMode.SPECIES)
        
        cells = np.zeros((10, 10), dtype=bool)
        cells[5, 5] = True
        genomes = {(5, 5): Genome.default()}
        
        char = renderer._get_cell_char(5, 5, cells, genomes, {})
        assert char == "."  # Глиф из генома
    
    def test_get_cell_char_density(self):
        """Тест получения символа в режиме плотности."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        renderer.set_mode(RenderMode.DENSITY)
        
        # Создаем паттерн с разной плотностью
        cells = np.zeros((10, 10), dtype=bool)
        cells[5, 5] = True  # Центральная клетка
        cells[4, 5] = True  # Сосед
        cells[6, 5] = True  # Сосед
        
        char = renderer._get_cell_char(5, 5, cells, {}, {})
        assert char in renderer.density_palette
    
    def test_get_normal_char(self):
        """Тест получения символа в обычном режиме."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        genome = Genome.default()
        char = renderer._get_normal_char(5, 5, {(5, 5): genome})
        assert char == genetics.get_glyph(genome.glyph_id)
    
    def test_get_age_char(self):
        """Тест получения символа возраста."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        char = renderer._get_age_char(5, 5, {(5, 5): 12})
        assert char in renderer.age_palette
        
        # Тест с большим возрастом
        char = renderer._get_age_char(5, 5, {(5, 5): 100})
        assert char in renderer.age_palette
    
    def test_get_species_char(self):
        """Тест получения символа вида."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        genome = Genome.default()
        char = renderer._get_species_char(5, 5, {(5, 5): genome})
        assert char == genetics.get_glyph(genome.glyph_id)
    
    def test_get_density_char(self):
        """Тест получения символа плотности."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        # Создаем паттерн с известной плотностью
        cells = np.zeros((10, 10), dtype=bool)
        cells[5, 5] = True  # Центральная клетка
        cells[4, 5] = True  # Сосед сверху
        cells[6, 5] = True  # Сосед снизу
        cells[5, 4] = True  # Сосед слева
        cells[5, 6] = True  # Сосед справа
        
        char = renderer._get_density_char(5, 5, cells)
        assert char in renderer.density_palette
    
    def test_add_status_panel(self):
        """Тест добавления панели статуса."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        stats = {
            'tick': 100,
            'alive': 50,
            'species': 3,
            'top_species': [(1, 20), (2, 15), (3, 10)]
        }
        
        renderer._add_status_panel(stats)
        
        # Проверяем, что панель добавлена
        assert len(renderer.buffer_lines) > renderer.height + 2
        status_line = renderer.buffer_lines[-1]
        assert "Tick:" in status_line
    
    def test_toggle_color(self):
        """Тест переключения цветного режима."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics, color_enabled=False)
        
        assert not renderer.color_enabled
        renderer.toggle_color()
        assert renderer.color_enabled
        renderer.toggle_color()
        assert not renderer.color_enabled
    
    def test_set_fps(self):
        """Тест установки частоты кадров."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics, fps=30)
        
        renderer.set_fps(60)
        assert renderer.fps == 60
        
        # Тест границ
        renderer.set_fps(0)
        assert renderer.fps == 1
        
        renderer.set_fps(200)
        assert renderer.fps == 120
    
    def test_get_supported_modes(self):
        """Тест получения поддерживаемых режимов."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        modes = renderer.get_supported_modes()
        assert len(modes) == len(RenderMode)
        assert all(mode in [m.value for m in RenderMode] for mode in modes)
    
    def test_render_overlay_info(self):
        """Тест отображения информации о клетке."""
        genetics = GeneticsEngine()
        renderer = Renderer(10, 10, genetics)
        
        # Пустая клетка
        renderer.render_overlay_info(5, 5, None)
        # Должно вывести информацию о пустой клетке
        
        # Живая клетка
        cell_info = {
            'genome': Genome.default(),
            'age': 10,
            'species_id': 1,
            'glyph': 'o',
            'color': '30'
        }
        renderer.render_overlay_info(5, 5, cell_info)
        # Должно вывести информацию о живой клетке


class TestRenderMode:
    """Тесты для перечисления RenderMode."""
    
    def test_render_mode_values(self):
        """Тест значений режимов отображения."""
        assert RenderMode.NORMAL.value == "normal"
        assert RenderMode.AGE.value == "age"
        assert RenderMode.SPECIES.value == "species"
        assert RenderMode.DENSITY.value == "density"
    
    def test_render_mode_enumeration(self):
        """Тест перечисления режимов."""
        modes = list(RenderMode)
        assert len(modes) == 4
        assert RenderMode.NORMAL in modes
        assert RenderMode.AGE in modes
        assert RenderMode.SPECIES in modes
        assert RenderMode.DENSITY in modes
