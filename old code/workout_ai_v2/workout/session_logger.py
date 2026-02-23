"""
FitGen AI v5.0 - Enhanced Session Logger Module
Logs workouts with 1-10 detailed rating scale
Exports raw data to CSV
Feature 15-19: Session logging, analytics, export
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import csv
import json
import os

from config import (
    DAILY_TIPS,
    MOTIVATION_MESSAGES,
    COLLECTIONS
)
from utils import (
    generate_session_id,
    get_current_datetime,
    get_week_ago,
    validate_workout_log,
    calculate_average,
    log_success,
    log_error
)
from db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# RATING SCALE WITH QUOTES (Feature 15 Enhancement)
# ============================================================================

EXERCISE_DIFFICULTY_SCALE = {
    1: "I couldn't even move the bar",
    2: "I could not lift it up completely",
    3: "Very difficult, struggled a lot",
    4: "Difficult, but managed with effort",
    5: "Moderate difficulty, challenging",
    6: "Fair difficulty, manageable",
    7: "Easy to moderate, completed smoothly",
    8: "Easy, didn't use full potential",
    9: "Very easy, could do more",
    10: "It was too easy"
}

WORKOUT_SATISFACTION_SCALE = {
    1: "Terrible workout, felt awful",
    2: "Very poor, something went wrong",
    3: "Poor, not satisfied",
    4: "Below average, could be better",
    5: "Average, was okay",
    6: "Good, accomplished goals",
    7: "Very good, felt strong",
    8: "Excellent, great session",
    9: "Outstanding, best yet",
    10: "Perfect workout, couldn't ask for better"
}

MOOD_SCALE = {
    1: "Very low, depressed",
    2: "Low, feeling down",
    3: "Poor, not well",
    4: "Below average",
    5: "Neutral, okay",
    6: "Good, feeling better",
    7: "Very good, positive",
    8: "Great, very positive",
    9: "Excellent, feeling amazing",
    10: "Perfect, couldn't be better"
}

# ============================================================================
# SESSION LOGGER CLASS
# ============================================================================

class SessionLogger:
    """
    Logs workouts with enhanced 1-10 rating scale
    Exports data to CSV for analysis
    Features 15-19: Session logging, analytics, streaks, strength, export
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize session logger"""
        self.db_manager = db_manager
        self.session_logs = COLLECTIONS['session_logs']
        self.motivation_logs = COLLECTIONS['motivation_logs']
        self.in_memory_sessions = {}
        self.in_memory_mood = {}
        
        # Create exports directory
        os.makedirs('exports', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    # ========================================================================
    # ENHANCED SESSION LOGGING (Feature 15 - NEW 1-10 SCALE)
    # ========================================================================
    
    def log_session(self, user_id: str, workout_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Feature 15: Log completed workout session with 1-10 scale
        
        Args:
            user_id: User identifier
            workout_data: Completed workout data with:
                - planned_duration
                - actual_duration
                - exercises: List of exercises with difficulty (1-10)
                - overall_satisfaction (1-10)
                - notes
        
        Returns:
            Tuple: (success, session_doc)
        """
        
        # Validate data
        if not workout_data.get('actual_duration'):
            log_error("Missing actual_duration")
            return False, None
        
        if not workout_data.get('exercises'):
            log_error("Missing exercises")
            return False, None
        
        # Calculate metrics
        exercise_ratings = [
            ex.get('difficulty_rating', 5) 
            for ex in workout_data.get('exercises', [])
            if isinstance(ex.get('difficulty_rating'), int) and 1 <= ex.get('difficulty_rating') <= 10
        ]
        
        avg_exercise_difficulty = calculate_average(exercise_ratings) if exercise_ratings else 5
        overall_satisfaction = workout_data.get('overall_satisfaction', 5)
        
        # Validate ratings
        if not (1 <= overall_satisfaction <= 10):
            overall_satisfaction = 5
        
        # Calculate completion percentage
        planned = workout_data.get('planned_duration', 60)
        actual = workout_data.get('actual_duration', 0)
        completion_percentage = min(100, int((actual / planned * 100) if planned > 0 else 100))
        
        session_log = {
            'session_id': generate_session_id(user_id),
            'user_id': user_id,
            'date': get_current_datetime(),
            'planned_duration': planned,
            'actual_duration': actual,
            'duration_variance': actual - planned,
            'completion_percentage': completion_percentage,
            'exercises': workout_data.get('exercises', []),
            'exercise_count': len(workout_data.get('exercises', [])),
            'avg_exercise_difficulty': round(avg_exercise_difficulty, 1),
            'overall_satisfaction': overall_satisfaction,
            'satisfaction_description': WORKOUT_SATISFACTION_SCALE.get(overall_satisfaction, 'Average'),
            'notes': workout_data.get('notes', ''),
            'energy_level': workout_data.get('energy_level', 5),
            'recovery_needed': workout_data.get('recovery_needed', False),
            'raw_data': True  # Mark for CSV export
        }
        
        if self.db_manager.is_connected():
            success = self.db_manager.insert_one(self.session_logs, session_log)
            if success:
                log_success(f"✅ Workout logged for {user_id} - Satisfaction: {overall_satisfaction}/10")
                
                # Auto-export to CSV
                self._export_session_to_csv(session_log)
                
                return True, session_log
            else:
                return False, None
        else:
            # In-memory fallback
            if user_id not in self.in_memory_sessions:
                self.in_memory_sessions[user_id] = []
            self.in_memory_sessions[user_id].append(session_log)
            
            # Auto-export to CSV
            self._export_session_to_csv(session_log)
            
            return True, session_log
    
    # ========================================================================
    # CSV EXPORT (Feature 19 - RAW DATA EXPORT)
    # ========================================================================
    
    def _export_session_to_csv(self, session: Dict) -> bool:
        """
        Export individual session to CSV (appends to raw data file)
        
        Args:
            session: Session document
        
        Returns:
            Success status
        """
        try:
            user_id = session.get('user_id', 'unknown')
            csv_file = f'exports/raw_workouts_{user_id}.csv'
            
            # Check if file exists
            file_exists = os.path.exists(csv_file)
            
            with open(csv_file, 'a', newline='') as csvfile:
                fieldnames = [
                    'session_id', 'user_id', 'date', 'planned_duration', 
                    'actual_duration', 'completion_%', 'exercise_count',
                    'avg_difficulty', 'overall_satisfaction', 'satisfaction_description',
                    'energy_level', 'recovery_needed', 'notes'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header only if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Write session data
                writer.writerow({
                    'session_id': session.get('session_id'),
                    'user_id': session.get('user_id'),
                    'date': session.get('date'),
                    'planned_duration': session.get('planned_duration'),
                    'actual_duration': session.get('actual_duration'),
                    'completion_%': session.get('completion_percentage'),
                    'exercise_count': session.get('exercise_count'),
                    'avg_difficulty': session.get('avg_exercise_difficulty'),
                    'overall_satisfaction': session.get('overall_satisfaction'),
                    'satisfaction_description': session.get('satisfaction_description'),
                    'energy_level': session.get('energy_level'),
                    'recovery_needed': session.get('recovery_needed'),
                    'notes': session.get('notes')
                })
            
            return True
        except Exception as e:
            log_error(f"CSV export failed: {e}")
            return False
    
    def export_all_sessions_to_csv(self, user_id: str, filepath: str = None) -> Tuple[bool, str]:
        """
        Feature 19: Export all sessions to CSV (raw data)
        
        Args:
            user_id: User identifier
            filepath: Optional custom filepath
        
        Returns:
            Tuple: (success, message)
        """
        if filepath is None:
            filepath = f'exports/workouts_{user_id}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        if self.db_manager.is_connected():
            sessions = self.db_manager.find_many(
                self.session_logs,
                limit=10000
            )
            sessions = [s for s in sessions if s.get('user_id') == user_id]
        else:
            sessions = self.in_memory_sessions.get(user_id, [])
        
        if not sessions:
            return False, "No sessions found for export"
        
        try:
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = [
                    'session_id', 'date', 'planned_duration', 'actual_duration',
                    'completion_%', 'exercise_count', 'avg_difficulty',
                    'overall_satisfaction', 'satisfaction_description',
                    'energy_level', 'recovery_needed', 'notes'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for session in sessions:
                    writer.writerow({
                        'session_id': session.get('session_id'),
                        'date': session.get('date'),
                        'planned_duration': session.get('planned_duration'),
                        'actual_duration': session.get('actual_duration'),
                        'completion_%': session.get('completion_percentage'),
                        'exercise_count': session.get('exercise_count'),
                        'avg_difficulty': session.get('avg_exercise_difficulty'),
                        'overall_satisfaction': session.get('overall_satisfaction'),
                        'satisfaction_description': session.get('satisfaction_description'),
                        'energy_level': session.get('energy_level'),
                        'recovery_needed': session.get('recovery_needed'),
                        'notes': session.get('notes')
                    })
            
            log_success(f"✅ Exported {len(sessions)} sessions to {filepath}")
            return True, f"Exported {len(sessions)} sessions to {filepath}"
        
        except Exception as e:
            log_error(f"Export failed: {e}")
            return False, f"Export failed: {e}"
    
    # ========================================================================
    # WEEKLY SUMMARY (Feature 16)
    # ========================================================================
    
    def get_weekly_summary(self, user_id: str) -> Dict:
        """
        Feature 16: Get weekly summary with new metrics
        
        Returns: Complete weekly statistics
        """
        week_ago = get_week_ago()
        
        if self.db_manager.is_connected():
            sessions = self.db_manager.find_many(
                self.session_logs,
                limit=1000
            )
            sessions = [s for s in sessions 
                       if s.get('user_id') == user_id 
                       and s.get('date', '') >= week_ago]
        else:
            sessions = [s for s in self.in_memory_sessions.get(user_id, [])
                       if s.get('date', '') >= week_ago]
        
        if not sessions:
            return {
                'workouts': 0,
                'total_time': 0,
                'avg_completion': 0.0,
                'avg_satisfaction': 0.0,
                'avg_difficulty': 0.0,
                'active_days': 0
            }
        
        total_time = sum(s.get('actual_duration', 0) for s in sessions)
        completion_rates = [s.get('completion_percentage', 100) for s in sessions]
        satisfaction_scores = [s.get('overall_satisfaction', 5) for s in sessions]
        difficulty_scores = [s.get('avg_exercise_difficulty', 5) for s in sessions]
        
        active_dates = set(s.get('date', '')[:10] for s in sessions)
        
        return {
            'total_workouts': len(sessions),
            'total_training_time': total_time,
            'avg_completion_rate': round(calculate_average(completion_rates), 1),
            'avg_satisfaction': round(calculate_average(satisfaction_scores), 1),
            'avg_difficulty': round(calculate_average(difficulty_scores), 1),
            'active_days': len(active_dates),
            'satisfaction_description': WORKOUT_SATISFACTION_SCALE.get(
                int(calculate_average(satisfaction_scores)), 'Average'
            )
        }
    
    # ========================================================================
    # STREAK TRACKING (Feature 17)
    # ========================================================================
    
    def get_streak(self, user_id: str) -> Dict:
        """Feature 17: Get streak tracking information"""
        if self.db_manager.is_connected():
            sessions = self.db_manager.find_many(
                self.session_logs,
                limit=1000
            )
            sessions = [s for s in sessions if s.get('user_id') == user_id]
        else:
            sessions = self.in_memory_sessions.get(user_id, [])
        
        if not sessions:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_sessions': 0
            }
        
        session_dates = sorted(set(s.get('date', '')[:10] for s in sessions))
        
        if not session_dates:
            return {'current_streak': 0, 'longest_streak': 0, 'total_sessions': 0}
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        date_objects = []
        for date_str in session_dates:
            try:
                date_obj = datetime.fromisoformat(date_str).date()
                date_objects.append(date_obj)
            except (ValueError, TypeError):
                continue
        
        date_objects.sort()
        
        for i in range(len(date_objects)):
            if i == 0:
                temp_streak = 1
            else:
                days_diff = (date_objects[i] - date_objects[i-1]).days
                if days_diff == 1:
                    temp_streak += 1
                else:
                    temp_streak = 1
            
            longest_streak = max(longest_streak, temp_streak)
        
        if date_objects and (datetime.now().date() - date_objects[-1]).days <= 1:
            current_streak = temp_streak
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_sessions': len(sessions)
        }
    
    # ========================================================================
    # STRENGTH PROGRESS (Feature 18)
    # ========================================================================
    
    def get_strength_progress(self, user_id: str) -> Dict:
        """
        Feature 18: Track strength progress and difficulty trends
        
        Returns: Strength progress data
        """
        if self.db_manager.is_connected():
            sessions = self.db_manager.find_many(
                self.session_logs,
                limit=1000
            )
            sessions = [s for s in sessions if s.get('user_id') == user_id]
        else:
            sessions = self.in_memory_sessions.get(user_id, [])
        
        if not sessions:
            return {'progression': [], 'avg_difficulty': 0, 'trend': 'stable'}
        
        # Extract difficulty data from sessions
        difficulty_data = []
        for session in sessions:
            difficulty_data.append({
                'date': session.get('date'),
                'avg_difficulty': session.get('avg_exercise_difficulty', 5),
                'overall_satisfaction': session.get('overall_satisfaction', 5),
                'exercise_count': session.get('exercise_count', 0)
            })
        
        difficulties = [d['avg_difficulty'] for d in difficulty_data]
        avg_difficulty = calculate_average(difficulties)
        
        # Determine trend
        trend = 'stable'
        if len(difficulties) > 1:
            recent_avg = calculate_average(difficulties[-5:])
            older_avg = calculate_average(difficulties[:-5]) if len(difficulties) > 5 else recent_avg
            if recent_avg > older_avg * 1.1:
                trend = 'increasing (getting harder)'
            elif recent_avg < older_avg * 0.9:
                trend = 'decreasing (easier)'
        
        return {
            'progression': difficulty_data,
            'avg_difficulty': round(avg_difficulty, 1),
            'trend': trend,
            'total_sessions_logged': len(difficulty_data)
        }
    
    # ========================================================================
    # MOOD TRACKING (Feature 21 - ENHANCED)
    # ========================================================================
    
    def log_mood(self, user_id: str, mood_score: int, notes: str = '') -> Tuple[bool, str]:
        """
        Feature 21: Log daily mood with 1-10 scale
        
        Args:
            user_id: User identifier
            mood_score: Mood score 1-10
            notes: Optional notes
        
        Returns:
            Tuple: (success, message)
        """
        if not (1 <= mood_score <= 10):
            return False, "Mood score must be 1-10"
        
        mood_log = {
            'user_id': user_id,
            'date': get_current_datetime(),
            'mood_score': mood_score,
            'mood_label': MOOD_SCALE.get(mood_score, 'Neutral'),
            'notes': notes
        }
        
        if self.db_manager.is_connected():
            success = self.db_manager.insert_one(self.motivation_logs, mood_log)
            if success:
                log_success(f"✅ Mood logged: {mood_score}/10 - {MOOD_SCALE.get(mood_score)}")
                return True, f"Mood logged: {mood_score}/10"
            else:
                return False, "Failed to log mood"
        else:
            if user_id not in self.in_memory_mood:
                self.in_memory_mood[user_id] = []
            self.in_memory_mood[user_id].append(mood_log)
            return True, f"Mood logged: {mood_score}/10"
    
    # ========================================================================
    # MOTIVATION HISTORY (Feature 24)
    # ========================================================================
    
    def get_mood_history(self, user_id: str, days: int = 30) -> Dict:
        """Feature 24: Get mood trend history with descriptions"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        if self.db_manager.is_connected():
            mood_logs = self.db_manager.find_many(
                self.motivation_logs,
                limit=10000
            )
            mood_logs = [m for m in mood_logs 
                        if m.get('user_id') == user_id 
                        and m.get('date', '') >= cutoff_date]
        else:
            mood_logs = [m for m in self.in_memory_mood.get(user_id, [])
                        if m.get('date', '') >= cutoff_date]
        
        if not mood_logs:
            return {'avg_mood': 0, 'trend': 'stable', 'entries': 0}
        
        mood_scores = [m.get('mood_score', 0) for m in mood_logs]
        avg_mood = calculate_average(mood_scores)
        
        # Determine trend
        trend = 'stable'
        if len(mood_scores) > 1:
            recent_mood = calculate_average(mood_scores[-7:])
            older_mood = calculate_average(mood_scores[:-7]) if len(mood_scores) > 7 else recent_mood
            if recent_mood > older_mood:
                trend = 'improving'
            elif recent_mood < older_mood:
                trend = 'declining'
        
        return {
            'avg_mood': round(avg_mood, 1),
            'mood_description': MOOD_SCALE.get(int(avg_mood), 'Neutral'),
            'trend': trend,
            'entries': len(mood_logs),
            'mood_data': mood_logs
        }

# ============================================================================
# BREATHING EXERCISES (Feature 22)
# ============================================================================

def get_breathing_exercise() -> Dict:
    """Feature 22: Guided breathing exercise"""
    return {
        'exercise': 'Box Breathing',
        'description': '4-count breathing cycle for stress reduction',
        'steps': [
            'Breathe in slowly: 1... 2... 3... 4',
            'Hold your breath: 1... 2... 3... 4',
            'Exhale slowly: 1... 2... 3... 4',
            'Hold empty: 1... 2... 3... 4',
            'Repeat 5-10 times'
        ],
        'benefits': [
            'Reduces stress and anxiety',
            'Improves focus and clarity',
            'Enhances breathing control',
            'Pre-workout activation'
        ]
    }
