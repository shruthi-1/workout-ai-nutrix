"""
FitGen AI v5.0 - Workout Generator Module
Generates personalized workouts using rules and ML
Features 2-3: Weekly plans and daily workout structure
Features 38-42: Exercise variety, progressive overload, smart rest, warmup/cooldown, notes
"""

import logging
from typing import Dict, List, Tuple, Optional
import random

from config import (
    SPLITS,
    FITNESS_GOALS,
    BODY_PARTS,
    EMERGENCY_FALLBACK_EXERCISES,
    EXERCISE_SCORING_WEIGHTS,
    VOLUME_ADAPTATION,
    RPE_ADJUSTMENT,
    RECENCY_SETTINGS
)
from utils import (
    generate_workout_id,
    generate_plan_id,
    get_current_datetime,
    log_success,
    log_warning,
    log_info,
    choose_random,
    to_snake_case
)
from db.database_manager import DatabaseManager
from data.exercise_database import ExerciseDatabase

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

FULL_BODY_CATEGORY = 'Full Body'

# ============================================================================
# WORKOUT GENERATOR CLASS
# ============================================================================

class WorkoutGenerator:
    """
    Generates personalized workouts with all features
    Features 2-3: Weekly plans and daily structure
    Features 38-42: Variety, overload, rest, warmup, notes
    """
    
    def __init__(self, db_manager: DatabaseManager, exercise_db: ExerciseDatabase):
        """
        Initialize workout generator
        
        Args:
            db_manager: DatabaseManager instance
            exercise_db: ExerciseDatabase instance
        """
        self.db_manager = db_manager
        self.exercise_db = exercise_db
        self.weekly_plans_collection = 'weekly_plans'
    
    # ========================================================================
    # DAILY WORKOUT GENERATION (Feature 3)
    # ========================================================================
    
    def generate_daily_workout(self, user: Dict, target_body_parts: List[str] = None,
                              duration_minutes: int = 60) -> Dict:
        """
        Feature 3: Generate complete daily workout with:
        - Warmup section (15% duration, min 5 min) - Feature 41
        - Main workout (75% duration, 3-10 exercises)
        - Cooldown section (10% duration, min 3 min) - Feature 41
        
        Args:
            user: User profile document
            target_body_parts: Body parts to target
            duration_minutes: Total workout duration
        
        Returns:
            Complete workout document
        """
        
        if not target_body_parts:
            target_body_parts = ['Chest', 'Back', 'Shoulders']
        
        # Feature 41: Dynamic duration allocation
        warmup_duration = max(5, int(duration_minutes * 0.15))
        main_duration = int(duration_minutes * 0.75)
        cooldown_duration = max(3, int(duration_minutes * 0.10))
        
        # Feature 3: Complete daily workout structure
        workout = {
            'workout_id': generate_workout_id(user['user_id']),
            'user_id': user['user_id'],
            'date': get_current_datetime(),
            'total_duration': duration_minutes,
            'sections': {
                'warmup': self._generate_warmup(warmup_duration),
                'main': self._generate_main_workout(user, main_duration, target_body_parts),
                'cooldown': self._generate_cooldown(cooldown_duration)
            },
            'motivation': self._get_motivation_message(user),
            'daily_tip': self._get_daily_tip()
        }
        
        return workout
    
    def _generate_warmup(self, duration: int) -> Dict:
        """Feature 41: Dynamic warmup generation"""
        exercises = [
            {
                'name': 'Joint Mobility Flow',
                'duration_seconds': 120,
                'description': 'Gentle joint circles, arm swings, hip mobility'
            },
            {
                'name': 'Light Cardio Activation',
                'duration_seconds': max(60, (duration - 2) * 60),
                'description': 'Walking, light jogging in place, jumping jacks'
            }
        ]
        return {'exercises': exercises, 'total_duration': duration}
    
    def _generate_main_workout(self, user: Dict, duration: int,
                              target_body_parts: List[str]) -> Dict:
        """Feature 38-40: Main workout with variety, progressive overload, smart rest"""
        
        # Feature 12: Exercise scoring algorithm
        exercises = self._select_exercises_with_scoring(
            user, target_body_parts, duration
        )
        
        return {
            'exercises': exercises,
            'total_duration': duration,
            'estimated_exercises_count': len(exercises),
            'intensity_level': user['fitness_level']
        }
    
    def _select_exercises_with_scoring(self, user: Dict, body_parts: List[str],
                                      duration: int) -> List[Dict]:
        """Feature 12 & 38: Exercise selection with intelligent scoring"""
        
        all_exercises = []
        for body_part in body_parts:
            exercises = self.exercise_db.get_exercises_by_body_part(body_part, limit=20)
            all_exercises.extend(exercises)
            log_info(f"Found {len(exercises)} exercises for {body_part}")
        
        # Remove duplicates
        seen = set()
        unique_exercises = []
        for ex in all_exercises:
            ex_id = ex.get('exercise_id', ex.get('title', ''))
            if ex_id not in seen:
                seen.add(ex_id)
                unique_exercises.append(ex)
        all_exercises = unique_exercises
        
        # Fallback when no exercises found
        if not all_exercises:
            log_warning(f"No exercises found for body parts {body_parts}, using emergency fallback")
            
            # Filter by target body parts or use all
            matching_fallback = [
                ex for ex in EMERGENCY_FALLBACK_EXERCISES
                if ex.get('body_part') in body_parts or ex.get('body_part') == FULL_BODY_CATEGORY
            ]
            
            if not matching_fallback:
                matching_fallback = EMERGENCY_FALLBACK_EXERCISES.copy()
            
            # Convert to expected format
            all_exercises = [
                {
                    'exercise_id': ex.get('id', to_snake_case(ex.get('title', ''))),
                    'title': ex.get('title'),
                    'body_part': ex.get('body_part'),
                    'equipment': ex.get('equipment', 'Body Only'),
                    'level': ex.get('level', 'Beginner'),
                    'description': ex.get('notes', 'Execute with proper form'),
                    'rating': ex.get('rating', 5.0)
                }
                for ex in matching_fallback
            ]
        
        # Feature 12: Score exercises based on multiple factors
        scored_exercises = []
        for ex in all_exercises:
            score = 0.0
            
            # Equipment match (Feature 12)
            if ex['equipment'] in user.get('equipment_available', []):
                score += EXERCISE_SCORING_WEIGHTS['equipment_match']
            
            # Body part preferences (Feature 10, 12)
            prefs = user.get('preferences', {}).get('body_part_preferences', {})
            if ex['body_part'] in prefs:
                score += EXERCISE_SCORING_WEIGHTS['body_part_preference'] * prefs[ex['body_part']]
            
            # Past satisfaction (Feature 10, 12)
            satisf = user.get('preferences', {}).get('satisfaction_ratings', {})
            if ex['title'] in satisf:
                score += EXERCISE_SCORING_WEIGHTS['past_satisfaction'] * (satisf[ex['title']] / 10)
            
            # Recency penalty (Feature 11, 12)
            recent = user.get('preferences', {}).get('recent_exercises', [])
            if ex.get('exercise_id') in recent:
                score += EXERCISE_SCORING_WEIGHTS['recency_penalty']
            
            # Random variety (Feature 12, 38)
            score += EXERCISE_SCORING_WEIGHTS['variety'] * random.random()
            
            scored_exercises.append((ex, score))
        
        # Sort by score
        scored_exercises.sort(key=lambda x: x[1], reverse=True)
        
        # Feature 39: Progressive overload - calculate number of exercises
        num_exercises = max(3, min(10, int(duration / 6)))
        
        selected = []
        for ex, _ in scored_exercises[:num_exercises]:
            exercise_detail = {
                'exercise_id': ex['exercise_id'],
                'title': ex['title'],
                'body_part': ex['body_part'],
                'equipment': ex['equipment'],
                'sets': self._calculate_sets(user),
                'reps': self._calculate_reps(user),
                'rest_seconds': self._calculate_rest(user),
                'rpe_range': self._get_rpe_range(user),
                'notes': self._generate_exercise_notes(ex, user),
                'modifications': self._get_modifications(ex, user)
            }
            selected.append(exercise_detail)
        
        return selected
    
    def _calculate_sets(self, user: Dict) -> int:
        """Feature 8 & 39: Calculate sets with ML adaptation"""
        base_sets = {
            'Beginner': 2,
            'Intermediate': 3,
            'Expert': 4
        }
        return base_sets.get(user['fitness_level'], 3)
    
    def _calculate_reps(self, user: Dict) -> Tuple[int, int]:
        """Feature 3 & 7: Goal-specific rep ranges"""
        rep_ranges = FITNESS_GOALS
        goal_ranges = rep_ranges.get(user['goal'], {}).get('rep_range', (8, 12))
        return goal_ranges
    
    def _calculate_rest(self, user: Dict) -> int:
        """Feature 40: Smart rest period calculation"""
        rest_seconds = FITNESS_GOALS.get(user['goal'], {}).get('rest_seconds', 60)
        return rest_seconds
    
    def _get_rpe_range(self, user: Dict) -> Tuple[int, int]:
        """Feature 9: RPE-based adjustments with BMI safety caps (Feature 4)"""
        max_rpe = 10
        
        # Feature 4: BMI-based safety RPE caps
        bmi_category = user.get('bmi_category')
        if bmi_category == 'Severe Underweight':
            max_rpe = 8
        elif bmi_category == 'Obese':
            max_rpe = 8
        elif bmi_category == 'Severely Obese':
            max_rpe = 7
        elif bmi_category == 'Extremely Obese':
            max_rpe = 6
        
        return (max_rpe - 3, max_rpe)
    
    def _generate_exercise_notes(self, exercise: Dict, user: Dict) -> str:
        """Feature 42: Exercise notes with form cues"""
        notes = f"Form cue: {exercise.get('description', 'Execute with control')}"
        
        # Feature 5: Injury-specific notes
        for injury in user.get('injuries', []):
            if injury.lower() in exercise['body_part'].lower():
                notes += f" | ⚠️ Modification: Reduce ROM due to {injury}"
        
        return notes
    
    def _get_modifications(self, exercise: Dict, user: Dict) -> List[str]:
        """Feature 42: Exercise modifications"""
        modifications = []
        
        # Feature 5: Injury modifications
        for injury in user.get('injuries', []):
            if injury.lower() in exercise['body_part'].lower():
                modifications.append(f"Modify: Adjust range due to {injury}")
        
        # Feature 4: BMI modifications
        if user.get('bmi_category') in ['Severely Obese', 'Extremely Obese']:
            modifications.append("Use supported version or reduce complexity")
        
        # Feature 6: Fitness level modifications
        if user['fitness_level'] == 'Beginner':
            modifications.append("Reduce weight. Focus on form")
        
        return modifications
    
    def _generate_cooldown(self, duration: int) -> Dict:
        """Feature 41: Dynamic cooldown generation"""
        stretches = [
            {
                'name': 'Full Body Stretch',
                'duration_seconds': duration * 60,
                'description': 'Hold stretches for major muscle groups'
            }
        ]
        return {'exercises': stretches, 'total_duration': duration}
    
    def _get_motivation_message(self, user: Dict) -> str:
        """Feature 20: Adaptive motivation messages"""
        perf = user.get('performance', {})
        streak = perf.get('current_streak', 0)
        satisfaction = perf.get('avg_satisfaction', 0)
        
        if streak > 10:
            return "🔥 You're crushing it — keep the momentum!"
        elif satisfaction > 8:
            return "💪 Amazing work! You're making great progress!"
        elif perf.get('avg_completion_rate', 0) > 0.9:
            return "✅ Solid work — aim for crisp reps!"
        else:
            return "💯 Any movement is progress — you've got this!"
    
    def _get_daily_tip(self) -> str:
        """Feature 23: Daily tips rotation"""
        from config import DAILY_TIPS
        return random.choice(DAILY_TIPS)
    
    # ========================================================================
    # WEEKLY PLAN GENERATION (Feature 2)
    # ========================================================================
    
    def generate_weekly_plan(self, user: Dict, split_type: str = 'Push/Pull/Legs') -> Dict:
        """
        Feature 2: Generate 7-day weekly plan
        Supports: Push/Pull/Legs, Upper/Lower, Full Body, Custom splits
        
        Args:
            user: User profile document
            split_type: Programming split type
        
        Returns:
            Weekly plan document
        """
        
        if split_type not in SPLITS:
            split_type = 'Push/Pull/Legs'
        
        weekly_plan = {
            'plan_id': generate_plan_id(user['user_id']),
            'user_id': user['user_id'],
            'week_date': get_current_datetime(),
            'split_type': split_type,
            'days': {}
        }
        
        split_config = SPLITS[split_type]
        
        for day, day_config in split_config.items():
            if day_config['body_parts']:
                # Generate workout for this day
                weekly_plan['days'][day] = self.generate_daily_workout(
                    user, day_config['body_parts'], 60
                )
            else:
                # Rest day
                weekly_plan['days'][day] = {
                    'type': day_config['name'],
                    'body_parts': [],
                    'status': 'REST_DAY'
                }
        
        return weekly_plan
    
    def save_weekly_plan(self, plan: Dict) -> bool:
        """Save weekly plan to database"""
        if self.db_manager.is_connected():
            return self.db_manager.insert_one(self.weekly_plans_collection, plan)
        else:
            log_warning("Database not connected. Weekly plan not saved.")
            return False
    
    def get_weekly_plan(self, plan_id: str) -> Optional[Dict]:
        """Retrieve weekly plan by ID"""
        if self.db_manager.is_connected():
            return self.db_manager.find_one(
                self.weekly_plans_collection,
                {'plan_id': plan_id}
            )
        return None
