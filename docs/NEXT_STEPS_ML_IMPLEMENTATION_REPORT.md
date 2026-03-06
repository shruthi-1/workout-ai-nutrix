# FitGen AI — Next Steps: ML Implementation Roadmap

> **Document scope:** This report provides an organisational-level plan for
> evolving FitGen AI from its current rule-based baseline into a fully
> data-driven personalisation platform.  It is anchored to the current v6.0
> codebase, references specific source files where integration work is needed,
> and organises the roadmap into three time-boxed phases with explicit
> acceptance criteria.

---

## Table of Contents

1. [Scope and Objectives](#1-scope-and-objectives)
2. [Current-State Assessment](#2-current-state-assessment)
3. [Target Architecture](#3-target-architecture)
4. [Phased Roadmap](#4-phased-roadmap)
   - [Phase 1 — Personalisation Foundation (Months 1–2)](#phase-1--personalisation-foundation-months-12)
   - [Phase 2 — Predictive Models (Months 3–5)](#phase-2--predictive-models-months-35)
   - [Phase 3 — Collaborative Intelligence (Months 6–9)](#phase-3--collaborative-intelligence-months-69)
5. [Integration Points](#5-integration-points)
   - [v6 Active Path](#51-v6-active-path-recommended)
   - [v5 Fallback Path](#52-v5-fallback-path)
6. [Data Contracts](#6-data-contracts)
7. [Model Lifecycle](#7-model-lifecycle)
   - [Training](#71-training)
   - [Evaluation](#72-evaluation)
   - [Deployment](#73-deployment)
8. [Observability](#8-observability)
9. [Feature Flags](#9-feature-flags)
10. [Security and Privacy](#10-security-and-privacy)
11. [Risk Register](#11-risk-register)
12. [Acceptance Criteria per Phase](#12-acceptance-criteria-per-phase)
13. [Dependency Notes](#13-dependency-notes)

---

## 1. Scope and Objectives

FitGen AI currently provides workout generation and real-time exercise logging
via a rule-based engine backed by MongoDB.  No trained statistical or neural
model is active in production.  This report defines the concrete steps to change
that.

**Primary objectives**

| # | Objective | Success metric |
|---|-----------|----------------|
| O1 | Personalise exercise selection per user | Session completion rate ≥ 80% |
| O2 | Implement progressive-overload prediction | Target weight accuracy MAE ≤ 2 kg |
| O3 | Reduce calorie-estimation error | MAE from ~18% to ≤ 10% |
| O4 | Introduce collaborative recommendations at scale | CTR (tap-on-recommended) ≥ 15% |
| O5 | Ship a reproducible model pipeline | Full CI/CD from data to deployed model |

**Out of scope (this document)**

- Wearable or heart-rate sensor integration (separate roadmap item)
- Nutrition recommendation ML (separate service)
- User authentication and RBAC (see Security section for notes)

---

## 2. Current-State Assessment

### 2.1 What exists today

| Component | Location | Type | Personalisation |
|-----------|----------|------|-----------------|
| Calorie estimator | `utils_v6/calorie_calculator.py` | MET lookup table | None — fixed per exercise type |
| Workout generator | `workout/workout_gen_v6.py` | Filter + `random.sample` | None — random selection |
| ML readiness gate | `workout/session_logger_v6.py` · `db/database_manager_v6.py` | Session count threshold | N/A — placeholder only |
| Analytics engine | `workout/session_logger_v6.py` `get_workout_analytics` | Aggregation / descriptive stats | None |
| Exercise database | `db/database_manager_v6.py` | MongoDB collection `dataset` | 2 918 exercises, rich metadata |

### 2.2 Gaps

1. **No trained model:** `scikit-learn`, `numpy`, and `pandas` are listed in
   `requirements.txt` but are never called in production code paths.
2. **Feedback loop missing:** `difficulty_rating`, `actual_reps`, and
   `weight_used_kg` are logged in `workout_history` but never read back to
   influence future workouts.
3. **Cold-start strategy:** First-time users receive the same random selection
   as veterans — no onboarding profile is collected.
4. **Model storage:** There is no artefact store, versioning, or serialisation
   layer for persisting trained models.
5. **Progressive overload:** Sets, reps, and target weight are heuristically
   assigned per fitness level in `workout_gen_v6.py`; they do not adapt over
   sessions.

### 2.3 Data assets available now

- **2 918 exercises** in MongoDB `dataset` collection with `body_part`,
  `equipment`, `level`, `type`, `rating`, and `met_value` fields.
- **Per-exercise logs** in `workout_history` with `difficulty_rating`,
  `actual_reps`, `weight_used_kg`, `calories_burned`, and `completed_at`.
- **Session count gate** already implemented — signals when ≥ 5 sessions
  exist for a user (configurable via `system_config` ML config).

---

## 3. Target Architecture

The diagram below describes the end-state for Phase 3.  Intermediate states
are described under each phase.

```
┌───────────────────────────────────────────────────────────────┐
│                         API Layer                             │
│  api_service_v6.py  (FastAPI, 18+ endpoints)                  │
└────────────┬──────────────────────────┬───────────────────────┘
             │ generate workout          │ log exercise
             ▼                           ▼
┌────────────────────────┐   ┌───────────────────────────────┐
│  WorkoutGeneratorV6    │   │  SessionLoggerV6               │
│  workout_gen_v6.py     │   │  session_logger_v6.py          │
│                        │   │                                │
│  ┌──────────────────┐  │   │  ┌────────────────────────┐   │
│  │ RecommenderEngine│  │   │  │  FeedbackCollector     │   │
│  │ (new - Phase 1)  │  │   │  │  (new - Phase 1)       │   │
│  └──────────────────┘  │   │  └────────────────────────┘   │
└────────────────────────┘   └───────────────────────────────┘
             │                           │
             ▼                           ▼
┌───────────────────────────────────────────────────────────────┐
│                     Model Layer (new)                         │
│                                                               │
│  models/content_filter.py    (Phase 1)                        │
│  models/overload_predictor.py (Phase 2)                       │
│  models/calorie_regressor.py  (Phase 2)                       │
│  models/collaborative_filter.py (Phase 3)                     │
│  models/model_registry.py    (Phases 1–3)                     │
└───────────────────────────┬───────────────────────────────────┘
                            │ read/write
                            ▼
┌───────────────────────────────────────────────────────────────┐
│              Database Layer                                   │
│  db/database_manager_v6.py                                    │
│                                                               │
│  Collections: dataset · workout_history · system_config       │
│  New:         model_artefacts · user_profiles                 │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. Phased Roadmap

---

### Phase 1 — Personalisation Foundation (Months 1–2)

**Goal:** Replace pure random selection with content-based personalisation
that uses each user's logged history.

#### 4.1.1 Content-Based Exercise Recommender

**Where:** New file `models/content_filter.py`; called from
`workout/workout_gen_v6.py` `_select_main_exercises`.

```python
# models/content_filter.py  (skeleton)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ContentBasedRecommender:
    """Score exercises by cosine similarity to the user's history."""

    def __init__(self, exercise_corpus: list[dict]):
        # Build a combined text feature from body_part + type + equipment
        texts = [
            f"{ex['body_part']} {ex['type']} {ex['equipment']}"
            for ex in exercise_corpus
        ]
        self._vectorizer = TfidfVectorizer()
        self._matrix = self._vectorizer.fit_transform(texts)
        self._ids = [ex['exercise_id'] for ex in exercise_corpus]

    def score(self, history_exercise_ids: list[str]) -> dict[str, float]:
        """Return {exercise_id: relevance_score} for all exercises."""
        if not history_exercise_ids:
            return {eid: 1.0 for eid in self._ids}  # cold-start: uniform

        history_indices = [
            self._ids.index(eid)
            for eid in history_exercise_ids
            if eid in self._ids
        ]
        profile_vector = self._matrix[history_indices].mean(axis=0)
        scores = cosine_similarity(profile_vector, self._matrix).flatten()
        return dict(zip(self._ids, scores))
```

**Integration point — `workout/workout_gen_v6.py`**

```python
# In WorkoutGeneratorV6._select_main_exercises():
from models.content_filter import ContentBasedRecommender

scored = self._recommender.score(user_history_ids)
candidates.sort(key=lambda ex: scored.get(ex['exercise_id'], 0), reverse=True)
selected = candidates[:k]   # top-k instead of random.sample
```

No new `requirements.txt` entries needed — `scikit-learn` is already listed.

#### 4.1.2 Feedback Collector

**Where:** `workout/session_logger_v6.py` · `db/database_manager_v6.py`

Currently `update_user_ml_data` raises the flag but calls no model.  Phase 1
closes this gap by persisting a `user_profiles` document that summarises
preferences inferred from completed sessions.

New MongoDB document structure:

```javascript
// collection: user_profiles
{
  user_id: "user_john_001",
  preferred_body_parts: ["Chest", "Back"],
  avoided_exercise_ids: ["ex_legpress_01"],  // difficulty_rating <= 2
  avg_difficulty_preferred: 7.2,
  last_updated: ISODate()
}
```

#### 4.1.3 Onboarding Profile

A new endpoint `POST /users/{user_id}/profile/onboarding` collects goals,
injury notes, and preferred body parts on first login, pre-seeding the
`user_profiles` collection to avoid a purely cold start.

---

### Phase 2 — Predictive Models (Months 3–5)

**Goal:** Predict progressive overload targets and improve calorie estimation
with data-driven models.

#### 4.2.1 Progressive Overload Predictor

**Where:** New file `models/overload_predictor.py`; called from
`workout/workout_gen_v6.py` during exercise parameterisation.

```python
# models/overload_predictor.py  (skeleton)
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib, pathlib

MODEL_PATH = pathlib.Path("models/artefacts/overload_ridge.joblib")

class OverloadPredictor:
    """Predict next-session target weight for a given exercise per user."""

    def __init__(self):
        self._scaler = StandardScaler()
        self._model = Ridge(alpha=1.0)

    def fit(self, X, y):
        X_scaled = self._scaler.fit_transform(X)
        cv_scores = cross_val_score(
            self._model, X_scaled, y, cv=5, scoring="neg_mean_absolute_error"
        )
        self._model.fit(X_scaled, y)
        return cv_scores  # caller logs/stores these

    def predict(self, X):
        return self._model.predict(self._scaler.transform(X))

    def save(self):
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump((self._scaler, self._model), MODEL_PATH)

    @classmethod
    def load(cls) -> "OverloadPredictor":
        inst = cls()
        inst._scaler, inst._model = joblib.load(MODEL_PATH)
        return inst
```

**Training features (`X`)**

| Feature | Source field | Notes |
|---------|-------------|-------|
| `session_number` | count of logs for user+exercise | Ordinal |
| `prev_weight_kg` | `weight_used_kg` lag-1 | Float |
| `prev_difficulty` | `difficulty_rating` lag-1 | Int 1–10 |
| `prev_actual_reps` | `actual_reps[-1]` | Int |
| `fitness_level_enc` | label-encoded `fitness_level` | Int |

**Target (`y`):** `weight_used_kg` in the next session.

**Minimum data requirement:** ≥ 3 logged sessions per user per exercise.
Fall back to current heuristic if below threshold.

#### 4.2.2 Calorie Regression Model

**Where:** New file `models/calorie_regressor.py`; replaces the lookup table
in `utils_v6/calorie_calculator.py` when sufficient training data exists.

```python
# models/calorie_regressor.py  (skeleton)
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
import joblib, pathlib

MODEL_PATH = pathlib.Path("models/artefacts/calorie_gbr.joblib")

class CalorieRegressor:
    """Gradient-boosted calorie estimator.

    Falls back to MET formula when model is absent or stale.
    """

    def __init__(self, n_estimators=200, max_depth=4):
        self._model = GradientBoostingRegressor(
            n_estimators=n_estimators, max_depth=max_depth, random_state=42
        )

    def fit(self, X, y_calories):
        scores = cross_val_score(
            self._model, X, y_calories, cv=5,
            scoring="neg_mean_absolute_error"
        )
        self._model.fit(X, y_calories)
        return scores

    def predict(self, X):
        return self._model.predict(X)

    def save(self):
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._model, MODEL_PATH)

    @classmethod
    def load(cls) -> "CalorieRegressor":
        inst = cls()
        inst._model = joblib.load(MODEL_PATH)
        return inst
```

**Training features (`X`)**

| Feature | Source | Notes |
|---------|--------|-------|
| `exercise_type_enc` | `dataset.type` | Encoded |
| `fitness_level_enc` | user profile | Encoded |
| `weight_kg` | user profile | Float |
| `duration_minutes` | `workout_history` | Float |
| `sets` | `workout_history` | Int |
| `actual_reps_avg` | `workout_history` | Float |
| `difficulty_rating` | `workout_history` | Int |

**Target (`y`):** Actual wearable-measured calories (future data source).
Initially, use MET-derived labels to train a warm-start model.

Expected improvement: MAE from ≈ 15–20% to ≈ 8–12%.

---

### Phase 3 — Collaborative Intelligence (Months 6–9)

**Goal:** Leverage the growing multi-user dataset for collaborative
recommendations and introduce online A/B testing.

#### 4.3.1 Collaborative Filter

**Where:** New file `models/collaborative_filter.py`.

**Prerequisite:** ≥ 100 distinct users with ≥ 10 logged sessions each.

```python
# models/collaborative_filter.py  (skeleton)
from sklearn.decomposition import NMF
import numpy as np
import joblib, pathlib

MODEL_PATH = pathlib.Path("models/artefacts/collab_nmf.joblib")

class CollaborativeFilter:
    """Non-negative Matrix Factorisation for exercise recommendations."""

    def __init__(self, n_components=20):
        self._model = NMF(n_components=n_components, random_state=42)

    def fit(self, user_exercise_matrix: np.ndarray):
        """user_exercise_matrix: rows=users, cols=exercises, values=completion_count."""
        self._W = self._model.fit_transform(user_exercise_matrix)
        self._H = self._model.components_
        return self

    def recommend(self, user_index: int, top_k: int = 10) -> list[int]:
        scores = self._W[user_index] @ self._H
        return np.argsort(scores)[::-1][:top_k].tolist()

    def save(self):
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump((self._model, self._W, self._H), MODEL_PATH)

    @classmethod
    def load(cls) -> "CollaborativeFilter":
        inst = cls()
        inst._model, inst._W, inst._H = joblib.load(MODEL_PATH)
        return inst
```

#### 4.3.2 Hybrid Recommender

Combine content-based scores (Phase 1) with collaborative scores (Phase 3)
using a weighted blend:

```python
final_score = alpha * content_score + (1 - alpha) * collab_score
```

`alpha` is a feature flag (see Section 9) tunable per user cohort.

#### 4.3.3 Hyperparameter Tuning Pipeline

Add `tools/tune_models.py`:

```python
from sklearn.model_selection import RandomizedSearchCV

search = RandomizedSearchCV(
    estimator=model,
    param_distributions=param_grid,
    n_iter=50,
    cv=5,
    scoring="neg_mean_absolute_error",
    n_jobs=-1,
    random_state=42,
)
search.fit(X_train, y_train)
```

Run via GitHub Actions on a weekly schedule against the latest snapshot.

---

## 5. Integration Points

### 5.1 v6 Active Path (Recommended)

This is the primary development target.  All new model code should be placed
under `models/` and called from the v6 modules listed below.

| Call site | File | Change required |
|-----------|------|-----------------|
| Exercise selection | `workout/workout_gen_v6.py` `_select_main_exercises` | Replace `random.sample` with scored sort (Phase 1) |
| Exercise parameterisation | `workout/workout_gen_v6.py` `_build_exercise_params` | Call `OverloadPredictor.predict` (Phase 2) |
| Calorie calculation | `utils_v6/calorie_calculator.py` `calculate_calories_burned` | Add model branch behind feature flag (Phase 2) |
| ML trigger | `workout/session_logger_v6.py` `update_user_ml_data` | Remove placeholder comment; call `ModelRegistry.retrain` (Phase 1) |
| DB queries | `db/database_manager_v6.py` | Add `get_user_history_for_training`, `upsert_user_profile` methods |
| API | `api_service_v6.py` | Add `/users/{user_id}/recommendations` and `/admin/models/retrain` endpoints |

### 5.2 v5 Fallback Path

If the deployment team cannot migrate to v6 in the near term, the same model
layer (`models/`) can be integrated into the v5 modules:

| Call site | File | Change required |
|-----------|------|-----------------|
| Exercise selection | `workout/workout_gen.py` | Same scored-sort pattern |
| Session logging | `workout/session_logger.py` | Mirror `update_user_ml_data` logic from v6 |
| DB | `db/database_manager.py` | Port v6 `get_ml_config` and history methods |

> **Recommendation:** Target v6 exclusively.  v5 is in `workout/__init__.py`
> and the `old code/` directory; the v6 path is the active service.

---

## 6. Data Contracts

### 6.1 `workout_history` document (existing, extended)

```javascript
{
  // Existing fields (v6.0)
  log_id:           String,       // "log_xyz789"
  user_id:          String,       // "user_john_001"
  workout_id:       String,       // "wk_20260210_143052"
  exercise_id:      String,       // "ex_a1b2c3d4"
  exercise_title:   String,
  phase:            String,       // "warmup" | "main_course" | "stretches"
  completed_at:     ISODate,
  planned_sets:     Int,
  completed_sets:   Int,
  planned_reps:     Int,
  actual_reps:      [Int],
  weight_used_kg:   Float,
  duration_minutes: Float,
  calories_burned:  Float,
  difficulty_rating: Int,         // 1–10
  notes:            String,
  workout_status:   String,       // "in_progress" | "completed"

  // New fields added in Phase 1
  recommended_by:   String | null  // "content_filter" | "rule_based" | null
}
```

### 6.2 `user_profiles` document (new — Phase 1)

```javascript
{
  user_id:                  String,
  fitness_level:            String,  // "Beginner" | "Intermediate" | "Expert"
  weight_kg:                Float,
  preferred_body_parts:     [String],
  avoided_exercise_ids:     [String],
  avg_difficulty_preferred: Float,
  total_sessions:           Int,
  last_active:              ISODate,
  onboarding_completed:     Boolean,
  last_updated:             ISODate
}
```

### 6.3 `model_artefacts` document (new — Phase 2)

```javascript
{
  model_name:     String,    // "content_filter" | "overload_predictor" | ...
  version:        String,    // semver "1.0.0"
  trained_at:     ISODate,
  train_samples:  Int,
  cv_mae:         Float,     // cross-val mean absolute error
  artefact_path:  String,    // path to joblib file
  is_active:      Boolean,
  promoted_by:    String     // user/system that flipped is_active
}
```

### 6.4 Feature vector schemas

Each model's expected input schema must be validated by a `pydantic.BaseModel`
sub-class placed in `models/schemas.py` to prevent silent data-drift failures.

---

## 7. Model Lifecycle

### 7.1 Training

**Trigger conditions** (configured in `system_config` ML config):

| Condition | Default value | Config key |
|-----------|---------------|------------|
| Minimum sessions per user | 5 | `min_sessions_for_training` |
| Training window (days) | 30 | `training_window_days` |
| Minimum total training samples | 50 | `min_total_samples` (new) |

**Training flow**

```
1. Gate check       →  db/database_manager_v6.py  get_ml_config()
2. Data fetch       →  db/database_manager_v6.py  get_user_history_for_training()
3. Feature eng.     →  models/feature_engineering.py  build_feature_matrix()
4. Train + CV       →  models/<model>.py  fit()
5. Evaluate         →  compare MAE against current production model
6. Persist          →  models/model_registry.py  register()
7. Flag update      →  db/database_manager_v6.py  update_model_artefact()
```

New method needed in `db/database_manager_v6.py`:

```python
def get_user_history_for_training(
    self,
    min_sessions: int,
    window_days: int,
    limit: int = 10_000,
) -> list[dict]: ...
```

### 7.2 Evaluation

Every model must pass the following gates before being marked `is_active`:

| Gate | Criterion | Checked by |
|------|-----------|-----------|
| CV score | MAE improvement ≥ 5% over baseline | `models/model_registry.py` |
| Sample size | ≥ `min_total_samples` training rows | training pipeline |
| Latency | p95 prediction latency ≤ 50 ms | integration test |
| Schema | All input fields present and typed correctly | pydantic schema |

Evaluation results are stored in the `model_artefacts` document and surfaced
via the new admin endpoint `GET /admin/models`.

### 7.3 Deployment

**Deployment strategy:** Blue/green via the `is_active` flag in
`model_artefacts`.  The model registry loads the currently active model at API
start-up; a retraining run that passes evaluation gates promotes itself by
setting `is_active = True` on the new artefact and `False` on the previous one.

**Rollback:** Set `is_active = True` on any previous artefact document.  The
API must call `ModelRegistry.reload()` after a rollback (new admin endpoint).

**Model storage for MVP:** Serialised `joblib` files stored in
`models/artefacts/`.  For production, replace with S3 / MLflow artefact store.

---

## 8. Observability

### 8.1 Metrics to emit

All metrics should be emitted to the existing Python logger at `INFO` level and,
in production, forwarded to a monitoring platform (e.g., Prometheus + Grafana).

| Metric | Type | Where emitted |
|--------|------|--------------|
| `recommendation_source` | Counter (`rule_based` / `content_filter` / `collab`) | `workout_gen_v6.py` |
| `prediction_latency_ms` | Histogram | `models/model_registry.py` |
| `model_cv_mae` | Gauge | training pipeline |
| `training_samples_count` | Gauge | training pipeline |
| `feature_missing_rate` | Counter | `models/schemas.py` validation |
| `model_fallback_count` | Counter | any model with heuristic fallback |

### 8.2 Logging conventions

Follow the existing pattern in `workout/session_logger_v6.py`:

```python
from utils_v6.logging_utils import log_success, log_warning, log_error

log_success(f"Model {model_name} retrained: MAE={mae:.4f}, n={n_samples}")
log_warning(f"Falling back to rule-based: {reason}")
log_error(f"Model load failed: {e}")
```

### 8.3 Alerts (recommended for production)

- Training MAE regresses > 10% compared to previous model version.
- Feature missing rate > 5% of incoming prediction requests.
- Model artefact not refreshed within `training_window_days + 7` days.

---

## 9. Feature Flags

Feature flags control the rollout of new ML behaviour without code deployments.
Store flags in the `system_config` collection alongside the existing ML config.

### 9.1 Flag definitions

| Flag key | Type | Default | Controls |
|----------|------|---------|---------|
| `enable_content_filter` | Boolean | `false` | Activate Phase 1 recommender |
| `enable_overload_predictor` | Boolean | `false` | Activate Phase 2 weight predictor |
| `enable_calorie_regressor` | Boolean | `false` | Activate Phase 2 calorie model |
| `enable_collaborative_filter` | Boolean | `false` | Activate Phase 3 collab filter |
| `hybrid_alpha` | Float 0–1 | `0.7` | Weight of content vs collab scores |
| `min_total_samples` | Int | `50` | Minimum training samples gate |

### 9.2 Reading flags at runtime

```python
# In workout_gen_v6.py
ml_config = self.db_manager.get_ml_config()
if ml_config.get('enable_content_filter', False) and self._recommender:
    scored = self._recommender.score(user_history_ids)
    # ... use scored sort
else:
    # existing random.sample path
```

Flags are updated via the existing `PUT /admin/ml-config` endpoint — extend its
Pydantic request model to accept the new keys.

---

## 10. Security and Privacy

### 10.1 Data minimisation

- `user_profiles` must store only the fields listed in Section 6.2.
- Personally identifiable information (name, email, date-of-birth) must **not**
  be written into `user_profiles` or `model_artefacts`.
- The `user_id` is an opaque identifier; do not embed real names in it.

### 10.2 Model artefact security

- `joblib` files are pickle-based and must only be loaded from the trusted
  `models/artefacts/` directory.  Never deserialise artefacts from
  user-controlled input.
- In production, sign artefacts with a checksum stored in `model_artefacts`
  and verify before loading.

### 10.3 Input sanitisation

All prediction inputs must pass through the pydantic schema defined in
`models/schemas.py`.  This is consistent with the existing API validation
pattern in `api_service_v6.py`.

### 10.4 Access control (recommended)

- Add JWT authentication before exposing `/admin/models/*` endpoints.
- Restrict `PUT /admin/ml-config` to admin role.
- See `IMPLEMENTATION_SUMMARY.md` section *Recommended for Production* for the
  full list of security hardening steps (JWT, RBAC, rate limiting, CORS, HTTPS).

### 10.5 Dependency supply-chain

Existing ML packages are well-maintained and currently have no known critical
CVEs (`scikit-learn 1.3.2`, `numpy 1.26.2`, `pandas 2.1.3`).  Pin versions in
`requirements.txt` and review with each phase milestone.

---

## 11. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|-----------|
| R1 | Insufficient user data for model training | Medium | High | Keep rule-based fallback; gate on `min_total_samples` |
| R2 | Model degrades after deployment (data drift) | Low | High | Automated MAE monitoring; rollback via `is_active` flag |
| R3 | `joblib` pickle exploit via malicious artefact | Low | Critical | Only load artefacts from trusted local path; add checksum validation |
| R4 | Feature schema breaks after DB schema change | Medium | Medium | Pydantic validation in `models/schemas.py` + integration tests |
| R5 | Overload predictor increases injury risk | Low | High | Cap predicted weight at 110% of previous; surface confidence intervals to user |
| R6 | Cold-start degrades new-user experience | High | Medium | Onboarding profile endpoint (Phase 1); content-based fallback needs no history |
| R7 | Training pipeline blocks API thread | Medium | Medium | Run retraining in a background thread / async task, not in the request path |
| R8 | v5 and v6 diverge, doubling maintenance effort | Medium | Medium | Formally deprecate v5 at Phase 2 milestone; move to `old code/` |

---

## 12. Acceptance Criteria per Phase

### Phase 1

| # | Criterion | How to verify |
|---|-----------|--------------|
| AC-1.1 | `ContentBasedRecommender` returns a score for every exercise in the corpus | Unit test in `tests/test_content_filter.py` |
| AC-1.2 | Cold-start (empty history) returns uniform scores without raising | Unit test |
| AC-1.3 | `_select_main_exercises` uses scored sort when `enable_content_filter=true` | Integration test with mock DB |
| AC-1.4 | `user_profiles` document upserted after every `complete_workout` call | Integration test |
| AC-1.5 | `recommended_by` field written to `workout_history` log | DB assertion in integration test |
| AC-1.6 | Feature flag `enable_content_filter=false` falls back to random selection | Integration test |
| AC-1.7 | Onboarding endpoint returns 201 with correct profile document | API test |

### Phase 2

| # | Criterion | How to verify |
|---|-----------|--------------|
| AC-2.1 | `OverloadPredictor.fit` returns CV MAE ≤ 5 kg on synthetic dataset | Unit test |
| AC-2.2 | Predictor falls back to heuristic when user has < 3 sessions for exercise | Unit test |
| AC-2.3 | `CalorieRegressor` MAE ≤ 10% on held-out workout_history sample | Evaluation script `tools/evaluate_calorie_model.py` |
| AC-2.4 | Both models saved to `models/artefacts/` and reloaded correctly | Unit test |
| AC-2.5 | `model_artefacts` document written to MongoDB on successful training | Integration test |
| AC-2.6 | `GET /admin/models` returns model list with `cv_mae` and `is_active` | API test |
| AC-2.7 | p95 prediction latency ≤ 50 ms (measured locally with 1 000 requests) | Benchmark script |

### Phase 3

| # | Criterion | How to verify |
|---|-----------|--------------|
| AC-3.1 | `CollaborativeFilter` requires ≥ 100 distinct users; raises `InsufficientDataError` otherwise | Unit test |
| AC-3.2 | Hybrid recommender score is a weighted blend of content + collab | Unit test (`hybrid_alpha=0.5` → equal weight) |
| AC-3.3 | `hybrid_alpha` flag change takes effect without service restart | Integration test via `PUT /admin/ml-config` |
| AC-3.4 | Weekly tuning CI job completes in < 30 minutes | CI timing metric |
| AC-3.5 | Rollback to previous model (via `is_active` flag) restores old predictions | Integration test |

---

## 13. Dependency Notes

All required packages are already present in `requirements.txt`:

| Package | Version | Used in which phase |
|---------|---------|---------------------|
| `scikit-learn` | 1.3.2 | All phases |
| `numpy` | 1.26.2 | All phases |
| `pandas` | 2.1.3 | Phase 2+ (feature engineering) |
| `joblib` | bundled with scikit-learn | Phase 2 (model serialisation) |

**No new packages are required for Phases 1 or 2.**  Phase 3 may benefit from
the `surprise` library for collaborative filtering, but `sklearn.decomposition.NMF`
is a viable in-tree alternative that avoids adding a dependency.

---

*Report generated for FitGen AI v6.0 — document date 2026-03-06.*  
*Base reference: `docs/ml-models-and-suitability.md` (last reviewed 2026-02-27).*
