"""
FitGen AI v6.0 - Enhanced Database Manager Module
Manages dataset, workout_history, and system_config collections
Provides methods for loading CSV data, exercise queries, and real-time logging
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE,
    COLLECTIONS,
    DATA_DIR
)
from utils import log_error, log_info, log_success, log_warning
from utils_v6.calorie_calculator import calculate_met_value

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MANAGER V6 CLASS
# ============================================================================

class DatabaseManagerV6:
    """
    Enhanced MongoDB connection manager for FitGen AI v6.0
    Manages: dataset, workout_history, system_config collections
    Handles: CSV loading, exercise queries, real-time logging, ML config
    """
    
    def __init__(self, connection_string: str = MONGODB_CONNECTION_STRING,
                 db_name: str = MONGODB_DATABASE):
        """
        Initialize enhanced database manager
        
        Args:
            connection_string: MongoDB connection string (local or Atlas)
            db_name: Database name (default: fitgen_db)
        """
        self.connection_string = connection_string
        self.db_name = db_name
        self.client = None
        self.db = None
        self.connected = False
        
        # Collection names
        self.dataset_collection = COLLECTIONS['dataset']
        self.workout_history_collection = COLLECTIONS['workout_history']
        self.system_config_collection = COLLECTIONS['system_config']
        
        # Connect and setup
        self.connect()
        if self.connected:
            self._create_indexes()
    
    def connect(self) -> bool:
        """
        Connect to MongoDB (Atlas or local)
        
        Returns:
            True if connected, False otherwise
        """
        if not MONGODB_AVAILABLE:
            log_error("MongoDB (pymongo) not installed")
            return False
        
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.connected = True
            
            log_success(f"✅ Connected to MongoDB: {self.db_name}")
            return True
        
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            log_error(f"MongoDB connection failed: {e}")
            self.connected = False
            return False
    
    def _create_indexes(self):
        """
        Create database indexes for optimal performance
        """
        try:
            if not self.connected:
                return
            
            # Dataset collection indexes
            self.db[self.dataset_collection].create_index(
                [("exercise_id", ASCENDING)], unique=True
            )
            self.db[self.dataset_collection].create_index([("body_part", ASCENDING)])
            self.db[self.dataset_collection].create_index([("equipment", ASCENDING)])
            self.db[self.dataset_collection].create_index([("level", ASCENDING)])
            self.db[self.dataset_collection].create_index([("type", ASCENDING)])
            
            # Workout history collection indexes
            self.db[self.workout_history_collection].create_index(
                [("user_id", ASCENDING), ("completed_at", DESCENDING)]
            )
            self.db[self.workout_history_collection].create_index([("workout_id", ASCENDING)])
            self.db[self.workout_history_collection].create_index([("exercise_id", ASCENDING)])
            
            # System config collection indexes
            self.db[self.system_config_collection].create_index([("config_type", ASCENDING)])
            
            log_info("✅ Database indexes created successfully")
        
        except Exception as e:
            log_warning(f"Error creating indexes: {e}")
    
    # ========================================================================
    # DATASET MANAGEMENT METHODS
    # ========================================================================
    
    def load_dataset_from_csv(self, csv_path: str = None) -> Dict[str, Any]:
        """
        Load exercises from CSV into dataset collection
        
        Args:
            csv_path: Path to CSV file (default: data/megaGymDataset.csv)
        
        Returns:
            Dictionary with loading statistics
        """
        if not self.connected:
            log_error("Not connected to MongoDB")
            return {"success": False, "error": "Not connected"}
        
        try:
            # Default CSV path
            if csv_path is None:
                csv_path = DATA_DIR / 'megaGymDataset.csv'
            
            log_info(f"Loading dataset from: {csv_path}")
            
            # Read CSV
            df = pd.read_csv(csv_path)
            df.columns = df.columns.str.strip()
            
            total_exercises = len(df)
            loaded_count = 0
            skipped_count = 0
            
            # Process each exercise
            for idx, row in df.iterrows():
                try:
                    # Generate exercise ID using hash of title for consistency
                    import hashlib
                    title = str(row.get('Title', '')).strip()
                    title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
                    exercise_id = f"ex_{title_hash}"
                    
                    # Extract exercise data
                    exercise_type = str(row.get('Type', 'Strength')).strip()
                    level = str(row.get('Level', 'Intermediate')).strip()
                    
                    # Calculate MET value
                    met_value = calculate_met_value(exercise_type, level)
                    
                    # Create exercise document
                    exercise_doc = {
                        'exercise_id': exercise_id,
                        'title': str(row.get('Title', '')).strip(),
                        'description': str(row.get('Desc', '')).strip(),
                        'type': exercise_type,
                        'body_part': str(row.get('BodyPart', '')).strip(),
                        'equipment': str(row.get('Equipment', '')).strip(),
                        'level': level,
                        'rating': float(row.get('Rating', 0.0)) if pd.notna(row.get('Rating')) else 0.0,
                        'rating_desc': str(row.get('RatingDesc', '')).strip() if pd.notna(row.get('RatingDesc')) else '',
                        'met_value': met_value,
                        'video_url': None,  # Placeholder for future S3 links
                        'video_duration_seconds': None,
                        'is_active': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                    
                    # Insert or update
                    self.db[self.dataset_collection].update_one(
                        {'exercise_id': exercise_id},
                        {'$set': exercise_doc},
                        upsert=True
                    )
                    
                    loaded_count += 1
                
                except Exception as e:
                    log_warning(f"Error loading exercise {idx}: {e}")
                    skipped_count += 1
            
            result = {
                'success': True,
                'total_exercises': total_exercises,
                'loaded': loaded_count,
                'skipped': skipped_count
            }
            
            log_success(f"✅ Loaded {loaded_count} exercises into dataset collection")
            return result
        
        except Exception as e:
            log_error(f"Error loading dataset from CSV: {e}")
            return {"success": False, "error": str(e)}
    
    def get_exercise_by_id(self, exercise_id: str) -> Optional[Dict[str, Any]]:
        """
        Get exercise details by ID
        
        Args:
            exercise_id: Exercise ID
        
        Returns:
            Exercise document or None
        """
        if not self.connected:
            return None
        
        try:
            exercise = self.db[self.dataset_collection].find_one(
                {'exercise_id': exercise_id, 'is_active': True}
            )
            
            if exercise:
                exercise['_id'] = str(exercise['_id'])
            
            return exercise
        
        except Exception as e:
            log_error(f"Error fetching exercise {exercise_id}: {e}")
            return None
    
    def get_exercises_by_filters(
        self,
        body_part: str = None,
        equipment: str = None,
        level: str = None,
        exercise_type: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get exercises with filters
        
        Args:
            body_part: Filter by body part
            equipment: Filter by equipment
            level: Filter by difficulty level
            exercise_type: Filter by exercise type
            limit: Maximum number of results
        
        Returns:
            List of exercise documents
        """
        if not self.connected:
            return []
        
        try:
            # Build query
            query = {'is_active': True}
            
            if body_part:
                query['body_part'] = body_part
            if equipment:
                query['equipment'] = equipment
            if level:
                query['level'] = level
            if exercise_type:
                query['type'] = exercise_type
            
            # Execute query
            exercises = list(
                self.db[self.dataset_collection]
                .find(query)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for exercise in exercises:
                exercise['_id'] = str(exercise['_id'])
            
            return exercises
        
        except Exception as e:
            log_error(f"Error fetching exercises with filters: {e}")
            return []
    
    def update_exercise(self, exercise_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update exercise fields (e.g., video URL)
        
        Args:
            exercise_id: Exercise ID
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            updates['updated_at'] = datetime.utcnow()
            
            result = self.db[self.dataset_collection].update_one(
                {'exercise_id': exercise_id},
                {'$set': updates}
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            log_error(f"Error updating exercise {exercise_id}: {e}")
            return False
    
    # ========================================================================
    # REAL-TIME EXERCISE LOGGING METHODS
    # ========================================================================
    
    def log_exercise_completion(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Log individual exercise completion in real-time
        
        Args:
            log_data: Exercise log dictionary with required fields
        
        Returns:
            Log ID if successful, None otherwise
        """
        if not self.connected:
            return None
        
        try:
            # Generate log ID
            from utils import generate_id
            log_id = f"log_{generate_id()}"
            
            # Create log document
            log_doc = {
                'log_id': log_id,
                'user_id': log_data['user_id'],
                'workout_id': log_data['workout_id'],
                'exercise_id': log_data['exercise_id'],
                'exercise_title': log_data.get('exercise_title', ''),
                'phase': log_data.get('phase', 'main_course'),
                'completed_at': datetime.utcnow(),
                'planned_sets': log_data.get('planned_sets', 0),
                'completed_sets': log_data.get('completed_sets', 0),
                'planned_reps': log_data.get('planned_reps', 0),
                'actual_reps': log_data.get('actual_reps', []),
                'weight_used_kg': log_data.get('weight_used_kg', 0),
                'duration_minutes': log_data.get('duration_minutes', 0),
                'calories_burned': log_data.get('calories_burned', 0),
                'difficulty_rating': log_data.get('difficulty_rating', 5),
                'notes': log_data.get('notes', ''),
                'workout_status': log_data.get('workout_status', 'in_progress')
            }
            
            # Insert log
            self.db[self.workout_history_collection].insert_one(log_doc)
            
            log_info(f"✅ Logged exercise: {log_data['exercise_title']}")
            return log_id
        
        except Exception as e:
            log_error(f"Error logging exercise completion: {e}")
            return None
    
    def get_workout_history(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's workout history with pagination
        
        Args:
            user_id: User ID
            limit: Number of records to return
            skip: Number of records to skip
        
        Returns:
            List of workout history documents
        """
        if not self.connected:
            return []
        
        try:
            history = list(
                self.db[self.workout_history_collection]
                .find({'user_id': user_id})
                .sort('completed_at', DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for log in history:
                log['_id'] = str(log['_id'])
            
            return history
        
        except Exception as e:
            log_error(f"Error fetching workout history: {e}")
            return []
    
    def get_workout_status(self, workout_id: str) -> Dict[str, Any]:
        """
        Get current workout status and progress
        
        Args:
            workout_id: Workout ID
        
        Returns:
            Dictionary with workout status and completed exercises
        """
        if not self.connected:
            return {}
        
        try:
            logs = list(
                self.db[self.workout_history_collection]
                .find({'workout_id': workout_id})
                .sort('completed_at', ASCENDING)
            )
            
            # Convert ObjectId to string
            for log in logs:
                log['_id'] = str(log['_id'])
            
            # Calculate summary
            total_exercises = len(logs)
            total_calories = sum(log.get('calories_burned', 0) for log in logs)
            total_duration = sum(log.get('duration_minutes', 0) for log in logs)
            
            status = logs[0].get('workout_status', 'in_progress') if logs else 'not_started'
            
            return {
                'workout_id': workout_id,
                'status': status,
                'total_exercises_completed': total_exercises,
                'total_calories_burned': round(total_calories, 1),
                'total_duration_minutes': round(total_duration, 1),
                'exercises': logs
            }
        
        except Exception as e:
            log_error(f"Error fetching workout status: {e}")
            return {}
    
    def complete_workout(self, workout_id: str) -> bool:
        """
        Mark workout as completed
        
        Args:
            workout_id: Workout ID
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            result = self.db[self.workout_history_collection].update_many(
                {'workout_id': workout_id},
                {'$set': {'workout_status': 'completed'}}
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            log_error(f"Error completing workout: {e}")
            return False
    
    def get_calories_burned_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get calorie burn statistics for a user
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            Dictionary with calorie statistics
        """
        if not self.connected:
            return {}
        
        try:
            # Calculate date range
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Query logs
            logs = list(
                self.db[self.workout_history_collection]
                .find({
                    'user_id': user_id,
                    'completed_at': {'$gte': start_date}
                })
            )
            
            # Calculate statistics
            total_calories = sum(log.get('calories_burned', 0) for log in logs)
            total_workouts = len(set(log['workout_id'] for log in logs))
            total_exercises = len(logs)
            avg_calories_per_workout = total_calories / total_workouts if total_workouts > 0 else 0
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_calories_burned': round(total_calories, 1),
                'total_workouts': total_workouts,
                'total_exercises': total_exercises,
                'avg_calories_per_workout': round(avg_calories_per_workout, 1)
            }
        
        except Exception as e:
            log_error(f"Error calculating calorie summary: {e}")
            return {}
    
    # ========================================================================
    # ML CONFIGURATION METHODS
    # ========================================================================
    
    def get_ml_config(self) -> Optional[Dict[str, Any]]:
        """
        Get current ML training configuration
        
        Returns:
            ML config document or None
        """
        if not self.connected:
            return None
        
        try:
            config = self.db[self.system_config_collection].find_one(
                {'config_type': 'ml_training'}
            )
            
            if config:
                config['_id'] = str(config['_id'])
            else:
                # Create default config if not exists
                config = self._create_default_ml_config()
            
            return config
        
        except Exception as e:
            log_error(f"Error fetching ML config: {e}")
            return None
    
    def _create_default_ml_config(self) -> Dict[str, Any]:
        """
        Create default ML training configuration
        
        Returns:
            Default ML config document
        """
        try:
            config = {
                'config_type': 'ml_training',
                'training_window_days': 30,
                'min_sessions_for_training': 5,
                'created_at': datetime.utcnow(),
                'last_updated': datetime.utcnow()
            }
            
            self.db[self.system_config_collection].insert_one(config)
            config['_id'] = str(config['_id'])
            
            log_info("✅ Created default ML training config")
            return config
        
        except Exception as e:
            log_error(f"Error creating default ML config: {e}")
            return {}
    
    def update_ml_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update ML training configuration
        
        Args:
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            updates['last_updated'] = datetime.utcnow()
            
            result = self.db[self.system_config_collection].update_one(
                {'config_type': 'ml_training'},
                {'$set': updates},
                upsert=True
            )
            
            log_success(f"✅ Updated ML config: {updates}")
            return True
        
        except Exception as e:
            log_error(f"Error updating ML config: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            log_info("MongoDB connection closed")
