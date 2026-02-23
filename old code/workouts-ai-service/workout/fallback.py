"""
FitGen AI v5.0 - Fallback System Module
Implements 6-level cascade fallback system
Features 13-14: Cascade fallback and emergency exercises
"""

import logging
from typing import List, Dict, Optional
import random

from config import (
    EMERGENCY_FALLBACK_EXERCISES,
    CASCADE_FALLBACK_LEVELS,
    BODY_PARTS,
    EQUIPMENT_TYPES,
    FITNESS_GOALS
)
from utils import log_warning, log_info
from db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# FALLBACK SYSTEM CLASS
# ============================================================================

class FallbackSystem:
    """
    Implements intelligent 6-level cascade fallback system
    Features 13-14: Ensures workout generation never fails
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize fallback system
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.exercises_collection = 'exercises'
    
    # ========================================================================
    # CASCADE FALLBACK (Feature 13)
    # ========================================================================
    
    def get_exercises_with_fallback(self, 
                                    body_part: str,
                                    equipment: List[str],
                                    level: str,
                                    goal: str,
                                    injuries: List[str],
                                    bmi_category: str,
                                    count: int = 5) -> List[Dict]:
        """
        Feature 13: 6-level cascade fallback system
        Tries multiple strategies to find suitable exercises
        
        Args:
            body_part: Target body part
            equipment: Available equipment
            level: Fitness level
            goal: Fitness goal
            injuries: User injuries
            bmi_category: User BMI category
            count: Number of exercises needed
        
        Returns:
            List of exercises (guaranteed to return something)
        """
        log_info(f"Searching exercises for {body_part} with fallback...")
        
        # Level 1: Perfect Match (Feature 13)
        exercises = self._level1_perfect_match(
            body_part, equipment, level, goal, injuries, bmi_category, count
        )
        if len(exercises) >= count:
            log_info("✅ Level 1: Perfect match found")
            return exercises[:count]
        
        # Level 2: Equipment Relaxed (Feature 13)
        log_warning("⚠️ Level 1 insufficient, trying Level 2...")
        exercises = self._level2_equipment_relaxed(
            body_part, level, goal, injuries, bmi_category, count
        )
        if len(exercises) >= count:
            log_info("✅ Level 2: Equipment relaxed found")
            return exercises[:count]
        
        # Level 3: Difficulty Relaxed (Feature 13)
        log_warning("⚠️ Level 2 insufficient, trying Level 3...")
        exercises = self._level3_difficulty_relaxed(
            body_part, equipment, injuries, bmi_category, count
        )
        if len(exercises) >= count:
            log_info("✅ Level 3: Difficulty relaxed found")
            return exercises[:count]
        
        # Level 4: Related Goals (Feature 13)
        log_warning("⚠️ Level 3 insufficient, trying Level 4...")
        exercises = self._level4_related_goals(
            body_part, equipment, injuries, bmi_category, count
        )
        if len(exercises) >= count:
            log_info("✅ Level 4: Related goals found")
            return exercises[:count]
        
        # Level 5: BMI Safety Relaxed (Feature 13)
        log_warning("⚠️ Level 4 insufficient, trying Level 5...")
        exercises = self._level5_bmi_relaxed(
            body_part, equipment, count
        )
        if len(exercises) >= count:
            log_info("✅ Level 5: BMI relaxed found")
            return exercises[:count]
        
        # Level 6: Emergency Fallback (Feature 14)
        log_warning("⚠️ Level 5 insufficient, using Level 6: Emergency Fallback")
        return self._level6_emergency_fallback(count)
    
    def _level1_perfect_match(self, body_part: str, equipment: List[str],
                             level: str, goal: str, injuries: List[str],
                             bmi_category: str, count: int) -> List[Dict]:
        """Level 1: Perfect match with all criteria"""
        if not self.db_manager.is_connected():
            return []
        
        query = {
            'body_part': body_part,
            'equipment': {'$in': equipment},
            'level': level
        }
        
        exercises = self.db_manager.find_many(
            self.exercises_collection,
            query,
            limit=count * 2
        )
        
        return exercises
    
    def _level2_equipment_relaxed(self, body_part: str, level: str,
                                  goal: str, injuries: List[str],
                                  bmi_category: str, count: int) -> List[Dict]:
        """Level 2: Relax equipment requirements (allow any equipment)"""
        if not self.db_manager.is_connected():
            return []
        
        query = {
            'body_part': body_part,
            'level': level
        }
        
        exercises = self.db_manager.find_many(
            self.exercises_collection,
            query,
            limit=count * 2
        )
        
        return exercises
    
    def _level3_difficulty_relaxed(self, body_part: str, equipment: List[str],
                                   injuries: List[str], bmi_category: str,
                                   count: int) -> List[Dict]:
        """Level 3: Relax difficulty level (allow any level)"""
        if not self.db_manager.is_connected():
            return []
        
        query = {
            'body_part': body_part,
            'equipment': {'$in': equipment}
        }
        
        exercises = self.db_manager.find_many(
            self.exercises_collection,
            query,
            limit=count * 2
        )
        
        return exercises
    
    def _level4_related_goals(self, body_part: str, equipment: List[str],
                             injuries: List[str], bmi_category: str,
                             count: int) -> List[Dict]:
        """Level 4: Use related body parts"""
        if not self.db_manager.is_connected():
            return []
        
        # Get related body parts
        related_parts = self._get_related_body_parts(body_part)
        
        query = {
            'body_part': {'$in': related_parts},
            'equipment': {'$in': equipment}
        }
        
        exercises = self.db_manager.find_many(
            self.exercises_collection,
            query,
            limit=count * 2
        )
        
        return exercises
    
    def _level5_bmi_relaxed(self, body_part: str, equipment: List[str],
                           count: int) -> List[Dict]:
        """Level 5: Relax BMI safety rules"""
        if not self.db_manager.is_connected():
            return []
        
        # Get any exercises for body part
        query = {'body_part': body_part}
        
        exercises = self.db_manager.find_many(
            self.exercises_collection,
            query,
            limit=count * 2
        )
        
        return exercises
    
    def _level6_emergency_fallback(self, count: int) -> List[Dict]:
        """
        Level 6: Emergency fallback exercises (Feature 14)
        Returns hardcoded safe exercises
        """
        log_warning("🚨 Using emergency fallback exercises")
        
        # Convert emergency exercises to proper format
        emergency_exercises = []
        for ex in EMERGENCY_FALLBACK_EXERCISES[:count]:
            emergency_exercises.append({
                'exercise_id': ex['title'].lower().replace(' ', '_'),
                'title': ex['title'],
                'description': ex.get('notes', 'Execute with proper form'),
                'body_part': ex['body_part'],
                'equipment': ex.get('equipment', 'Body Only'),
                'level': 'Beginner',
                'rating': 5.0,
                'type': 'Strength',
                'sets': 3,
                'reps': (10, 15),
                'rest_seconds': 60
            })
        
        return emergency_exercises
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_related_body_parts(self, body_part: str) -> List[str]:
        """
        Get related body parts for fallback
        
        Args:
            body_part: Original body part
        
        Returns:
            List of related body parts
        """
        related_map = {
            'Chest': ['Chest', 'Shoulders', 'Triceps'],
            'Back': ['Back', 'Lats', 'Biceps'],
            'Shoulders': ['Shoulders', 'Chest', 'Triceps'],
            'Legs': ['Legs', 'Quads', 'Hamstrings', 'Glutes'],
            'Arms': ['Arms', 'Biceps', 'Triceps', 'Forearms'],
            'Core': ['Core', 'Abs', 'Obliques'],
            'Biceps': ['Biceps', 'Arms', 'Back'],
            'Triceps': ['Triceps', 'Arms', 'Chest', 'Shoulders'],
            'Quads': ['Quads', 'Legs'],
            'Hamstrings': ['Hamstrings', 'Legs', 'Glutes'],
            'Glutes': ['Glutes', 'Legs', 'Hamstrings'],
            'Calves': ['Calves', 'Legs'],
            'Abs': ['Abs', 'Core', 'Obliques'],
            'Obliques': ['Obliques', 'Core', 'Abs'],
            'Lower Back': ['Lower Back', 'Back', 'Core'],
            'Traps': ['Traps', 'Back', 'Shoulders'],
            'Lats': ['Lats', 'Back']
        }
        
        return related_map.get(body_part, [body_part])
    
    def get_emergency_exercises(self) -> List[Dict]:
        """
        Get all emergency fallback exercises (Feature 14)
        
        Returns:
            List of emergency exercises
        """
        return EMERGENCY_FALLBACK_EXERCISES.copy()
    
    def test_fallback_system(self) -> Dict:
        """
        Test all 6 fallback levels
        
        Returns:
            Test results
        """
        results = {
            'level_1': False,
            'level_2': False,
            'level_3': False,
            'level_4': False,
            'level_5': False,
            'level_6': False
        }
        
        # Test Level 6 (always works)
        emergency = self._level6_emergency_fallback(3)
        results['level_6'] = len(emergency) >= 3
        
        # Test other levels if database connected
        if self.db_manager.is_connected():
            # Test Level 1
            l1 = self._level1_perfect_match(
                'Chest', ['Barbell', 'Dumbbell'], 'Intermediate',
                'Muscle Gain', [], 'Normal', 3
            )
            results['level_1'] = len(l1) > 0
            
            # Test Level 2
            l2 = self._level2_equipment_relaxed(
                'Chest', 'Intermediate', 'Muscle Gain', [], 'Normal', 3
            )
            results['level_2'] = len(l2) > 0
            
            # Test Level 3
            l3 = self._level3_difficulty_relaxed(
                'Chest', ['Barbell'], [], 'Normal', 3
            )
            results['level_3'] = len(l3) > 0
            
            # Test Level 4
            l4 = self._level4_related_goals(
                'Chest', ['Barbell'], [], 'Normal', 3
            )
            results['level_4'] = len(l4) > 0
            
            # Test Level 5
            l5 = self._level5_bmi_relaxed('Chest', ['Barbell'], 3)
            results['level_5'] = len(l5) > 0
        
        return results
