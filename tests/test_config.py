"""
Тесты для модуля конфигурации.
"""

import pytest
import tempfile
import os
from evolife.config import Config, create_argument_parser, load_config, validate_config


class TestConfig:
    """Тесты для класса Config."""
    
    def test_config_creation(self):
        """Тест создания конфигурации по умолчанию."""
        config = Config()
        
        assert config.width == 120
        assert config.height == 60
        assert config.seed is None
        assert config.fps == 30
        assert config.default_rule == "B3/S23"
        assert config.mutation_rate_multiplier == 1.0
        assert config.max_mutations_per_birth == 2
        assert config.species_hamming_threshold == 2
        assert config.age_max_default == 64
        assert config.catastrophe_probability == 0.0
        assert config.init_density == 0.15
        assert not config.color_enabled
        assert not config.empty_dot
        assert config.record_file is None
        assert config.load_file is None
        assert config.save_interval == 500
        assert config.glyph_count == 14
        assert config.mutation_enabled
    
    def test_config_from_file_toml(self):
        """Тест загрузки конфигурации из TOML файла."""
        toml_content = """
[evolife]
width = 100
height = 50
fps = 60
color_enabled = true
mutation_rate_multiplier = 2.0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = Config.from_file(f.name)
            
            assert config.width == 100
            assert config.height == 50
            assert config.fps == 60
            assert config.color_enabled
            assert config.mutation_rate_multiplier == 2.0
            
            # Остальные параметры должны быть по умолчанию
            assert config.seed is None
            assert config.default_rule == "B3/S23"
        
        os.unlink(f.name)
    
    def test_config_from_file_yaml(self):
        """Тест загрузки конфигурации из YAML файла."""
        yaml_content = """
evolife:
  width: 80
  height: 40
  fps: 45
  color_enabled: true
  mutation_rate_multiplier: 1.5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            config = Config.from_file(f.name)
            
            assert config.width == 80
            assert config.height == 40
            assert config.fps == 45
            assert config.color_enabled
            assert config.mutation_rate_multiplier == 1.5
        
        os.unlink(f.name)
    
    def test_config_to_file_toml(self):
        """Тест сохранения конфигурации в TOML файл."""
        config = Config(width=100, height=50, fps=60, color_enabled=True)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            config.to_file(f.name)
            
            # Читаем обратно
            loaded_config = Config.from_file(f.name)
            assert loaded_config.width == 100
            assert loaded_config.height == 50
            assert loaded_config.fps == 60
            assert loaded_config.color_enabled
        
        os.unlink(f.name)
    
    def test_config_to_file_yaml(self):
        """Тест сохранения конфигурации в YAML файл."""
        config = Config(width=80, height=40, fps=45, color_enabled=True)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config.to_file(f.name)
            
            # Читаем обратно
            loaded_config = Config.from_file(f.name)
            assert loaded_config.width == 80
            assert loaded_config.height == 40
            assert loaded_config.fps == 45
            assert loaded_config.color_enabled
        
        os.unlink(f.name)
    
    def test_config_merge_with_args(self):
        """Тест объединения конфигурации с аргументами."""
        config = Config(width=100, height=50, fps=30)
        
        # Создаем объект аргументов
        class Args:
            def __init__(self):
                self.width = 200
                self.height = None
                self.fps = 60
                self.seed = 42
        
        args = Args()
        merged_config = config.merge_with_args(args)
        
        assert merged_config.width == 200  # Переопределено
        assert merged_config.height == 50  # Осталось из оригинала
        assert merged_config.fps == 60  # Переопределено
        assert merged_config.seed == 42  # Добавлено


class TestArgumentParser:
    """Тесты для парсера аргументов."""
    
    def test_parser_creation(self):
        """Тест создания парсера аргументов."""
        parser = create_argument_parser()
        assert parser is not None
    
    def test_parser_help(self):
        """Тест справки парсера."""
        parser = create_argument_parser()
        help_text = parser.format_help()
        
        assert "Эволюционная симуляция" in help_text
        assert "--width" in help_text
        assert "--height" in help_text
        assert "--fps" in help_text
        assert "--color" in help_text
        assert "--mutation-rate" in help_text
    
    def test_parser_parse_args(self):
        """Тест парсинга аргументов."""
        parser = create_argument_parser()
        
        args = parser.parse_args(["--width", "100", "--height", "50", "--fps", "60"])
        
        assert args.width == 100
        assert args.height == 50
        assert args.fps == 60
        assert not args.color_enabled  # По умолчанию False
    
    def test_parser_parse_all_args(self):
        """Тест парсинга всех аргументов."""
        parser = create_argument_parser()
        
        args = parser.parse_args([
            "--width", "100",
            "--height", "50",
            "--seed", "42",
            "--fps", "60",
            "--default-rule", "B3/S23",
            "--mutation-rate", "2.0",
            "--max-mutations-per-birth", "3",
            "--species-hamming-threshold", "1",
            "--age-max-default", "32",
            "--catastrophe", "0.01",
            "--init-density", "0.2",
            "--color",
            "--empty-dot",
            "--record", "metrics.jsonl",
            "--load", "state.bin",
            "--save-interval", "1000",
            "--glyph-count", "20",
            "--no-mutations"
        ])
        
        assert args.width == 100
        assert args.height == 50
        assert args.seed == 42
        assert args.fps == 60
        assert args.default_rule == "B3/S23"
        assert args.mutation_rate_multiplier == 2.0
        assert args.max_mutations_per_birth == 3
        assert args.species_hamming_threshold == 1
        assert args.age_max_default == 32
        assert args.catastrophe_probability == 0.01
        assert args.init_density == 0.2
        assert args.color_enabled
        assert args.empty_dot
        assert args.record_file == "metrics.jsonl"
        assert args.load_file == "state.bin"
        assert args.save_interval == 1000
        assert args.glyph_count == 20
        assert not args.mutation_enabled


class TestConfigValidation:
    """Тесты для валидации конфигурации."""
    
    def test_validate_config_valid(self):
        """Тест валидации корректной конфигурации."""
        config = Config(width=100, height=50, fps=30, init_density=0.1)
        
        # Не должно вызывать исключений
        validate_config(config)
    
    def test_validate_config_invalid_width(self):
        """Тест валидации некорректной ширины."""
        config = Config(width=5, height=50)
        
        with pytest.raises(ValueError, match="Размеры поля должны быть не менее 10x10"):
            validate_config(config)
    
    def test_validate_config_invalid_height(self):
        """Тест валидации некорректной высоты."""
        config = Config(width=100, height=5)
        
        with pytest.raises(ValueError, match="Размеры поля должны быть не менее 10x10"):
            validate_config(config)
    
    def test_validate_config_invalid_fps(self):
        """Тест валидации некорректного FPS."""
        config = Config(fps=0)
        
        with pytest.raises(ValueError, match="FPS должен быть в диапазоне 1-120"):
            validate_config(config)
        
        config = Config(fps=200)
        
        with pytest.raises(ValueError, match="FPS должен быть в диапазоне 1-120"):
            validate_config(config)
    
    def test_validate_config_invalid_density(self):
        """Тест валидации некорректной плотности."""
        config = Config(init_density=-0.1)
        
        with pytest.raises(ValueError, match="Плотность инициализации должна быть в диапазоне 0-1"):
            validate_config(config)
        
        config = Config(init_density=1.5)
        
        with pytest.raises(ValueError, match="Плотность инициализации должна быть в диапазоне 0-1"):
            validate_config(config)
    
    def test_validate_config_invalid_mutation_rate(self):
        """Тест валидации некорректной частоты мутаций."""
        config = Config(mutation_rate_multiplier=-1.0)
        
        with pytest.raises(ValueError, match="Множитель частоты мутаций не может быть отрицательным"):
            validate_config(config)
    
    def test_validate_config_invalid_max_mutations(self):
        """Тест валидации некорректного максимума мутаций."""
        config = Config(max_mutations_per_birth=-1)
        
        with pytest.raises(ValueError, match="Максимум мутаций за рождение не может быть отрицательным"):
            validate_config(config)
    
    def test_validate_config_invalid_hamming_threshold(self):
        """Тест валидации некорректного порога Хэмминга."""
        config = Config(species_hamming_threshold=-1)
        
        with pytest.raises(ValueError, match="Порог Хэмминга не может быть отрицательным"):
            validate_config(config)
    
    def test_validate_config_invalid_age_max(self):
        """Тест валидации некорректного максимального возраста."""
        config = Config(age_max_default=0)
        
        with pytest.raises(ValueError, match="Максимальный возраст должен быть в диапазоне 1-255"):
            validate_config(config)
        
        config = Config(age_max_default=300)
        
        with pytest.raises(ValueError, match="Максимальный возраст должен быть в диапазоне 1-255"):
            validate_config(config)
    
    def test_validate_config_invalid_catastrophe_probability(self):
        """Тест валидации некорректной вероятности катастрофы."""
        config = Config(catastrophe_probability=-0.1)
        
        with pytest.raises(ValueError, match="Вероятность катастрофы должна быть в диапазоне 0-1"):
            validate_config(config)
        
        config = Config(catastrophe_probability=1.5)
        
        with pytest.raises(ValueError, match="Вероятность катастрофы должна быть в диапазоне 0-1"):
            validate_config(config)
    
    def test_validate_config_invalid_glyph_count(self):
        """Тест валидации некорректного количества глифов."""
        config = Config(glyph_count=0)
        
        with pytest.raises(ValueError, match="Количество глифов должно быть положительным"):
            validate_config(config)
    
    def test_validate_config_invalid_save_interval(self):
        """Тест валидации некорректного интервала сохранения."""
        config = Config(save_interval=0)
        
        with pytest.raises(ValueError, match="Интервал сохранения должен быть положительным"):
            validate_config(config)
