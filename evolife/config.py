"""
Модуль конфигурации для эволюционной симуляции 'Жизнь'.

Содержит классы для чтения и управления конфигурационными параметрами.
"""

import os
import argparse
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

# Условные импорты для конфигурационных файлов
try:
    import toml
except ImportError:
    toml = None

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class Config:
    """Конфигурация симуляции."""
    # Основные параметры
    width: int = 120
    height: int = 60
    seed: Optional[int] = None
    fps: int = 30
    
    # Правила и генетика
    default_rule: str = "B3/S23"
    mutation_rate_multiplier: float = 1.0
    max_mutations_per_birth: int = 2
    species_hamming_threshold: int = 2
    age_max_default: int = 64
    catastrophe_probability: float = 0.0
    
    # Инициализация
    init_density: float = 0.15
    
    # Отображение
    color_enabled: bool = False
    empty_dot: bool = False
    
    # Файлы
    record_file: Optional[str] = None
    load_file: Optional[str] = None
    save_interval: int = 500
    
    # Дополнительные параметры
    glyph_count: int = 14
    mutation_enabled: bool = True
    
    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Загружает конфигурацию из файла."""
        config_dict = {}
        
        if filepath.endswith('.toml'):
            if toml is None:
                raise ImportError("toml не установлен. Установите: pip install toml")
            with open(filepath, 'r', encoding='utf-8') as f:
                config_dict = toml.load(f)
        elif filepath.endswith(('.yml', '.yaml')):
            if yaml is None:
                raise ImportError("pyyaml не установлен. Установите: pip install pyyaml")
            with open(filepath, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {filepath}")
        
        # Извлекаем параметры из секции [evolife] если есть
        if 'evolife' in config_dict:
            config_dict = config_dict['evolife']
        
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})
    
    def to_file(self, filepath: str) -> None:
        """Сохраняет конфигурацию в файл."""
        config_dict = {k: v for k, v in self.__dict__.items() if v is not None}
        
        if filepath.endswith('.toml'):
            if toml is None:
                raise ImportError("toml не установлен. Установите: pip install toml")
            with open(filepath, 'w', encoding='utf-8') as f:
                toml.dump({'evolife': config_dict}, f)
        elif filepath.endswith(('.yml', '.yaml')):
            if yaml is None:
                raise ImportError("pyyaml не установлен. Установите: pip install pyyaml")
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump({'evolife': config_dict}, f, default_flow_style=False)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {filepath}")
    
    def merge_with_args(self, args: argparse.Namespace) -> "Config":
        """Объединяет конфигурацию с аргументами командной строки."""
        new_config = Config()
        
        # Копируем текущие значения
        for key, value in self.__dict__.items():
            setattr(new_config, key, value)
        
        # Переопределяем значениями из аргументов
        for key, value in args.__dict__.items():
            if hasattr(new_config, key) and value is not None:
                setattr(new_config, key, value)
        
        return new_config


def create_default_config() -> Config:
    """Создает конфигурацию по умолчанию."""
    return Config()


def load_config(config_path: Optional[str] = None) -> Config:
    """Загружает конфигурацию из файла или создает по умолчанию."""
    if config_path and os.path.exists(config_path):
        return Config.from_file(config_path)
    
    # Пробуем найти конфигурационный файл в стандартных местах
    default_paths = [
        "config.toml",
        "config.yml",
        "config.yaml",
        os.path.expanduser("~/.evolife/config.toml"),
        os.path.expanduser("~/.evolife/config.yml")
    ]
    
    for path in default_paths:
        if os.path.exists(path):
            return Config.from_file(path)
    
    return create_default_config()


def create_argument_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Эволюционная симуляция 'Игра Жизнь' с мутациями в ASCII",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python -m evolife.main --width 160 --height 80 --mutation-rate 0 --fps 30
  python -m evolife.main --seed 42 --init-density 0.2 --mutation-rate 0.02 --color --fps 20
  python -m evolife.main --age-max-default 32 --mutation-rate 0.01
  python -m evolife.main --species-hamming-threshold 0 --mutation-rate 0.005
        """
    )
    
    # Основные параметры
    parser.add_argument("--width", type=int, help="Ширина поля (по умолчанию: 120)")
    parser.add_argument("--height", type=int, help="Высота поля (по умолчанию: 60)")
    parser.add_argument("--seed", type=int, help="Семя для генератора случайных чисел")
    parser.add_argument("--fps", type=int, help="Частота кадров (по умолчанию: 30)")
    
    # Правила и генетика
    parser.add_argument("--default-rule", type=str, help="Правило по умолчанию (по умолчанию: B3/S23)")
    parser.add_argument("--mutation-rate", type=float, dest="mutation_rate_multiplier", 
                       help="Глобальный множитель частоты мутаций (по умолчанию: 1.0)")
    parser.add_argument("--max-mutations-per-birth", type=int, 
                       help="Максимум мутаций за рождение (по умолчанию: 2)")
    parser.add_argument("--species-hamming-threshold", type=int, 
                       help="Порог Хэмминга для видов (по умолчанию: 2)")
    parser.add_argument("--age-max-default", type=int, 
                       help="Максимальный возраст по умолчанию (по умолчанию: 64)")
    parser.add_argument("--catastrophe", type=float, dest="catastrophe_probability",
                       help="Вероятность катастрофы на клетку (по умолчанию: 0.0)")
    
    # Инициализация
    parser.add_argument("--init-density", type=float, 
                       help="Плотность начального заполнения (по умолчанию: 0.15)")
    
    # Отображение
    parser.add_argument("--color", action="store_true", dest="color_enabled",
                       help="Включить цветной режим")
    parser.add_argument("--empty-dot", action="store_true", 
                       help="Показывать точки вместо пробелов для пустых клеток")
    
    # Файлы
    parser.add_argument("--record", type=str, dest="record_file",
                       help="Файл для записи метрик (JSONL)")
    parser.add_argument("--load", type=str, dest="load_file",
                       help="Файл состояния для загрузки")
    parser.add_argument("--save-interval", type=int,
                       help="Интервал автосохранения в тиках (по умолчанию: 500)")
    
    # Дополнительные параметры
    parser.add_argument("--glyph-count", type=int,
                       help="Количество глифов в палитре (по умолчанию: 14)")
    parser.add_argument("--no-mutations", action="store_false", dest="mutation_enabled",
                       help="Отключить мутации")
    
    # Конфигурационные файлы
    parser.add_argument("--config", type=str,
                       help="Путь к конфигурационному файлу")
    parser.add_argument("--save-config", type=str,
                       help="Сохранить текущую конфигурацию в файл")
    
    return parser


def validate_config(config: Config) -> None:
    """Валидирует конфигурацию и выдает предупреждения."""
    if config.width < 10 or config.height < 10:
        raise ValueError("Размеры поля должны быть не менее 10x10")
    
    if config.fps < 1 or config.fps > 120:
        raise ValueError("FPS должен быть в диапазоне 1-120")
    
    if config.init_density < 0 or config.init_density > 1:
        raise ValueError("Плотность инициализации должна быть в диапазоне 0-1")
    
    if config.mutation_rate_multiplier < 0:
        raise ValueError("Множитель частоты мутаций не может быть отрицательным")
    
    if config.max_mutations_per_birth < 0:
        raise ValueError("Максимум мутаций за рождение не может быть отрицательным")
    
    if config.species_hamming_threshold < 0:
        raise ValueError("Порог Хэмминга не может быть отрицательным")
    
    if config.age_max_default < 1 or config.age_max_default > 255:
        raise ValueError("Максимальный возраст должен быть в диапазоне 1-255")
    
    if config.catastrophe_probability < 0 or config.catastrophe_probability > 1:
        raise ValueError("Вероятность катастрофы должна быть в диапазоне 0-1")
    
    if config.glyph_count < 1:
        raise ValueError("Количество глифов должно быть положительным")
    
    if config.save_interval < 1:
        raise ValueError("Интервал сохранения должен быть положительным")
