"""
FitGen AI v6.0 - Utils V6 Package
Calorie calculator and related utilities for v6.0
"""

from .calorie_calculator import (
    calculate_met_value,
    calculate_calories_burned,
    calculate_exercise_calories,
    estimate_exercise_duration,
    calculate_workout_calories,
    MET_VALUES
)

__all__ = [
    'calculate_met_value',
    'calculate_calories_burned',
    'calculate_exercise_calories',
    'estimate_exercise_duration',
    'calculate_workout_calories',
    'MET_VALUES'
]


