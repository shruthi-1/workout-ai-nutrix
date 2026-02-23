# FitGen AI v6.0 - Enhanced Feature Implementation

## 🎯 Overview

FitGen AI v6.0 is an enterprise-grade fitness application with advanced features including:

- ✅ **Dataset Management**: Load and manage 2,918+ exercises from CSV
- ✅ **Structured Workout Generation**: Warmup, Main Course, and Stretches phases
- ✅ **Real-Time Exercise Logging**: Track individual exercise completion
- ✅ **Accurate Calorie Tracking**: MET-based calorie burn calculations
- ✅ **Workout Analytics**: Comprehensive insights and ML adaptation
- ✅ **ML Configuration**: Server-side ML training parameters
- ✅ **RESTful API**: FastAPI with automatic documentation

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install manually
pip install fastapi uvicorn pymongo pandas pydantic
```

### 2. MongoDB Configuration

Set your MongoDB Atlas URI as an environment variable:

```bash
export MONGODB_ATLAS_URI="mongodb+srv://user:pass@cluster.mongodb.net/fitgen_db?retryWrites=true&w=majority"
```

Or use local MongoDB:
```bash
# Default: mongodb://localhost:27017
```

### 3. Run the API

```bash
uvicorn api_service_v6:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 5. Load Exercise Dataset

```bash
curl -X POST "http://localhost:8000/admin/dataset/load"
```

## 📁 Project Structure

```
workout_ai_v2/
├── api_service_v6.py          # FastAPI application with all endpoints
├── db/
│   └── database_manager_v6.py # Enhanced MongoDB operations
├── workout/
│   ├── workout_gen_v6.py      # Structured workout generation
│   └── session_logger_v6.py   # Real-time exercise logging
├── utils_v6/
│   ├── __init__.py
│   └── calorie_calculator.py  # MET-based calorie calculations
├── docs/
│   └── API_DOCUMENTATION.md   # Comprehensive API guide
├── data/
│   └── megaGymDataset.csv     # 2,918 exercises
├── test_v6_features.py        # Integration test suite
└── README_v6.md               # This file
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_v6_features.py
```

Expected output:
```
🎉 All tests passed! FitGen AI v6.0 is ready.
TOTAL: 5/5 tests passed
```

## 📊 Key Features

### 1. Dataset Management

Load 2,918 exercises with automatic MET value assignment:

```bash
POST /admin/dataset/load
```

Each exercise includes:
- Exercise ID, Title, Description
- Type, Body Part, Equipment, Level
- MET value for calorie calculations
- Video URL placeholder
- Active status and timestamps

### 2. Structured Workout Generation

Generate workouts with three phases:

```bash
POST /users/{user_id}/workouts/generate
```

Request:
```json
{
  "target_body_parts": ["Chest", "Back"],
  "duration_minutes": 60,
  "user_weight_kg": 75.0,
  "fitness_level": "Intermediate"
}
```

Response includes:
- **Warmup Phase**: 2-3 exercises (5-10 minutes)
- **Main Course**: 5-8 exercises (40-50 minutes)
- **Stretches**: 3-5 exercises (5-10 minutes)

Each exercise has:
- Sets, reps, rest time
- MET value and estimated calories
- Full description and video URL

### 3. Real-Time Exercise Logging

Log each exercise as it's completed:

```bash
POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log
```

Log includes:
- Planned vs. completed sets/reps
- Weight used, duration, calories burned
- Difficulty rating (1-10)
- User notes
- Workout status (in_progress, completed)

### 4. Calorie Calculations

Accurate calorie burn using MET formula:

```
Calories = MET × Weight(kg) × Time(hours)
```

MET Values by Exercise Type:

| Type | Beginner | Intermediate | Expert |
|------|----------|--------------|--------|
| Strength | 3.5 | 5.0 | 6.0 |
| Cardio | 5.0 | 7.0 | 10.0 |
| Stretching | 2.5 | 2.5 | 2.5 |
| Warmup | 4.0 | 4.0 | 4.0 |
| HIIT | 10.0 | 10.0 | 10.0 |

### 5. Workout Analytics

Get comprehensive insights:

```bash
# Calorie summary
GET /users/{user_id}/calories?days=30

# ML analytics
GET /users/{user_id}/analytics/ml

# Workout history
GET /users/{user_id}/history?page=1&per_page=50
```

### 6. ML Configuration

Configure machine learning parameters:

```bash
# Get current config
GET /admin/ml-config

# Update config
PUT /admin/ml-config
{
  "training_window_days": 45,
  "min_sessions_for_training": 10
}
```

## 🔧 API Endpoints

### Dataset Management
- `POST /admin/dataset/load` - Load CSV into MongoDB
- `GET /dataset/exercises` - Get exercises with filters
- `GET /dataset/exercises/{id}` - Get exercise details
- `PUT /admin/dataset/exercises/{id}` - Update exercise

### Workout Generation
- `POST /users/{user_id}/workouts/generate` - Generate workout

### Real-Time Logging
- `POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log` - Log exercise
- `GET /users/{user_id}/workouts/{workout_id}/status` - Get workout status
- `POST /users/{user_id}/workouts/{workout_id}/complete` - Complete workout

### Analytics
- `GET /users/{user_id}/history` - Workout history
- `GET /users/{user_id}/calories` - Calorie summary
- `GET /users/{user_id}/analytics/ml` - ML analytics

### Admin Configuration
- `GET /admin/ml-config` - Get ML config
- `PUT /admin/ml-config` - Update ML config

### System
- `GET /health` - Health check
- `GET /` - API info

## 💡 Example Workflow

### Complete Workout Flow

1. **Generate Workout**
```bash
curl -X POST "http://localhost:8000/users/john/workouts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "target_body_parts": ["Chest"],
    "duration_minutes": 45,
    "user_weight_kg": 75.0,
    "fitness_level": "Intermediate"
  }'
```

2. **Log Each Exercise**
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
    "difficulty_rating": 7
  }'
```

3. **Check Progress**
```bash
curl -X GET "http://localhost:8000/users/john/workouts/wk_123/status"
```

4. **Complete Workout**
```bash
curl -X POST "http://localhost:8000/users/john/workouts/wk_123/complete"
```

5. **View Analytics**
```bash
curl -X GET "http://localhost:8000/users/john/analytics/ml"
```

## 📦 Database Collections

### `dataset` Collection
- Exercise library (2,918+ exercises)
- Includes MET values, descriptions, body parts
- Indexed by: exercise_id, body_part, equipment, level

### `workout_history` Collection
- Per-exercise logs
- Real-time tracking during workouts
- Indexed by: user_id, workout_id, completed_at

### `system_config` Collection
- ML training configuration
- Admin-configurable parameters
- Training window and minimum sessions

## 🔒 Security Considerations

- Input validation using Pydantic models
- MongoDB injection prevention
- Sanitized user inputs
- **TODO**: Add JWT authentication for production
- **TODO**: Implement role-based access control (RBAC)
- **TODO**: Add rate limiting

## 🚀 Production Deployment

### Environment Variables

```bash
export MONGODB_ATLAS_URI="your_mongodb_atlas_connection_string"
export MONGODB_DATABASE="fitgen_db"
```

### Run with Gunicorn

```bash
gunicorn api_service_v6:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api_service_v6:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Performance

- Dataset load: < 60 seconds (2,918 exercises)
- Workout generation: < 2 seconds
- Exercise logging: < 500ms
- History query: < 1 second (1000+ records)
- Proper indexing for all frequent queries

## 🎓 Documentation

Full API documentation available at:
- **Local**: http://localhost:8000/docs
- **Markdown**: `docs/API_DOCUMENTATION.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python3 test_v6_features.py`
5. Submit a pull request

## 📝 Version History

### v6.0.0 (2026-02-10)
- ✅ Dataset management with CSV loading
- ✅ Structured workout generation (warmup/main/stretches)
- ✅ Real-time per-exercise logging
- ✅ MET-based calorie calculations
- ✅ Workout analytics and ML configuration
- ✅ Comprehensive FastAPI endpoints
- ✅ Full API documentation

### v5.0.0 (Previous)
- Basic workout generation
- Simple logging
- Local MongoDB support

## 📧 Support

For issues, questions, or feature requests:
- **GitHub Issues**: [repository]/issues
- **Documentation**: http://localhost:8000/docs

---

**FitGen AI v6.0** - Enterprise-grade fitness application with advanced ML capabilities

Made with ❤️ for fitness enthusiasts
