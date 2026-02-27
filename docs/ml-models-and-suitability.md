# FitGen AI — ML Models & Algorithm Suitability Review

> **Document scope:** This report inventories every algorithm and model-like
> component present in the *current* codebase (v6.0), assesses whether each is
> the best tool for the described use-case, and recommends concrete next steps.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Algorithm Inventory](#2-algorithm-inventory)
   - 2.1 [MET-value Lookup Table (Calorie Estimator)](#21-met-value-lookup-table-calorie-estimator)
   - 2.2 [Rule-Based Workout Generator](#22-rule-based-workout-generator)
   - 2.3 [ML-Training Readiness Gate](#23-ml-training-readiness-gate)
   - 2.4 [Descriptive Analytics Engine](#24-descriptive-analytics-engine)
3. [Suitability Assessment](#3-suitability-assessment)
4. [Recommended Next Steps](#4-recommended-next-steps)
5. [Dependency Audit](#5-dependency-audit)

---

## 1. Overview

FitGen AI v6.0 is a workout recommendation and logging service.  
Despite having `scikit-learn` listed in `requirements.txt`, **no trained
statistical or neural-network model is currently instantiated or persisted**.
All "intelligent" behaviour is implemented through deterministic look-up tables
and heuristic rules.  The sections below document each algorithm component.

---

## 2. Algorithm Inventory

### 2.1 MET-value Lookup Table (Calorie Estimator)

| Attribute | Detail |
|-----------|--------|
| **File** | `utils_v6/calorie_calculator.py` |
| **Algorithm type** | Lookup table + deterministic formula |
| **Purpose** | Estimate calories burned during a workout session |
| **Input features** | `exercise_type` (string), `fitness_level` (string), `weight_kg` (float), `duration_minutes` (float), `sets` (int), `reps` (int) |
| **Output** | `calories_burned` (float, kcal) |

#### How it works

The estimator uses the **Metabolic Equivalent of Task (MET)** formula:

```
Calories = MET × weight_kg × (duration_minutes / 60)
```

MET values are hard-coded in a Python dictionary (`MET_VALUES`) keyed by
exercise type and (optionally) difficulty level.  For example:

```python
MET_VALUES = {
    'Strength': {'Beginner': 3.5, 'Intermediate': 5.0, 'Expert': 6.0},
    'Cardio':   {'Beginner': 5.0, 'Intermediate': 7.0, 'Expert': 10.0},
    'Stretching': 2.5,
    ...
}
```

#### Suitability

**Appropriate for the current stage.**  The MET formula is the recognised
standard used by the American College of Sports Medicine and is accurate to
within ±15–20% for most activities.  A lookup table is transparent, fast, and
requires no training data.

**Limitations:**
- MET values do not account for individual variation (body composition, fitness
  adaptation, heart rate response).
- Duration is assumed to be fully active; rest periods between sets inflate the
  estimate.
- The `estimate_exercise_duration` helper uses a fixed `seconds_per_rep` table,
  which is a rough approximation.

---

### 2.2 Rule-Based Workout Generator

| Attribute | Detail |
|-----------|--------|
| **File** | `workout/workout_gen_v6.py` |
| **Algorithm type** | Filter + uniform random sampling |
| **Purpose** | Select exercises for warmup, main course, and stretch phases given user preferences |
| **Input features** | `target_body_parts` (list), `fitness_level` (string), `duration_minutes` (int), `user_weight_kg` (float) |
| **Output** | A structured workout dictionary with per-exercise calorie estimates |

#### How it works

1. **Filter:** Query the exercise database (MongoDB) for exercises matching
   `body_part`, `level`, and `type` constraints.
2. **Sample:** Call `random.sample(unique_exercises, k)` to pick *k* exercises.
   - Warmup: up to 3 exercises
   - Main course: 5–8 exercises depending on `duration_minutes // 8`
   - Stretches: 3–5 exercises
3. **Parameterise:** Apply heuristic rules for sets/reps/rest based on
   `fitness_level` (e.g., Beginner → 3 sets × 12 reps × 60 s rest).
4. **Fallback:** If no exercises are found in the database, hard-coded fallback
   exercises (Push-ups, Jumping Jacks, Hamstring Stretch) are returned.

#### Suitability

**Appropriate as a baseline but limited in personalisation.**

The random-selection approach is easy to reason about and avoids cold-start
problems.  However it has several shortcomings:

- **No preference learning:** A user who always skips leg day will still
  receive leg exercises if they select "Legs" as a target.
- **No progressive overload:** Sets/reps/weight are static per fitness level
  and do not increase over time.
- **No feedback loop:** User difficulty ratings (`difficulty_rating` in logs)
  and completion rates are stored but never fed back into exercise selection.

---

### 2.3 ML-Training Readiness Gate

| Attribute | Detail |
|-----------|--------|
| **File** | `workout/session_logger_v6.py` · `db/database_manager_v6.py` |
| **Algorithm type** | Threshold check (count-based gate) |
| **Purpose** | Determine whether a user has enough data to justify retraining a personalisation model |
| **Input** | User's workout history count within the last `training_window_days` (default 30) |
| **Output** | Boolean `ml_training_ready` |

#### How it works

```python
if workout_count >= min_sessions_for_training:   # default: 5
    return True   # signal that ML update can be triggered
```

The actual model retraining is noted as a placeholder comment:
> *"In a real implementation, this would trigger ML model retraining"*

No scikit-learn or deep learning model is trained or called anywhere in the
current codebase.

#### Suitability

**The gate logic is sound; the missing piece is the model itself.**  Triggering
retraining only after a minimum number of sessions prevents over-fitting to
sparse data.  However, the ML pipeline it is meant to guard does not yet exist.

---

### 2.4 Descriptive Analytics Engine

| Attribute | Detail |
|-----------|--------|
| **File** | `workout/session_logger_v6.py` (`get_workout_analytics`) · `api_service_v6.py` |
| **Algorithm type** | Aggregation / descriptive statistics |
| **Purpose** | Report total calories, workout frequency, average difficulty, and top exercises to the user |
| **Input** | User's `exercise_log` documents in MongoDB |
| **Output** | Summary dictionary surfaced via `GET /users/{user_id}/analytics/ml` |

#### How it works

Pure Python aggregation:
- Sum calories per workout session.
- Count unique workouts in a rolling 30-day window.
- Count exercise occurrences to produce a "top exercises" list.
- Compute workout frequency as `total_workouts / period_days`.

No statistical or ML model is involved.

#### Suitability

**Appropriate for current reporting needs.**  Descriptive statistics are the
right first step before building a predictive layer.

---

## 3. Suitability Assessment

| Component | Current approach | Is it appropriate? | Key concern |
|-----------|------------------|--------------------|-------------|
| Calorie estimation | MET lookup table | ✅ Yes — industry standard | Over-estimates during rest periods |
| Workout selection | Filter + random sample | ⚠️ Adequate baseline | No personalisation, no progressive overload |
| ML readiness gate | Session count threshold | ✅ Yes — reasonable guard | The downstream model does not yet exist |
| Analytics reporting | Aggregation | ✅ Yes | Limited to descriptive stats; no predictive value |

---

## 4. Recommended Next Steps

### 4.1 Short-term (add personalisation to the existing generator)

**Content-based filtering** using exercise features already present in the
database (body part, equipment, type, rating) is a natural first improvement:

```python
# Pseudocode
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Build a feature matrix from exercise attributes
# Score exercises by similarity to the user's logged history
```

This does not require a training loop and can be implemented without additional
dependencies beyond `scikit-learn` (already in `requirements.txt`).

### 4.2 Progressive overload model

Track `weight_used_kg`, `actual_reps`, and `difficulty_rating` over time.  Use
a simple **linear regression** to predict the next session's target weight:

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_history, y_next_weight)
```

Validate with k-fold cross-validation (`cross_val_score`) before shipping.

### 4.3 Exercise recommendation — collaborative filtering

Once ≥100 users have logged workouts, **matrix factorisation** (e.g.,
`sklearn.decomposition.NMF` or the `surprise` library) can recommend exercises
based on what similar users complete and enjoy.

**Tradeoffs vs. current approach:**

| | Rule-based | Content-based | Collaborative |
|-|-----------|---------------|---------------|
| Cold start | ✅ No problem | ✅ Features only | ❌ Needs history |
| Personalisation | ❌ None | ✅ Moderate | ✅ High |
| Explainability | ✅ Full | ✅ Moderate | ❌ Opaque |
| Data required | ✅ None | ✅ Minimal | ❌ Many users |

### 4.4 Calorie model improvement

Replace the single-number MET lookup with a **gradient-boosted regression**
trained on the wearable sensor datasets (e.g., ExCET, PMData).  Features could
include heart rate, age, gender, body fat percentage.

```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score

gbr = GradientBoostingRegressor(n_estimators=200, max_depth=4)
scores = cross_val_score(gbr, X, y_calories, cv=5, scoring='neg_mean_absolute_error')
```

Expected improvement: MAE reduced from ≈15–20% to ≈8–12%.

### 4.5 Hyperparameter tuning

For any trained model, use `sklearn.model_selection.GridSearchCV` or
`RandomizedSearchCV` before declaring a model production-ready:

```python
from sklearn.model_selection import RandomizedSearchCV

search = RandomizedSearchCV(model, param_distributions, n_iter=50, cv=5)
search.fit(X_train, y_train)
```

### 4.6 Baseline comparisons

Before deploying a new algorithm, always compare against the current rule-based
baseline using the same evaluation metric (e.g., user satisfaction rating,
session completion rate).  Add benchmark scripts to `tools/` for each model.

---

## 5. Dependency Audit

The following packages in `requirements.txt` relate to ML/analytics:

| Package | Version | Used in current code? | Purpose |
|---------|---------|----------------------|---------|
| `numpy` | 1.26.2 | No (imported but not called) | Numerical operations |
| `pandas` | 2.1.3 | No | Data manipulation |
| `scikit-learn` | 1.3.2 | No | ML algorithms |

**Recommendation:** These are good choices for the roadmap items above and
should be retained.  Until active model training is added, they are dormant but
not harmful.

---

*Report generated for FitGen AI v6.0 — last reviewed 2026-02-27.*
