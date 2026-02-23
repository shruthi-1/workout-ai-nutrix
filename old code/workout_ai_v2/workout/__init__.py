"""
FitGen AI v5.0 - Workout Package
"""

from .workout_gen import WorkoutGenerator
from .session_logger import SessionLogger
from .fallback import FallbackSystem

__all__ = ['WorkoutGenerator', 'SessionLogger', 'FallbackSystem']
