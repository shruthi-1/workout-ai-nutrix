"""
FitGen AI v5.0 - Configuration Module
Centralized configuration, constants, and environment variables
"""

import os
from pathlib import Path

# ============================================================================
# DIRECTORY PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
BACKUPS_DIR = BASE_DIR / 'backups'

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR = BASE_DIR / 'exports'
EXPORTS_DIR.mkdir(exist_ok=True)

# ============================================================================
# MONGODB CONFIGURATION
# ============================================================================

# Default MongoDB connection (LOCAL)
MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'fitgen_db')

# Connection string for local MongoDB
MONGODB_CONNECTION_STRING_LOCAL = f'mongodb://{MONGODB_HOST}:{MONGODB_PORT}'

# Connection string for MongoDB Atlas (Cloud)
# Format: mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
MONGODB_CONNECTION_STRING_ATLAS = os.getenv(
    'MONGODB_ATLAS_URI',
    None  # Set this via environment variable for production
)

# Use Atlas if available, otherwise local
MONGODB_CONNECTION_STRING = MONGODB_CONNECTION_STRING_ATLAS or MONGODB_CONNECTION_STRING_LOCAL

# ============================================================================
# DATABASE COLLECTIONS
# ============================================================================

COLLECTIONS = {
    'users': 'users',
    'exercises': 'exercises',
    'weekly_plans': 'weekly_plans',
    'session_logs': 'session_logs',
    'motivation_logs': 'motivation_logs',
    'exercise_history': 'exercise_history',
    'user_preferences': 'user_preferences',
    'progress_tracking': 'progress_tracking',
    # v6.0 collections
    'dataset': 'dataset',
    'workout_history': 'workout_history',
    'system_config': 'system_config'
}

# ============================================================================
# BMI CATEGORIES (Feature 4: 7 categories)
# ============================================================================

BMI_CATEGORIES = {
    'Severe Underweight': (0, 16),
    'Underweight': (16, 18.5),
    'Normal': (18.5, 25),
    'Overweight': (25, 30),
    'Obese': (30, 35),
    'Severely Obese': (35, 40),
    'Extremely Obese': (40, float('inf'))
}

BMI_SAFETY_RULES = {
    'Severe Underweight': {
        'excluded_exercises': ['Heavy Lifting', 'Powerlifting', 'Max Effort'],
        'max_rpe': 8,
        'modifications': 'Reduce volume, focus on technique'
    },
    'Underweight': {
        'excluded_exercises': ['Heavy Powerlifting'],
        'max_rpe': 9,
        'modifications': 'Standard training with focus on recovery'
    },
    'Normal': {
        'excluded_exercises': [],
        'max_rpe': 10,
        'modifications': 'Full training freedom'
    },
    'Overweight': {
        'excluded_exercises': ['High-Impact Plyometrics'],
        'max_rpe': 9,
        'modifications': 'Focus on joint-friendly exercises'
    },
    'Obese': {
        'excluded_exercises': ['Jumps', 'Plyometrics', 'Running', 'High-Impact'],
        'max_rpe': 8,
        'modifications': 'Emphasize controlled movements'
    },
    'Severely Obese': {
        'excluded_exercises': ['Jumps', 'Sprints', 'Burpees', 'All High-Impact'],
        'max_rpe': 7,
        'modifications': 'Bodyweight-only or machine exercises'
    },
    'Extremely Obese': {
        'excluded_exercises': ['All Plyometrics', 'Complex Movements'],
        'max_rpe': 6,
        'modifications': 'Seated, supported exercises only'
    }
}

# ============================================================================
# INJURY TYPES (Feature 5: 8 injury types)
# ============================================================================

INJURY_TYPES = [
    'Lower Back',
    'Knee',
    'Shoulder',
    'Wrist',
    'Ankle',
    'Hip',
    'Elbow',
    'Neck'
]

# ============================================================================
# FITNESS LEVELS (Feature 6: 3 levels)
# ============================================================================

FITNESS_LEVELS = [
    'Beginner',
    'Intermediate',
    'Expert'
]

# ============================================================================
# FITNESS GOALS (Feature 7: 6 fitness goals)
# ============================================================================

FITNESS_GOALS = {
    'Weight Loss': {
        'rep_range': (12, 15),
        'rest_seconds': 30,
        'sets_modifier': 0,
        'focus': 'High-rep circuits, cardio focus'
    },
    'Muscle Gain': {
        'rep_range': (8, 12),
        'rest_seconds': 90,
        'sets_modifier': 1,
        'focus': 'Hypertrophy training'
    },
    'Strength': {
        'rep_range': (3, 6),
        'rest_seconds': 180,
        'sets_modifier': 1,
        'focus': 'Heavy compounds, powerlifting'
    },
    'Endurance': {
        'rep_range': (15, 20),
        'rest_seconds': 45,
        'sets_modifier': -1,
        'focus': 'High-rep training, circuits'
    },
    'General Fitness': {
        'rep_range': (8, 12),
        'rest_seconds': 60,
        'sets_modifier': 0,
        'focus': 'Balanced approach'
    },
    'Athletic Performance': {
        'rep_range': (6, 10),
        'rest_seconds': 120,
        'sets_modifier': 0,
        'focus': 'Explosive, power movements'
    }
}

# ============================================================================
# EQUIPMENT TYPES
# ============================================================================

EQUIPMENT_TYPES = [
    'Body Only',
    'Dumbbell',
    'Barbell',
    'Cable',
    'Machine',
    'Kettlebells',
    'Bands',
    'Medicine Ball',
    'Exercise Ball',
    'E-Z Curl Bar',
    'Other'
]

# ============================================================================
# BODY PARTS (17+ categories)
# ============================================================================

BODY_PARTS = [
    'Chest',
    'Back',
    'Shoulders',
    'Biceps',
    'Triceps',
    'Forearms',
    'Quadriceps',
    'Hamstrings',
    'Glutes',
    'Calves',
    'Abdominals',
    'Obliques',
    'Lower Back',
    'Middle Back',
    'Lats',
    'Traps',
    'Neck',
    'Hip Flexors',
    'Adductors',
    'Abductors',
    'Full Body'
]

# ============================================================================
# PROGRAMMING SPLITS
# ============================================================================

SPLITS = {
    'Push/Pull/Legs': {
        'Monday': {'name': 'Push', 'body_parts': ['Chest', 'Shoulders', 'Triceps']},
        'Tuesday': {'name': 'Pull', 'body_parts': ['Back', 'Biceps', 'Forearms']},
        'Wednesday': {'name': 'Legs', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Thursday': {'name': 'Rest', 'body_parts': []},
        'Friday': {'name': 'Push', 'body_parts': ['Chest', 'Shoulders', 'Triceps']},
        'Saturday': {'name': 'Pull', 'body_parts': ['Back', 'Biceps', 'Forearms']},
        'Sunday': {'name': 'Legs', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']}
    },
    'Upper/Lower': {
        'Monday': {'name': 'Upper', 'body_parts': ['Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps']},
        'Tuesday': {'name': 'Lower', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Wednesday': {'name': 'Rest', 'body_parts': []},
        'Thursday': {'name': 'Upper', 'body_parts': ['Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps']},
        'Friday': {'name': 'Lower', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Saturday': {'name': 'Core & Cardio', 'body_parts': ['Abdominals', 'Obliques']},
        'Sunday': {'name': 'Rest', 'body_parts': []}
    },
    'Full Body': {
        'Monday': {'name': 'Full Body A', 'body_parts': ['Chest', 'Back', 'Quadriceps', 'Shoulders', 'Abdominals']},
        'Tuesday': {'name': 'Rest', 'body_parts': []},
        'Wednesday': {'name': 'Full Body B', 'body_parts': ['Back', 'Hamstrings', 'Glutes', 'Biceps', 'Triceps']},
        'Thursday': {'name': 'Rest', 'body_parts': []},
        'Friday': {'name': 'Full Body C', 'body_parts': ['Chest', 'Shoulders', 'Quadriceps', 'Calves', 'Abdominals']},
        'Saturday': {'name': 'Active Recovery', 'body_parts': []},
        'Sunday': {'name': 'Rest', 'body_parts': []}
    },
    'Bro Split': {
        'Monday': {'name': 'Chest', 'body_parts': ['Chest', 'Triceps']},
        'Tuesday': {'name': 'Back', 'body_parts': ['Back', 'Biceps', 'Forearms']},
        'Wednesday': {'name': 'Shoulders', 'body_parts': ['Shoulders', 'Traps']},
        'Thursday': {'name': 'Legs', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Friday': {'name': 'Arms', 'body_parts': ['Biceps', 'Triceps', 'Forearms']},
        'Saturday': {'name': 'Core', 'body_parts': ['Abdominals', 'Obliques', 'Lower Back']},
        'Sunday': {'name': 'Rest', 'body_parts': []}
    },
    'Arnold Split': {
        'Monday': {'name': 'Chest & Back', 'body_parts': ['Chest', 'Back', 'Abdominals']},
        'Tuesday': {'name': 'Shoulders & Arms', 'body_parts': ['Shoulders', 'Biceps', 'Triceps']},
        'Wednesday': {'name': 'Legs', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Thursday': {'name': 'Chest & Back', 'body_parts': ['Chest', 'Back', 'Abdominals']},
        'Friday': {'name': 'Shoulders & Arms', 'body_parts': ['Shoulders', 'Biceps', 'Triceps']},
        'Saturday': {'name': 'Legs', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Sunday': {'name': 'Rest', 'body_parts': []}
    },
    'PHUL': {
        'Monday': {'name': 'Power Upper', 'body_parts': ['Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps']},
        'Tuesday': {'name': 'Power Lower', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Wednesday': {'name': 'Rest', 'body_parts': []},
        'Thursday': {'name': 'Hypertrophy Upper', 'body_parts': ['Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps']},
        'Friday': {'name': 'Hypertrophy Lower', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Saturday': {'name': 'Core & Arms', 'body_parts': ['Abdominals', 'Obliques', 'Biceps', 'Triceps']},
        'Sunday': {'name': 'Rest', 'body_parts': []}
    },
    'Core Focus': {
        'Monday': {'name': 'Abs & Lower Back', 'body_parts': ['Abdominals', 'Obliques', 'Lower Back']},
        'Tuesday': {'name': 'Upper Body', 'body_parts': ['Chest', 'Back', 'Shoulders']},
        'Wednesday': {'name': 'Core Circuit', 'body_parts': ['Abdominals', 'Obliques']},
        'Thursday': {'name': 'Lower Body', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes']},
        'Friday': {'name': 'Full Core', 'body_parts': ['Abdominals', 'Obliques', 'Lower Back']},
        'Saturday': {'name': 'Active Recovery', 'body_parts': []},
        'Sunday': {'name': 'Rest', 'body_parts': []}
    },
    'Muscle Group Focus': {
        'Monday': {'name': 'Chest & Triceps', 'body_parts': ['Chest', 'Triceps']},
        'Tuesday': {'name': 'Back & Biceps', 'body_parts': ['Back', 'Lats', 'Biceps']},
        'Wednesday': {'name': 'Legs & Glutes', 'body_parts': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves']},
        'Thursday': {'name': 'Shoulders & Traps', 'body_parts': ['Shoulders', 'Traps', 'Neck']},
        'Friday': {'name': 'Arms & Forearms', 'body_parts': ['Biceps', 'Triceps', 'Forearms']},
        'Saturday': {'name': 'Core & Lower Back', 'body_parts': ['Abdominals', 'Obliques', 'Lower Back']},
        'Sunday': {'name': 'Rest', 'body_parts': []}
    }
}

# ============================================================================
# MOTIVATION MESSAGES
# ============================================================================

MOTIVATION_MESSAGES = {
    'high': "🔥 You're crushing it — keep the momentum!",
    'medium': "💪 Amazing work! You're making great progress!",
    'good': "✅ Solid work — aim for crisp reps!",
    'low': "💯 Any movement is progress — you've got this!"
}

# ============================================================================
# DAILY TIPS
# ============================================================================

DAILY_TIPS = [
    "💧 Stay hydrated throughout your workout!",
    "🧠 Mind-muscle connection improves results.",
    "😴 Recovery is where growth happens.",
    "📈 Progressive overload drives strength gains.",
    "🎯 Focus on form over ego lifting.",
    "⏱️ Rest periods are part of your workout.",
    "🍎 Nutrition supports your training goals.",
    "📱 Track your workouts to monitor progress.",
    "🔥 Warm up properly to prevent injuries.",
    "💪 Consistency beats perfection every time."
]

# ============================================================================
# EMERGENCY FALLBACK EXERCISES (Feature 14: 7 safe exercises)
# ============================================================================

EMERGENCY_FALLBACK_EXERCISES = [
    {
        'id': 'fallback_001',
        'title': 'Push-ups',
        'body_part': 'Chest',
        'equipment': 'Body Only',
        'level': 'Beginner',
        'type': 'Strength',
        'rating': 9.0,
        'notes': 'Basic upper body pressing exercise'
    },
    {
        'id': 'fallback_002',
        'title': 'Bodyweight Squats',
        'body_part': 'Quadriceps',
        'equipment': 'Body Only',
        'level': 'Beginner',
        'type': 'Strength',
        'rating': 9.0,
        'notes': 'Fundamental lower body exercise'
    },
    {
        'id': 'fallback_003',
        'title': 'Plank',
        'body_part': 'Abdominals',
        'equipment': 'Body Only',
        'level': 'Beginner',
        'type': 'Strength',
        'rating': 8.5,
        'notes': 'Core stability exercise'
    },
    {
        'id': 'fallback_004',
        'title': 'Lunges',
        'body_part': 'Hamstrings',
        'equipment': 'Body Only',
        'level': 'Beginner',
        'type': 'Strength',
        'rating': 8.5,
        'notes': 'Single leg strength exercise'
    },
    {
        'id': 'fallback_005',
        'title': 'Jumping Jacks',
        'body_part': 'Full Body',
        'equipment': 'Body Only',
        'level': 'Beginner',
        'type': 'Cardio',
        'rating': 8.0,
        'notes': 'Full body cardio exercise'
    },
    {
        'id': 'fallback_006',
        'title': 'Burpees',
        'body_part': 'Full Body',
        'equipment': 'Body Only',
        'level': 'Intermediate',
        'type': 'Strength',
        'rating': 8.5,
        'notes': 'Full body compound exercise'
    },
    {
        'id': 'fallback_007',
        'title': 'Mountain Climbers',
        'body_part': 'Full Body',
        'equipment': 'Body Only',
        'level': 'Intermediate',
        'type': 'Cardio',
        'rating': 8.0,
        'notes': 'Cardio and core exercise'
    }
]

# ============================================================================
# EXERCISE SCORING WEIGHTS (Feature 12)
# ============================================================================

EXERCISE_SCORING_WEIGHTS = {
    'equipment_match': 0.1,
    'body_part_preference': 0.2,
    'past_satisfaction': 0.15,
    'recency_penalty': -0.3,
    'variety': 0.1
}

# ============================================================================
# ML ADAPTATION THRESHOLDS
# ============================================================================

# Feature 8: ML Volume Adaptation
VOLUME_ADAPTATION = {
    'low_completion_threshold': 0.70,  # If <70%, reduce sets
    'high_completion_threshold': 0.95,  # If >95%, increase sets
    'low_completion_action': -1,  # Reduce sets by 1
    'high_completion_action': 1  # Increase sets by 1
}

# Feature 9: RPE-Based Rest Adjustment
RPE_ADJUSTMENT = {
    'high_rpe_threshold': 8.5,  # High RPE
    'low_rpe_threshold': 6.0,   # Low RPE
    'high_rpe_adjustment': 15,  # Add 15 seconds
    'low_rpe_adjustment': -15   # Reduce 15 seconds
}

# ============================================================================
# RECENCY SETTINGS (Feature 11)
# ============================================================================

RECENCY_SETTINGS = {
    'recent_exercises_count': 20,  # Track last 20 exercises
    'recency_penalty': -0.3  # Penalty for recent exercises
}

# ============================================================================
# CASCADE FALLBACK LEVELS (Feature 13: 6 levels)
# ============================================================================

CASCADE_FALLBACK_LEVELS = [
    'Perfect Match',      # Level 1: Exact criteria
    'Equipment Relaxed',  # Level 2: Relax equipment
    'Difficulty Relaxed', # Level 3: ±1 fitness level
    'Related Goals',      # Level 4: Similar goals
    'BMI Safety Relaxed', # Level 5: Relax BMI bounds
    'Emergency Fallback'  # Level 6: Hardcoded safe exercises
]

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_FILE = LOGS_DIR / 'fitgen.log'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ============================================================================
# CSV DATASET CONFIGURATION
# ============================================================================

DATASET_CSV_PATH = DATA_DIR / 'megaGymDataset.csv'
DATASET_CHUNK_SIZE = 500  # Process CSV in chunks

# ============================================================================
# FEATURE CHECKLIST (All 42 Features)
# ============================================================================

FEATURES = {
    1: 'Exercise Database (2,918 exercises)',
    2: 'Weekly Plan Generation',
    3: 'Daily Workout Structure',
    4: 'BMI-Based Safety Rules',
    5: 'Injury Contraindications',
    6: 'Fitness Level Adaptation',
    7: 'Goal-Based Programming',
    8: 'ML-Based Volume Adaptation',
    9: 'RPE-Based Rest Adjustment',
    10: 'Body Part Preference Learning',
    11: 'Recency Management',
    12: 'Exercise Scoring Algorithm',
    13: '6-Level Cascade Fallback',
    14: 'Emergency Fallback',
    15: 'Session Logging',
    16: 'Weekly Summary',
    17: 'Streak Tracking',
    18: 'Strength Progress',
    19: 'Data Export',
    20: 'Adaptive Motivation Messages',
    21: 'Mood Check-In',
    22: 'Guided Breathing',
    23: 'Daily Tips',
    24: 'Motivation History',
    25: 'User Profiles',
    26: 'User Data Tracking',
    27: 'Profile Editing',
    28: 'Single MongoDB Database',
    29: 'Database Admin Tools',
    30: 'Data Import',
    31: 'Beautiful CLI Menu',
    32: 'Enhanced Workout Display',
    33: 'Interactive Features',
    34: 'FastAPI Integration',
    35: 'Error Handling',
    36: 'Configuration Management',
    37: 'Synthetic Data Generation',
    38: 'Exercise Variety Algorithm',
    39: 'Progressive Overload',
    40: 'Smart Rest Periods',
    41: 'Dynamic Warmup/Cooldown',
    42: 'Exercise Notes System'
}
