"""
FitGen AI v5.0 - Utilities Module
Helper functions for hashing, datetime, validation, etc.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional
import random
from config import LOG_FILE, LOG_FORMAT, LOG_LEVEL

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# ============================================================================
# HASHING & ID GENERATION
# ============================================================================

def generate_id(data: str) -> str:
    """Generate unique ID from data using MD5 hash (first 8 chars)"""
    return hashlib.md5(data.encode()).hexdigest()[:8]


def generate_session_id(user_id: str) -> str:
    """Generate unique session ID"""
    timestamp = datetime.now().isoformat()
    data = f"{user_id}_{timestamp}"
    return generate_id(data)


def generate_workout_id(user_id: str) -> str:
    """Generate unique workout ID"""
    timestamp = datetime.now().isoformat()
    data = f"{user_id}_{timestamp}_workout"
    return generate_id(data)


def generate_plan_id(user_id: str) -> str:
    """Generate unique weekly plan ID"""
    timestamp = datetime.now().isoformat()
    data = f"{user_id}_{timestamp}_plan"
    return generate_id(data)


# ============================================================================
# DATETIME HELPERS
# ============================================================================

def get_current_datetime() -> str:
    """Get current datetime in ISO format"""
    return datetime.now().isoformat()


def get_week_ago() -> str:
    """Get datetime from 7 days ago"""
    return (datetime.now() - timedelta(days=7)).isoformat()


def get_month_ago() -> str:
    """Get datetime from 30 days ago"""
    return (datetime.now() - timedelta(days=30)).isoformat()


def parse_date(date_string: str) -> datetime:
    """Parse ISO format date string"""
    try:
        return datetime.fromisoformat(date_string)
    except:
        logger.error(f"Failed to parse date: {date_string}")
        return None


def days_between(date1: str, date2: str) -> int:
    """Calculate days between two ISO format dates"""
    try:
        dt1 = datetime.fromisoformat(date1)
        dt2 = datetime.fromisoformat(date2)
        return abs((dt2 - dt1).days)
    except:
        return 0


# ============================================================================
# BMI CALCULATIONS
# ============================================================================

def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate BMI from height (cm) and weight (kg)"""
    if not height_cm or not weight_kg or height_cm == 0:
        return 0.0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def get_bmi_category(bmi: float) -> str:
    """Get BMI category from BMI value"""
    from config import BMI_CATEGORIES
    
    for category, (min_val, max_val) in BMI_CATEGORIES.items():
        if min_val <= bmi < max_val:
            return category
    return 'Extremely Obese'


# ============================================================================
# VALIDATION
# ============================================================================

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_user_profile(profile: Dict) -> Tuple[bool, str]:
    """Validate user profile data"""
    required_fields = ['name', 'age', 'height_cm', 'weight_kg', 'fitness_level', 'goal']
    
    for field in required_fields:
        if field not in profile or not profile[field]:
            return False, f"Missing required field: {field}"
    
    # Validate age
    if not isinstance(profile['age'], int) or profile['age'] < 10 or profile['age'] > 120:
        return False, "Invalid age (must be 10-120)"
    
    # Validate height
    if not isinstance(profile['height_cm'], (int, float)) or profile['height_cm'] < 100 or profile['height_cm'] > 250:
        return False, "Invalid height (must be 100-250 cm)"
    
    # Validate weight
    if not isinstance(profile['weight_kg'], (int, float)) or profile['weight_kg'] < 20 or profile['weight_kg'] > 300:
        return False, "Invalid weight (must be 20-300 kg)"
    
    return True, "Valid"


def validate_workout_log(workout_log: Dict) -> Tuple[bool, str]:
    """Validate workout log data"""
    required_fields = ['completion_percentage', 'satisfaction_rating']
    
    for field in required_fields:
        if field not in workout_log or workout_log[field] is None:
            return False, f"Missing required field: {field}"
    
    # Validate completion percentage
    completion = workout_log['completion_percentage']
    if not isinstance(completion, (int, float)) or completion < 0 or completion > 100:
        return False, "Completion percentage must be 0-100"
    
    # Validate satisfaction rating
    satisfaction = workout_log['satisfaction_rating']
    if not isinstance(satisfaction, int) or satisfaction < 1 or satisfaction > 10:
        return False, "Satisfaction rating must be 1-10"
    
    return True, "Valid"


def validate_mood_score(mood: int) -> Tuple[bool, str]:
    """Validate mood score (1-10)"""
    if not isinstance(mood, int) or mood < 1 or mood > 10:
        return False, "Mood score must be 1-10"
    return True, "Valid"


# ============================================================================
# DATA CONVERSION & FORMATTING
# ============================================================================

def format_duration(minutes: int) -> str:
    """Format duration in minutes to readable format"""
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.1f}%"


def format_time_duration(seconds: int) -> str:
    """Format seconds to readable time"""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if secs == 0:
        return f"{minutes}m"
    return f"{minutes}m {secs}s"


def dict_to_readable(data: Dict) -> str:
    """Convert dictionary to readable format"""
    lines = []
    for key, value in data.items():
        # Convert snake_case to Title Case
        key_display = key.replace('_', ' ').title()
        lines.append(f"  {key_display}: {value}")
    return "\n".join(lines)


# ============================================================================
# LIST & RANDOM OPERATIONS
# ============================================================================

def choose_random(items: List[Any]) -> Any:
    """Choose random item from list"""
    if not items:
        return None
    return random.choice(items)


def choose_multiple_random(items: List[Any], count: int) -> List[Any]:
    """Choose multiple random items from list"""
    if not items or count <= 0:
        return []
    return random.sample(items, min(count, len(items)))


def shuffle_list(items: List[Any]) -> List[Any]:
    """Shuffle list"""
    shuffled = items.copy()
    random.shuffle(shuffled)
    return shuffled


def remove_duplicates(items: List[Any]) -> List[Any]:
    """Remove duplicates from list while preserving order"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ============================================================================
# STATISTICS & CALCULATIONS
# ============================================================================

def calculate_average(values: List[float]) -> float:
    """Calculate average of list"""
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def calculate_total(values: List[float]) -> float:
    """Calculate total of list"""
    return sum(values) if values else 0.0


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change"""
    if old_value == 0:
        return 0.0
    return round(((new_value - old_value) / old_value) * 100, 2)


def get_median(values: List[float]) -> float:
    """Calculate median of list"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    return sorted_values[n // 2]


# ============================================================================
# STRING OPERATIONS
# ============================================================================

def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def capitalize_words(text: str) -> str:
    """Capitalize each word"""
    return " ".join(word.capitalize() for word in text.split())


def remove_special_characters(text: str) -> str:
    """Remove special characters from text"""
    import re
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)


def to_snake_case(text: str) -> str:
    """Convert text to snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# ============================================================================
# ERROR HANDLING & LOGGING
# ============================================================================

def log_error(error_msg: str, exception: Exception = None):
    """Log error message"""
    if exception:
        logger.error(f"{error_msg}: {str(exception)}", exc_info=True)
    else:
        logger.error(error_msg)


def log_warning(warning_msg: str):
    """Log warning message"""
    logger.warning(warning_msg)


def log_info(info_msg: str):
    """Log info message"""
    logger.info(info_msg)


def log_success(success_msg: str):
    """Log success message"""
    logger.info(f"[SUCCESS] {success_msg}")


# ============================================================================
# TYPE CHECKING
# ============================================================================

def is_valid_objectid(obj_id: Any) -> bool:
    """Check if valid MongoDB ObjectID"""
    from bson import ObjectId
    try:
        ObjectId(str(obj_id))
        return True
    except:
        return False


def ensure_list(value: Any) -> List:
    """Ensure value is a list"""
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def ensure_dict(value: Any) -> Dict:
    """Ensure value is a dictionary"""
    if isinstance(value, dict):
        return value
    return {}


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def read_file(filepath: str) -> str:
    """Read file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        log_error(f"Failed to read file {filepath}", e)
        return ""


def write_file(filepath: str, content: str) -> bool:
    """Write content to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        log_error(f"Failed to write to file {filepath}", e)
        return False


def file_exists(filepath: str) -> bool:
    """Check if file exists"""
    import os
    return os.path.exists(filepath)


# ============================================================================
# DATA STRUCTURE OPERATIONS
# ============================================================================

def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def filter_dict(data: Dict, keys: List[str]) -> Dict:
    """Filter dictionary by keys"""
    return {k: v for k, v in data.items() if k in keys}


def exclude_dict(data: Dict, keys: List[str]) -> Dict:
    """Exclude keys from dictionary"""
    return {k: v for k, v in data.items() if k not in keys}
