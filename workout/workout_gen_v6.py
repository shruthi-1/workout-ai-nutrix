"""
FitGen AI v6.0 - Enhanced Workout Generator Module
Generates structured workouts with warmup, main course, and stretches phases
Includes calorie calculations and full exercise descriptions
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random

from config import COLLECTIONS
from db.database_manager_v6 import DatabaseManagerV6
from utils_v6.calorie_calculator import (
    calculate_met_value,
    calculate_calories_burned,
    estimate_exercise_duration
)
from utils import generate_id, get_current_datetime

logger = logging.getLogger(__name__)

# ============================================================================
# WORKOUT GENERATOR V6 CLASS
# ============================================================================

class WorkoutGeneratorV6:
    """
    Enhanced workout generator for FitGen AI v6.0
    Generates structured workouts with warmup, main course, and stretches
    """
    
    def __init__(self, db_manager: DatabaseManagerV6):
        """
        Initialize workout generator
        
        Args:
            db_manager: DatabaseManagerV6 instance
        """
        self.db_manager = db_manager
    
    def generate_structured_workout(
        self,
        user_id: str,
        target_body_parts: List[str],
        duration_minutes: int = 60,
        user_weight_kg: float = 70.0,
        include_warmup: bool = True,
        include_stretches: bool = True,
        fitness_level: str = 'Intermediate'
    ) -> Dict:
        """
        Generate a complete structured workout with phases
        
        Args:
            user_id: User identifier
            target_body_parts: List of body parts to target
            duration_minutes: Total workout duration
            user_weight_kg: User's weight for calorie calculation
            include_warmup: Include warmup phase
            include_stretches: Include stretches phase
            fitness_level: User's fitness level (Beginner, Intermediate, Expert)
        
        Returns:
            Structured workout dictionary
        """
        try:
            # Generate workout ID
            workout_id = f"wk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Allocate time for phases
            warmup_duration = 8 if include_warmup else 0
            stretches_duration = 7 if include_stretches else 0
            main_duration = duration_minutes - warmup_duration - stretches_duration
            
            if main_duration < 10:
                main_duration = duration_minutes  # Minimum viable workout
                warmup_duration = 0
                stretches_duration = 0
                include_warmup = False
                include_stretches = False
            
            # Generate phases
            warmup_exercises = []
            if include_warmup:
                warmup_exercises = self._select_warmup_exercises(
                    warmup_duration, user_weight_kg, fitness_level
                )
            
            main_exercises = self._select_main_exercises(
                target_body_parts, main_duration, user_weight_kg, fitness_level
            )
            
            stretches_exercises = []
            if include_stretches:
                stretches_exercises = self._select_stretches(
                    target_body_parts, stretches_duration, user_weight_kg
                )
            
            # Calculate total calories
            all_exercises = warmup_exercises + main_exercises + stretches_exercises
            total_calories = sum(ex.get('estimated_calories', 0) for ex in all_exercises)
            total_duration = sum(ex.get('duration_minutes', 0) for ex in all_exercises)
            
            # Calculate phase summaries
            warmup_calories = sum(ex.get('estimated_calories', 0) for ex in warmup_exercises)
            warmup_time = sum(ex.get('duration_minutes', 0) for ex in warmup_exercises)
            
            main_calories = sum(ex.get('estimated_calories', 0) for ex in main_exercises)
            main_time = sum(ex.get('duration_minutes', 0) for ex in main_exercises)
            
            stretches_calories = sum(ex.get('estimated_calories', 0) for ex in stretches_exercises)
            stretches_time = sum(ex.get('duration_minutes', 0) for ex in stretches_exercises)
            
            # Build workout structure
            workout = {
                'workout_id': workout_id,
                'user_id': user_id,
                'generated_at': datetime.utcnow().isoformat(),
                'total_duration_minutes': round(total_duration, 1),
                'estimated_total_calories': round(total_calories, 1),
                'target_body_parts': target_body_parts,
                'fitness_level': fitness_level,
                'phases': {
                    'warmup': {
                        'duration_minutes': round(warmup_time, 1),
                        'estimated_calories': round(warmup_calories, 1),
                        'exercises': warmup_exercises
                    },
                    'main_course': {
                        'duration_minutes': round(main_time, 1),
                        'estimated_calories': round(main_calories, 1),
                        'exercises': main_exercises
                    },
                    'stretches': {
                        'duration_minutes': round(stretches_time, 1),
                        'estimated_calories': round(stretches_calories, 1),
                        'exercises': stretches_exercises
                    }
                }
            }
            
            logger.info(f"✅ Generated workout {workout_id} with {len(all_exercises)} exercises")
            return workout
        
        except Exception as e:
            logger.error(f"Error generating structured workout: {e}")
            return {
                'error': 'Failed to generate workout',
                'message': 'An error occurred during workout generation. Please try again.',
                'workout_id': None
            }
    
    def _select_warmup_exercises(
        self,
        duration_minutes: int,
        user_weight_kg: float,
        fitness_level: str
    ) -> List[Dict]:
        """
        Select warmup exercises (2-3 exercises, 5-10 minutes total)
        
        Args:
            duration_minutes: Total warmup duration
            user_weight_kg: User's weight
            fitness_level: User's fitness level
        
        Returns:
            List of warmup exercise dictionaries
        """
        try:
            # Get warmup-suitable exercises (light cardio, mobility)
            warmup_body_parts = ['Full Body', 'Cardio', 'Core']
            warmup_types = ['Cardio', 'Stretching', 'Warmup']
            
            # Fetch exercises
            all_warmup = []
            for body_part in warmup_body_parts:
                exercises = self.db_manager.get_exercises_by_filters(
                    body_part=body_part,
                    level='Beginner',
                    limit=20
                )
                all_warmup.extend(exercises)
            
            # Also get by type
            for ex_type in warmup_types:
                exercises = self.db_manager.get_exercises_by_filters(
                    exercise_type=ex_type,
                    limit=20
                )
                all_warmup.extend(exercises)
            
            # Remove duplicates
            seen_ids = set()
            unique_warmup = []
            for ex in all_warmup:
                if ex['exercise_id'] not in seen_ids:
                    seen_ids.add(ex['exercise_id'])
                    unique_warmup.append(ex)
            
            if not unique_warmup:
                logger.warning("No warmup exercises found, using fallback")
                return self._create_fallback_warmup(duration_minutes, user_weight_kg)
            
            # Select 2-3 exercises
            num_exercises = min(3, len(unique_warmup))
            selected = random.sample(unique_warmup, num_exercises)
            
            # Configure each exercise
            time_per_exercise = duration_minutes / num_exercises
            warmup_exercises = []
            
            for order, exercise in enumerate(selected, 1):
                # Warmup exercises: 1-2 sets, higher reps, minimal rest
                sets = 1
                reps = 20 if 'Cardio' in exercise.get('type', '') else 10
                rest_seconds = 0
                
                # Calculate duration and calories
                duration = round(time_per_exercise, 1)
                met_value = exercise.get('met_value', 4.0)
                calories = calculate_calories_burned(met_value, user_weight_kg, duration)
                
                warmup_ex = {
                    'exercise_id': exercise['exercise_id'],
                    'title': exercise['title'],
                    'description': exercise.get('description', ''),
                    'duration_minutes': duration,
                    'sets': sets,
                    'reps': reps,
                    'rest_seconds': rest_seconds,
                    'met_value': met_value,
                    'estimated_calories': calories,
                    'video_url': exercise.get('video_url'),
                    'order': order,
                    'phase': 'warmup'
                }
                
                warmup_exercises.append(warmup_ex)
            
            return warmup_exercises
        
        except Exception as e:
            logger.error(f"Error selecting warmup exercises: {e}")
            return self._create_fallback_warmup(duration_minutes, user_weight_kg)
    
    def _select_main_exercises(
        self,
        target_body_parts: List[str],
        duration_minutes: int,
        user_weight_kg: float,
        fitness_level: str
    ) -> List[Dict]:
        """
        Select main workout exercises based on target body parts
        
        Args:
            target_body_parts: List of body parts to target
            duration_minutes: Total main workout duration
            user_weight_kg: User's weight
            fitness_level: User's fitness level
        
        Returns:
            List of main exercise dictionaries
        """
        try:
            # Fetch exercises for target body parts
            all_exercises = []
            for body_part in target_body_parts:
                exercises = self.db_manager.get_exercises_by_filters(
                    body_part=body_part,
                    level=fitness_level,
                    limit=50
                )
                all_exercises.extend(exercises)
            
            if not all_exercises:
                logger.warning("No exercises found for target body parts, using fallback")
                return self._create_fallback_main(duration_minutes, user_weight_kg, fitness_level)
            
            # Remove duplicates
            seen_ids = set()
            unique_exercises = []
            for ex in all_exercises:
                if ex['exercise_id'] not in seen_ids:
                    seen_ids.add(ex['exercise_id'])
                    unique_exercises.append(ex)
            
            # Select 5-8 exercises based on duration
            num_exercises = min(8, max(5, duration_minutes // 8))
            num_exercises = min(num_exercises, len(unique_exercises))
            selected = random.sample(unique_exercises, num_exercises)
            
            # Configure each exercise
            time_per_exercise = duration_minutes / num_exercises
            main_exercises = []
            
            for order, exercise in enumerate(selected, 1):
                # Main exercises: 3-4 sets, moderate reps, proper rest
                sets = 4 if fitness_level == 'Expert' else 3
                reps = 12 if fitness_level == 'Beginner' else 10 if fitness_level == 'Intermediate' else 8
                rest_seconds = 60 if fitness_level == 'Beginner' else 90 if fitness_level == 'Intermediate' else 120
                
                # Calculate duration and calories
                duration = round(time_per_exercise, 1)
                met_value = exercise.get('met_value', 5.0)
                calories = calculate_calories_burned(met_value, user_weight_kg, duration)
                
                main_ex = {
                    'exercise_id': exercise['exercise_id'],
                    'title': exercise['title'],
                    'description': exercise.get('description', ''),
                    'duration_minutes': duration,
                    'sets': sets,
                    'reps': reps,
                    'rest_seconds': rest_seconds,
                    'met_value': met_value,
                    'estimated_calories': calories,
                    'video_url': exercise.get('video_url'),
                    'order': order,
                    'phase': 'main_course'
                }
                
                main_exercises.append(main_ex)
            
            return main_exercises
        
        except Exception as e:
            logger.error(f"Error selecting main exercises: {e}")
            return self._create_fallback_main(duration_minutes, user_weight_kg, fitness_level)
    
    def _select_stretches(
        self,
        target_body_parts: List[str],
        duration_minutes: int,
        user_weight_kg: float
    ) -> List[Dict]:
        """
        Select stretching exercises (3-5 exercises, 5-10 minutes total)
        
        Args:
            target_body_parts: List of body parts to stretch
            duration_minutes: Total stretching duration
            user_weight_kg: User's weight
        
        Returns:
            List of stretching exercise dictionaries
        """
        try:
            # Get stretching exercises
            stretching_exercises = self.db_manager.get_exercises_by_filters(
                exercise_type='Stretching',
                limit=50
            )
            
            # Also get yoga/flexibility exercises
            flexibility_exercises = self.db_manager.get_exercises_by_filters(
                equipment='Body Only',
                level='Beginner',
                limit=30
            )
            
            all_stretches = stretching_exercises + flexibility_exercises
            
            # Remove duplicates
            seen_ids = set()
            unique_stretches = []
            for ex in all_stretches:
                if ex['exercise_id'] not in seen_ids and 'stretch' in ex.get('title', '').lower():
                    seen_ids.add(ex['exercise_id'])
                    unique_stretches.append(ex)
            
            if not unique_stretches:
                logger.warning("No stretching exercises found, using fallback")
                return self._create_fallback_stretches(duration_minutes, user_weight_kg)
            
            # Select 3-5 exercises
            num_exercises = min(5, max(3, len(unique_stretches)))
            selected = random.sample(unique_stretches, min(num_exercises, len(unique_stretches)))
            
            # Configure each exercise
            time_per_exercise = duration_minutes / len(selected)
            stretch_exercises = []
            
            for order, exercise in enumerate(selected, 1):
                # Stretches: 1-2 sets, hold for 30-60 seconds, no rest
                sets = 2
                reps = 1  # One hold
                rest_seconds = 0
                
                # Calculate duration and calories
                duration = round(time_per_exercise, 1)
                met_value = 2.5  # Stretching MET value
                calories = calculate_calories_burned(met_value, user_weight_kg, duration)
                
                stretch_ex = {
                    'exercise_id': exercise['exercise_id'],
                    'title': exercise['title'],
                    'description': exercise.get('description', ''),
                    'duration_minutes': duration,
                    'sets': sets,
                    'reps': reps,
                    'rest_seconds': rest_seconds,
                    'met_value': met_value,
                    'estimated_calories': calories,
                    'video_url': exercise.get('video_url'),
                    'order': order,
                    'phase': 'stretches'
                }
                
                stretch_exercises.append(stretch_ex)
            
            return stretch_exercises
        
        except Exception as e:
            logger.error(f"Error selecting stretches: {e}")
            return self._create_fallback_stretches(duration_minutes, user_weight_kg)
    
    # ========================================================================
    # FALLBACK METHODS
    # ========================================================================
    
    def _create_fallback_warmup(self, duration_minutes: int, user_weight_kg: float) -> List[Dict]:
        """Create fallback warmup exercises"""
        return [
            {
                'exercise_id': 'fallback_warmup_1',
                'title': 'Jumping Jacks',
                'description': 'Full body warmup exercise',
                'duration_minutes': duration_minutes / 2,
                'sets': 1,
                'reps': 30,
                'rest_seconds': 0,
                'met_value': 4.0,
                'estimated_calories': calculate_calories_burned(4.0, user_weight_kg, duration_minutes / 2),
                'video_url': None,
                'order': 1,
                'phase': 'warmup'
            },
            {
                'exercise_id': 'fallback_warmup_2',
                'title': 'Arm Circles',
                'description': 'Shoulder warmup exercise',
                'duration_minutes': duration_minutes / 2,
                'sets': 1,
                'reps': 20,
                'rest_seconds': 0,
                'met_value': 3.5,
                'estimated_calories': calculate_calories_burned(3.5, user_weight_kg, duration_minutes / 2),
                'video_url': None,
                'order': 2,
                'phase': 'warmup'
            }
        ]
    
    def _create_fallback_main(self, duration_minutes: int, user_weight_kg: float, fitness_level: str) -> List[Dict]:
        """Create fallback main exercises"""
        met_value = 5.0 if fitness_level == 'Intermediate' else 6.0
        return [
            {
                'exercise_id': 'fallback_main_1',
                'title': 'Push-ups',
                'description': 'Chest and triceps exercise',
                'duration_minutes': duration_minutes / 4,
                'sets': 3,
                'reps': 12,
                'rest_seconds': 60,
                'met_value': met_value,
                'estimated_calories': calculate_calories_burned(met_value, user_weight_kg, duration_minutes / 4),
                'video_url': None,
                'order': 1,
                'phase': 'main_course'
            }
        ]
    
    def _create_fallback_stretches(self, duration_minutes: int, user_weight_kg: float) -> List[Dict]:
        """Create fallback stretching exercises"""
        return [
            {
                'exercise_id': 'fallback_stretch_1',
                'title': 'Hamstring Stretch',
                'description': 'Stretch hamstrings and lower back',
                'duration_minutes': duration_minutes / 3,
                'sets': 1,
                'reps': 1,
                'rest_seconds': 0,
                'met_value': 2.5,
                'estimated_calories': calculate_calories_burned(2.5, user_weight_kg, duration_minutes / 3),
                'video_url': None,
                'order': 1,
                'phase': 'stretches'
            }
        ]
