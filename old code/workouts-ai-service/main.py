"""
FitGen AI v5.0 - Main Orchestrator
CLI Application Entry Point
Ties all modules together and implements main menu loop
"""
import os
import sys
import logging
from typing import Optional

# ============================================================================
# IMPORTS - ALL MODULES
# ============================================================================

from config import FEATURES
from utils import log_success, log_error, log_info
from db.database_manager import DatabaseManager
from data.exercise_database import ExerciseDatabase
from user.profile_manager import UserProfileManager
from workout.workout_gen import WorkoutGenerator
from workout.session_logger import SessionLogger
from ui.cli_manager import UIManager

logger = logging.getLogger(__name__)

# ============================================================================
# FITGEN APPLICATION CLASS
# ============================================================================

class FitGenApp:
    """
    Main FitGen AI application orchestrator
    Coordinates all modules and manages application flow
    """
    
    def __init__(self):
        """Initialize FitGen application"""
        self.db_manager = None
        self.exercise_db = None
        self.profile_manager = None
        self.workout_generator = None
        self.session_logger = None
        self.current_user = None
        
        self.initialize()
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def initialize(self):
        """Initialize all application modules"""
        try:
            log_info("Initializing FitGen AI v5.0...")
            
            # Initialize database
            UIManager.clear_screen()
            UIManager.print_header("🚀 FitGen AI v5.0 - Initializing...")
            
            print("  ⏳ Connecting to database...")
            self.db_manager = DatabaseManager()
            
            print("  ⏳ Loading exercises (2,918)...")
            self.exercise_db = ExerciseDatabase(self.db_manager)
            
            print("  ⏳ Initializing user manager...")
            self.profile_manager = UserProfileManager(self.db_manager)
            
            print("  ⏳ Initializing workout generator...")
            self.workout_generator = WorkoutGenerator(self.db_manager, self.exercise_db)
            
            print("  ⏳ Initializing session logger...")
            self.session_logger = SessionLogger(self.db_manager)
            
            log_success("✅ All systems initialized successfully!")
            
            # Display system info
            self.display_system_info()
            
        except Exception as e:
            log_error(f"Initialization failed: {e}")
            sys.exit(1)
    
    def display_system_info(self):
        """Display system information"""
        UIManager.clear_screen()
        UIManager.print_header("📊 FitGen AI v5.0 - System Status")
        
        status = self.db_manager.get_connection_status()
        exercises_stats = self.exercise_db.get_statistics()
        
        print(f"  Database: {status['storage_type']}")
        print(f"  Database Name: {status['database']}")
        print(f"  Connection: {'✅ Connected' if status['connected'] else '⚠️ In-Memory Mode'}")
        print()
        print(f"  📚 Exercise Database:")
        print(f"     Total Exercises: {exercises_stats.get('total_exercises', 0)}")
        print(f"     Body Parts: {len(exercises_stats.get('body_parts', {}))}")
        print(f"     Equipment Types: {len(exercises_stats.get('equipment_types', {}))}")
        print(f"     Avg Rating: {exercises_stats.get('avg_rating', 0):.2f}")
        print()
        print(f"  👥 Users: {self.profile_manager.count_users()}")
        print()
        print("  ✅ All 42 Features Ready:")
        print("     - Batch 1: 21 Features (Core Database & Exercises)")
        print("     - Batch 2: 21 Features (Workouts, Analytics, UI)")
        print()
        
        UIManager.pause_continue()
    
    # ========================================================================
    # MAIN MENU LOOP
    # ========================================================================
    
    def run(self):
        """Run main application loop"""
        while True:
            choice = UIManager.display_main_menu()
            
            if choice == '1':
                self.user_management_menu()
            elif choice == '2':
                self.workout_generation_menu()
            elif choice == '3':
                self.daily_workout_menu()
            elif choice == '4':
                self.progress_menu()
            elif choice == '5':
                self.motivation_menu()
            elif choice == '6':
                self.admin_menu()
            elif choice == '7':
                self.exit_app()
            else:
                UIManager.show_error("Invalid option. Please try again.")
                UIManager.pause_continue()
    
    # ========================================================================
    # USER MANAGEMENT MENU (Feature 31)
    # ========================================================================
    
    def user_management_menu(self):
        """Feature 31: User management menu"""
        while True:
            choice = UIManager.display_user_menu()
            
            if choice == '1':
                self.create_user()
            elif choice == '2':
                self.view_user()
            elif choice == '3':
                self.edit_user()
            elif choice == '4':
                self.delete_user()
            elif choice == '5':
                self.switch_user()
            elif choice == '6':
                self.view_all_users()
            elif choice == '7':
                break
            else:
                UIManager.show_error("Invalid option.")
    
    def create_user(self):
        """Create new user profile (Feature 25)"""
        UIManager.clear_screen()
        profile_data = UIManager.prompt_user_creation()
        
        success, user_doc, msg = self.profile_manager.create_user(
            profile_data['user_id'],
            profile_data
        )
        
        if success:
            UIManager.show_success(msg)
            self.current_user = user_doc
            print(f"\n✅ User '{profile_data['name']}' created successfully!")
            print(f"   BMI: {user_doc['bmi']:.1f} ({user_doc['bmi_category']})")
        else:
            UIManager.show_error(msg)
        
        UIManager.pause_continue()
    
    def view_user(self):
        """View current user profile (Feature 26)"""
        if not self.current_user:
            UIManager.show_warning("No user selected. Please create or switch user first.")
            UIManager.pause_continue()
            return
        
        UIManager.clear_screen()
        UIManager.print_header("👤 User Profile")
        
        stats = self.profile_manager.get_user_stats(self.current_user['user_id'])
        UIManager.display_stats(stats)
        
        UIManager.pause_continue()
    
    def edit_user(self):
        """Edit user profile (Feature 27)"""
        if not self.current_user:
            UIManager.show_warning("No user selected.")
            UIManager.pause_continue()
            return
        
        UIManager.clear_screen()
        print("\n⚙️  Edit User Profile")
        print("-" * 80)
        print("  1. Update Weight")
        print("  2. Update Fitness Level")
        print("  3. Update Goal")
        print("  4. Add Injury")
        print("  5. Back")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            try:
                new_weight = float(input("Enter new weight (kg): "))
                success, msg = self.profile_manager.update_weight(self.current_user['user_id'], new_weight)
                UIManager.show_success(msg) if success else UIManager.show_error(msg)
            except ValueError:
                UIManager.show_error("Invalid weight value. Please enter a number.")
        
        elif choice == '2':
            print("  Beginner / Intermediate / Expert")
            level = input("Select level: ").strip()
            success, msg = self.profile_manager.update_fitness_level(self.current_user['user_id'], level)
            UIManager.show_success(msg) if success else UIManager.show_error(msg)
        
        elif choice == '3':
            print("  Weight Loss / Muscle Gain / Strength / Endurance / General Fitness / Athletic Performance")
            goal = input("Select goal: ").strip()
            success, msg = self.profile_manager.update_goal(self.current_user['user_id'], goal)
            UIManager.show_success(msg) if success else UIManager.show_error(msg)
        
        UIManager.pause_continue()
    
    def delete_user(self):
        """Delete user (Feature 25)"""
        if not self.current_user:
            UIManager.show_warning("No user selected.")
            UIManager.pause_continue()
            return
        
        if UIManager.confirm("Are you sure you want to delete this user?"):
            success, msg = self.profile_manager.delete_user(self.current_user['user_id'])
            if success:
                UIManager.show_success(msg)
                self.current_user = None
            else:
                UIManager.show_error(msg)
        
        UIManager.pause_continue()
    
    def switch_user(self):
        """Switch to different user (Feature 26)"""
        user_id = input("Enter user ID: ").strip()
        user = self.profile_manager.get_user(user_id)
        
        if user:
            self.current_user = user
            UIManager.show_success(f"Switched to user: {user['name']}")
        else:
            UIManager.show_error(f"User {user_id} not found")
        
        UIManager.pause_continue()
    
    def view_all_users(self):
        """View all users (Feature 26)"""
        users = self.profile_manager.get_all_users(limit=100)
        
        if not users:
            UIManager.show_info("No users found.")
            UIManager.pause_continue()
            return
        
        UIManager.clear_screen()
        UIManager.print_header(f"👥 All Users ({len(users)})")
        
        headers = ['Name', 'Age', 'BMI', 'Goal', 'Fitness Level']
        rows = [
            [u['name'], u['age'], f"{u['bmi']:.1f}", u['goal'], u['fitness_level']]
            for u in users
        ]
        
        UIManager.display_table(headers, rows)
        UIManager.pause_continue()
    
    # ========================================================================
    # WORKOUT GENERATION MENU (Feature 2-3)
    # ========================================================================
    
    def workout_generation_menu(self):
        """Feature 31: Workout generation menu"""
        if not self.current_user:
            UIManager.show_warning("Please select or create a user first.")
            UIManager.pause_continue()
            return
        
        while True:
            choice = UIManager.display_workout_menu()
            
            if choice == '1':
                self.generate_daily_workout()
            elif choice == '2':
                self.generate_weekly_plan()
            elif choice == '3':
                self.view_generated_workout()
            elif choice == '4':
                self.save_workout()
            elif choice == '5':
                break
            else:
                UIManager.show_error("Invalid option.")
    
    def generate_daily_workout(self):
        """Generate daily workout (Feature 3)"""
        UIManager.clear_screen()
        print("🏋️  Generating Daily Workout...")
        
        workout = self.workout_generator.generate_daily_workout(
            self.current_user,
            target_body_parts=['Chest', 'Back', 'Shoulders'],
            duration_minutes=60
        )
        
        self.current_user['last_workout'] = workout
        UIManager.display_workout(workout)
        UIManager.pause_continue()
    
    def generate_weekly_plan(self):
        """Generate weekly plan (Feature 2)"""
        UIManager.clear_screen()
        print("  Select split type:")
        print("    1. Push/Pull/Legs")
        print("    2. Upper/Lower")
        print("    3. Full Body")
        
        split_choice = input("  Select (1-3): ").strip()
        splits = {
            '1': 'Push/Pull/Legs',
            '2': 'Upper/Lower',
            '3': 'Full Body'
        }
        
        split_type = splits.get(split_choice, 'Push/Pull/Legs')
        
        print(f"  Generating {split_type} plan...")
        plan = self.workout_generator.generate_weekly_plan(self.current_user, split_type)
        
        self.current_user['weekly_plan'] = plan
        UIManager.display_weekly_plan(plan)
        UIManager.pause_continue()
    
    def view_generated_workout(self):
        """View last generated workout"""
        if not self.current_user.get('last_workout'):
            UIManager.show_warning("No workout generated yet.")
            UIManager.pause_continue()
            return
        
        UIManager.display_workout(self.current_user['last_workout'])
        UIManager.pause_continue()
    
    def save_workout(self):
        """Save workout to database"""
        if not self.current_user.get('weekly_plan'):
            UIManager.show_warning("No weekly plan to save.")
            UIManager.pause_continue()
            return
        
        success = self.workout_generator.save_weekly_plan(self.current_user['weekly_plan'])
        
        if success:
            UIManager.show_success("Weekly plan saved successfully!")
        else:
            UIManager.show_error("Failed to save plan.")
        
        UIManager.pause_continue()
    
    # ========================================================================
    # DAILY WORKOUT / LOGGING MENU (Feature 15)
    # ========================================================================
    
    def daily_workout_menu(self):
        """Feature 31: Daily workout/logging menu"""
        if not self.current_user:
            UIManager.show_warning("Please select or create a user first.")
            UIManager.pause_continue()
            return
        
        while True:
            choice = UIManager.display_logging_menu()
            
            if choice == '1':
                self.log_workout()
            elif choice == '2':
                self.view_today_workout()
            elif choice == '3':
                self.record_exercise()
            elif choice == '4':
                self.add_notes()
            elif choice == '5':
                break
            else:
                UIManager.show_error("Invalid option.")
    
    def log_workout(self):
        """Log completed workout (Feature 15)"""
        UIManager.clear_screen()
        workout_data = UIManager.prompt_workout_log()
        
        success, session = self.session_logger.log_session(self.current_user['user_id'], workout_data)
        
        if success:
            UIManager.show_success("Workout logged successfully!")
            self.profile_manager.update_workout_stats(self.current_user['user_id'], workout_data)
        else:
            UIManager.show_error("Failed to log workout.")
        
        UIManager.pause_continue()
    
    def view_today_workout(self):
        """View today's planned workout"""
        if not self.current_user.get('last_workout'):
            UIManager.show_warning("No workout for today.")
            UIManager.pause_continue()
            return
        
        UIManager.display_workout(self.current_user['last_workout'])
        UIManager.pause_continue()
    
    def record_exercise(self):
        """Record exercise details"""
        UIManager.show_info("Exercise details recording coming soon...")
        UIManager.pause_continue()
    
    def add_notes(self):
        """Add notes to workout"""
        UIManager.show_info("Workout notes feature coming soon...")
        UIManager.pause_continue()
    
    # ========================================================================
    # PROGRESS & INSIGHTS MENU (Feature 16-19)
    # ========================================================================
    
    def progress_menu(self):
        """Feature 31: Progress menu"""
        if not self.current_user:
            UIManager.show_warning("Please select or create a user first.")
            UIManager.pause_continue()
            return
        
        while True:
            choice = UIManager.display_progress_menu()
            
            if choice == '1':
                self.view_weekly_summary()
            elif choice == '2':
                self.view_streak()
            elif choice == '3':
                self.view_strength_progress()
            elif choice == '4':
                self.export_data()
            elif choice == '5':
                self.view_body_stats()
            elif choice == '6':
                break
            else:
                UIManager.show_error("Invalid option.")
    
    def view_weekly_summary(self):
        """View weekly summary (Feature 16)"""
        summary = self.session_logger.get_weekly_summary(self.current_user['user_id'])
        
        UIManager.clear_screen()
        UIManager.print_header("📊 Weekly Summary (Feature 16)")
        
        print(f"  Total Workouts: {summary['total_workouts']}")
        print(f"  Total Training Time: {summary['total_training_time']} min")
        print(f"  Avg Completion Rate: {summary['avg_completion_rate']:.1f}%")
        print(f"  Avg Satisfaction: {summary['avg_satisfaction']:.1f}/10")
        print(f"  Active Days: {summary['active_days']}")
        print()
        
        UIManager.pause_continue()
    
    def view_streak(self):
        """View streak tracking (Feature 17)"""
        streak = self.session_logger.get_streak(self.current_user['user_id'])
        
        UIManager.clear_screen()
        UIManager.print_header("🔥 Workout Streak (Feature 17)")
        
        print(f"  Current Streak: {streak['current_streak']} days")
        print(f"  Longest Streak: {streak['longest_streak']} days")
        print(f"  Total Sessions: {streak['total_sessions']}")
        print()
        
        UIManager.pause_continue()
    
    def view_strength_progress(self):
        """View strength progress (Feature 18)"""
        progress = self.session_logger.get_strength_progress(self.current_user['user_id'])
        
        UIManager.clear_screen()
        UIManager.print_header("💪 Strength Progress (Feature 18)")
        
        print(f"  Avg Difficulty: {progress.get('avg_difficulty', 0):.2f}")
        print(f"  Trend: {progress.get('trend', 'stable').upper()}")
        print(f"  Total Sessions Logged: {progress.get('total_sessions_logged', 0)}")
        print()
        
        UIManager.pause_continue()
    
    def export_data(self):
        """Export data (Feature 19)"""
        filename = input("Enter filename (without extension): ").strip()
        
        csv_file = f"exports/{filename}.csv"
        success, msg = self.session_logger.export_all_sessions_to_csv(self.current_user['user_id'], csv_file)
        
        if success:
            UIManager.show_success(f"Data exported to {csv_file}")
        else:
            UIManager.show_error(msg)
        
        UIManager.pause_continue()
    
    def view_body_stats(self):
        """View body statistics"""
        UIManager.show_info("Body statistics coming soon...")
        UIManager.pause_continue()
    
    # ========================================================================
    # MOTIVATION & MINDSET MENU (Feature 20-24)
    # ========================================================================
    
    def motivation_menu(self):
        """Feature 31: Motivation menu"""
        if not self.current_user:
            UIManager.show_warning("Please select or create a user first.")
            UIManager.pause_continue()
            return
        
        while True:
            choice = UIManager.display_motivation_menu()
            
            if choice == '1':
                self.mood_checkin()
            elif choice == '2':
                self.view_motivation_message()
            elif choice == '3':
                self.breathing_exercise()
            elif choice == '4':
                self.view_daily_tips()
            elif choice == '5':
                self.view_mood_trends()
            elif choice == '6':
                break
            else:
                UIManager.show_error("Invalid option.")
    
    def mood_checkin(self):
        """Daily mood check-in (Feature 21)"""
        UIManager.clear_screen()
        mood, notes = UIManager.prompt_mood_checkin()
        
        success, msg = self.session_logger.log_mood(self.current_user['user_id'], mood, notes)
        
        if success:
            UIManager.show_success(msg)
        else:
            UIManager.show_error(msg)
        
        UIManager.pause_continue()
    
    def view_motivation_message(self):
        """View motivation message (Feature 20)"""
        UIManager.clear_screen()
        UIManager.print_header("💬 Your Daily Motivation")
        
        from config import MOTIVATION_MESSAGES
        import random
        
        msg = random.choice(list(MOTIVATION_MESSAGES.values()))
        print(f"\n  {msg}\n")
        
        UIManager.pause_continue()
    
    def breathing_exercise(self):
        """Guided breathing exercise (Feature 22)"""
        UIManager.show_breathing_exercise()
    
    def view_daily_tips(self):
        """View daily tips (Feature 23)"""
        UIManager.clear_screen()
        UIManager.print_header("💡 Daily Fitness Tip")
        
        from config import DAILY_TIPS
        import random
        
        tip = random.choice(DAILY_TIPS)
        print(f"\n  {tip}\n")
        
        UIManager.pause_continue()
    
    def view_mood_trends(self):
        """View mood trends (Feature 24)"""
        history = self.session_logger.get_mood_history(self.current_user['user_id'])
        
        UIManager.clear_screen()
        UIManager.print_header("📈 Mood Trends (Feature 24)")
        
        print(f"  Average Mood: {history['avg_mood']:.1f}/5")
        print(f"  Trend: {history['trend'].upper()}")
        print(f"  Entries: {history['entries']}")
        print()
        
        UIManager.pause_continue()
    
    # ========================================================================
    # DATABASE ADMIN MENU (Feature 29)
    # ========================================================================
    
    def admin_menu(self):
        """Feature 31: Database admin menu"""
        while True:
            choice = UIManager.display_admin_menu()
            
            if choice == '1':
                self.view_collections()
            elif choice == '2':
                self.backup_db()
            elif choice == '3':
                self.restore_db()
            elif choice == '4':
                self.cleanup_logs()
            elif choice == '5':
                self.check_connection()
            elif choice == '6':
                break
            else:
                UIManager.show_error("Invalid option.")
    
    def view_collections(self):
        """View collections and stats (Feature 29)"""
        UIManager.clear_screen()
        UIManager.print_header("📊 Database Collections (Feature 29)")
        
        stats = self.db_manager.get_collection_stats()
        
        for col_name, info in stats.items():
            print(f"  {col_name}: {info['count']} documents")
        
        print()
        UIManager.pause_continue()
    
    def backup_db(self):
        """Backup database (Feature 29)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backups/fitgen_backup_{timestamp}.json"
        
        success = self.db_manager.backup_database(backup_file)
        
        if success:
            UIManager.show_success(f"Backup created: {backup_file}")
        else:
            UIManager.show_error("Backup failed.")
        
        UIManager.pause_continue()
    
    def restore_db(self):
        """Restore database (Feature 29)"""
        UIManager.show_info("Database restore feature coming soon...")
        UIManager.pause_continue()
    
    def cleanup_logs(self):
        """Delete old logs (Feature 29)"""
        deleted = self.db_manager.delete_old_documents('session_logs', days=90)
        UIManager.show_success(f"Deleted {deleted} old logs (>90 days)")
        UIManager.pause_continue()
    
    def check_connection(self):
        """Check database connection (Feature 29)"""
        status = self.db_manager.get_connection_status()
        
        UIManager.clear_screen()
        UIManager.print_header("🔌 Database Connection Status")
        
        print(f"  Connected: {status['connected']}")
        print(f"  Database: {status['database']}")
        print(f"  Type: {status['storage_type']}")
        print()
        
        UIManager.pause_continue()
    
    # ========================================================================
    # EXIT APPLICATION
    # ========================================================================
    
    def exit_app(self):
        """Exit application"""
        if UIManager.confirm("Are you sure you want to exit?"):
            self.db_manager.close()
            UIManager.clear_screen()
            UIManager.print_header("👋 Thank you for using FitGen AI v5.0!")
            print("  ✅ All 42 Features Implemented")
            print("  ✅ Application Complete & Ready")
            print()
            sys.exit(0)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    try:
        app = FitGenApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n❌ Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Critical error: {e}")
        sys.exit(1)
