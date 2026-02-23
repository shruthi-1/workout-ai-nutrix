"""
Soak test for FitGen AI v6.0 FastAPI (api_service_v6.py).

Covers workflow + data flow by iterating:
- GET  /dataset/exercises
- POST /users/{user_id}/workouts/generate
- POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log   (for a few exercises)
- GET  /users/{user_id}/workouts/history
- GET  /users/{user_id}/analytics/calories

It records success/fail + latency stats per endpoint and performs basic invariants checks.

Run:
  uvicorn api_service_v6:app --reload --port 8000

Then:
  python soak_test_api_v6.py --iterations 200 --base-url http://127.0.0.1:8000 --user-id john
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests


def percentile(values: List[float], p: float) -> float:
    if not values:
        return float("nan")
    v = sorted(values)
    k = (len(v) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return v[int(k)]
    return v[f] * (c - k) + v[c] * (k - f)


@dataclass
class Stats:
    name: str
    ok: int = 0
    fail: int = 0
    lat_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add(self, ok: bool, ms: float, err: Optional[str] = None) -> None:
        self.lat_ms.append(ms)
        if ok:
            self.ok += 1
        else:
            self.fail += 1
            if err:
                self.errors.append(err[:700])

    def report(self) -> Dict[str, Any]:
        l = self.lat_ms
        return {
            "endpoint": self.name,
            "ok": self.ok,
            "fail": self.fail,
            "min_ms": round(min(l), 2) if l else None,
            "avg_ms": round(statistics.mean(l), 2) if l else None,
            "p95_ms": round(percentile(l, 0.95), 2) if l else None,
            "max_ms": round(max(l), 2) if l else None,
            "sample_errors": self.errors[:3],
        }


def http_json(
    s: requests.Session,
    method: str,
    url: str,
    *,
    body: Optional[dict] = None,
    timeout: float = 30.0,
) -> Tuple[bool, float, Any, Optional[str]]:
    t0 = time.perf_counter()
    try:
        r = s.request(method, url, json=body, timeout=timeout)
        ms = (time.perf_counter() - t0) * 1000.0
        try:
            data = r.json()
        except Exception:
            data = r.text
        ok = 200 <= r.status_code < 300
        err = None if ok else f"HTTP {r.status_code}: {data}"
        return ok, ms, data, err
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000.0
        return False, ms, None, f"{type(e).__name__}: {e}"


# -----------------------
# Invariants (data checks)
# -----------------------
def assert_workout_shape(workout: Any) -> Optional[str]:
    if not isinstance(workout, dict):
        return "workout response is not a JSON object"
    for key in ("workout_id", "user_id", "phases"):
        if key not in workout:
            return f"missing key '{key}' in workout response"
    phases = workout.get("phases")
    if not isinstance(phases, dict) or not phases:
        return "phases is missing/empty or not a dict"

    # Expect at least main_course
    if "main_course" not in phases:
        return "phases does not include 'main_course'"

    # Basic duration/calorie sanity if fields exist
    tdur = workout.get("total_duration_minutes")
    if isinstance(tdur, (int, float)) and tdur <= 0:
        return "total_duration_minutes <= 0"

    return None


def pick_exercise_ids(workout: dict, max_ids: int) -> List[Tuple[str, str]]:
    """
    Returns list of (exercise_id, phase).
    """
    out: List[Tuple[str, str]] = []
    phases = workout.get("phases", {})
    if not isinstance(phases, dict):
        return out

    # Prefer main_course then others
    phase_order = ["main_course", "warmup", "stretches"]
    for ph in phase_order + [p for p in phases.keys() if p not in phase_order]:
        block = phases.get(ph)
        if not isinstance(block, dict):
            continue
        exs = block.get("exercises")
        if not isinstance(exs, list):
            continue
        for ex in exs:
            if isinstance(ex, dict) and isinstance(ex.get("exercise_id"), str):
                out.append((ex["exercise_id"], ph))
                if len(out) >= max_ids:
                    return out
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--iterations", "-n", type=int, default=200)
    ap.add_argument("--user-id", default="john")
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--randomize", action="store_true", help="Randomize generate payload each iteration")
    ap.add_argument("--log-per-workout", type=int, default=2, help="How many exercises to log per generated workout")
    args = ap.parse_args()

    random.seed(args.seed)
    base = args.base_url.rstrip("/")
    n = args.iterations
    user_id = args.user_id

    # A small set to randomize from if you pass --randomize
    body_parts_pool = ["Chest", "Back", "Shoulders", "Legs", "Arms", "Core"]
    fitness_levels = ["Beginner", "Intermediate", "Expert"]

    def build_generate_payload(i: int) -> dict:
        if not args.randomize:
            return {
                "target_body_parts": ["Chest", "Back"],
                "duration_minutes": 60,
                "user_weight_kg": 75.0,
                "include_warmup": True,
                "include_stretches": True,
                "fitness_level": "Intermediate",
            }

        # randomized but still realistic
        parts = random.sample(body_parts_pool, k=random.choice([1, 2, 3]))
        return {
            "target_body_parts": parts,
            "duration_minutes": random.choice([30, 45, 60, 75]),
            "user_weight_kg": random.choice([55.0, 65.0, 75.0, 85.0, 95.0]),
            "include_warmup": True,
            "include_stretches": True,
            "fitness_level": random.choice(fitness_levels),
        }

    stats: Dict[str, Stats] = {}
    def S(name: str) -> Stats:
        stats.setdefault(name, Stats(name))
        return stats[name]

    s = requests.Session()

    for i in range(1, n + 1):
        # 1) dataset list
        ok, ms, ex_list, err = http_json(s, "GET", f"{base}/dataset/exercises")
        S("GET /dataset/exercises").add(ok, ms, err)

        # 2) generate workout
        payload = build_generate_payload(i)
        ok2, ms2, workout, err2 = http_json(
            s,
            "POST",
            f"{base}/users/{user_id}/workouts/generate",
            body=payload,
        )

        # extra invariant check
        inv_err = None
        if ok2:
            inv_err = assert_workout_shape(workout)
            if inv_err:
                ok2 = False
                err2 = f"Invariant failed: {inv_err}. Response: {workout}"

        S("POST /users/{user_id}/workouts/generate").add(ok2, ms2, err2)

        workout_id = workout.get("workout_id") if isinstance(workout, dict) else None

        # 3) log exercises
        if ok2 and isinstance(workout_id, str):
            chosen = pick_exercise_ids(workout, max_ids=max(1, args.log_per_workout))
            if not chosen:
                S("POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log").add(
                    False, 0.0, "No exercise_ids found in generated workout phases"
                )
            else:
                for (exercise_id, phase) in chosen:
                    log_body = {
                        "exercise_title": "Soak Test",
                        "phase": phase,
                        "planned_sets": 3,
                        "completed_sets": 3,
                        "planned_reps": 10,
                        "actual_reps": [10, 10, 10],
                        "weight_used_kg": 20.0,
                        "duration_minutes": 10.0,
                        "calories_burned": 50.0,
                        "difficulty_rating": 6,
                        "notes": f"iter={i}",
                    }
                    ok3, ms3, data3, err3 = http_json(
                        s,
                        "POST",
                        f"{base}/users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log",
                        body=log_body,
                    )
                    S("POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log").add(ok3, ms3, err3)
        else:
            S("POST /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/log").add(
                False, 0.0, "Skipped logging because workout generation failed"
            )

        # 4) history + analytics
        ok4, ms4, data4, err4 = http_json(s, "GET", f"{base}/users/{user_id}/workouts/history")
        S("GET /users/{user_id}/workouts/history").add(ok4, ms4, err4)

        ok5, ms5, data5, err5 = http_json(s, "GET", f"{base}/users/{user_id}/analytics/calories")
        S("GET /users/{user_id}/analytics/calories").add(ok5, ms5, err5)

        if args.sleep > 0:
            time.sleep(args.sleep)

    print("\n=== FitGen v6 API workflow soak test ===")
    print(f"base_url={base} iterations={n} user_id={user_id} randomize={args.randomize}\n")
    for k in sorted(stats.keys()):
        print(json.dumps(stats[k].report(), indent=2))

    total_fail = sum(v.fail for v in stats.values())
    if total_fail:
        raise SystemExit(f"\nFAIL: {total_fail} failed requests/invariant checks")
    print("\nPASS: all checks succeeded")


if __name__ == "__main__":
    main()