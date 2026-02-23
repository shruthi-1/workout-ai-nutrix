"""
FitGen AI v5.0 - API Service Layer
Provides API-compatible methods for all FitGen functionality
Feature 34: FastAPI Integration Support
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from db.database_manager import DatabaseManager
from data.exercise_database import ExerciseDatabase
from user.profile_manager import UserProfileManager
from workout.workout_gen import WorkoutGenerator
from workout.session_logger import SessionLogger
from motivation.motivation_system import MotivationSystem
from utils import log_error, log_success, log_info

logger = logging.getLogger(__name__)


class FitGenService:
    """
    Service layer providing API-compatible methods for FitGen AI
    All methods return JSON-serializable Dict with 'success' key
    """
    
    def __init__(self):
        """Initialize FitGen service with all components"""
        try:
            self.db_manager = DatabaseManager()
            self.exercise_db = ExerciseDatabase(self.db_manager)
            self.profile_manager = UserProfileManager(self.db_manager)
            self.workout_generator = WorkoutGenerator(self.db_manager, self.exercise_db)
            self.session_logger = SessionLogger(self.db_manager)
            self.motivation_system = MotivationSystem(self.db_manager)
            log_success("FitGenService initialized successfully")
        except Exception as e:
            log_error(f"Failed to initialize FitGenService: {e}")
            raise
    
    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================
    
    def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user profile
        
        Args:
            user_data: Dict with name, age, height_cm, weight_kg, fitness_level, goal, etc.
        
        Returns:
            Dict with success, message, and user_id if successful
        """
        try:
            success, result = self.profile_manager.create_user(
                name=user_data.get('name'),
                age=user_data.get('age'),
                height_cm=user_data.get('height_cm'),
                weight_kg=user_data.get('weight_kg'),
                fitness_level=user_data.get('fitness_level', 'Beginner'),
                goal=user_data.get('goal', 'General Fitness'),
                gender=user_data.get('gender', 'Other'),
                equipment_available=user_data.get('equipment', ['Body Only']),
                injuries=user_data.get('injuries', [])
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'User created successfully',
                    'user_id': result
                }
            else:
                return {
                    'success': False,
                    'message': result
                }
        except Exception as e:
            log_error(f"Error creating user: {e}")
            return {
                'success': False,
                'message': f"Error creating user: {str(e)}"
            }
    
    def get_user(self, user_id: str) -> Dict:
        """
        Get user profile by ID
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with success, message, and user data if found
        """
        try:
            user = self.profile_manager.get_user(user_id)
            if user:
                return {
                    'success': True,
                    'user': user
                }
            else:
                return {
                    'success': False,
                    'message': 'User not found'
                }
        except Exception as e:
            log_error(f"Error getting user: {e}")
            return {
                'success': False,
                'message': f"Error getting user: {str(e)}"
            }
    
    def update_user(self, user_id: str, updates: Dict) -> Dict:
        """
        Update user profile
        
        Args:
            user_id: User identifier
            updates: Dict with fields to update (weight_kg, fitness_level, goal, etc.)
        
        Returns:
            Dict with success and message
        """
        try:
            results = []
            
            if 'weight_kg' in updates:
                success, msg = self.profile_manager.update_weight(user_id, updates['weight_kg'])
                results.append((success, msg))
            
            if 'fitness_level' in updates:
                success, msg = self.profile_manager.update_fitness_level(user_id, updates['fitness_level'])
                results.append((success, msg))
            
            if 'goal' in updates:
                success, msg = self.profile_manager.update_goal(user_id, updates['goal'])
                results.append((success, msg))
            
            if all(r[0] for r in results):
                return {
                    'success': True,
                    'message': 'User updated successfully'
                }
            else:
                failed = [r[1] for r in results if not r[0]]
                return {
                    'success': False,
                    'message': f"Some updates failed: {', '.join(failed)}"
                }
        except Exception as e:
            log_error(f"Error updating user: {e}")
            return {
                'success': False,
                'message': f"Error updating user: {str(e)}"
            }
    
    def delete_user(self, user_id: str) -> Dict:
        """
        Delete user profile
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with success and message
        """
        try:
            success, msg = self.profile_manager.delete_user(user_id)
            return {
                'success': success,
                'message': msg
            }
        except Exception as e:
            log_error(f"Error deleting user: {e}")
            return {
                'success': False,
                'message': f"Error deleting user: {str(e)}"
            }
    
    def get_all_users(self) -> Dict:
        """
        Get all user profiles
        
        Returns:
            Dict with success, message, and list of users
        """
        try:
            users = self.profile_manager.get_all_users()
            return {
                'success': True,
                'users': users,
                'count': len(users)
            }
        except Exception as e:
            log_error(f"Error getting all users: {e}")
            return {
                'success': False,
                'message': f"Error getting users: {str(e)}",
                'users': []
            }
    
    # ========================================================================
    # WORKOUT GENERATION
    # ========================================================================
    
    def generate_daily_workout(self, user_id: str, target_body_parts: Optional[List[str]] = None,
                               duration_minutes: int = 45) -> Dict:
        """
        Generate a daily workout for user
        
        Args:
            user_id: User identifier
            target_body_parts: Optional list of body parts to target
            duration_minutes: Workout duration in minutes
        
        Returns:
            Dict with success, message, and workout data
        """
        try:
            user = self.profile_manager.get_user(user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            workout = self.workout_generator.generate_daily_workout(
                user=user,
                target_body_parts=target_body_parts,
                duration_minutes=duration_minutes
            )
            
            return {
                'success': True,
                'workout': workout
            }
        except Exception as e:
            log_error(f"Error generating workout: {e}")
            return {
                'success': False,
                'message': f"Error generating workout: {str(e)}"
            }
    
    def generate_weekly_plan(self, user_id: str, split_type: str = 'Push/Pull/Legs') -> Dict:
        """
        Generate a weekly workout plan for user
        
        Args:
            user_id: User identifier
            split_type: Training split type
        
        Returns:
            Dict with success, message, and weekly plan data
        """
        try:
            user = self.profile_manager.get_user(user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            plan = self.workout_generator.generate_weekly_plan(
                user=user,
                split_type=split_type
            )
            
            return {
                'success': True,
                'plan': plan
            }
        except Exception as e:
            log_error(f"Error generating weekly plan: {e}")
            return {
                'success': False,
                'message': f"Error generating weekly plan: {str(e)}"
            }
    
    def save_weekly_plan(self, plan: Dict) -> Dict:
        """
        Save weekly plan to database
        
        Args:
            plan: Weekly plan document
        
        Returns:
            Dict with success and message
        """
        try:
            success = self.workout_generator.save_weekly_plan(plan)
            if success:
                return {
                    'success': True,
                    'message': 'Weekly plan saved successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to save weekly plan. Database may not be connected.'
                }
        except Exception as e:
            log_error(f"Error saving weekly plan: {e}")
            return {
                'success': False,
                'message': f"Error saving weekly plan: {str(e)}"
            }
    
    # ========================================================================
    # SESSION LOGGING
    # ========================================================================
    
    def log_workout_session(self, user_id: str, workout_data: Dict) -> Dict:
        """
        Log a completed workout session
        
        Args:
            user_id: User identifier
            workout_data: Dict with workout details (duration, exercises, ratings, etc.)
        
        Returns:
            Dict with success, message, and session_id if successful
        """
        try:
            success, result = self.session_logger.log_workout(
                user_id=user_id,
                workout_id=workout_data.get('workout_id'),
                planned_duration=workout_data.get('planned_duration', 60),
                actual_duration=workout_data.get('actual_duration', 60),
                completion_rate=workout_data.get('completion_rate', 100),
                satisfaction_rating=workout_data.get('satisfaction_rating', 7),
                exercises_completed=workout_data.get('exercises_completed', []),
                notes=workout_data.get('notes', '')
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Workout logged successfully',
                    'session_id': result
                }
            else:
                return {
                    'success': False,
                    'message': result
                }
        except Exception as e:
            log_error(f"Error logging workout: {e}")
            return {
                'success': False,
                'message': f"Error logging workout: {str(e)}"
            }
    
    def get_weekly_summary(self, user_id: str) -> Dict:
        """
        Get weekly workout summary for user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with success and summary data
        """
        try:
            summary = self.session_logger.get_weekly_summary(user_id)
            return {
                'success': True,
                'summary': summary
            }
        except Exception as e:
            log_error(f"Error getting weekly summary: {e}")
            return {
                'success': False,
                'message': f"Error getting weekly summary: {str(e)}"
            }
    
    def get_streak(self, user_id: str) -> Dict:
        """
        Get workout streak for user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with success and streak data
        """
        try:
            current_streak, longest_streak = self.session_logger.get_workout_streak(user_id)
            return {
                'success': True,
                'current_streak': current_streak,
                'longest_streak': longest_streak
            }
        except Exception as e:
            log_error(f"Error getting streak: {e}")
            return {
                'success': False,
                'message': f"Error getting streak: {str(e)}"
            }
    
    def get_strength_progress(self, user_id: str) -> Dict:
        """
        Get strength progress for user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with success and progress data
        """
        try:
            progress = self.session_logger.get_strength_progress(user_id)
            return {
                'success': True,
                'progress': progress
            }
        except Exception as e:
            log_error(f"Error getting strength progress: {e}")
            return {
                'success': False,
                'message': f"Error getting strength progress: {str(e)}"
            }
    
    def export_sessions_to_csv(self, user_id: str, filepath: Optional[str] = None) -> Dict:
        """
        Export user sessions to CSV
        
        Args:
            user_id: User identifier
            filepath: Optional file path for CSV
        
        Returns:
            Dict with success, message, and filepath if successful
        """
        try:
            success, msg = self.session_logger.export_all_sessions_to_csv(user_id, filepath)
            if success:
                return {
                    'success': True,
                    'message': msg,
                    'filepath': filepath or msg.split(': ')[-1] if ': ' in msg else filepath
                }
            else:
                return {
                    'success': False,
                    'message': msg
                }
        except Exception as e:
            log_error(f"Error exporting sessions: {e}")
            return {
                'success': False,
                'message': f"Error exporting sessions: {str(e)}"
            }
    
    # ========================================================================
    # MOOD TRACKING
    # ========================================================================
    
    def log_mood(self, user_id: str, mood_score: int, notes: str = '') -> Dict:
        """
        Log mood check-in for user
        
        Args:
            user_id: User identifier
            mood_score: Mood score (1-10)
            notes: Optional notes
        
        Returns:
            Dict with success and message
        """
        try:
            success, msg = self.motivation_system.log_mood_checkin(user_id, mood_score, notes)
            return {
                'success': success,
                'message': msg
            }
        except Exception as e:
            log_error(f"Error logging mood: {e}")
            return {
                'success': False,
                'message': f"Error logging mood: {str(e)}"
            }
    
    def get_mood_history(self, user_id: str) -> Dict:
        """
        Get mood history for user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with success and mood history data
        """
        try:
            history = self.motivation_system.get_mood_summary(user_id)
            return {
                'success': True,
                'mood_history': history
            }
        except Exception as e:
            log_error(f"Error getting mood history: {e}")
            return {
                'success': False,
                'message': f"Error getting mood history: {str(e)}"
            }
    
    # ========================================================================
    # EXERCISE DATABASE
    # ========================================================================
    
    def get_exercises(self, filters: Optional[Dict] = None, limit: int = 50) -> Dict:
        """
        Get exercises from database with optional filters
        
        Args:
            filters: Optional dict with body_part, equipment, level filters
            limit: Maximum number of exercises to return
        
        Returns:
            Dict with success and exercises list
        """
        try:
            exercises = []
            
            if filters and 'body_part' in filters:
                exercises = self.exercise_db.get_exercises_by_body_part(
                    filters['body_part'], limit=limit
                )
            elif filters and 'equipment' in filters:
                exercises = self.exercise_db.get_exercises_by_equipment(
                    filters['equipment'], limit=limit
                )
            else:
                # Get random exercises if no filter
                exercises = self.exercise_db.get_random_exercises(limit)
            
            return {
                'success': True,
                'exercises': exercises,
                'count': len(exercises)
            }
        except Exception as e:
            log_error(f"Error getting exercises: {e}")
            return {
                'success': False,
                'message': f"Error getting exercises: {str(e)}",
                'exercises': []
            }
    
    def get_exercise_statistics(self) -> Dict:
        """
        Get exercise database statistics
        
        Returns:
            Dict with success and statistics
        """
        try:
            stats = self.exercise_db.get_statistics()
            return {
                'success': True,
                'statistics': stats
            }
        except Exception as e:
            log_error(f"Error getting exercise statistics: {e}")
            return {
                'success': False,
                'message': f"Error getting exercise statistics: {str(e)}"
            }
    
    def search_exercises(self, query: str, limit: int = 20) -> Dict:
        """
        Search exercises by title
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            Dict with success and search results
        """
        try:
            exercises = self.exercise_db.search_exercises(query, limit=limit)
            return {
                'success': True,
                'exercises': exercises,
                'count': len(exercises)
            }
        except Exception as e:
            log_error(f"Error searching exercises: {e}")
            return {
                'success': False,
                'message': f"Error searching exercises: {str(e)}",
                'exercises': []
            }
    
    # ========================================================================
    # ADMIN & SYSTEM
    # ========================================================================
    
    def get_connection_status(self) -> Dict:
        """
        Get database connection status
        
        Returns:
            Dict with connection information
        """
        try:
            status = self.db_manager.get_connection_status()
            return {
                'success': True,
                'status': status
            }
        except Exception as e:
            log_error(f"Error getting connection status: {e}")
            return {
                'success': False,
                'message': f"Error getting connection status: {str(e)}"
            }
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics for all collections
        
        Returns:
            Dict with collection statistics
        """
        try:
            stats = self.db_manager.get_collection_stats()
            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            log_error(f"Error getting collection stats: {e}")
            return {
                'success': False,
                'message': f"Error getting collection stats: {str(e)}"
            }
    
    def backup_database(self, backup_path: Optional[str] = None) -> Dict:
        """
        Backup database to file
        
        Args:
            backup_path: Optional custom backup path
        
        Returns:
            Dict with success and backup path
        """
        try:
            success, result = self.db_manager.backup_database(backup_path)
            if success:
                return {
                    'success': True,
                    'message': 'Database backed up successfully',
                    'backup_path': result
                }
            else:
                return {
                    'success': False,
                    'message': result
                }
        except Exception as e:
            log_error(f"Error backing up database: {e}")
            return {
                'success': False,
                'message': f"Error backing up database: {str(e)}"
            }
    
    def close(self) -> Dict:
        """
        Close all connections and cleanup
        
        Returns:
            Dict with success message
        """
        try:
            if self.db_manager:
                self.db_manager.close()
            return {
                'success': True,
                'message': 'FitGenService closed successfully'
            }
        except Exception as e:
            log_error(f"Error closing service: {e}")
            return {
                'success': False,
                'message': f"Error closing service: {str(e)}"
            }
