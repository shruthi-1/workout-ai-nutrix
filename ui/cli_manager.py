"""
FitGen AI v5.0 - Enhanced CLI Manager Module
Updated to handle 1-10 rating scale with descriptions
Feature 31-33: Beautiful CLI menus with improved ratings
"""

import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============================================================================
# RATING SCALE DISPLAY
# ============================================================================

EXERCISE_DIFFICULTY_DISPLAY = {
    1: "1️⃣ I couldn't even move the bar",
    2: "2️⃣ I could not lift it up completely",
    3: "3️⃣ Very difficult, struggled a lot",
    4: "4️⃣ Difficult, but managed with effort",
    5: "5️⃣ Moderate difficulty, challenging",
    6: "6️⃣ Fair difficulty, manageable",
    7: "7️⃣ Easy to moderate, completed smoothly",
    8: "8️⃣ Easy, didn't use full potential",
    9: "9️⃣ Very easy, could do more",
    10: "🔟 It was too easy"
}

WORKOUT_SATISFACTION_DISPLAY = {
    1: "1️⃣ Terrible workout, felt awful",
    2: "2️⃣ Very poor, something went wrong",
    3: "3️⃣ Poor, not satisfied",
    4: "4️⃣ Below average, could be better",
    5: "5️⃣ Average, was okay",
    6: "6️⃣ Good, accomplished goals",
    7: "7️⃣ Very good, felt strong",
    8: "8️⃣ Excellent, great session",
    9: "9️⃣ Outstanding, best yet",
    10: "🔟 Perfect workout, couldn't ask for better"
}

MOOD_DISPLAY = {
    1: "1️⃣ Very low, depressed",
    2: "2️⃣ Low, feeling down",
    3: "3️⃣ Poor, not well",
    4: "4️⃣ Below average",
    5: "5️⃣ Neutral, okay",
    6: "6️⃣ Good, feeling better",
    7: "7️⃣ Very good, positive",
    8: "8️⃣ Great, very positive",
    9: "9️⃣ Excellent, feeling amazing",
    10: "🔟 Perfect, couldn't be better"
}

# ============================================================================
# CLI MANAGER CLASS
# ============================================================================

class UIManager:
    """Enhanced UI Manager with 1-10 rating scales"""
    
    # ========================================================================
    # SCREEN MANAGEMENT
    # ========================================================================
    
    @staticmethod
    def clear_screen():
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    @staticmethod
    def print_header(text: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"  {text}")
        print(f"{'='*80}\n")
    
    @staticmethod
    def pause_continue():
        """Pause and wait for user to continue"""
        input("\n  Press Enter to continue...")
    
    # ========================================================================
    # WORKOUT LOGGING - ENHANCED WITH 1-10 SCALE
    # ========================================================================
    
    @staticmethod
    def prompt_workout_log() -> Dict:
        """
        Prompt user to log workout with 1-10 scale
        
        Returns:
            Workout data dict
        """
        UIManager.clear_screen()
        UIManager.print_header("📋 Log Your Workout")
        
        # Duration
        try:
            actual_duration = int(input("  Actual workout duration (minutes): "))
        except ValueError:
            actual_duration = 60
        
        # Exercise ratings
        print("\n  ├─ Rate each exercise (1-10):")
        exercises = []
        while True:
            ex_name = input("  │  Exercise name (or press Enter to finish): ").strip()
            if not ex_name:
                break
            
            # Show rating scale
            UIManager.clear_screen()
            UIManager.print_header(f"📋 Rate: {ex_name}")
            print("  How difficult was this exercise?\n")
            for i in range(1, 11):
                print(f"  {EXERCISE_DIFFICULTY_DISPLAY[i]}")
            
            try:
                rating = int(input("\n  Your rating (1-10): "))
                if 1 <= rating <= 10:
                    exercises.append({
                        'title': ex_name,
                        'difficulty_rating': rating,
                        'difficulty_description': EXERCISE_DIFFICULTY_DISPLAY[rating]
                    })
                else:
                    print("  ⚠️  Invalid rating, using 5")
                    exercises.append({
                        'title': ex_name,
                        'difficulty_rating': 5,
                        'difficulty_description': EXERCISE_DIFFICULTY_DISPLAY[5]
                    })
            except ValueError:
                print("  ⚠️  Invalid input, using 5")
                exercises.append({
                    'title': ex_name,
                    'difficulty_rating': 5,
                    'difficulty_description': EXERCISE_DIFFICULTY_DISPLAY[5]
                })
        
        # Overall satisfaction
        UIManager.clear_screen()
        UIManager.print_header("📋 Overall Workout Satisfaction")
        print("  How satisfied are you with this workout?\n")
        for i in range(1, 11):
            print(f"  {WORKOUT_SATISFACTION_DISPLAY[i]}")
        
        try:
            overall_satisfaction = int(input("\n  Your rating (1-10): "))
            if not (1 <= overall_satisfaction <= 10):
                overall_satisfaction = 5
        except ValueError:
            overall_satisfaction = 5
        
        # Energy level
        UIManager.clear_screen()
        UIManager.print_header("📋 Energy Level")
        print("  How was your energy during the workout?\n")
        for i in range(1, 11):
            print(f"  {MOOD_DISPLAY[i]}")
        
        try:
            energy_level = int(input("\n  Your rating (1-10): "))
            if not (1 <= energy_level <= 10):
                energy_level = 5
        except ValueError:
            energy_level = 5
        
        # Recovery needed
        recovery_needed = input("\n  Do you need recovery time? (yes/no): ").lower().strip() == 'yes'
        
        # Notes
        notes = input("  Any additional notes: ").strip()
        
        return {
            'planned_duration': 60,
            'actual_duration': actual_duration,
            'exercises': exercises,
            'overall_satisfaction': overall_satisfaction,
            'energy_level': energy_level,
            'recovery_needed': recovery_needed,
            'notes': notes
        }
    
    # ========================================================================
    # MOOD CHECK-IN - ENHANCED WITH 1-10 SCALE
    # ========================================================================
    
    @staticmethod
    def prompt_mood_checkin() -> Tuple[int, str]:
        """
        Prompt for mood check-in with 1-10 scale
        
        Returns:
            Tuple: (mood_score, notes)
        """
        UIManager.clear_screen()
        UIManager.print_header("💭 Daily Mood Check-In")
        
        print("  How are you feeling today?\n")
        for i in range(1, 11):
            print(f"  {MOOD_DISPLAY[i]}")
        
        try:
            mood = int(input("\n  Your mood (1-10): "))
            if not (1 <= mood <= 10):
                mood = 5
        except ValueError:
            mood = 5
        
        notes = input("\n  Any notes: ").strip()
        
        return mood, notes
    
    # ========================================================================
    # DISPLAY FUNCTIONS
    # ========================================================================
    
    @staticmethod
    def display_session_summary(summary: Dict):
        """Display session summary with ratings"""
        UIManager.clear_screen()
        UIManager.print_header("📊 Session Summary")
        
        print(f"  Total Workouts: {summary.get('total_workouts', 0)}")
        print(f"  Total Time: {summary.get('total_training_time', 0)} minutes")
        print(f"  Avg Completion: {summary.get('avg_completion_rate', 0)}%")
        print(f"  Avg Satisfaction: {summary.get('avg_satisfaction', 0)}/10")
        print(f"  Satisfaction: {summary.get('satisfaction_description', 'Average')}")
        print(f"  Avg Exercise Difficulty: {summary.get('avg_difficulty', 0)}/10")
        print(f"  Active Days: {summary.get('active_days', 0)}")
        print()
    
    @staticmethod
    def display_mood_summary(mood_data: Dict):
        """Display mood summary"""
        UIManager.clear_screen()
        UIManager.print_header("💭 Mood Summary")
        
        print(f"  Average Mood: {mood_data.get('avg_mood', 0)}/10")
        print(f"  Mood: {mood_data.get('mood_description', 'Neutral')}")
        print(f"  Trend: {mood_data.get('trend', 'stable').upper()}")
        print(f"  Entries: {mood_data.get('entries', 0)}")
        print()
    
    @staticmethod
    def prompt_user_creation() -> Dict:
        """
        Prompt user to create a new profile
        
        Returns:
            Dict with user data including user_id, name, age, height_cm, weight_kg,
            fitness_level, goal, gender, equipment, injuries
        """
        UIManager.clear_screen()
        UIManager.print_header("➕ Create New User Profile")
        
        # Collect user information
        name = input("  Enter your name: ").strip()
        
        try:
            age = int(input("  Enter your age: "))
        except ValueError:
            age = 25
        
        try:
            height_cm = float(input("  Enter your height (cm): "))
        except ValueError:
            height_cm = 170.0
        
        try:
            weight_kg = float(input("  Enter your weight (kg): "))
        except ValueError:
            weight_kg = 70.0
        
        print("\n  Fitness Levels: Beginner / Intermediate / Expert")
        fitness_level = input("  Select fitness level: ").strip() or "Beginner"
        
        print("\n  Goals: Weight Loss / Muscle Gain / Strength / Endurance / General Fitness / Athletic Performance")
        goal = input("  Select your goal: ").strip() or "General Fitness"
        
        print("\n  Gender: Male / Female / Other")
        gender = input("  Select gender: ").strip() or "Other"
        
        print("\n  Available Equipment (comma-separated):")
        print("  Body Only, Dumbbell, Barbell, Cable, Machine, Kettlebells, Bands, etc.")
        equipment_str = input("  Enter equipment: ").strip()
        equipment = [eq.strip() for eq in equipment_str.split(",")] if equipment_str else ["Body Only"]
        
        print("\n  Injuries (comma-separated, or press Enter if none):")
        print("  Lower Back, Knee, Shoulder, Wrist, Ankle, Hip, Elbow, Neck")
        injuries_str = input("  Enter injuries: ").strip()
        injuries = [inj.strip() for inj in injuries_str.split(",")] if injuries_str else []
        
        # Generate user ID
        user_id = f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            'user_id': user_id,
            'name': name,
            'age': age,
            'height_cm': height_cm,
            'weight_kg': weight_kg,
            'fitness_level': fitness_level,
            'goal': goal,
            'gender': gender,
            'equipment': equipment,
            'injuries': injuries
        }
    
    @staticmethod
    def display_workout(workout: Dict):
        """
        Display a daily workout with all details
        
        Args:
            workout: Dict containing workout structure with warmup, main exercises, cooldown
        """
        UIManager.clear_screen()
        UIManager.print_header("🏋️ Today's Workout")
        
        print(f"  Workout ID: {workout.get('workout_id', 'N/A')}")
        print(f"  Date: {workout.get('date', 'N/A')}")
        print(f"  Total Duration: {workout.get('total_duration', 0)} minutes")
        print()
        
        # Warmup section
        sections = workout.get('sections', {})
        warmup = sections.get('warmup', {})
        if warmup:
            print("  🔥 WARMUP")
            print("  " + "="*75)
            for ex in warmup.get('exercises', []):
                print(f"    • {ex.get('name', 'Exercise')}")
                print(f"      Duration: {ex.get('duration_seconds', 0)}s")
                print(f"      {ex.get('description', '')}")
                print()
        
        # Main workout section
        main = sections.get('main', {})
        if main:
            print("  💪 MAIN WORKOUT")
            print("  " + "="*75)
            for i, ex in enumerate(main.get('exercises', []), 1):
                print(f"    {i}. {ex.get('title', 'Exercise')}")
                print(f"       Body Part: {ex.get('body_part', 'N/A')}")
                print(f"       Equipment: {ex.get('equipment', 'N/A')}")
                
                # Sets and reps
                sets = ex.get('sets', 3)
                reps = ex.get('reps', (8, 12))
                if isinstance(reps, tuple):
                    print(f"       Sets: {sets} x {reps[0]}-{reps[1]} reps")
                else:
                    print(f"       Sets: {sets} x {reps} reps")
                
                # Rest and RPE
                print(f"       Rest: {ex.get('rest_seconds', 60)}s")
                rpe = ex.get('rpe_range', (7, 9))
                if isinstance(rpe, tuple):
                    print(f"       RPE: {rpe[0]}-{rpe[1]}/10")
                else:
                    print(f"       RPE: {rpe}/10")
                
                # Notes and modifications
                if ex.get('notes'):
                    print(f"       Notes: {ex.get('notes')}")
                if ex.get('modifications'):
                    print(f"       Modifications: {ex.get('modifications')}")
                print()
        
        # Cooldown section
        cooldown = sections.get('cooldown', {})
        if cooldown:
            print("  🧘 COOLDOWN")
            print("  " + "="*75)
            for ex in cooldown.get('exercises', []):
                print(f"    • {ex.get('name', 'Exercise')}")
                print(f"      Duration: {ex.get('duration_seconds', 0)}s")
                print(f"      {ex.get('description', '')}")
                print()
        
        # Motivation and tips
        if workout.get('motivation'):
            print(f"  💬 {workout['motivation']}")
        if workout.get('daily_tip'):
            print(f"  💡 Tip: {workout['daily_tip']}")
        print()
    
    @staticmethod
    def display_weekly_plan(plan: Dict):
        """
        Display a 7-day weekly workout plan
        
        Args:
            plan: Dict containing weekly plan with 7 days of workouts
        """
        UIManager.clear_screen()
        UIManager.print_header("📅 Weekly Workout Plan")
        
        print(f"  Plan ID: {plan.get('plan_id', 'N/A')}")
        print(f"  Split: {plan.get('split_type', 'N/A')}")
        print(f"  Created: {plan.get('created_date', 'N/A')}")
        print()
        
        days = plan.get('days', {})
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_name in day_names:
            day_workout = days.get(day_name, {})
            print(f"  📆 {day_name.upper()}")
            print("  " + "-"*75)
            
            if day_workout.get('is_rest_day'):
                print("    REST DAY - Recovery and relaxation")
                print()
                continue
            
            # Show workout details
            focus = day_workout.get('focus', 'Workout')
            body_parts = day_workout.get('target_body_parts', [])
            exercises = day_workout.get('exercises', [])
            
            print(f"    Focus: {focus}")
            if body_parts:
                print(f"    Target: {', '.join(body_parts)}")
            print(f"    Exercises: {len(exercises)}")
            
            # List exercises
            if exercises:
                for i, ex in enumerate(exercises[:5], 1):  # Show first 5
                    title = ex.get('title', 'Exercise')
                    print(f"      {i}. {title}")
                if len(exercises) > 5:
                    print(f"      ... and {len(exercises) - 5} more")
            print()
        
        print("  💪 Good luck with your training!")
        print()
    
    @staticmethod
    def show_success(message: str):
        """Show success message"""
        print(f"\n  ✅ {message}\n")
    
    @staticmethod
    def show_error(message: str):
        """Show error message"""
        print(f"\n  ❌ {message}\n")
    
    @staticmethod
    def show_warning(message: str):
        """Show warning message"""
        print(f"\n  ⚠️  {message}\n")
    
    @staticmethod
    def show_info(message: str):
        """Show info message"""
        print(f"\n  ℹ️  {message}\n")
    
    @staticmethod
    def confirm(message: str) -> bool:
        """Ask for confirmation"""
        response = input(f"\n  {message} (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    # ========================================================================
    # MENU DISPLAY
    # ========================================================================
    
    @staticmethod
    def display_main_menu() -> str:
        """Display main menu"""
        UIManager.clear_screen()
        UIManager.print_header("🏋️ FitGen AI v5.0 - Main Menu")
        
        print("  1. 👥 User Management")
        print("  2. 🏋️ Workout Generation")
        print("  3. 📋 Daily Workout/Logging")
        print("  4. 📈 Progress & Insights")
        print("  5. 💬 Motivation & Mindset")
        print("  6. 🧩 Database Admin")
        print("  7. ❌ Exit")
        print()
        
        return input("  Select option (1-7): ").strip()
    
    @staticmethod
    def display_user_menu() -> str:
        """Display user management menu"""
        UIManager.clear_screen()
        UIManager.print_header("👥 User Management")
        
        print("  1. ➕ Create User")
        print("  2. 👤 View User")
        print("  3. ✏️ Edit User")
        print("  4. 🗑️ Delete User")
        print("  5. 🔄 Switch User")
        print("  6. 📋 View All Users")
        print("  7. ⬅️ Back")
        print()
        
        return input("  Select option (1-7): ").strip()
    
    @staticmethod
    def display_workout_menu() -> str:
        """Display workout generation menu"""
        UIManager.clear_screen()
        UIManager.print_header("🏋️ Workout Generation")
        
        print("  1. 📅 Generate Daily Workout")
        print("  2. 📆 Generate Weekly Plan")
        print("  3. 👁️ View Generated Workout")
        print("  4. 💾 Save Workout")
        print("  5. ⬅️ Back")
        print()
        
        return input("  Select option (1-5): ").strip()
    
    @staticmethod
    def display_logging_menu() -> str:
        """Display logging menu"""
        UIManager.clear_screen()
        UIManager.print_header("📋 Daily Workout/Logging")
        
        print("  1. 📝 Log Workout")
        print("  2. 👁️ View Today's Workout")
        print("  3. 💪 Record Exercise")
        print("  4. 📝 Add Notes")
        print("  5. ⬅️ Back")
        print()
        
        return input("  Select option (1-5): ").strip()
    
    @staticmethod
    def display_progress_menu() -> str:
        """Display progress menu"""
        UIManager.clear_screen()
        UIManager.print_header("📈 Progress & Insights")
        
        print("  1. 📊 Weekly Summary")
        print("  2. 🔥 Streak Tracking")
        print("  3. 💪 Strength Progress")
        print("  4. 📥 Export Data")
        print("  5. 📊 Body Statistics")
        print("  6. ⬅️ Back")
        print()
        
        return input("  Select option (1-6): ").strip()
    
    @staticmethod
    def display_motivation_menu() -> str:
        """Display motivation menu"""
        UIManager.clear_screen()
        UIManager.print_header("💬 Motivation & Mindset")
        
        print("  1. 💭 Mood Check-In")
        print("  2. 💬 Motivation Message")
        print("  3. 🫁 Breathing Exercise")
        print("  4. 💡 Daily Tips")
        print("  5. 📈 Mood Trends")
        print("  6. ⬅️ Back")
        print()
        
        return input("  Select option (1-6): ").strip()
    
    @staticmethod
    def display_admin_menu() -> str:
        """Display admin menu"""
        UIManager.clear_screen()
        UIManager.print_header("🧩 Database Admin")
        
        print("  1. 📊 View Collections")
        print("  2. 💾 Backup Database")
        print("  3. 🔄 Restore Database")
        print("  4. 🧹 Cleanup Old Logs")
        print("  5. 🔌 Check Connection")
        print("  6. ⬅️ Back")
        print()
        
        return input("  Select option (1-6): ").strip()
    
    # ========================================================================
    # TABLE DISPLAY
    # ========================================================================
    
    @staticmethod
    def display_table(headers: List[str], rows: List[List]):
        """Display formatted table"""
        # Calculate column widths
        widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            widths.append(max_width + 2)
        
        # Print header
        print("  ├─ " + "─".join(f"{h:<{w}}" for h, w in zip(headers, widths)))
        
        # Print rows
        for row in rows:
            print("  │  " + "  ".join(f"{str(v):<{w}}" for v, w in zip(row, widths)))
        
        print("  └─")
    
    @staticmethod
    def display_stats(stats: Dict):
        """Display statistics"""
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    @staticmethod
    def show_breathing_exercise():
        """Display breathing exercise"""
        UIManager.clear_screen()
        UIManager.print_header("🫁 Guided Breathing Exercise")
        
        print("  Box Breathing Exercise")
        print("  ─" * 40)
        print("  This exercise reduces stress and improves focus.\n")
        
        print("  INSTRUCTIONS:")
        print("  1. Breathe in slowly: 1... 2... 3... 4")
        print("  2. Hold your breath: 1... 2... 3... 4")
        print("  3. Exhale slowly: 1... 2... 3... 4")
        print("  4. Hold empty: 1... 2... 3... 4")
        print("  5. Repeat 5-10 times\n")
        
        print("  BENEFITS:")
        print("  ✓ Reduces stress and anxiety")
        print("  ✓ Improves focus and clarity")
        print("  ✓ Enhances breathing control")
        print("  ✓ Pre-workout activation\n")
        
        print("  Ready to begin? This will take about 3-4 minutes.\n")
