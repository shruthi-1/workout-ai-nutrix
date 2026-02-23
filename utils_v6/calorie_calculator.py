"""
FitGen AI v6.0 - Calorie Calculator Module
Accurate calorie burn calculation using MET (Metabolic Equivalent of Task) values
Formula: Calories = MET × weight(kg) × time(hours)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# MET VALUE MAPPINGS
# ============================================================================

MET_VALUES = {
    'Strength': {
        'Beginner': 3.5,
        'Intermediate': 5.0,
        'Expert': 6.0
    },
    'Cardio': {
        'Beginner': 5.0,
        'Intermediate': 7.0,
        'Expert': 10.0
    },
    'Stretching': 2.5,
    'Warmup': 4.0,
    'Plyometrics': 8.0,
    'Powerlifting': 6.0,
    'Olympic Weightlifting': 6.0,
    'Strongman': 7.0,
    'Crossfit': 8.0,
    'HIIT': 10.0,
    'Yoga': 2.5,
    'Pilates': 3.0,
    'Circuit Training': 8.0,
    'Default': 4.5  # Fallback value
}

# ============================================================================
# CALORIE CALCULATION FUNCTIONS
# ============================================================================

def calculate_met_value(exercise_type: str, level: str = 'Intermediate') -> float:
    """
    Calculate MET value based on exercise type and difficulty level
    
    Args:
        exercise_type: Type of exercise (Strength, Cardio, etc.)
        level: Difficulty level (Beginner, Intermediate, Expert)
    
    Returns:
        MET value as float
    """
    try:
        # Normalize inputs
        exercise_type = exercise_type.strip() if exercise_type else 'Default'
        level = level.strip() if level else 'Intermediate'
        
        # Check if exercise type has level-specific MET values
        if exercise_type in MET_VALUES and isinstance(MET_VALUES[exercise_type], dict):
            # Return level-specific MET value
            return MET_VALUES[exercise_type].get(level, MET_VALUES[exercise_type].get('Intermediate', 5.0))
        
        # Check if exercise type has a fixed MET value
        if exercise_type in MET_VALUES and isinstance(MET_VALUES[exercise_type], (int, float)):
            return float(MET_VALUES[exercise_type])
        
        # Default fallback
        logger.warning(f"No MET value found for exercise_type='{exercise_type}', using default")
        return MET_VALUES['Default']
    
    except Exception as e:
        logger.error(f"Error calculating MET value: {e}")
        return MET_VALUES['Default']


def calculate_calories_burned(
    met_value: float,
    weight_kg: float,
    duration_minutes: float
) -> float:
    """
    Calculate calories burned using MET formula
    
    Formula: Calories = MET × weight(kg) × time(hours)
    
    Args:
        met_value: Metabolic Equivalent of Task value
        weight_kg: User's weight in kilograms
        duration_minutes: Exercise duration in minutes
    
    Returns:
        Calories burned (rounded to 1 decimal place)
    """
    try:
        if met_value <= 0 or weight_kg <= 0 or duration_minutes <= 0:
            logger.warning(f"Invalid input for calorie calculation: met={met_value}, weight={weight_kg}, duration={duration_minutes}")
            return 0.0
        
        duration_hours = duration_minutes / 60.0
        calories = met_value * weight_kg * duration_hours
        
        return round(calories, 1)
    
    except Exception as e:
        logger.error(f"Error calculating calories: {e}")
        return 0.0


def calculate_exercise_calories(
    exercise_type: str,
    level: str,
    weight_kg: float,
    duration_minutes: float,
    sets: int = 1,
    reps: int = 1,
    rest_seconds: int = 0
) -> Dict[str, float]:
    """
    Calculate calories for an exercise including rest time
    
    Args:
        exercise_type: Type of exercise
        level: Difficulty level
        weight_kg: User's weight in kg
        duration_minutes: Total exercise duration
        sets: Number of sets
        reps: Repetitions per set
        rest_seconds: Rest time between sets
    
    Returns:
        Dictionary with MET value and calories burned
    """
    try:
        # Calculate MET value
        met_value = calculate_met_value(exercise_type, level)
        
        # Calculate calories for active time
        calories = calculate_calories_burned(met_value, weight_kg, duration_minutes)
        
        return {
            'met_value': met_value,
            'calories_burned': calories,
            'duration_minutes': duration_minutes
        }
    
    except Exception as e:
        logger.error(f"Error calculating exercise calories: {e}")
        return {
            'met_value': 4.5,
            'calories_burned': 0.0,
            'duration_minutes': duration_minutes
        }


def estimate_exercise_duration(
    exercise_type: str,
    sets: int,
    reps: int,
    rest_seconds: int = 60
) -> float:
    """
    Estimate exercise duration based on sets, reps, and rest
    
    Args:
        exercise_type: Type of exercise
        sets: Number of sets
        reps: Repetitions per set
        rest_seconds: Rest time between sets in seconds
    
    Returns:
        Estimated duration in minutes
    """
    try:
        # Estimate time per rep (seconds)
        time_per_rep = {
            'Strength': 4,  # 4 seconds per rep (2 up, 2 down)
            'Cardio': 3,    # 3 seconds per rep
            'Stretching': 30,  # 30 seconds per rep (hold)
            'Warmup': 4,    # 4 seconds per rep
            'Plyometrics': 2,
            'Default': 3
        }
        
        rep_time = time_per_rep.get(exercise_type, time_per_rep['Default'])
        
        # Calculate work time (sets * reps * time_per_rep)
        work_time_seconds = sets * reps * rep_time
        
        # Calculate total rest time (rest_seconds * (sets - 1))
        total_rest_seconds = rest_seconds * (sets - 1) if sets > 1 else 0
        
        # Total duration in minutes
        total_seconds = work_time_seconds + total_rest_seconds
        total_minutes = total_seconds / 60.0
        
        return round(total_minutes, 1)
    
    except Exception as e:
        logger.error(f"Error estimating duration: {e}")
        return 5.0  # Default 5 minutes


def calculate_workout_calories(
    exercises: list,
    weight_kg: float
) -> Dict[str, float]:
    """
    Calculate total calories for a complete workout
    
    Args:
        exercises: List of exercise dictionaries with 'estimated_calories' field
        weight_kg: User's weight in kg
    
    Returns:
        Dictionary with total duration and calories
    """
    try:
        total_calories = 0.0
        total_duration = 0.0
        
        for exercise in exercises:
            total_calories += exercise.get('estimated_calories', 0.0)
            total_duration += exercise.get('duration_minutes', 0.0)
        
        return {
            'total_duration_minutes': round(total_duration, 1),
            'total_calories': round(total_calories, 1)
        }
    
    except Exception as e:
        logger.error(f"Error calculating workout calories: {e}")
        return {
            'total_duration_minutes': 0.0,
            'total_calories': 0.0
        }
