"""
Эволюционная симуляция 'Игра Жизнь' с мутациями в ASCII.

Этот пакет реализует клеточный автомат с генетической системой,
позволяющий клеткам эволюционировать и наследовать правила поведения.
"""

__version__ = "1.0.0"
__author__ = "Evolife Team"

from .genetics import Genome, Species
from .engine import LifeEngine
from .render import Renderer
from .config import Config

__all__ = ["Genome", "Species", "LifeEngine", "Renderer", "Config"]
