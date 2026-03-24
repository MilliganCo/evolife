"""
Модуль метрик для эволюционной симуляции 'Жизнь'.

Содержит функции для расчета статистики, энтропии и анализа эволюции.
"""

import math
from typing import Dict, List, Tuple, Any
from collections import Counter
import numpy as np
from .genetics import Genome


def calculate_entropy(species_counts: Dict[int, int]) -> float:
    """Вычисляет энтропию Шеннона для распределения видов."""
    if not species_counts:
        return 0.0
    
    total = sum(species_counts.values())
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in species_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy


def calculate_diversity_metrics(species_counts: Dict[int, int]) -> Dict[str, float]:
    """Вычисляет различные метрики разнообразия."""
    if not species_counts:
        return {
            "entropy": 0.0,
            "simpson_diversity": 0.0,
            "species_richness": 0,
            "evenness": 0.0
        }
    
    total = sum(species_counts.values())
    if total == 0:
        return {
            "entropy": 0.0,
            "simpson_diversity": 0.0,
            "species_richness": 0,
            "evenness": 0.0
        }
    
    # Энтропия Шеннона
    entropy = calculate_entropy(species_counts)
    
    # Индекс Симпсона
    simpson_diversity = 0.0
    for count in species_counts.values():
        p = count / total
        simpson_diversity += p * p
    simpson_diversity = 1.0 - simpson_diversity
    
    # Богатство видов
    species_richness = len(species_counts)
    
    # Равномерность (evenness)
    max_entropy = math.log2(species_richness) if species_richness > 1 else 0.0
    evenness = entropy / max_entropy if max_entropy > 0 else 0.0
    
    return {
        "entropy": entropy,
        "simpson_diversity": simpson_diversity,
        "species_richness": species_richness,
        "evenness": evenness
    }


def analyze_genome_distribution(genomes: Dict[Tuple[int, int], Genome]) -> Dict[str, Any]:
    """Анализирует распределение генетических признаков."""
    if not genomes:
        return {
            "total_genomes": 0,
            "mutation_rates": [],
            "age_limits": [],
            "glyph_distribution": {},
            "color_distribution": {},
            "rule_distribution": {}
        }
    
    mutation_rates = []
    age_limits = []
    glyph_counts = Counter()
    color_counts = Counter()
    rule_counts = Counter()
    
    for genome in genomes.values():
        mutation_rates.append(genome.mutation_rate)
        age_limits.append(genome.age_max)
        glyph_counts[genome.glyph_id] += 1
        color_counts[genome.color_id] += 1
        rule_counts[(genome.birth_mask, genome.survive_mask)] += 1
    
    return {
        "total_genomes": len(genomes),
        "mutation_rates": {
            "mean": np.mean(mutation_rates),
            "std": np.std(mutation_rates),
            "min": np.min(mutation_rates),
            "max": np.max(mutation_rates)
        },
        "age_limits": {
            "mean": np.mean(age_limits),
            "std": np.std(age_limits),
            "min": np.min(age_limits),
            "max": np.max(age_limits)
        },
        "glyph_distribution": dict(glyph_counts),
        "color_distribution": dict(color_counts),
        "rule_distribution": {str(rule): count for rule, count in rule_counts.items()}
    }


def calculate_evolution_rate(previous_stats: Dict[str, Any], 
                           current_stats: Dict[str, Any]) -> Dict[str, float]:
    """Вычисляет скорость эволюции между двумя состояниями."""
    if not previous_stats or not current_stats:
        return {
            "species_change_rate": 0.0,
            "population_growth_rate": 0.0,
            "diversity_change_rate": 0.0
        }
    
    # Скорость изменения количества видов
    prev_species = previous_stats.get("species", 0)
    curr_species = current_stats.get("species", 0)
    species_change_rate = (curr_species - prev_species) / max(prev_species, 1)
    
    # Скорость роста популяции
    prev_alive = previous_stats.get("alive", 0)
    curr_alive = current_stats.get("alive", 0)
    population_growth_rate = (curr_alive - prev_alive) / max(prev_alive, 1)
    
    # Скорость изменения разнообразия
    prev_entropy = previous_stats.get("entropy", 0.0)
    curr_entropy = current_stats.get("entropy", 0.0)
    diversity_change_rate = curr_entropy - prev_entropy
    
    return {
        "species_change_rate": species_change_rate,
        "population_growth_rate": population_growth_rate,
        "diversity_change_rate": diversity_change_rate
    }


def detect_patterns(cells: np.ndarray, min_size: int = 3) -> List[Dict[str, Any]]:
    """Обнаруживает паттерны в поле (блоки, осцилляторы, глайдеры)."""
    patterns = []
    height, width = cells.shape
    
    # Простой детектор блоков 2x2
    for y in range(height - 1):
        for x in range(width - 1):
            if (cells[y, x] and cells[y, x+1] and 
                cells[y+1, x] and cells[y+1, x+1]):
                patterns.append({
                    "type": "block",
                    "x": x,
                    "y": y,
                    "width": 2,
                    "height": 2
                })
    
    # Детектор осцилляторов (простые паттерны)
    for y in range(height - 2):
        for x in range(width - 2):
            # Проверяем на blinker (3x1)
            if (cells[y, x] and cells[y, x+1] and cells[y, x+2] and
                not cells[y+1, x] and not cells[y+1, x+1] and not cells[y+1, x+2]):
                patterns.append({
                    "type": "blinker",
                    "x": x,
                    "y": y,
                    "width": 3,
                    "height": 1
                })
    
    return patterns


def calculate_spatial_metrics(cells: np.ndarray) -> Dict[str, float]:
    """Вычисляет пространственные метрики распределения клеток."""
    if not np.any(cells):
        return {
            "density": 0.0,
            "clustering": 0.0,
            "fragmentation": 0.0
        }
    
    height, width = cells.shape
    total_cells = np.sum(cells)
    density = total_cells / (height * width)
    
    # Простая мера кластеризации (доля клеток с живыми соседями)
    clustering = 0.0
    if total_cells > 0:
        neighbor_counts = np.zeros((height, width), dtype=int)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                shifted = np.roll(np.roll(cells, dy, axis=0), dx, axis=1)
                neighbor_counts += shifted.astype(int)
        
        clustered_cells = np.sum((cells & (neighbor_counts > 0)))
        clustering = clustered_cells / total_cells
    
    # Простая мера фрагментации (отношение периметра к площади)
    # Периметр = количество границ между живыми и мертвыми клетками
    perimeter = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            shifted = np.roll(np.roll(cells, dy, axis=0), dx, axis=1)
            perimeter += np.sum(cells & ~shifted)
    
    fragmentation = perimeter / max(total_cells, 1)
    
    return {
        "density": density,
        "clustering": clustering,
        "fragmentation": fragmentation
    }


def generate_report(stats: Dict[str, Any], 
                   diversity_metrics: Dict[str, float],
                   genome_analysis: Dict[str, Any],
                   spatial_metrics: Dict[str, float]) -> str:
    """Генерирует текстовый отчет о состоянии симуляции."""
    report = []
    report.append("=== ОТЧЕТ О СИМУЛЯЦИИ ===")
    report.append(f"Тик: {stats.get('tick', 0)}")
    report.append(f"Живых клеток: {stats.get('alive', 0)}")
    report.append(f"Видов: {stats.get('species', 0)}")
    
    report.append("\n--- МЕТРИКИ РАЗНООБРАЗИЯ ---")
    report.append(f"Энтропия Шеннона: {diversity_metrics.get('entropy', 0.0):.3f}")
    report.append(f"Индекс Симпсона: {diversity_metrics.get('simpson_diversity', 0.0):.3f}")
    report.append(f"Богатство видов: {diversity_metrics.get('species_richness', 0)}")
    report.append(f"Равномерность: {diversity_metrics.get('evenness', 0.0):.3f}")
    
    report.append("\n--- ГЕНЕТИЧЕСКИЙ АНАЛИЗ ---")
    genome_stats = genome_analysis.get('mutation_rates', {})
    report.append(f"Средняя частота мутаций: {genome_stats.get('mean', 0.0):.4f}")
    report.append(f"Средний максимальный возраст: {genome_analysis.get('age_limits', {}).get('mean', 0.0):.1f}")
    
    report.append("\n--- ПРОСТРАНСТВЕННЫЕ МЕТРИКИ ---")
    report.append(f"Плотность: {spatial_metrics.get('density', 0.0):.3f}")
    report.append(f"Кластеризация: {spatial_metrics.get('clustering', 0.0):.3f}")
    report.append(f"Фрагментация: {spatial_metrics.get('fragmentation', 0.0):.3f}")
    
    if 'top_species' in stats and stats['top_species']:
        report.append("\n--- ТОП ВИДЫ ---")
        for i, (species_id, count) in enumerate(stats['top_species'][:5], 1):
            report.append(f"{i}. Вид {species_id}: {count} особей")
    
    return "\n".join(report)
