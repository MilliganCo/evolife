"""
Модуль командной строки для эволюционной симуляции 'Жизнь'.

Содержит основной цикл симуляции и обработку пользовательского ввода.
"""

import sys
import time
import threading
from typing import Dict, Any
import msvcrt  # Для Windows
import select  # Для Unix/Linux
from .config import Config, create_argument_parser, load_config, validate_config
from .engine import LifeEngine
from .render import Renderer, RenderMode
from .io import StateFormat, MetricsRecorder
from .metrics import calculate_diversity_metrics
from .genetics import Genome


class SimulationController:
    """Контроллер симуляции с обработкой пользовательского ввода."""
    
    def __init__(self, config: Config):
        self.config = config
        self.engine = LifeEngine(
            width=config.width,
            height=config.height,
            seed=config.seed,
            default_rule=config.default_rule,
            mutation_rate_multiplier=config.mutation_rate_multiplier,
            max_mutations_per_birth=config.max_mutations_per_birth,
            species_hamming_threshold=config.species_hamming_threshold,
            age_max_default=config.age_max_default,
            catastrophe_probability=config.catastrophe_probability
        )
        
        self.renderer = Renderer(
            width=config.width,
            height=config.height,
            genetics=self.engine.genetics,
            color_enabled=config.color_enabled,
            empty_dot=config.empty_dot,
            fps=config.fps
        )
        
        self.metrics_recorder = MetricsRecorder(config.record_file)
        self.running = False
        self.paused = False
        self.step_mode = False
        self.last_stats = None
        
        # Загружаем начальное состояние
        if config.load_file:
            self.load_state(config.load_file)
        else:
            self.engine.initialize_random(config.init_density)
    
    def run(self) -> None:
        """Запускает основной цикл симуляции."""
        self.running = True
        self.renderer.clear_screen()
        
        # Запускаем поток для обработки ввода
        input_thread = threading.Thread(target=self._input_handler, daemon=True)
        input_thread.start()
        
        try:
            while self.running:
                if not self.paused or self.step_mode:
                    self._update_simulation()
                    self.step_mode = False
                
                self._render_frame()
                self._sleep()
                
        except KeyboardInterrupt:
            self.running = False
        finally:
            self._cleanup()
    
    def _update_simulation(self) -> None:
        """Обновляет состояние симуляции."""
        self.engine.step()
        
        # Записываем метрики
        if self.metrics_recorder.file:
            stats = self.engine.get_stats()
            diversity_metrics = calculate_diversity_metrics(self.engine.species.species_counts)
            self.metrics_recorder.record(
                tick=stats['tick'],
                alive=stats['alive'],
                species=stats['species'],
                top_species=stats['top_species'],
                entropy=diversity_metrics['entropy']
            )
        
        # Автосохранение
        if (self.config.save_interval > 0 and 
            self.engine.tick % self.config.save_interval == 0 and 
            self.engine.tick > 0):
            self.save_state(f"autosave_{self.engine.tick}.bin")
    
    def _render_frame(self) -> None:
        """Рендерит текущий кадр."""
        stats = self.engine.get_stats()
        self.renderer.render(
            cells=self.engine.cells,
            genomes=self.engine.genomes,
            ages=self.engine.ages,
            stats=stats
        )
        self.last_stats = stats
    
    def _sleep(self) -> None:
        """Ожидание между кадрами."""
        if not self.paused:
            time.sleep(1.0 / self.renderer.fps)
    
    def _input_handler(self) -> None:
        """Обработчик пользовательского ввода."""
        while self.running:
            try:
                if self._has_input():
                    key = self._get_key()
                    self._handle_key(key)
            except Exception as e:
                print(f"Ошибка ввода: {e}")
                time.sleep(0.1)
    
    def _has_input(self) -> bool:
        """Проверяет наличие ввода."""
        if sys.platform == 'win32':
            return msvcrt.kbhit()
        else:
            return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    
    def _get_key(self) -> str:
        """Получает нажатую клавишу."""
        if sys.platform == 'win32':
            return msvcrt.getch().decode('utf-8', errors='ignore')
        else:
            return sys.stdin.read(1)
    
    def _handle_key(self, key: str) -> None:
        """Обрабатывает нажатую клавишу."""
        key = key.lower()
        
        if key == 'q':
            self.running = False
        elif key == ' ':
            self.paused = not self.paused
        elif key == '.':
            self.step_mode = True
        elif key == '+':
            self.renderer.set_fps(min(120, self.renderer.fps + 5))
        elif key == '-':
            self.renderer.set_fps(max(1, self.renderer.fps - 5))
        elif key == 'r':
            self._randomize_area()
        elif key == 'm':
            self._toggle_mutations()
        elif key == 's':
            self.save_state("manual_save.bin")
        elif key == 'l':
            self.load_state("manual_save.bin")
        elif key == 'a':
            self._cycle_render_mode()
        elif key == 'c':
            self.renderer.toggle_color()
        elif key == 'i':
            self._show_info()
        elif key == 'h':
            self._show_help()
    
    def _randomize_area(self) -> None:
        """Случайно заполняет область."""
        import random
        center_x = self.config.width // 2
        center_y = self.config.height // 2
        size = 20
        
        for y in range(center_y - size//2, center_y + size//2):
            for x in range(center_x - size//2, center_x + size//2):
                if (0 <= x < self.config.width and 
                    0 <= y < self.config.height and 
                    random.random() < 0.3):
                    self.engine._add_cell(x, y, Genome.random(self.engine.rng))
    
    def _toggle_mutations(self) -> None:
        """Переключает мутации."""
        if self.engine.genetics.mutation_rate_multiplier > 0:
            self.engine.genetics.mutation_rate_multiplier = 0
            print("Мутации отключены")
        else:
            self.engine.genetics.mutation_rate_multiplier = 1.0
            print("Мутации включены")
    
    def _cycle_render_mode(self) -> None:
        """Переключает режим отображения."""
        modes = list(RenderMode)
        current_index = modes.index(self.renderer.mode)
        next_index = (current_index + 1) % len(modes)
        self.renderer.set_mode(modes[next_index])
        print(f"Режим: {modes[next_index].value}")
    
    def _show_info(self) -> None:
        """Показывает информацию о симуляции."""
        if self.last_stats:
            print(f"\n=== ИНФОРМАЦИЯ ===")
            print(f"Тик: {self.last_stats['tick']}")
            print(f"Живых клеток: {self.last_stats['alive']}")
            print(f"Видов: {self.last_stats['species']}")
            print(f"FPS: {self.renderer.fps}")
            print(f"Режим: {self.renderer.mode.value}")
            print(f"Цвета: {'включены' if self.renderer.color_enabled else 'выключены'}")
            print(f"Мутации: {'включены' if self.engine.genetics.mutation_rate_multiplier > 0 else 'выключены'}")
    
    def _show_help(self) -> None:
        """Показывает справку по управлению."""
        help_text = """
=== УПРАВЛЕНИЕ ===
Пробел    - Пауза/продолжить
.         - Один шаг
+/-       - Ускорить/замедлить
r         - Случайная область
m         - Включить/выключить мутации
s         - Сохранить состояние
l         - Загрузить состояние
a         - Переключить режим отображения
c         - Переключить цвета
i         - Показать информацию
h         - Показать эту справку
q         - Выход
        """
        print(help_text)
    
    def save_state(self, filepath: str) -> None:
        """Сохраняет состояние симуляции."""
        try:
            StateFormat.save_state(
                filepath=filepath,
                cells=self.engine.cells,
                genomes=self.engine.genomes,
                ages=self.engine.ages,
                age_maxs=self.engine.age_maxs,
                tick=self.engine.tick,
                rng_state=self.engine.rng.getstate(),
                compress=True
            )
            print(f"Состояние сохранено в {filepath}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def load_state(self, filepath: str) -> None:
        """Загружает состояние симуляции."""
        try:
            cells, genomes, ages, age_maxs, tick, rng_state = StateFormat.load_state(filepath)
            self.engine.cells = cells
            self.engine.genomes = genomes
            self.engine.ages = ages
            self.engine.age_maxs = age_maxs
            self.engine.tick = tick
            self.engine.rng.setstate(rng_state)
            print(f"Состояние загружено из {filepath}")
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
    
    def _cleanup(self) -> None:
        """Очистка ресурсов."""
        self.metrics_recorder.close()
        if self.last_stats:
            print(f"\nСимуляция завершена на тике {self.last_stats['tick']}")
            print(f"Финальное количество клеток: {self.last_stats['alive']}")
            print(f"Финальное количество видов: {self.last_stats['species']}")


def main() -> None:
    """Главная функция программы."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Загружаем конфигурацию
    config = load_config(args.config)
    config = config.merge_with_args(args)
    
    # Валидируем конфигурацию
    try:
        validate_config(config)
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    
    # Сохраняем конфигурацию если нужно
    if args.save_config:
        config.to_file(args.save_config)
        print(f"Конфигурация сохранена в {args.save_config}")
        return
    
    # Создаем и запускаем контроллер
    controller = SimulationController(config)
    controller.run()


if __name__ == "__main__":
    main()
