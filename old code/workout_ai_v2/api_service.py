
"""
FitGen AI v5.0 - FastAPI Service
Exposes REST endpoints for users, workouts, logging, and mood tracking
"""

from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field

from config import FEATURES
from utils import log_info, log_error
from db.database_manager import DatabaseManager
from data.exercise_database import ExerciseDatabase
from user.profile_manager import UserProfileManager
from workout.workout_gen import WorkoutGenerator
from workout.session_logger import SessionLogger

# ============================================================
# APP INIT & SINGLETONS
# ============================================================

app = FastAPI(
    title="FitGen AI v5.0 API",
    description="FastAPI wrapper over FitGen AI core engine",
    version="5.0.0",
)

# We'll use simple module-level singletons for now
_db_manager: Optional[DatabaseManager] = None
_exercise_db: Optional[ExerciseDatabase] = None
_profile_manager: Optional[UserProfileManager] = None
_workout_generator: Optional[WorkoutGenerator] = None
_session_logger: Optional[SessionLogger] = None


@app.on_event("startup")
def startup_event():
    """Initialize FitGen core objects on API startup."""
    global _db_manager, _exercise_db, _profile_manager, _workout_generator, _session_logger

    log_info("🚀 Starting FitGen AI v5.0 FastAPI service")

    _db_manager = DatabaseManager()
    _exercise_db = ExerciseDatabase(_db_manager)
    _profile_manager = UserProfileManager(_db_manager)
    _workout_generator = WorkoutGenerator(_db_manager, _exercise_db)
    _session_logger = SessionLogger(_db_manager)

    log_info("✅ FitGen core initialized in API context")


# ============================================================
# DEPENDENCIES
# ============================================================

def get_db() -> DatabaseManager:
    if _db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db_manager


def get_profile_manager() -> UserProfileManager:
    if _profile_manager is None:
        raise HTTPException(status_code=500, detail="Profile manager not initialized")
    return _profile_manager


def get_workout_generator() -> WorkoutGenerator:
    if _workout_generator is None:
        raise HTTPException(status_code=500, detail="Workout generator not initialized")
    return _workout_generator


def get_session_logger() -> SessionLogger:
    if _session_logger is None:
        raise HTTPException(status_code=500, detail="Session logger not initialized")
    return _session_logger


# ============================================================
# PYDANTIC MODELS
# ============================================================

class UserCreate(BaseModel):
    name: str
    age: int
    height_cm: float
    weight_kg: float
    fitness_level: str = Field("Beginner", description="Beginner / Intermediate / Expert")
    goal: str = Field("General Fitness")
    gender: str = Field("Other")
    equipment: List[str] = Field(default_factory=lambda: ["Body Only"])
    injuries: List[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    user_id: str
    name: str
    age: int
    height_cm: float
    weight_kg: float
    bmi: float
    bmi_category: str
    fitness_level: str
    goal: str
    gender: str
    equipment: List[str]
    injuries: List[str]


class WorkoutGenerateRequest(BaseModel):
    target_body_parts: Optional[List[str]] = None
    duration_minutes: int = 60


class ExerciseRating(BaseModel):
    title: str
    difficulty_rating: int = Field(5, ge=1, le=10)
    difficulty_description: Optional[str] = None


class WorkoutLogRequest(BaseModel):
    planned_duration: int = 60
    actual_duration: int
    exercises: List[ExerciseRating]
    overall_satisfaction: int = Field(5, ge=1, le=10)
    energy_level: int = Field(5, ge=1, le=10)
    recovery_needed: bool = False
    notes: Optional[str] = ""


class MoodLogRequest(BaseModel):
    mood_score: int = Field(..., ge=1, le=10)
    notes: Optional[str] = ""


# Generic response wrappers
class WeeklySummaryResponse(BaseModel):
    total_workouts: int
    total_training_time: int
    avg_completion_rate: float
    avg_satisfaction: float
    avg_difficulty: float
    active_days: int
    satisfaction_description: str


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_sessions: int


class StrengthProgressResponse(BaseModel):
    progression: List[Dict[str, Any]]
    avg_difficulty: float
    trend: str
    total_sessions_logged: int


class MoodHistoryResponse(BaseModel):
    avg_mood: float
    mood_description: str
    trend: str
    entries: int
    mood_data: List[Dict[str, Any]]


# ============================================================
# HEALTH & META
# ============================================================

@app.get("/health")
def health_check(db: DatabaseManager = Depends(get_db)):
    status = db.get_connection_status()
    return {
        "status": "ok",
        "database": status,
        "features": len(FEATURES),
    }


# ============================================================
# USER ENDPOINTS
# ============================================================

@app.post("/users", response_model=UserResponse)
def create_user(
    payload: UserCreate,
    pm: UserProfileManager = Depends(get_profile_manager),
):
    """Create a new user profile (Feature 25)."""
    from datetime import datetime

    user_id = f"{payload.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    profile_data = {
        "user_id": user_id,
        "name": payload.name,
        "age": payload.age,
        "height_cm": payload.height_cm,
        "weight_kg": payload.weight_kg,
        "fitness_level": payload.fitness_level,
        "goal": payload.goal,
        "gender": payload.gender,
        "equipment": payload.equipment,
        "injuries": payload.injuries,
    }

    success, user_doc, msg = pm.create_user(user_id, profile_data)
    if not success or not user_doc:
        raise HTTPException(status_code=400, detail=msg)

    return UserResponse(
        user_id=user_doc["user_id"],
        name=user_doc["name"],
        age=user_doc["age"],
        height_cm=user_doc["height_cm"],
        weight_kg=user_doc["weight_kg"],
        bmi=user_doc.get("bmi", 0),
        bmi_category=user_doc.get("bmi_category", "Unknown"),
        fitness_level=user_doc["fitness_level"],
        goal=user_doc["goal"],
        gender=user_doc.get("gender", "Other"),
        equipment=user_doc.get("equipment", []),
        injuries=user_doc.get("injuries", []),
    )


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    pm: UserProfileManager = Depends(get_profile_manager),
):
    """Get user profile."""
    user = pm.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=user["user_id"],
        name=user["name"],
        age=user["age"],
        height_cm=user["height_cm"],
        weight_kg=user["weight_kg"],
        bmi=user.get("bmi", 0),
        bmi_category=user.get("bmi_category", "Unknown"),
        fitness_level=user["fitness_level"],
        goal=user["goal"],
        gender=user.get("gender", "Other"),
        equipment=user.get("equipment", []),
        injuries=user.get("injuries", []),
    )


# ============================================================
# WORKOUT GENERATION
# ============================================================

@app.post("/users/{user_id}/workouts/daily")
def generate_daily_workout(
    user_id: str,
    payload: WorkoutGenerateRequest,
    pm: UserProfileManager = Depends(get_profile_manager),
    wg: WorkoutGenerator = Depends(get_workout_generator),
):
    """Generate a daily workout for a user (Feature 3)."""
    user = pm.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    workout = wg.generate_daily_workout(
        user,
        target_body_parts=payload.target_body_parts,
        duration_minutes=payload.duration_minutes,
    )
    # You can define a Pydantic model for a stricter schema later;
    # for now we just pass the dict through.
    return workout


# ============================================================
# SESSION LOGGING
# ============================================================

@app.post("/users/{user_id}/sessions")
def log_session(
    user_id: str,
    payload: WorkoutLogRequest,
    sl: SessionLogger = Depends(get_session_logger),
):
    """Log a completed workout session (Feature 15)."""

    # Convert ExerciseRating models to the dict structure expected by SessionLogger
    exercises = []
    for ex in payload.exercises:
        desc = ex.difficulty_description or "Difficulty recorded"
        exercises.append(
            {
                "title": ex.title,
                "difficulty_rating": ex.difficulty_rating,
                "difficulty_description": desc,
            }
        )

    workout_data = {
        "planned_duration": payload.planned_duration,
        "actual_duration": payload.actual_duration,
        "exercises": exercises,
        "overall_satisfaction": payload.overall_satisfaction,
        "energy_level": payload.energy_level,
        "recovery_needed": payload.recovery_needed,
        "notes": payload.notes or "",
    }

    success, session_doc = sl.log_session(user_id, workout_data)
    if not success or not session_doc:
        raise HTTPException(status_code=400, detail="Failed to log session")

    return {"status": "ok", "session_id": session_doc["session_id"], "session": session_doc}


@app.get("/users/{user_id}/summary/weekly", response_model=WeeklySummaryResponse)
def weekly_summary(
    user_id: str,
    sl: SessionLogger = Depends(get_session_logger),
):
    """Get weekly training summary (Feature 16)."""
    summary = sl.get_weekly_summary(user_id)
    return WeeklySummaryResponse(**summary)


@app.get("/users/{user_id}/summary/streak", response_model=StreakResponse)
def streak_summary(
    user_id: str,
    sl: SessionLogger = Depends(get_session_logger),
):
    """Get streak tracking info (Feature 17)."""
    return StreakResponse(**sl.get_streak(user_id))


@app.get("/users/{user_id}/strength", response_model=StrengthProgressResponse)
def strength_progress(
    user_id: str,
    sl: SessionLogger = Depends(get_session_logger),
):
    """Get strength/difficulty trend (Feature 18)."""
    return StrengthProgressResponse(**sl.get_strength_progress(user_id))


# ============================================================
# MOOD & MOTIVATION
# ============================================================

@app.post("/users/{user_id}/mood")
def log_mood(
    user_id: str,
    payload: MoodLogRequest,
    sl: SessionLogger = Depends(get_session_logger),
):
    """Log daily mood (Feature 21)."""
    success, msg = sl.log_mood(user_id, payload.mood_score, payload.notes or "")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "ok", "message": msg}


@app.get("/users/{user_id}/mood/history", response_model=MoodHistoryResponse)
def mood_history(
    user_id: str,
    days: int = 30,
    sl: SessionLogger = Depends(get_session_logger),
):
    """Get mood history and trend (Feature 24)."""
    history = sl.get_mood_history(user_id, days=days)
    return MoodHistoryResponse(**history)
