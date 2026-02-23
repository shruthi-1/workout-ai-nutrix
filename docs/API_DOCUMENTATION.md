# FitGen AI v6.0 - API Documentation

## Overview

FitGen AI v6.0 is an enterprise-grade fitness application API that provides:
- **Dataset Management**: Load and manage 2,918+ exercises from CSV
- **Structured Workout Generation**: Create personalized workouts with warmup, main course, and stretches phases
- **Real-Time Exercise Logging**: Track individual exercise completion during workouts
- **Calorie Tracking**: Accurate calorie burn calculations using MET (Metabolic Equivalent of Task) values
- **Workout Analytics**: Comprehensive insights into user fitness progress
- **ML Configuration**: Server-side machine learning adaptation settings

---

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api/v6`

---

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export MONGODB_ATLAS_URI="mongodb+srv://user:pass@cluster.mongodb.net/fitgen_db"
```

3. Run API:
```bash
uvicorn api_service_v6:app --reload
```

4. Access docs: http://localhost:8000/docs

---

## Authentication

Currently uses simple user_id. For production, implement JWT/OAuth.

---

## Core Workflows

### 1. Initial Setup
```bash
# Load dataset from CSV
POST /admin/dataset/load
```

### 2. Generate Workout
```bash
POST /users/{user_id}/workouts/generate
{
  "target_body_parts": ["Chest", "Back"],
  "duration_minutes": 60,
  "user_weight_kg": 75.0,
  "fitness_level": "Intermediate"
}
```

### 3. Log Exercises
```bash
POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log
{
  "exercise_title": "Bench Press",
  "phase": "main_course",
  "planned_sets": 4,
  "completed_sets": 4,
  "actual_reps": [10, 10, 9, 8],
  "calories_burned": 75.0
}
```

### 4. View Analytics
```bash
GET /users/{user_id}/analytics/ml
GET /users/{user_id}/calories?days=30
```

---

## API Endpoints Reference

See full endpoint documentation at: http://localhost:8000/docs

### Dataset Management
- `POST /admin/dataset/load` - Load exercises from CSV
- `GET /dataset/exercises` - Get exercises with filters
- `GET /dataset/exercises/{exercise_id}` - Get exercise details
- `PUT /admin/dataset/exercises/{exercise_id}` - Update exercise

### Workout Generation
- `POST /users/{user_id}/workouts/generate` - Generate structured workout

### Real-Time Logging
- `POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log` - Log exercise
- `GET /users/{user_id}/workouts/{workout_id}/status` - Get workout status
- `POST /users/{user_id}/workouts/{workout_id}/complete` - Complete workout

### Analytics
- `GET /users/{user_id}/history` - Get workout history
- `GET /users/{user_id}/calories` - Get calorie summary
- `GET /users/{user_id}/analytics/ml` - Get ML analytics

### Admin Configuration
- `GET /admin/ml-config` - Get ML configuration
- `PUT /admin/ml-config` - Update ML configuration

### System
- `GET /health` - Health check
- `GET /` - API info

---

## Calorie Calculation

Formula: `Calories = MET × Weight(kg) × Time(hours)`

### MET Values

| Exercise Type | Beginner | Intermediate | Expert |
|---------------|----------|--------------|--------|
| Strength | 3.5 | 5.0 | 6.0 |
| Cardio | 5.0 | 7.0 | 10.0 |
| Stretching | 2.5 | 2.5 | 2.5 |
| Warmup | 4.0 | 4.0 | 4.0 |

---

## MongoDB Configuration

### Environment Variables
```bash
MONGODB_ATLAS_URI=mongodb+srv://user:pass@cluster.mongodb.net/fitgen_db
MONGODB_DATABASE=fitgen_db
```

### Collections
- `dataset` - Exercise library
- `workout_history` - Per-exercise logs
- `system_config` - ML configuration

---

## Example Requests

### Generate Workout
```bash
curl -X POST "http://localhost:8000/users/john/workouts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "target_body_parts": ["Chest", "Back"],
    "duration_minutes": 60,
    "user_weight_kg": 75.0,
    "include_warmup": true,
    "include_stretches": true,
    "fitness_level": "Intermediate"
  }'
```

### Log Exercise
```bash
curl -X POST "http://localhost:8000/users/john/workouts/wk_123/exercises/ex_001/log" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_title": "Bench Press",
    "phase": "main_course",
    "planned_sets": 4,
    "completed_sets": 4,
    "planned_reps": 10,
    "actual_reps": [10, 10, 9, 8],
    "weight_used_kg": 60.0,
    "duration_minutes": 12.0,
    "calories_burned": 75.0,
    "difficulty_rating": 7,
    "notes": "Felt strong today"
  }'
```

### Get Analytics
```bash
curl -X GET "http://localhost:8000/users/john/analytics/ml"
```

---

## Error Codes

- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Resource Not Found
- `500` - Internal Server Error

---

## Deployment

### Local
```bash
uvicorn api_service_v6:app --host 0.0.0.0 --port 8000 --reload
```

### Production
```bash
gunicorn api_service_v6:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Support

- GitHub: [repository]/issues
- Docs: http://localhost:8000/docs
- Interactive testing: http://localhost:8000/docs

---

## Version: 6.0.0
