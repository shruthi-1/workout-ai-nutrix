"""
FitGen AI v6.0 - Enhanced Session Logger Module
Real-time per-exercise logging with workout history and analytics
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from db.database_manager_v6 import DatabaseManagerV6
from utils import log_success, log_error, log_info

logger = logging.getLogger(__name__)

# ============================================================================
# SESSION LOGGER V6 CLASS
# ============================================================================

class SessionLoggerV6:
    """
    Enhanced session logger for FitGen AI v6.0
    Handles real-time per-exercise logging and workout analytics
    """
    
    def __init__(self, db_manager: DatabaseManagerV6):
        """
        Initialize session logger
        
        Args:
            db_manager: DatabaseManagerV6 instance
        """
        self.db_manager = db_manager
    
    def log_exercise_realtime(
        self,
        user_id: str,
        workout_id: str,
        exercise_id: str,
        exercise_title: str,
        phase: str,
        planned_sets: int,
        completed_sets: int,
        planned_reps: int,
        actual_reps: List[int],
        weight_used_kg: float = 0.0,
        duration_minutes: float = 0.0,
        calories_burned: float = 0.0,
        difficulty_rating: int = 5,
        notes: str = "",
        workout_status: str = "in_progress"
    ) -> Optional[str]:
        """
        Log individual exercise completion in real-time
        
        Args:
            user_id: User identifier
            workout_id: Workout identifier
            exercise_id: Exercise identifier
            exercise_title: Exercise name
            phase: Workout phase (warmup, main_course, stretches)
            planned_sets: Number of planned sets
            completed_sets: Number of completed sets
            planned_reps: Planned reps per set
            actual_reps: List of actual reps completed per set
            weight_used_kg: Weight used in kg
            duration_minutes: Exercise duration
            calories_burned: Estimated calories burned
            difficulty_rating: Difficulty rating (1-10)
            notes: User notes
            workout_status: Workout status (in_progress, completed)
        
        Returns:
            Log ID if successful, None otherwise
        """
        try:
            log_data = {
                'user_id': user_id,
                'workout_id': workout_id,
                'exercise_id': exercise_id,
                'exercise_title': exercise_title,
                'phase': phase,
                'planned_sets': planned_sets,
                'completed_sets': completed_sets,
                'planned_reps': planned_reps,
                'actual_reps': actual_reps,
                'weight_used_kg': weight_used_kg,
                'duration_minutes': duration_minutes,
                'calories_burned': calories_burned,
                'difficulty_rating': difficulty_rating,
                'notes': notes,
                'workout_status': workout_status
            }
            
            log_id = self.db_manager.log_exercise_completion(log_data)
            
            if log_id:
                log_success(f"✅ Logged exercise: {exercise_title} ({completed_sets}/{planned_sets} sets)")
                return log_id
            else:
                log_error(f"Failed to log exercise: {exercise_title}")
                return None
        
        except Exception as e:
            log_error(f"Error in log_exercise_realtime: {e}")
            return None
    
    def get_current_workout_status(self, workout_id: str) -> Dict:
        """
        Get current workout status and progress
        
        Args:
            workout_id: Workout identifier
        
        Returns:
            Dictionary with workout status and progress
        """
        try:
            status = self.db_manager.get_workout_status(workout_id)
            
            if status:
                log_info(f"Fetched status for workout {workout_id}: {status.get('total_exercises_completed', 0)} exercises completed")
            else:
                log_info(f"No status found for workout {workout_id}")
            
            return status
        
        except Exception as e:
            log_error(f"Error getting workout status: {e}")
            return {}
    
    def complete_workout(self, workout_id: str) -> bool:
        """
        Mark workout as complete
        
        Args:
            workout_id: Workout identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.db_manager.complete_workout(workout_id)
            
            if success:
                log_success(f"✅ Completed workout: {workout_id}")
            else:
                log_error(f"Failed to complete workout: {workout_id}")
            
            return success
        
        except Exception as e:
            log_error(f"Error completing workout: {e}")
            return False
    
    def get_workout_history(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 50
    ) -> Dict:
        """
        Get user's workout history with pagination
        
        Args:
            user_id: User identifier
            page: Page number (1-indexed)
            per_page: Results per page
        
        Returns:
            Dictionary with workout history and pagination info
        """
        try:
            skip = (page - 1) * per_page
            
            history = self.db_manager.get_workout_history(
                user_id=user_id,
                limit=per_page,
                skip=skip
            )
            
            log_info(f"Fetched {len(history)} workout history records for user {user_id}")
            
            return {
                'user_id': user_id,
                'page': page,
                'per_page': per_page,
                'total_records': len(history),
                'history': history
            }
        
        except Exception as e:
            log_error(f"Error fetching workout history: {e}")
            return {
                'user_id': user_id,
                'page': page,
                'per_page': per_page,
                'total_records': 0,
                'history': []
            }
    
    def get_calories_burned_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict:
        """
        Get calorie burn statistics for a user
        
        Args:
            user_id: User identifier
            days: Number of days to look back
        
        Returns:
            Dictionary with calorie statistics
        """
        try:
            summary = self.db_manager.get_calories_burned_summary(
                user_id=user_id,
                days=days
            )
            
            if summary:
                log_info(f"Calorie summary for user {user_id}: {summary.get('total_calories_burned', 0)} calories in {days} days")
            
            return summary
        
        except Exception as e:
            log_error(f"Error getting calorie summary: {e}")
            return {}
    
    def update_user_ml_data(self, user_id: str) -> bool:
        """
        Trigger ML model updates based on configuration
        
        Args:
            user_id: User identifier
        
        Returns:
            True if ML update triggered, False otherwise
        """
        try:
            # Get ML configuration
            ml_config = self.db_manager.get_ml_config()
            
            if not ml_config:
                log_error("ML configuration not found")
                return False
            
            training_window_days = ml_config.get('training_window_days', 30)
            min_sessions = ml_config.get('min_sessions_for_training', 5)
            
            # Get user's workout history for the training window
            history = self.db_manager.get_workout_history(
                user_id=user_id,
                limit=1000  # Get enough history
            )
            
            # Count unique workouts in the training window
            cutoff_date = datetime.utcnow() - timedelta(days=training_window_days)
            recent_workouts = set()
            
            for log in history:
                completed_at = log.get('completed_at')
                if isinstance(completed_at, datetime) and completed_at >= cutoff_date:
                    recent_workouts.add(log.get('workout_id'))
            
            workout_count = len(recent_workouts)
            
            # Check if user meets minimum sessions requirement
            if workout_count >= min_sessions:
                log_info(f"✅ User {user_id} has {workout_count} workouts in last {training_window_days} days - ML update triggered")
                # In a real implementation, this would trigger ML model retraining
                return True
            else:
                log_info(f"User {user_id} has only {workout_count} workouts (need {min_sessions}) - ML update not triggered")
                return False
        
        except Exception as e:
            log_error(f"Error updating user ML data: {e}")
            return False
    
    def get_workout_analytics(self, user_id: str, days: int = 30) -> Dict:
        """
        Get comprehensive workout analytics for a user
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
        
        Returns:
            Dictionary with analytics data
        """
        try:
            # Get calorie summary
            calorie_summary = self.get_calories_burned_summary(user_id, days)
            
            # Get workout history
            history = self.db_manager.get_workout_history(user_id, limit=1000)
            
            # Calculate workout frequency
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_logs = [
                log for log in history
                if isinstance(log.get('completed_at'), datetime)
                and log.get('completed_at') >= cutoff_date
            ]
            
            # Get unique workouts
            unique_workouts = set(log.get('workout_id') for log in recent_logs)
            workout_frequency = len(unique_workouts) / days if days > 0 else 0
            
            # Calculate average difficulty
            difficulty_ratings = [
                log.get('difficulty_rating', 5) for log in recent_logs
                if log.get('difficulty_rating') is not None
            ]
            avg_difficulty = sum(difficulty_ratings) / len(difficulty_ratings) if difficulty_ratings else 5
            
            # Get most common exercises
            exercise_counts = {}
            for log in recent_logs:
                ex_title = log.get('exercise_title', 'Unknown')
                exercise_counts[ex_title] = exercise_counts.get(ex_title, 0) + 1
            
            top_exercises = sorted(
                exercise_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            analytics = {
                'user_id': user_id,
                'period_days': days,
                'calorie_summary': calorie_summary,
                'workout_frequency': round(workout_frequency, 2),
                'total_exercises_logged': len(recent_logs),
                'average_difficulty': round(avg_difficulty, 1),
                'top_exercises': [{'title': title, 'count': count} for title, count in top_exercises]
            }
            
            log_info(f"Generated analytics for user {user_id}")
            return analytics
        
        except Exception as e:
            log_error(f"Error generating workout analytics: {e}")
            return {}
