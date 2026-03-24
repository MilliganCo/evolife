"""
Модуль рендеринга для ASCII визуализации симуляции 'Жизнь'.

Содержит классы для отображения клеток, палитр, цветов и различных режимов просмотра.
"""

import os
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import numpy as np
from .genetics import GeneticsEngine


class RenderMode(Enum):
    """Режимы отображения."""
    NORMAL = "normal"
    AGE = "age"
    SPECIES = "species"
    DENSITY = "density"


class Renderer:
    """Класс для ASCII рендеринга симуляции."""
    
    def __init__(self, 
                 width: int, 
                 height: int,
                 genetics: GeneticsEngine,
                 color_enabled: bool = False,
                 empty_dot: bool = False,
                 fps: int = 30):
        self.width = width
        self.height = height
        self.genetics = genetics
        self.color_enabled = color_enabled
        self.empty_dot = empty_dot
        self.fps = fps
        self.mode = RenderMode.NORMAL
        
        # ANSI escape коды
        self.ANSI_CLEAR = "\033[2J"
        self.ANSI_HOME = "\033[H"
        self.ANSI_RESET = "\033[0m"
        self.ANSI_BOLD = "\033[1m"
        
        # Палитра для отображения возраста
        self.age_palette = [".", "`", "'", "^", "*", "+", "o", "x", "O", "X", "#", "@", "%", "&"]
        
        # Палитра для отображения плотности
        self.density_palette = [" ", ".", ":", ";", "=", "+", "*", "#", "%", "@"]
        
        # Буферы для двойной буферизации
        self.buffer_lines: List[str] = []
        self._init_buffers()

    def _init_buffers(self) -> None:
        """Инициализирует буферы для рендеринга."""
        self.buffer_lines = [""] * (self.height + 2)  # +2 для границ

    def clear_screen(self) -> None:
        """Очищает экран."""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/macOS
            print(self.ANSI_CLEAR + self.ANSI_HOME, end='')

    def set_mode(self, mode: RenderMode) -> None:
        """Устанавливает режим отображения."""
        self.mode = mode

    def render(self, 
               cells: np.ndarray, 
               genomes: Dict[Tuple[int, int], Any],
               ages: Dict[Tuple[int, int], int],
               stats: Dict[str, Any]) -> None:
        """Рендерит текущее состояние симуляции."""
        self._build_frame(cells, genomes, ages, stats)
        self._display_frame()

    def _build_frame(self, 
                    cells: np.ndarray, 
                    genomes: Dict[Tuple[int, int], Any],
                    ages: Dict[Tuple[int, int], int],
                    stats: Dict[str, Any]) -> None:
        """Строит кадр для отображения."""
        # Верхняя граница
        self.buffer_lines[0] = "┌" + "─" * self.width + "┐"
        
        # Основное поле
        for y in range(self.height):
            line = "│"
            for x in range(self.width):
                char = self._get_cell_char(x, y, cells, genomes, ages)
                line += char
            line += "│"
            self.buffer_lines[y + 1] = line
        
        # Нижняя граница
        self.buffer_lines[self.height + 1] = "└" + "─" * self.width + "┘"
        
        # Статусная панель
        self._add_status_panel(stats)

    def _get_cell_char(self, 
                      x: int, 
                      y: int, 
                      cells: np.ndarray, 
                      genomes: Dict[Tuple[int, int], Any],
                      ages: Dict[Tuple[int, int], int]) -> str:
        """Возвращает символ для отображения клетки."""
        if not cells[y, x]:
            return "." if self.empty_dot else " "
        
        if self.mode == RenderMode.NORMAL:
            return self._get_normal_char(x, y, genomes)
        elif self.mode == RenderMode.AGE:
            return self._get_age_char(x, y, ages)
        elif self.mode == RenderMode.SPECIES:
            return self._get_species_char(x, y, genomes)
        elif self.mode == RenderMode.DENSITY:
            return self._get_density_char(x, y, cells)
        else:
            return "?"

    def _get_normal_char(self, x: int, y: int, genomes: Dict[Tuple[int, int], Any]) -> str:
        """Возвращает символ в обычном режиме."""
        if (x, y) in genomes:
            genome = genomes[(x, y)]
            char = self.genetics.get_glyph(genome.glyph_id)
            if self.color_enabled:
                color_code = self.genetics.get_color_code(genome.color_id)
                return f"\033[{color_code}m{char}\033[0m"
            return char
        return "o"  # Fallback

    def _get_age_char(self, x: int, y: int, ages: Dict[Tuple[int, int], int]) -> str:
        """Возвращает символ в режиме отображения возраста."""
        age = ages.get((x, y), 0)
        char_index = min(age // 4, len(self.age_palette) - 1)
        char = self.age_palette[char_index]
        
        if self.color_enabled:
            # Цвет зависит от возраста
            color_index = min(age // 8, 15)
            color_code = self.genetics.color_palette[color_index % len(self.genetics.color_palette)]
            return f"\033[{color_code}m{char}\033[0m"
        
        return char

    def _get_species_char(self, x: int, y: int, genomes: Dict[Tuple[int, int], Any]) -> str:
        """Возвращает символ в режиме отображения видов."""
        if (x, y) in genomes:
            genome = genomes[(x, y)]
            # Используем глиф, но цвет зависит от вида
            char = self.genetics.get_glyph(genome.glyph_id)
            if self.color_enabled:
                # Цвет определяется хэшем масок
                species_hash = hash((genome.birth_mask, genome.survive_mask))
                color_index = species_hash % 16
                color_code = self.genetics.color_palette[color_index]
                return f"\033[{color_code}m{char}\033[0m"
            return char
        return "?"

    def _get_density_char(self, x: int, y: int, cells: np.ndarray) -> str:
        """Возвращает символ в режиме отображения плотности."""
        # Подсчитываем плотность в окрестности 3x3
        density = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                if cells[ny, nx]:
                    density += 1
        
        char_index = min(density, len(self.density_palette) - 1)
        char = self.density_palette[char_index]
        
        if self.color_enabled:
            # Цвет зависит от плотности
            color_index = min(density * 2, 15)
            color_code = self.genetics.color_palette[color_index % len(self.genetics.color_palette)]
            return f"\033[{color_code}m{char}\033[0m"
        
        return char

    def _add_status_panel(self, stats: Dict[str, Any]) -> None:
        """Добавляет панель статуса."""
        tick = stats.get("tick", 0)
        alive = stats.get("alive", 0)
        species = stats.get("species", 0)
        top_species = stats.get("top_species", [])
        
        status_line = f"Tick: {tick:6d} | Alive: {alive:6d} | Species: {species:3d} | FPS: {self.fps:2d}"
        
        if top_species:
            top_str = " | Top: " + ", ".join([f"S{species_id}({count})" for species_id, count in top_species[:3]])
            status_line += top_str
        
        # Обрезаем до ширины экрана
        max_width = self.width + 2
        if len(status_line) > max_width:
            status_line = status_line[:max_width - 3] + "..."
        
        self.buffer_lines.append(status_line)

    def _display_frame(self) -> None:
        """Отображает построенный кадр."""
        # Перемещаем курсор в начало
        print(self.ANSI_HOME, end='')
        
        # Выводим все строки
        for line in self.buffer_lines:
            print(line)
        
        # Очищаем остаток экрана
        remaining_lines = max(0, 25 - len(self.buffer_lines))  # Предполагаем 25 строк терминала
        for _ in range(remaining_lines):
            print(" " * (self.width + 2))

    def render_overlay_info(self, x: int, y: int, cell_info: Optional[Dict[str, Any]]) -> None:
        """Отображает информацию о клетке в позиции (x, y)."""
        if cell_info is None:
            print(f"Position ({x}, {y}): Empty")
        else:
            genome = cell_info["genome"]
            age = cell_info["age"]
            species_id = cell_info["species_id"]
            
            print(f"Position ({x}, {y}):")
            print(f"  Age: {age}")
            print(f"  Species: {species_id}")
            print(f"  Birth mask: {bin(genome.birth_mask)}")
            print(f"  Survive mask: {bin(genome.survive_mask)}")
            print(f"  Mutation rate: {genome.mutation_rate:.3f}")
            print(f"  Max age: {genome.age_max}")
            print(f"  Glyph: {cell_info['glyph']}")
            print(f"  Color: {cell_info['color']}")

    def get_supported_modes(self) -> List[str]:
        """Возвращает список поддерживаемых режимов отображения."""
        return [mode.value for mode in RenderMode]

    def toggle_color(self) -> None:
        """Переключает цветной режим."""
        self.color_enabled = not self.color_enabled

    def set_fps(self, fps: int) -> None:
        """Устанавливает частоту кадров."""
        self.fps = max(1, min(120, fps))  # Ограничиваем 1-120 FPS
