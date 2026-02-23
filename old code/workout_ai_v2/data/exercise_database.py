"""
FitGen AI v5.0 - Exercise Database Module
Manages 2,918 exercises from MegaGym dataset
Feature 1: Exercise Database
Feature 30: Data Import from CSV
"""

import logging
from typing import Optional, Dict, List
import pandas as pd
from db.database_manager import DatabaseManager
from config import DATASET_CSV_PATH, COLLECTIONS
from utils import log_error, log_info, log_success, generate_id

logger = logging.getLogger(__name__)

# ============================================================================
# BODY PART ALIASES FOR FLEXIBLE MATCHING
# ============================================================================

BODY_PART_ALIASES = {
    'Chest': ['Chest', 'Pectorals', 'Pecs'],
    'Back': ['Back', 'Lats', 'Middle Back', 'Upper Back'],
    'Shoulders': ['Shoulders', 'Delts', 'Deltoids'],
    'Biceps': ['Biceps', 'Arms', 'Upper Arms'],
    'Triceps': ['Triceps', 'Arms', 'Upper Arms'],
    'Forearms': ['Forearms', 'Lower Arms'],
    'Quadriceps': ['Quadriceps', 'Quads', 'Upper Legs', 'Thighs'],
    'Hamstrings': ['Hamstrings', 'Upper Legs', 'Thighs'],
    'Glutes': ['Glutes', 'Gluteus', 'Hips', 'Buttocks'],
    'Calves': ['Calves', 'Lower Legs'],
    'Abdominals': ['Abdominals', 'Abs', 'Core'],
    'Obliques': ['Obliques', 'Core', 'Abs'],
    'Lower Back': ['Lower Back', 'Back', 'Erector Spinae'],
    'Lats': ['Lats', 'Latissimus', 'Back'],
    'Traps': ['Traps', 'Trapezius', 'Upper Back', 'Neck'],
    'Neck': ['Neck', 'Traps'],
    'Full Body': ['Full Body', 'Total Body', 'Compound']
}

# ============================================================================
# EXERCISE DATABASE CLASS
# ============================================================================

class ExerciseDatabase:
    """
    Manages 2,918 exercises from MegaGym dataset
    Feature 1: Complete exercise library with intelligent filtering
    Feature 30: CSV import and data standardization
    """
    
    def __init__(self, db_manager: DatabaseManager, csv_path: str = str(DATASET_CSV_PATH)):
        """
        Initialize exercise database
        
        Args:
            db_manager: DatabaseManager instance
            csv_path: Path to MegaGym CSV dataset
        """
        self.db_manager = db_manager
        self.csv_path = csv_path
        self.exercises_collection = COLLECTIONS['exercises']
        self.in_memory_exercises = []
        
        # Load exercises
        self.load_exercises()
    
    def load_exercises(self) -> bool:
        """
        Load exercises from CSV into database
        Feature 1: Load 2,918 exercises
        Feature 30: Data import and standardization
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read CSV
            df = pd.read_csv(self.csv_path)
            df.columns = df.columns.str.strip()
            
            # Clean data
            df = df.dropna(subset=['Title', 'BodyPart', 'Equipment', 'Level'])
            
            log_info(f"📚 Loaded {len(df)} exercises from CSV")
            
            # Check if exercises already in database
            if self.db_manager.is_connected():
                existing_count = self.db_manager.count(self.exercises_collection)
                
                if existing_count == 0:
                    # Import exercises to database
                    exercises = []
                    for _, row in df.iterrows():
                        exercise = self._prepare_exercise(row)
                        exercises.append(exercise)
                    
                    # Batch insert
                    self.db_manager.insert_many(self.exercises_collection, exercises)
                    log_success(f"Imported {len(exercises)} exercises to database")
                else:
                    log_info(f"Database already contains {existing_count} exercises")
            else:
                # In-memory fallback
                for _, row in df.iterrows():
                    exercise = self._prepare_exercise(row)
                    self.in_memory_exercises.append(exercise)
                log_success(f"Loaded {len(self.in_memory_exercises)} exercises to memory")
            
            return True
        
        except FileNotFoundError:
            log_error(f"Exercise dataset not found: {self.csv_path}")
            return False
        except Exception as e:
            log_error(f"Failed to load exercises: {e}")
            return False
    
    def _prepare_exercise(self, row: pd.Series) -> Dict:
        """
        Prepare exercise document for database
        Feature 30: Data standardization
        
        Args:
            row: Pandas Series from CSV
        
        Returns:
            Exercise document
        """
        exercise_id = generate_id(str(row['Title']))
        
        return {
            'exercise_id': exercise_id,
            'title': str(row['Title']).strip(),
            'description': str(row.get('Desc', '')).strip(),
            'body_part': str(row['BodyPart']).strip(),
            'equipment': str(row['Equipment']).strip(),
            'level': str(row['Level']).strip(),
            'type': str(row.get('Type', 'Strength')).strip(),
            'rating': float(row['Rating']) if pd.notna(row.get('Rating')) else 0.0,
            'is_valid': True,
            'last_used': None,
            'usage_count': 0
        }
    
    # ========================================================================
    # EXERCISE FILTERING & SEARCH
    # ========================================================================
    
    def get_exercises(self, filters: Dict = None, limit: int = 50) -> List[Dict]:
        """
        Get exercises with intelligent filtering
        
        Args:
            filters: Filter criteria (body_part, equipment, level)
            limit: Maximum results
        
        Returns:
            List of exercise documents
        """
        if self.db_manager.is_connected():
            query = {}
            if filters:
                for key, value in filters.items():
                    if isinstance(value, str):
                        # Case-insensitive regex match
                        query[key] = {'$regex': f'^{value}$', '$options': 'i'}
                    else:
                        query[key] = value
            return self.db_manager.find_many(
                self.exercises_collection,
                query,
                limit=limit
            )
        else:
            # In-memory filtering
            return self._filter_in_memory(filters, limit)
    
    def _filter_in_memory(self, filters: Dict, limit: int) -> List[Dict]:
        """Filter exercises in memory if no database"""
        results = self.in_memory_exercises
        
        if filters:
            if 'body_part' in filters:
                results = [e for e in results 
                          if e['body_part'].lower() == filters['body_part'].lower()]
            if 'equipment' in filters:
                results = [e for e in results 
                          if e['equipment'].lower() == filters['equipment'].lower()]
            if 'level' in filters:
                results = [e for e in results 
                          if e['level'].lower() == filters['level'].lower()]
        
        return results[:limit]
    
    def get_exercises_by_body_part(self, body_part: str, limit: int = 50) -> List[Dict]:
        """
        Get exercises by body part with alias support
        Feature 2: Weekly plan generation uses this
        """
        # Get aliases for this body part
        aliases = BODY_PART_ALIASES.get(body_part, [body_part])
        
        all_exercises = []
        for alias in aliases:
            exercises = self.get_exercises({'body_part': alias}, limit=limit)
            all_exercises.extend(exercises)
            if len(all_exercises) >= limit:
                break
        
        # Remove duplicates by exercise_id
        seen = set()
        unique_exercises = []
        for ex in all_exercises:
            if ex.get('exercise_id') not in seen:
                seen.add(ex.get('exercise_id'))
                unique_exercises.append(ex)
        
        return unique_exercises[:limit]
    
    def get_exercises_by_equipment(self, equipment: str, limit: int = 50) -> List[Dict]:
        """Get exercises by equipment type"""
        return self.get_exercises({'equipment': equipment}, limit)
    
    def get_exercises_by_level(self, level: str, limit: int = 50) -> List[Dict]:
        """Get exercises by fitness level (Feature 6)"""
        return self.get_exercises({'level': level}, limit)
    
    def get_exercises_by_type(self, exercise_type: str, limit: int = 50) -> List[Dict]:
        """Get exercises by type (Strength, Cardio, etc.)"""
        return self.get_exercises({'type': exercise_type}, limit)
    
    def search_exercises(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Search exercises by title
        Feature 30: Search functionality
        """
        all_exercises = self.db_manager.find_many(self.exercises_collection, limit=1000)
        
        if not all_exercises:
            all_exercises = self.in_memory_exercises
        
        # Case-insensitive search
        search_lower = search_term.lower()
        results = [
            e for e in all_exercises
            if search_lower in e['title'].lower()
        ]
        
        return results[:limit]
    
    def get_random_exercises(self, count: int = 5) -> List[Dict]:
        """
        Get random exercises
        Feature 38: Exercise variety algorithm uses this
        """
        import random
        
        if self.db_manager.is_connected():
            all_exercises = self.db_manager.find_many(self.exercises_collection, limit=1000)
        else:
            all_exercises = self.in_memory_exercises
        
        if len(all_exercises) <= count:
            return all_exercises
        
        return random.sample(all_exercises, count)
    
    # ========================================================================
    # EXERCISE STATISTICS & ANALYTICS
    # ========================================================================
    
    def get_statistics(self) -> Dict:
        """
        Get dataset statistics
        Feature 1: Exercise database stats
        """
        if self.db_manager.is_connected():
            all_exercises = self.db_manager.find_many(self.exercises_collection, limit=3000)
        else:
            all_exercises = self.in_memory_exercises
        
        if not all_exercises:
            return {'error': 'No exercises found'}
        
        # Calculate statistics
        body_parts = {}
        equipment_types = {}
        levels = {}
        exercise_types = {}
        
        for ex in all_exercises:
            # Body parts
            bp = ex.get('body_part', 'Unknown')
            body_parts[bp] = body_parts.get(bp, 0) + 1
            
            # Equipment
            eq = ex.get('equipment', 'Unknown')
            equipment_types[eq] = equipment_types.get(eq, 0) + 1
            
            # Levels
            lv = ex.get('level', 'Unknown')
            levels[lv] = levels.get(lv, 0) + 1
            
            # Exercise types
            et = ex.get('type', 'Unknown')
            exercise_types[et] = exercise_types.get(et, 0) + 1
        
        return {
            'total_exercises': len(all_exercises),
            'body_parts': body_parts,
            'equipment_types': equipment_types,
            'difficulty_levels': levels,
            'exercise_types': exercise_types,
            'avg_rating': sum(e.get('rating', 0) for e in all_exercises) / len(all_exercises) if all_exercises else 0
        }
    
    def get_body_part_count(self) -> Dict:
        """Get count of exercises per body part"""
        stats = self.get_statistics()
        return stats.get('body_parts', {})
    
    def get_equipment_count(self) -> Dict:
        """Get count of exercises per equipment"""
        stats = self.get_statistics()
        return stats.get('equipment_types', {})
    
    def get_level_count(self) -> Dict:
        """Get count of exercises per difficulty level"""
        stats = self.get_statistics()
        return stats.get('difficulty_levels', {})
    
    # ========================================================================
    # EXERCISE MANAGEMENT
    # ========================================================================
    
    def get_exercise_by_id(self, exercise_id: str) -> Optional[Dict]:
        """Get specific exercise by ID"""
        if self.db_manager.is_connected():
            return self.db_manager.find_one(
                self.exercises_collection,
                {'exercise_id': exercise_id}
            )
        else:
            for ex in self.in_memory_exercises:
                if ex['exercise_id'] == exercise_id:
                    return ex
            return None
    
    def get_exercise_by_title(self, title: str) -> Optional[Dict]:
        """Get exercise by exact title match"""
        if self.db_manager.is_connected():
            return self.db_manager.find_one(
                self.exercises_collection,
                {'title': title}
            )
        else:
            for ex in self.in_memory_exercises:
                if ex['title'].lower() == title.lower():
                    return ex
            return None
    
    def get_related_exercises(self, exercise_id: str, limit: int = 10) -> List[Dict]:
        """
        Get related exercises (same body part)
        Feature 38: Exercise variety - suggests related exercises
        """
        exercise = self.get_exercise_by_id(exercise_id)
        if not exercise:
            return []
        
        related = self.get_exercises_by_body_part(
            exercise['body_part'],
            limit=limit
        )
        
        # Remove the original exercise from results
        return [e for e in related if e['exercise_id'] != exercise_id]
    
    def update_exercise_usage(self, exercise_id: str) -> bool:
        """
        Update exercise usage tracking
        Feature 11: Recency management tracks usage
        """
        if self.db_manager.is_connected():
            exercise = self.get_exercise_by_id(exercise_id)
            if exercise:
                new_count = exercise.get('usage_count', 0) + 1
                self.db_manager.update_one(
                    self.exercises_collection,
                    {'exercise_id': exercise_id},
                    {
                        'usage_count': new_count,
                        'last_used': pd.Timestamp.now().isoformat()
                    }
                )
                return True
        else:
            for ex in self.in_memory_exercises:
                if ex['exercise_id'] == exercise_id:
                    ex['usage_count'] = ex.get('usage_count', 0) + 1
                    ex['last_used'] = pd.Timestamp.now().isoformat()
                    return True
        
        return False
    
    def get_most_used_exercises(self, limit: int = 10) -> List[Dict]:
        """Get most frequently used exercises"""
        if self.db_manager.is_connected():
            return self.db_manager.find_many(
                self.exercises_collection,
                limit=limit,
                sort_by='usage_count'
            )
        else:
            sorted_ex = sorted(
                self.in_memory_exercises,
                key=lambda x: x.get('usage_count', 0),
                reverse=True
            )
            return sorted_ex[:limit]
    
    def get_top_rated_exercises(self, limit: int = 10) -> List[Dict]:
        """Get highest rated exercises (Feature 1)"""
        if self.db_manager.is_connected():
            return self.db_manager.find_many(
                self.exercises_collection,
                limit=limit,
                sort_by='rating'
            )
        else:
            sorted_ex = sorted(
                self.in_memory_exercises,
                key=lambda x: x.get('rating', 0),
                reverse=True
            )
            return sorted_ex[:limit]
