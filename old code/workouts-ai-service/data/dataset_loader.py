"""
FitGen AI v5.0 - Dataset Loader Module
Loads exercises from CSV dataset into MongoDB
Feature 30: Data Import from CSV (megaGymDataset.csv)
"""

import logging
import csv
import os
from typing import List, Dict, Tuple, Optional
from config import BODY_PARTS, EQUIPMENT_TYPES, FITNESS_LEVELS
from utils import log_success, log_error, log_info, log_warning
from db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# DATASET LOADER CLASS
# ============================================================================

class DatasetLoader:
    """
    Loads exercise data from CSV files into MongoDB
    Feature 30: Data Import and standardization
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize dataset loader
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.exercises_collection = 'exercises'
    
    # ========================================================================
    # CSV LOADING (Feature 30)
    # ========================================================================
    
    def load_from_csv(self, filepath: str = 'data/megaGymDataset.csv') -> Tuple[bool, int]:
        """
        Feature 30: Load exercises from CSV file
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Tuple: (success, count)
        """
        if not os.path.exists(filepath):
            log_error(f"CSV file not found: {filepath}")
            return False, 0
        
        try:
            log_info(f"Loading exercises from {filepath}...")
            
            exercises = []
            
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    # Clean and standardize data
                    exercise = self._standardize_exercise(row)
                    if exercise:
                        exercises.append(exercise)
            
            if not exercises:
                log_warning("No exercises found in CSV")
                return False, 0
            
            # Batch insert to database
            if self.db_manager.is_connected():
                # Clear existing exercises first
                self.db_manager.db[self.exercises_collection].delete_many({})
                
                # Insert new exercises
                success = self.db_manager.insert_many(self.exercises_collection, exercises)
                
                if success:
                    log_success(f"✅ Loaded {len(exercises)} exercises into database")
                    return True, len(exercises)
                else:
                    log_error("Failed to insert exercises into database")
                    return False, 0
            else:
                log_warning("Database not connected. Exercises loaded in memory only.")
                return True, len(exercises)
        
        except Exception as e:
            log_error(f"Error loading CSV: {e}")
            return False, 0
    
    def _standardize_exercise(self, row: Dict) -> Optional[Dict]:
        """
        Standardize exercise data from CSV row
        
        Args:
            row: CSV row as dict
        
        Returns:
            Standardized exercise dict or None
        """
        try:
            # Generate unique ID from title
            title = row.get('Title', '').strip()
            if not title:
                return None
            
            exercise_id = title.lower().replace(' ', '_').replace('-', '_')
            
            # Standardize body part
            body_part = row.get('BodyPart', 'Other').strip()
            if body_part not in BODY_PARTS:
                body_part = self._map_body_part(body_part)
            
            # Standardize equipment
            equipment = row.get('Equipment', 'Bodyweight').strip()
            if equipment not in EQUIPMENT_TYPES:
                equipment = self._map_equipment(equipment)
            
            # Determine fitness level
            level = row.get('Level', 'Intermediate').strip()
            if level not in FITNESS_LEVELS:
                level = 'Intermediate'
            
            # Get description
            description = row.get('Desc', 'Execute with proper form').strip()
            if not description:
                description = 'Execute with proper form and control'
            
            # Get rating (default to 0 if not present)
            try:
                rating = float(row.get('Rating', 0))
            except:
                rating = 0.0
            
            # Get rating description
            rating_desc = row.get('RatingDesc', '').strip()
            
            return {
                'exercise_id': exercise_id,
                'title': title,
                'description': description,
                'body_part': body_part,
                'equipment': equipment,
                'level': level,
                'rating': rating,
                'rating_desc': rating_desc,
                'type': row.get('Type', 'Strength').strip(),
                'usage_count': 0,
                'last_used': None,
                'average_satisfaction': 0.0
            }
        
        except Exception as e:
            log_warning(f"Failed to standardize exercise: {e}")
            return None
    
    def _map_body_part(self, body_part: str) -> str:
        """
        Map non-standard body part names to standard names
        
        Args:
            body_part: Original body part name
        
        Returns:
            Standardized body part name
        """
        mappings = {
            'upper legs': 'Legs',
            'lower legs': 'Legs',
            'upper arms': 'Arms',
            'lower arms': 'Arms',
            'cardio': 'Cardio',
            'waist': 'Core',
            'abs': 'Core',
            'abdominals': 'Core'
        }
        
        body_part_lower = body_part.lower()
        
        for key, value in mappings.items():
            if key in body_part_lower:
                return value
        
        # Try to find partial match in BODY_PARTS
        for standard_part in BODY_PARTS:
            if standard_part.lower() in body_part_lower or body_part_lower in standard_part.lower():
                return standard_part
        
        return 'Other'
    
    def _map_equipment(self, equipment: str) -> str:
        """
        Map non-standard equipment names to standard names
        
        Args:
            equipment: Original equipment name
        
        Returns:
            Standardized equipment name
        """
        mappings = {
            'body weight': 'Bodyweight',
            'bodyweight': 'Bodyweight',
            'body only': 'Bodyweight',
            'assisted': 'Machine',
            'leverage machine': 'Machine',
            'smith machine': 'Machine',
            'cable': 'Cable',
            'band': 'Resistance Band',
            'medicine ball': 'Medicine Ball',
            'stability ball': 'Stability Ball',
            'foam roll': 'Other',
            'kettlebells': 'Kettlebell',
            'e-z curl bar': 'Barbell'
        }
        
        equipment_lower = equipment.lower()
        
        for key, value in mappings.items():
            if key in equipment_lower:
                return value
        
        # Try to find partial match in EQUIPMENT_TYPES
        for standard_equip in EQUIPMENT_TYPES:
            if standard_equip.lower() in equipment_lower or equipment_lower in standard_equip.lower():
                return standard_equip
        
        return 'Other'
    
    # ========================================================================
    # DATASET STATISTICS
    # ========================================================================
    
    def get_dataset_info(self, filepath: str = 'data/megaGymDataset.csv') -> Dict:
        """
        Get information about CSV dataset
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Dataset statistics
        """
        if not os.path.exists(filepath):
            return {'error': 'File not found', 'exists': False}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                # Count by categories
                body_parts = {}
                equipment_types = {}
                levels = {}
                
                for row in rows:
                    # Body parts
                    bp = row.get('BodyPart', 'Unknown')
                    body_parts[bp] = body_parts.get(bp, 0) + 1
                    
                    # Equipment
                    eq = row.get('Equipment', 'Unknown')
                    equipment_types[eq] = equipment_types.get(eq, 0) + 1
                    
                    # Levels
                    lv = row.get('Level', 'Unknown')
                    levels[lv] = levels.get(lv, 0) + 1
                
                return {
                    'exists': True,
                    'total_exercises': len(rows),
                    'body_parts': body_parts,
                    'equipment_types': equipment_types,
                    'levels': levels,
                    'filepath': filepath
                }
        
        except Exception as e:
            log_error(f"Error reading dataset info: {e}")
            return {'error': str(e), 'exists': True}
    
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    def reload_dataset(self, filepath: str = 'data/megaGymDataset.csv') -> Tuple[bool, str]:
        """
        Reload entire dataset (delete old + load new)
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Tuple: (success, message)
        """
        log_info("Reloading dataset...")
        
        success, count = self.load_from_csv(filepath)
        
        if success:
            return True, f"Successfully reloaded {count} exercises"
        else:
            return False, "Failed to reload dataset"
    
    def validate_dataset(self, filepath: str = 'data/megaGymDataset.csv') -> Dict:
        """
        Validate CSV dataset structure
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Validation results
        """
        if not os.path.exists(filepath):
            return {
                'valid': False,
                'error': 'File not found'
            }
        
        try:
            required_columns = ['Title', 'BodyPart', 'Equipment']
            
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                columns = reader.fieldnames
                
                if not columns:
                    return {
                        'valid': False,
                        'error': 'No columns found'
                    }
                
                missing = [col for col in required_columns if col not in columns]
                
                if missing:
                    return {
                        'valid': False,
                        'error': f'Missing required columns: {missing}',
                        'columns': columns
                    }
                
                # Count rows
                row_count = sum(1 for _ in reader)
                
                return {
                    'valid': True,
                    'columns': list(columns),
                    'row_count': row_count,
                    'required_columns': required_columns
                }
        
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
