"""
FitGen AI v5.0 - Motivation System Module
Manages motivation messages, mood tracking, and mental wellness
Features 20-24: Motivation, mood check-in, breathing, tips, history
"""

import logging
from typing import Dict, List, Optional
import random
from datetime import datetime

from config import (
    MOTIVATION_MESSAGES,
    DAILY_TIPS,
    COLLECTIONS
)
from utils import log_success, log_info
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# MOTIVATION SYSTEM CLASS
# ============================================================================

class MotivationSystem:
    """
    Comprehensive motivation and mental wellness system
    Features 20-24: Adaptive motivation, mood tracking, breathing, tips
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize motivation system
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.motivation_logs = COLLECTIONS['motivation_logs']
    
    # ========================================================================
    # ADAPTIVE MOTIVATION (Feature 20)
    # ========================================================================
    
    def get_adaptive_message(self, user_performance: Dict) -> str:
        """
        Feature 20: Get adaptive motivation message based on user performance
        
        Args:
            user_performance: Dict with streak, completion_rate, satisfaction
        
        Returns:
            Personalized motivation message
        """
        streak = user_performance.get('current_streak', 0)
        completion = user_performance.get('avg_completion_rate', 0)
        satisfaction = user_performance.get('avg_satisfaction', 0)
        
        # High performance (Feature 20)
        if streak >= 10 and completion >= 90:
            return random.choice(MOTIVATION_MESSAGES['high_motivation'])
        
        # Medium performance (Feature 20)
        elif streak >= 5 or completion >= 75:
            return random.choice(MOTIVATION_MESSAGES['medium_motivation'])
        
        # Good effort (Feature 20)
        elif streak >= 2 or completion >= 60:
            return random.choice(MOTIVATION_MESSAGES['good_motivation'])
        
        # Needs encouragement (Feature 20)
        else:
            return random.choice(MOTIVATION_MESSAGES['low_motivation'])
    
    def get_random_motivation(self) -> str:
        """
        Get random motivation message
        
        Returns:
            Random motivation message
        """
        all_messages = []
        for category in MOTIVATION_MESSAGES.values():
            all_messages.extend(category)
        
        return random.choice(all_messages)
    
    def get_motivation_by_level(self, level: str) -> str:
        """
        Get motivation message by level
        
        Args:
            level: high_motivation, medium_motivation, good_motivation, low_motivation
        
        Returns:
            Motivation message
        """
        messages = MOTIVATION_MESSAGES.get(level, MOTIVATION_MESSAGES['good_motivation'])
        return random.choice(messages)
    
    # ========================================================================
    # DAILY TIPS (Feature 23)
    # ========================================================================
    
    def get_daily_tip(self) -> str:
        """
        Feature 23: Get daily fitness tip (rotates through 10 tips)
        
        Returns:
            Daily tip
        """
        return random.choice(DAILY_TIPS)
    
    def get_tip_of_day(self) -> str:
        """
        Get tip based on day of year (consistent per day)
        
        Returns:
            Tip for today
        """
        day_of_year = datetime.now().timetuple().tm_yday
        tip_index = day_of_year % len(DAILY_TIPS)
        return DAILY_TIPS[tip_index]
    
    def get_all_tips(self) -> List[str]:
        """
        Get all available tips
        
        Returns:
            List of all tips
        """
        return DAILY_TIPS.copy()
    
    # ========================================================================
    # BREATHING EXERCISES (Feature 22)
    # ========================================================================
    
    def get_breathing_exercise(self, exercise_type: str = 'box') -> Dict:
        """
        Feature 22: Get guided breathing exercise
        
        Args:
            exercise_type: Type of breathing exercise
        
        Returns:
            Breathing exercise instructions
        """
        exercises = {
            'box': {
                'name': 'Box Breathing',
                'description': '4-count breathing cycle for stress reduction',
                'duration_seconds': 240,
                'steps': [
                    {'step': 1, 'action': 'Breathe in slowly', 'duration': 4, 'instruction': '1... 2... 3... 4'},
                    {'step': 2, 'action': 'Hold your breath', 'duration': 4, 'instruction': '1... 2... 3... 4'},
                    {'step': 3, 'action': 'Exhale slowly', 'duration': 4, 'instruction': '1... 2... 3... 4'},
                    {'step': 4, 'action': 'Hold empty', 'duration': 4, 'instruction': '1... 2... 3... 4'},
                ],
                'repetitions': 5,
                'benefits': [
                    'Reduces stress and anxiety',
                    'Improves focus and clarity',
                    'Enhances breathing control',
                    'Pre-workout activation',
                    'Better oxygen flow'
                ]
            },
            '478': {
                'name': '4-7-8 Breathing',
                'description': 'Relaxation breathing for better sleep',
                'duration_seconds': 180,
                'steps': [
                    {'step': 1, 'action': 'Breathe in', 'duration': 4, 'instruction': 'Count to 4'},
                    {'step': 2, 'action': 'Hold breath', 'duration': 7, 'instruction': 'Count to 7'},
                    {'step': 3, 'action': 'Exhale completely', 'duration': 8, 'instruction': 'Count to 8'}
                ],
                'repetitions': 4,
                'benefits': [
                    'Promotes relaxation',
                    'Helps with sleep',
                    'Reduces anxiety',
                    'Calms nervous system'
                ]
            },
            'coherent': {
                'name': 'Coherent Breathing',
                'description': 'Equal inhale/exhale for balance',
                'duration_seconds': 300,
                'steps': [
                    {'step': 1, 'action': 'Breathe in', 'duration': 5, 'instruction': 'Count to 5'},
                    {'step': 2, 'action': 'Breathe out', 'duration': 5, 'instruction': 'Count to 5'}
                ],
                'repetitions': 10,
                'benefits': [
                    'Balances nervous system',
                    'Improves heart rate variability',
                    'Reduces stress',
                    'Enhances focus'
                ]
            }
        }
        
        return exercises.get(exercise_type, exercises['box'])
    
    def get_all_breathing_exercises(self) -> List[Dict]:
        """
        Get all available breathing exercises
        
        Returns:
            List of all breathing exercises
        """
        return [
            self.get_breathing_exercise('box'),
            self.get_breathing_exercise('478'),
            self.get_breathing_exercise('coherent')
        ]
    
    # ========================================================================
    # MOOD TRACKING (Feature 21)
    # ========================================================================
    
    def log_mood(self, user_id: str, mood_score: int, notes: str = '') -> bool:
        """
        Feature 21: Log daily mood (1-5 scale)
        
        Args:
            user_id: User identifier
            mood_score: Mood score (1-5)
            notes: Optional notes
        
        Returns:
            Success status
        """
        if not 1 <= mood_score <= 5:
            log_info("Invalid mood score. Must be 1-5")
            return False
        
        mood_log = {
            'user_id': user_id,
            'date': datetime.now().isoformat(),
            'mood_score': mood_score,
            'mood_label': self._get_mood_label(mood_score),
            'notes': notes
        }
        
        if self.db_manager.is_connected():
            success = self.db_manager.insert_one(self.motivation_logs, mood_log)
            if success:
                log_success(f"Mood logged for {user_id}: {mood_score}/5")
            return success
        
        return False
    
    def _get_mood_label(self, score: int) -> str:
        """Get mood label from score"""
        labels = {
            1: 'Very Low',
            2: 'Low',
            3: 'Neutral',
            4: 'Good',
            5: 'Excellent'
        }
        return labels.get(score, 'Unknown')
    
    def get_mood_emoji(self, score: int) -> str:
        """Get emoji for mood score"""
        emojis = {
            1: '😢',
            2: '😕',
            3: '😐',
            4: '😊',
            5: '😄'
        }
        return emojis.get(score, '😐')
    
    # ========================================================================
    # MOOD HISTORY (Feature 24)
    # ========================================================================
    
    def get_mood_history(self, user_id: str, days: int = 30) -> Dict:
        """
        Feature 24: Get mood history and trends
        
        Args:
            user_id: User identifier
            days: Number of days to look back
        
        Returns:
            Mood history with trends
        """
        if not self.db_manager.is_connected():
            return {
                'avg_mood': 0,
                'trend': 'No data',
                'entries': 0,
                'mood_data': []
            }
        
        # Get mood logs
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        mood_logs = self.db_manager.find_many(
            self.motivation_logs,
            limit=1000
        )
        
        # Filter by user and date
        user_moods = [
            m for m in mood_logs
            if m.get('user_id') == user_id and m.get('date', '') >= cutoff
        ]
        
        if not user_moods:
            return {
                'avg_mood': 0,
                'trend': 'No data',
                'entries': 0,
                'mood_data': []
            }
        
        # Calculate statistics
        scores = [m['mood_score'] for m in user_moods]
        avg_mood = sum(scores) / len(scores)
        
        # Determine trend (Feature 24)
        trend = 'Stable'
        if len(scores) > 7:
            recent = sum(scores[-7:]) / 7
            older = sum(scores[:-7]) / (len(scores) - 7)
            
            if recent > older + 0.5:
                trend = 'Improving'
            elif recent < older - 0.5:
                trend = 'Declining'
        
        return {
            'avg_mood': round(avg_mood, 2),
            'trend': trend,
            'entries': len(user_moods),
            'mood_data': user_moods,
            'recent_avg': round(sum(scores[-7:]) / min(7, len(scores)), 2) if scores else 0
        }
    
    # ========================================================================
    # MOTIVATIONAL INSIGHTS
    # ========================================================================
    
    def get_motivational_insights(self, user_id: str) -> Dict:
        """
        Get comprehensive motivational insights
        
        Args:
            user_id: User identifier
        
        Returns:
            Motivational insights
        """
        mood_data = self.get_mood_history(user_id, days=30)
        
        insights = {
            'avg_mood': mood_data['avg_mood'],
            'trend': mood_data['trend'],
            'message': '',
            'recommendation': '',
            'breathing_exercise': 'box'
        }
        
        # Generate personalized message
        if mood_data['avg_mood'] >= 4:
            insights['message'] = "You're doing amazing! Keep up the positive energy!"
            insights['recommendation'] = "Maintain your current routine"
        elif mood_data['avg_mood'] >= 3:
            insights['message'] = "You're on the right track. Stay consistent!"
            insights['recommendation'] = "Focus on regular workouts"
        else:
            insights['message'] = "It's okay to have tough days. We're here for you!"
            insights['recommendation'] = "Try breathing exercises and lighter workouts"
            insights['breathing_exercise'] = '478'
        
        return insights
    
    def generate_weekly_motivation_report(self, user_id: str) -> Dict:
        """
        Generate weekly motivation report
        
        Args:
            user_id: User identifier
        
        Returns:
            Weekly motivation report
        """
        mood_data = self.get_mood_history(user_id, days=7)
        
        report = {
            'period': 'Last 7 Days',
            'avg_mood': mood_data['avg_mood'],
            'entries_logged': mood_data['entries'],
            'trend': mood_data['trend'],
            'daily_tip': self.get_daily_tip(),
            'motivation_message': self.get_random_motivation(),
            'suggested_breathing': self.get_breathing_exercise('box')
        }
        
        return report
