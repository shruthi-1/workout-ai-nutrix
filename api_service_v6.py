"""
FitGen AI v6.0 - Comprehensive FastAPI Service
Exposes REST endpoints for dataset, workouts, logging, and analytics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator

from config import COLLECTIONS
from utils import log_info, log_error, log_success
from db.database_manager_v6 import DatabaseManagerV6
from workout.workout_gen_v6 import WorkoutGeneratorV6
from workout.session_logger_v6 import SessionLoggerV6

# ============================================================
# PYDANTIC MODELS - REQUEST/RESPONSE SCHEMAS
# ============================================================

# Dataset Models
class ExerciseResponse(BaseModel):
    """Exercise response model"""
    exercise_id: str
    title: str
    description: str
    type: str
    body_part: str
    equipment: str
    level: str
    rating: float
    met_value: float
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    is_active: bool
    created_at: str
    updated_at: str

class ExerciseListResponse(BaseModel):
    """Exercise list response model"""
    total: int
    exercises: List[ExerciseResponse]

class ExerciseUpdateRequest(BaseModel):
    """Request model for updating exercise"""
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    is_active: Optional[bool] = None

# Workout Generation Models
class WorkoutGenerationRequest(BaseModel):
    """Request model for workout generation"""
    target_body_parts: List[str] = Field(..., min_items=1, description="List of target body parts")
    duration_minutes: int = Field(60, ge=10, le=180, description="Total workout duration")
    user_weight_kg: float = Field(70.0, ge=30.0, le=200.0, description="User weight in kg")
    include_warmup: bool = Field(True, description="Include warmup phase")
    include_stretches: bool = Field(True, description="Include stretches phase")
    fitness_level: str = Field('Intermediate', description="Fitness level")
    
    @validator('fitness_level')
    def validate_fitness_level(cls, v):
        allowed = ['Beginner', 'Intermediate', 'Expert']
        if v not in allowed:
            raise ValueError(f"fitness_level must be one of {allowed}")
        return v

class ExerciseDetail(BaseModel):
    """Exercise detail in workout"""
    exercise_id: str
    title: str
    description: str
    duration_minutes: float
    sets: int
    reps: int
    rest_seconds: int
    met_value: float
    estimated_calories: float
    video_url: Optional[str] = None
    order: int
    phase: str

class WorkoutPhase(BaseModel):
    """Workout phase model"""
    duration_minutes: float
    estimated_calories: float
    exercises: List[ExerciseDetail]

class WorkoutResponse(BaseModel):
    """Complete workout response"""
    workout_id: str
    user_id: str
    generated_at: str
    total_duration_minutes: float
    estimated_total_calories: float
    target_body_parts: List[str]
    fitness_level: str
    phases: Dict[str, WorkoutPhase]

# Exercise Logging Models
class ExerciseLogRequest(BaseModel):
    """Request model for exercise logging"""
    exercise_title: str
    phase: str = Field(..., description="Workout phase (warmup, main_course, stretches)")
    planned_sets: int = Field(..., ge=1)
    completed_sets: int = Field(..., ge=0)
    planned_reps: int = Field(..., ge=1)
    actual_reps: List[int] = Field(..., description="List of actual reps per set")
    weight_used_kg: float = Field(0.0, ge=0.0, description="Weight used in kg")
    duration_minutes: float = Field(..., ge=0.0)
    calories_burned: float = Field(..., ge=0.0)
    difficulty_rating: int = Field(5, ge=1, le=10, description="Difficulty rating (1-10)")
    notes: str = Field("", description="Optional notes")

class ExerciseLogResponse(BaseModel):
    """Response model for exercise logging"""
    log_id: str
    user_id: str
    workout_id: str
    exercise_id: str
    exercise_title: str
    completed_at: str
    status: str

class WorkoutStatusResponse(BaseModel):
    """Workout status response"""
    workout_id: str
    status: str
    total_exercises_completed: int
    total_calories_burned: float
    total_duration_minutes: float

# ML Configuration Models
class MLConfigResponse(BaseModel):
    """ML configuration response"""
    config_type: str
    training_window_days: int
    min_sessions_for_training: int
    created_at: str
    last_updated: str

class MLConfigUpdateRequest(BaseModel):
    """Request model for ML config update"""
    training_window_days: int = Field(..., ge=7, le=90, description="Training window in days")
    min_sessions_for_training: int = Field(..., ge=1, le=100, description="Minimum sessions required")

# Analytics Models
class CalorieSummaryResponse(BaseModel):
    """Calorie summary response"""
    user_id: str
    period_days: int
    total_calories_burned: float
    total_workouts: int
    total_exercises: int
    avg_calories_per_workout: float

class WorkoutHistoryItem(BaseModel):
    """Workout history item"""
    log_id: str
    workout_id: str
    exercise_id: str
    exercise_title: str
    phase: str
    completed_at: str
    completed_sets: int
    calories_burned: float
    difficulty_rating: int

class WorkoutHistoryResponse(BaseModel):
    """Workout history response"""
    user_id: str
    page: int
    per_page: int
    total_records: int
    history: List[Dict]

# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(
    title="FitGen AI v6.0 API",
    description="Enterprise-grade fitness app with workout generation, real-time logging, and ML capabilities",
    version="6.0.0",
)

# Global singletons
_db_manager: Optional[DatabaseManagerV6] = None
_workout_generator: Optional[WorkoutGeneratorV6] = None
_session_logger: Optional[SessionLoggerV6] = None

@app.on_event("startup")
def startup_event():
    """Initialize FitGen v6.0 core objects on API startup"""
    global _db_manager, _workout_generator, _session_logger
    
    log_info(" Starting FitGen AI v6.0 FastAPI service")
    
    _db_manager = DatabaseManagerV6()
    _workout_generator = WorkoutGeneratorV6(_db_manager)
    _session_logger = SessionLoggerV6(_db_manager)
    
    log_success(" FitGen v6.0 core initialized")

@app.on_event("shutdown")
def shutdown_event():
    """Clean up on shutdown"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
    log_info(" FitGen AI v6.0 service stopped")

# Dependencies
def get_db() -> DatabaseManagerV6:
    if _db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db_manager

def get_workout_generator() -> WorkoutGeneratorV6:
    if _workout_generator is None:
        raise HTTPException(status_code=500, detail="Workout generator not initialized")
    return _workout_generator

def get_session_logger() -> SessionLoggerV6:
    if _session_logger is None:
        raise HTTPException(status_code=500, detail="Session logger not initialized")
    return _session_logger

# ============================================================
# DATASET ENDPOINTS
# ============================================================

@app.post("/admin/dataset/load", tags=["Admin - Dataset"])
def load_dataset(csv_path: Optional[str] = None):
    """
    Load exercises from CSV into MongoDB dataset collection (Admin only)
    
    Args:
        csv_path: Optional path to CSV file
    
    Returns:
        Loading statistics
    """
    try:
        db = get_db()
        result = db.load_dataset_from_csv(csv_path)
        
        if result.get('success'):
            return {
                "status": "success",
                "message": f"Loaded {result['loaded']} exercises",
                "details": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
    
    except Exception as e:
        log_error(f"Error loading dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dataset/exercises", tags=["Dataset"], response_model=Dict)
def get_exercises(
    body_part: Optional[str] = Query(None, description="Filter by body part"),
    equipment: Optional[str] = Query(None, description="Filter by equipment"),
    level: Optional[str] = Query(None, description="Filter by difficulty level"),
    exercise_type: Optional[str] = Query(None, description="Filter by exercise type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results")
):
    """
    Get exercises with optional filters
    
    Returns:
        List of exercises matching filters
    """
    try:
        db = get_db()
        exercises = db.get_exercises_by_filters(
            body_part=body_part,
            equipment=equipment,
            level=level,
            exercise_type=exercise_type,
            limit=limit
        )
        
        return {
            "total": len(exercises),
            "filters": {
                "body_part": body_part,
                "equipment": equipment,
                "level": level,
                "exercise_type": exercise_type
            },
            "exercises": exercises
        }
    
    except Exception as e:
        log_error(f"Error fetching exercises: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dataset/exercises/{exercise_id}", tags=["Dataset"])
def get_exercise_by_id(exercise_id: str):
    """
    Get exercise details by ID
    
    Args:
        exercise_id: Exercise identifier
    
    Returns:
        Exercise details
    """
    try:
        db = get_db()
        exercise = db.get_exercise_by_id(exercise_id)
        
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        return exercise
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error fetching exercise {exercise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/dataset/exercises/{exercise_id}", tags=["Admin - Dataset"])
def update_exercise(exercise_id: str, updates: ExerciseUpdateRequest):
    """
    Update exercise fields (e.g., video URL) - Admin only
    
    Args:
        exercise_id: Exercise identifier
        updates: Fields to update
    
    Returns:
        Success status
    """
    try:
        db = get_db()
        
        update_dict = updates.dict(exclude_none=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        success = db.update_exercise(exercise_id, update_dict)
        
        if success:
            return {"status": "success", "message": "Exercise updated", "exercise_id": exercise_id}
        else:
            raise HTTPException(status_code=404, detail="Exercise not found or not modified")
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error updating exercise {exercise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# WORKOUT GENERATION ENDPOINTS
# ============================================================

@app.post("/users/{user_id}/workouts/generate", tags=["Workouts"], response_model=Dict)
def generate_workout(user_id: str, request: WorkoutGenerationRequest):
    """
    Generate structured workout with warmup, main course, and stretches
    
    Args:
        user_id: User identifier
        request: Workout generation parameters
    
    Returns:
        Generated workout with all phases
    """
    try:
        generator = get_workout_generator()
        
        workout = generator.generate_structured_workout(
            user_id=user_id,
            target_body_parts=request.target_body_parts,
            duration_minutes=request.duration_minutes,
            user_weight_kg=request.user_weight_kg,
            include_warmup=request.include_warmup,
            include_stretches=request.include_stretches,
            fitness_level=request.fitness_level
        )
        
        if not workout:
            raise HTTPException(status_code=500, detail="Failed to generate workout")
        
        return workout
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error generating workout: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate workout. Please try again.")

# ============================================================
# REAL-TIME LOGGING ENDPOINTS
# ============================================================

@app.post("/users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log", tags=["Logging"])
def log_exercise(
    user_id: str,
    workout_id: str,
    exercise_id: str,
    log_data: ExerciseLogRequest
):
    """
    Log individual exercise completion in real-time
    
    Args:
        user_id: User identifier
        workout_id: Workout identifier
        exercise_id: Exercise identifier
        log_data: Exercise completion data
    
    Returns:
        Log confirmation
    """
    try:
        logger = get_session_logger()
        
        log_id = logger.log_exercise_realtime(
            user_id=user_id,
            workout_id=workout_id,
            exercise_id=exercise_id,
            exercise_title=log_data.exercise_title,
            phase=log_data.phase,
            planned_sets=log_data.planned_sets,
            completed_sets=log_data.completed_sets,
            planned_reps=log_data.planned_reps,
            actual_reps=log_data.actual_reps,
            weight_used_kg=log_data.weight_used_kg,
            duration_minutes=log_data.duration_minutes,
            calories_burned=log_data.calories_burned,
            difficulty_rating=log_data.difficulty_rating,
            notes=log_data.notes,
            workout_status="in_progress"
        )
        
        if not log_id:
            raise HTTPException(status_code=500, detail="Failed to log exercise")
        
        return {
            "status": "success",
            "log_id": log_id,
            "user_id": user_id,
            "workout_id": workout_id,
            "exercise_id": exercise_id,
            "message": "Exercise logged successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error logging exercise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/workouts/{workout_id}/status", tags=["Logging"])
def get_workout_status(user_id: str, workout_id: str):
    """
    Get current workout status and progress
    
    Args:
        user_id: User identifier
        workout_id: Workout identifier
    
    Returns:
        Workout status and progress
    """
    try:
        logger = get_session_logger()
        status = logger.get_current_workout_status(workout_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Workout not found")
        
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error getting workout status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/{user_id}/workouts/{workout_id}/complete", tags=["Logging"])
def complete_workout(user_id: str, workout_id: str):
    """
    Mark workout as completed
    
    Args:
        user_id: User identifier
        workout_id: Workout identifier
    
    Returns:
        Completion confirmation
    """
    try:
        logger = get_session_logger()
        success = logger.complete_workout(workout_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workout not found or already completed")
        
        return {
            "status": "success",
            "workout_id": workout_id,
            "message": "Workout completed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error completing workout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# HISTORY & ANALYTICS ENDPOINTS
# ============================================================

@app.get("/users/{user_id}/workouts/history", tags=["Analytics"])
@app.get("/users/{user_id}/history", tags=["Analytics"])
def get_workout_history(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page")
):
    """
    Get user's workout history with pagination
    
    Args:
        user_id: User identifier
        page: Page number
        per_page: Results per page
    
    Returns:
        Paginated workout history
    """
    try:
        logger = get_session_logger()
        history = logger.get_workout_history(user_id, page, per_page)
        
        return history
    
    except Exception as e:
        log_error(f"Error fetching workout history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/analytics/calories", tags=["Analytics"])
@app.get("/users/{user_id}/calories", tags=["Analytics"])
def get_calorie_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get calorie burn statistics for a user
    
    Args:
        user_id: User identifier
        days: Number of days to look back
    
    Returns:
        Calorie statistics
    """
    try:
        logger = get_session_logger()
        summary = logger.get_calories_burned_summary(user_id, days)
        
        if not summary:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_calories_burned": 0,
                "total_workouts": 0,
                "total_exercises": 0,
                "avg_calories_per_workout": 0
            }
        
        return summary
    
    except Exception as e:
        log_error(f"Error fetching calorie summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/analytics/ml", tags=["Analytics"])
def get_ml_analytics(user_id: str):
    """
    Get ML adaptation insights for a user
    
    Args:
        user_id: User identifier
    
    Returns:
        ML analytics and adaptation status
    """
    try:
        logger = get_session_logger()
        
        # Get comprehensive analytics
        analytics = logger.get_workout_analytics(user_id, days=30)
        
        # Check if user meets ML training criteria
        ml_ready = logger.update_user_ml_data(user_id)
        
        analytics['ml_training_ready'] = ml_ready
        
        return analytics
    
    except Exception as e:
        log_error(f"Error fetching ML analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ADMIN CONFIGURATION ENDPOINTS
# ============================================================

@app.get("/admin/ml-config", tags=["Admin - Configuration"])
def get_ml_config():
    """
    Get current ML training configuration (Admin only)
    
    Returns:
        ML configuration
    """
    try:
        db = get_db()
        config = db.get_ml_config()
        
        if not config:
            raise HTTPException(status_code=404, detail="ML configuration not found")
        
        return config
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error fetching ML config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/ml-config", tags=["Admin - Configuration"])
def update_ml_config(request: MLConfigUpdateRequest):
    """
    Update ML training configuration (Admin only)
    
    Args:
        request: ML configuration updates
    
    Returns:
        Updated configuration
    """
    try:
        db = get_db()
        
        updates = {
            'training_window_days': request.training_window_days,
            'min_sessions_for_training': request.min_sessions_for_training
        }
        
        success = db.update_ml_config(updates)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update ML configuration")
        
        # Return updated config
        config = db.get_ml_config()
        
        return {
            "status": "success",
            "message": "ML configuration updated",
            "config": config
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error updating ML config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint
    
    Returns:
        System status
    """
    try:
        db = get_db()
        db_status = "connected" if db.connected else "disconnected"
        
        return {
            "status": "healthy",
            "version": "6.0.0",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/", tags=["System"])
def root():
    """
    Root endpoint with API information
    
    Returns:
        API welcome message
    """
    return {
        "message": "FitGen AI v6.0 API",
        "version": "6.0.0",
        "docs_url": "/docs",
        "health_check": "/health"
    }
