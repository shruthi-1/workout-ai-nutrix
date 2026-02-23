"""
FitGen AI v5.0 - User Profile Manager Module
Manages user profiles with all tracking data and personalization
Features 25-27: User Profiles, User Data, Profile Editing
"""

import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from config import (
    FITNESS_LEVELS,
    FITNESS_GOALS,
    INJURY_TYPES,
    EQUIPMENT_TYPES,
    BMI_CATEGORIES
)
from utils import (
    calculate_bmi,
    generate_id,
    get_current_datetime,
    validate_user_profile,
    log_error,
    log_success,
    log_info
)
from db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# USER PROFILE MANAGER CLASS
# ============================================================================

class UserProfileManager:
    """
    Manages user profiles with comprehensive tracking
    Features 25-27: User profiles, data tracking, profile editing
    Stores: age, height, weight, BMI, fitness level, goals, equipment, injuries
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize user profile manager
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.users_collection = 'users'
        self.in_memory_users = {}
    
    # ========================================================================
    # USER CREATION (Feature 25)
    # ========================================================================
    
    def create_user(self, user_id: str, profile: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Create new user profile
        Feature 25: Create unlimited user profiles
        
        Args:
            user_id: Unique user identifier
            profile: User profile data dict
        
        Returns:
            Tuple: (success, user_doc, message)
        """
        # Validate profile
        valid, msg = validate_user_profile(profile)
        if not valid:
            return False, None, msg
        
        # Check if user already exists
        existing = self.get_user(user_id)
        if existing:
            return False, None, f"User {user_id} already exists"
        
        # Calculate BMI
        bmi = calculate_bmi(profile.get('height_cm'), profile.get('weight_kg'))
        bmi_category = self._get_bmi_category(bmi)
        
        # Create user document
        user_doc = {
            'user_id': user_id,
            'name': profile.get('name', 'User'),
            'age': profile.get('age'),
            'gender': profile.get('gender', 'Not specified'),
            'height_cm': profile.get('height_cm'),
            'weight_kg': profile.get('weight_kg'),
            'bmi': bmi,
            'bmi_category': bmi_category,
            'fitness_level': profile.get('fitness_level', 'Intermediate'),
            'goal': profile.get('goal', 'General Fitness'),
            'equipment_available': profile.get('equipment', []),
            'injuries': profile.get('injuries', []),
            'created_at': get_current_datetime(),
            'updated_at': get_current_datetime(),
            'last_workout': None,
            'preferences': {
                'body_part_preferences': {},
                'recent_exercises': [],
                'satisfaction_ratings': {}
            },
            'performance': {
                'total_workouts': 0,
                'avg_completion_rate': 0.0,
                'avg_satisfaction': 0.0,
                'total_training_minutes': 0,
                'current_streak': 0,
                'longest_streak': 0
            }
        }
        
        # Insert to database
        if self.db_manager.is_connected():
            success = self.db_manager.insert_one(self.users_collection, user_doc)
            if success:
                log_success(f"User created: {user_id}")
                return True, user_doc, "User created successfully"
            else:
                return False, None, "Failed to insert user to database"
        else:
            # In-memory fallback
            self.in_memory_users[user_id] = user_doc
            log_success(f"User created (in-memory): {user_id}")
            return True, user_doc, "User created successfully (in-memory)"
    
    # ========================================================================
    # RETRIEVE USER DATA (Feature 26)
    # ========================================================================
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get user profile by ID
        Feature 26: Retrieve user data
        
        Args:
            user_id: User identifier
        
        Returns:
            User document or None
        """
        if self.db_manager.is_connected():
            return self.db_manager.find_one(self.users_collection, {'user_id': user_id})
        else:
            return self.in_memory_users.get(user_id)
    
    def get_all_users(self, limit: int = 100) -> List[Dict]:
        """
        Get all users (Feature 26)
        
        Args:
            limit: Maximum users to return
        
        Returns:
            List of user documents
        """
        if self.db_manager.is_connected():
            return self.db_manager.find_many(self.users_collection, limit=limit)
        else:
            return list(self.in_memory_users.values())[:limit]
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        return self.get_user(user_id) is not None
    
    # ========================================================================
    # UPDATE USER PROFILE (Feature 27)
    # ========================================================================
    
    def update_user(self, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """
        Update user profile
        Feature 27: Profile editing
        
        Args:
            user_id: User identifier
            updates: Fields to update
        
        Returns:
            Tuple: (success, message)
        """
        user = self.get_user(user_id)
        if not user:
            return False, f"User {user_id} not found"
        
        # Recalculate BMI if weight/height updated
        if 'height_cm' in updates or 'weight_kg' in updates:
            height = updates.get('height_cm', user.get('height_cm'))
            weight = updates.get('weight_kg', user.get('weight_kg'))
            bmi = calculate_bmi(height, weight)
            updates['bmi'] = bmi
            updates['bmi_category'] = self._get_bmi_category(bmi)
        
        # Add timestamp
        updates['updated_at'] = get_current_datetime()
        
        if self.db_manager.is_connected():
            success = self.db_manager.update_one(
                self.users_collection,
                {'user_id': user_id},
                updates
            )
            if success:
                log_success(f"User updated: {user_id}")
                return True, "User updated successfully"
            else:
                return False, "Failed to update user"
        else:
            # In-memory update
            if user_id in self.in_memory_users:
                self.in_memory_users[user_id].update(updates)
                log_success(f"User updated (in-memory): {user_id}")
                return True, "User updated successfully (in-memory)"
            else:
                return False, "User not found"
    
    def update_weight(self, user_id: str, new_weight: float) -> Tuple[bool, str]:
        """
        Update user weight (Feature 27)
        Automatically recalculates BMI and category
        """
        return self.update_user(user_id, {'weight_kg': new_weight})
    
    def update_fitness_level(self, user_id: str, level: str) -> Tuple[bool, str]:
        """
        Update user fitness level (Feature 27)
        Must be: Beginner, Intermediate, or Expert
        """
        if level not in FITNESS_LEVELS:
            return False, f"Invalid fitness level. Must be one of: {FITNESS_LEVELS}"
        return self.update_user(user_id, {'fitness_level': level})
    
    def update_goal(self, user_id: str, goal: str) -> Tuple[bool, str]:
        """
        Update user fitness goal (Feature 27)
        Must be one of the 6 fitness goals
        """
        if goal not in [
            'Weight Loss', 'Muscle Gain', 'Strength',
            'Endurance', 'General Fitness', 'Athletic Performance'
        ]:
            return False, f"Invalid goal. Must be one of: {list(['Weight Loss', 'Muscle Gain', 'Strength', 'Endurance', 'General Fitness', 'Athletic Performance'])}"
        return self.update_user(user_id, {'goal': goal})
    
    def update_equipment(self, user_id: str, equipment: List[str]) -> Tuple[bool, str]:
        """
        Update available equipment (Feature 27)
        """
        # Validate equipment types
        valid_equipment = all(e in EQUIPMENT_TYPES for e in equipment)
        if not valid_equipment:
            return False, f"Invalid equipment types. Must be from: {EQUIPMENT_TYPES}"
        
        return self.update_user(user_id, {'equipment_available': equipment})
    
    def add_injury(self, user_id: str, injury: str) -> Tuple[bool, str]:
        """
        Add injury to user profile (Feature 27, Feature 5)
        """
        if injury not in INJURY_TYPES:
            return False, f"Invalid injury type. Must be one of: {INJURY_TYPES}"
        
        user = self.get_user(user_id)
        if not user:
            return False, f"User {user_id} not found"
        
        injuries = user.get('injuries', [])
        if injury not in injuries:
            injuries.append(injury)
            return self.update_user(user_id, {'injuries': injuries})
        else:
            return False, f"User already has {injury} injury recorded"
    
    def remove_injury(self, user_id: str, injury: str) -> Tuple[bool, str]:
        """
        Remove injury from user profile (Feature 27)
        """
        user = self.get_user(user_id)
        if not user:
            return False, f"User {user_id} not found"
        
        injuries = user.get('injuries', [])
        if injury in injuries:
            injuries.remove(injury)
            return self.update_user(user_id, {'injuries': injuries})
        else:
            return False, f"User does not have {injury} injury recorded"
    
    # ========================================================================
    # DELETE USER
    # ========================================================================
    
    def delete_user(self, user_id: str) -> Tuple[bool, str]:
        """
        Delete user profile (Feature 25)
        
        Args:
            user_id: User identifier
        
        Returns:
            Tuple: (success, message)
        """
        user = self.get_user(user_id)
        if not user:
            return False, f"User {user_id} not found"
        
        if self.db_manager.is_connected():
            success = self.db_manager.delete_one(self.users_collection, {'user_id': user_id})
            if success:
                log_success(f"User deleted: {user_id}")
                return True, "User deleted successfully"
            else:
                return False, "Failed to delete user"
        else:
            # In-memory delete
            if user_id in self.in_memory_users:
                del self.in_memory_users[user_id]
                log_success(f"User deleted (in-memory): {user_id}")
                return True, "User deleted successfully (in-memory)"
            else:
                return False, "User not found"
    
    # ========================================================================
    # BMI & SAFETY RULES (Feature 4)
    # ========================================================================
    
    def _get_bmi_category(self, bmi: float) -> str:
        """Get BMI category from BMI value"""
        if bmi < 16:
            return 'Severe Underweight'
        elif bmi < 18.5:
            return 'Underweight'
        elif bmi < 25:
            return 'Normal'
        elif bmi < 30:
            return 'Overweight'
        elif bmi < 35:
            return 'Obese'
        elif bmi < 40:
            return 'Severely Obese'
        else:
            return 'Extremely Obese'
    
    def get_bmi_info(self, user_id: str) -> Optional[Dict]:
        """
        Get user's BMI information (Feature 4)
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with BMI info or None
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        from config import BMI_SAFETY_RULES
        
        return {
            'bmi': user.get('bmi'),
            'category': user.get('bmi_category'),
            'height_cm': user.get('height_cm'),
            'weight_kg': user.get('weight_kg'),
            'safety_rules': BMI_SAFETY_RULES.get(user.get('bmi_category'), {})
        }
    
    # ========================================================================
    # USER PREFERENCES (Feature 10)
    # ========================================================================
    
    def set_body_part_preference(self, user_id: str, body_part: str, score: float) -> Tuple[bool, str]:
        """
        Set preference score for body part (Feature 10)
        Score: 0.0 to 1.0
        """
        user = self.get_user(user_id)
        if not user:
            return False, f"User {user_id} not found"
        
        if not 0 <= score <= 1:
            return False, "Score must be between 0 and 1"
        
        preferences = user.get('preferences', {})
        body_part_prefs = preferences.get('body_part_preferences', {})
        body_part_prefs[body_part] = score
        preferences['body_part_preferences'] = body_part_prefs
        
        return self.update_user(user_id, {'preferences': preferences})
    
    def get_body_part_preferences(self, user_id: str) -> Optional[Dict]:
        """
        Get user's body part preferences (Feature 10)
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        return user.get('preferences', {}).get('body_part_preferences', {})
    
    def add_to_recent_exercises(self, user_id: str, exercise_id: str) -> Tuple[bool, str]:
        """
        Add exercise to recent history (Feature 11: Recency Management)
        """
        user = self.get_user(user_id)
        if not user:
            return False, f"User {user_id} not found"
        
        preferences = user.get('preferences', {})
        recent = preferences.get('recent_exercises', [])
        
        # Keep only last 20
        if exercise_id in recent:
            recent.remove(exercise_id)
        recent.append(exercise_id)
        recent = recent[-20:]
        
        preferences['recent_exercises'] = recent
        return self.update_user(user_id, {'preferences': preferences})
    
    # ========================================================================
    # USER STATISTICS
    # ========================================================================
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """
        Get user performance statistics
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        return {
            'user_id': user_id,
            'name': user.get('name'),
            'age': user.get('age'),
            'bmi': user.get('bmi'),
            'fitness_level': user.get('fitness_level'),
            'goal': user.get('goal'),
            'injuries': user.get('injuries', []),
            'performance': user.get('performance', {}),
            'created_at': user.get('created_at'),
            'last_workout': user.get('last_workout')
        }
    
    def update_workout_stats(self, user_id: str, workout_data: Dict) -> Tuple[bool, str]:
        """
        Update user's workout statistics after logging a session
        """
        user = self.get_user(user_id)
        if not user:
            return False, f"User {user_id} not found"
        
        performance = user.get('performance', {})
        
        # Update totals
        performance['total_workouts'] = performance.get('total_workouts', 0) + 1
        
        # Update completion rate
        completion = workout_data.get('completion_percentage', 100)
        current_avg = performance.get('avg_completion_rate', 0)
        total_workouts = performance['total_workouts']
        performance['avg_completion_rate'] = (
            (current_avg * (total_workouts - 1) + completion) / total_workouts
        )
        
        # Update satisfaction
        satisfaction = workout_data.get('satisfaction_rating', 5)
        current_satisfaction = performance.get('avg_satisfaction', 0)
        performance['avg_satisfaction'] = (
            (current_satisfaction * (total_workouts - 1) + satisfaction) / total_workouts
        )
        
        # Update training time
        duration = workout_data.get('duration', 0)
        performance['total_training_minutes'] = performance.get('total_training_minutes', 0) + duration
        
        # Update last workout
        updates = {
            'performance': performance,
            'last_workout': get_current_datetime()
        }
        
        return self.update_user(user_id, updates)
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def count_users(self) -> int:
        """Get total number of users"""
        if self.db_manager.is_connected():
            return self.db_manager.count(self.users_collection)
        else:
            return len(self.in_memory_users)
    
    def get_users_by_goal(self, goal: str, limit: int = 50) -> List[Dict]:
        """Get users with specific fitness goal"""
        if self.db_manager.is_connected():
            return self.db_manager.find_many(
                self.users_collection,
                {'goal': goal},
                limit=limit
            )
        else:
            return [u for u in self.in_memory_users.values() if u.get('goal') == goal][:limit]
    
    def get_users_by_fitness_level(self, level: str, limit: int = 50) -> List[Dict]:
        """Get users with specific fitness level"""
        if self.db_manager.is_connected():
            return self.db_manager.find_many(
                self.users_collection,
                {'fitness_level': level},
                limit=limit
            )
        else:
            return [u for u in self.in_memory_users.values() if u.get('fitness_level') == level][:limit]
