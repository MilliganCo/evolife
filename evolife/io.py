"""
Модуль ввода-вывода для эволюционной симуляции 'Жизнь'.

Содержит функции для сохранения/загрузки состояний, импорта паттернов и записи метрик.
"""

import json
import pickle
import struct
import zlib
import io
from typing import Dict, List, Tuple, Optional, BinaryIO
import numpy as np
from .genetics import Genome


class StateFormat:
    """Формат для сериализации состояния симуляции."""
    
    VERSION = 1
    MAGIC = b"EVOLIFE"
    
    @staticmethod
    def save_state(filepath: str, 
                   cells: np.ndarray, 
                   genomes: Dict[Tuple[int, int], Genome],
                   ages: Dict[Tuple[int, int], int],
                   age_maxs: Dict[Tuple[int, int], int],
                   tick: int,
                   rng_state: tuple,
                   compress: bool = True) -> None:
        """Сохраняет состояние симуляции в файл."""
        with open(filepath, 'wb') as f:
            # Заголовок
            f.write(StateFormat.MAGIC)
            f.write(struct.pack('<I', StateFormat.VERSION))
            
            # Размеры поля
            height, width = cells.shape
            f.write(struct.pack('<II', width, height))
            
            # Тик и состояние RNG
            f.write(struct.pack('<I', tick))
            rng_data = pickle.dumps(rng_state)
            f.write(struct.pack('<I', len(rng_data)))
            f.write(rng_data)
            
            # Матрица клеток
            cells_data = cells.astype(np.uint8).tobytes()
            f.write(struct.pack('<I', len(cells_data)))
            f.write(cells_data)
            
            # Геномы
            genomes_data = pickle.dumps(genomes)
            f.write(struct.pack('<I', len(genomes_data)))
            f.write(genomes_data)
            
            # Возрасты
            ages_data = pickle.dumps(ages)
            f.write(struct.pack('<I', len(ages_data)))
            f.write(ages_data)
            
            # Максимальные возрасты
            age_maxs_data = pickle.dumps(age_maxs)
            f.write(struct.pack('<I', len(age_maxs_data)))
            f.write(age_maxs_data)
            
            # Сжатие всего файла если нужно
            if compress:
                f.seek(0)
                data = f.read()
                f.seek(0)
                f.truncate()
                compressed = zlib.compress(data)
                f.write(StateFormat.MAGIC)
                f.write(struct.pack('<I', StateFormat.VERSION | 0x80000000))  # Флаг сжатия
                f.write(struct.pack('<I', len(compressed)))
                f.write(compressed)
    
    @staticmethod
    def load_state(filepath: str) -> Tuple[np.ndarray, Dict[Tuple[int, int], Genome], 
                                         Dict[Tuple[int, int], int], Dict[Tuple[int, int], int], 
                                         int, tuple]:
        """Загружает состояние симуляции из файла."""
        with open(filepath, 'rb') as f:
            # Проверяем магическое число
            magic = f.read(len(StateFormat.MAGIC))
            if magic != StateFormat.MAGIC:
                raise ValueError("Неверный формат файла")
            
            # Версия
            version = struct.unpack('<I', f.read(4))[0]
            compressed = bool(version & 0x80000000)
            version &= 0x7FFFFFFF
            
            if version != StateFormat.VERSION:
                raise ValueError(f"Неподдерживаемая версия файла: {version}")
            
            # Если сжато, распаковываем
            if compressed:
                compressed_size = struct.unpack('<I', f.read(4))[0]
                compressed_data = f.read(compressed_size)
                data = zlib.decompress(compressed_data)
                f = io.BytesIO(data)
                f.read(len(StateFormat.MAGIC))  # Пропускаем магическое число
                version = struct.unpack('<I', f.read(4))[0]
            
            # Размеры поля
            width, height = struct.unpack('<II', f.read(8))
            
            # Тик и состояние RNG
            tick = struct.unpack('<I', f.read(4))[0]
            rng_data_size = struct.unpack('<I', f.read(4))[0]
            rng_data = f.read(rng_data_size)
            rng_state = pickle.loads(rng_data)
            
            # Матрица клеток
            cells_data_size = struct.unpack('<I', f.read(4))[0]
            cells_data = f.read(cells_data_size)
            cells = np.frombuffer(cells_data, dtype=np.uint8).reshape(height, width).astype(bool)
            
            # Геномы
            genomes_data_size = struct.unpack('<I', f.read(4))[0]
            genomes_data = f.read(genomes_data_size)
            genomes = pickle.loads(genomes_data)
            
            # Возрасты
            ages_data_size = struct.unpack('<I', f.read(4))[0]
            ages_data = f.read(ages_data_size)
            ages = pickle.loads(ages_data)
            
            # Максимальные возрасты
            age_maxs_data_size = struct.unpack('<I', f.read(4))[0]
            age_maxs_data = f.read(age_maxs_data_size)
            age_maxs = pickle.loads(age_maxs_data)
            
            return cells, genomes, ages, age_maxs, tick, rng_state


class MetricsRecorder:
    """Класс для записи метрик симуляции."""
    
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath
        self.file: Optional[BinaryIO] = None
        if filepath:
            self.file = open(filepath, 'w', encoding='utf-8')
    
    def record(self, tick: int, alive: int, species: int, 
              top_species: List[Tuple[int, int]], entropy: float) -> None:
        """Записывает метрики для текущего тика."""
        if not self.file:
            return
        
        data = {
            "t": tick,
            "alive": alive,
            "species": species,
            "top": [[mask_pair, count] for mask_pair, count in top_species],
            "entropy": entropy
        }
        
        self.file.write(json.dumps(data) + '\n')
        self.file.flush()
    
    def close(self) -> None:
        """Закрывает файл метрик."""
        if self.file:
            self.file.close()
            self.file = None


class PatternImporter:
    """Класс для импорта паттернов из различных форматов."""
    
    @staticmethod
    def import_rle(filepath: str) -> List[Tuple[int, int]]:
        """Импортирует паттерн из файла RLE (Run Length Encoded)."""
        pattern = []
        x, y = 0, 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Пропускаем комментарии и заголовки
        data_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('x'):
                data_lines.append(line)
        
        # Парсим данные
        data = ''.join(data_lines)
        i = 0
        count = 0
        
        while i < len(data):
            char = data[i]
            
            if char.isdigit():
                # Собираем число
                count_str = ''
                while i < len(data) and data[i].isdigit():
                    count_str += data[i]
                    i += 1
                count = int(count_str)
            else:
                if char == 'b':
                    # Пустая клетка
                    x += count if count > 0 else 1
                    count = 0
                elif char == 'o':
                    # Живая клетка
                    for _ in range(count if count > 0 else 1):
                        pattern.append((x, y))
                        x += 1
                    count = 0
                elif char == '$':
                    # Конец строки
                    x = 0
                    y += count if count > 0 else 1
                    count = 0
                elif char == '!':
                    # Конец паттерна
                    break
                else:
                    i += 1
                    continue
                i += 1
        
        return pattern
    
    @staticmethod
    def import_lif(filepath: str) -> List[Tuple[int, int]]:
        """Импортирует паттерн из файла LIF (Life 1.05/1.06)."""
        pattern = []
        x, y = 0, 0
        in_pattern = False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('#P'):
                    # Позиция паттерна
                    parts = line.split()
                    if len(parts) >= 3:
                        x = int(parts[1])
                        y = int(parts[2])
                    in_pattern = True
                elif line.startswith('#') or not line:
                    # Комментарий или пустая строка
                    continue
                elif in_pattern:
                    # Строка паттерна
                    for i, char in enumerate(line):
                        if char == '*':
                            pattern.append((x + i, y))
                    y += 1
        
        return pattern
    
    @staticmethod
    def import_pattern(filepath: str) -> List[Tuple[int, int]]:
        """Импортирует паттерн из файла (автоопределение формата)."""
        if filepath.endswith('.rle'):
            return PatternImporter.import_rle(filepath)
        elif filepath.endswith(('.lif', '.life')):
            return PatternImporter.import_lif(filepath)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {filepath}")


def save_snapshot(filepath: str, cells: np.ndarray, 
                 genomes: Dict[Tuple[int, int], Genome],
                 ages: Dict[Tuple[int, int], int]) -> None:
    """Сохраняет снимок состояния в текстовом формате."""
    height, width = cells.shape
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Evolife Snapshot - {width}x{height}\n")
        f.write(f"# Generated at tick: {len(genomes)}\n\n")
        
        for y in range(height):
            line = ""
            for x in range(width):
                if cells[y, x]:
                    if (x, y) in genomes:
                        genome = genomes[(x, y)]
                        char = genome.glyph_id % 14  # Используем индекс глифа
                        line += chr(ord('.') + char)
                    else:
                        line += "o"
                else:
                    line += "."
            f.write(line + "\n")


def load_snapshot(filepath: str) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
    """Загружает снимок состояния из текстового формата."""
    pattern = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Пропускаем комментарии
    data_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            data_lines.append(line)
    
    if not data_lines:
        return np.zeros((1, 1), dtype=bool), []
    
    height = len(data_lines)
    width = len(data_lines[0])
    
    cells = np.zeros((height, width), dtype=bool)
    
    for y, line in enumerate(data_lines):
        for x, char in enumerate(line):
            if char != '.':
                cells[y, x] = True
                pattern.append((x, y))
    
    return cells, pattern
