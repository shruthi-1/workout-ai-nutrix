"""
In-process stress test for v6 modules:
- DatabaseManagerV6
- WorkoutGeneratorV6
- SessionLoggerV6

This bypasses HTTP and focuses on algorithm/data logic.
Requires that your local MongoDB (or whatever DatabaseManagerV6 expects) is available.

Run:
  python stress_test_modules_v6.py --iterations 200 --user-id john
"""

from __future__ import annotations

import argparse
import random
import time
from typing import Any, Dict, List, Tuple

from db.database_manager_v6 import DatabaseManagerV6
from workout.workout_gen_v6 import WorkoutGeneratorV6
from workout.session_logger_v6 import SessionLoggerV6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", "-n", type=int, default=200)
    ap.add_argument("--user-id", default="john")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--randomize", action="store_true")
    args = ap.parse_args()

    random.seed(args.seed)

    db = DatabaseManagerV6()
    gen = WorkoutGeneratorV6(db)
    logger = SessionLoggerV6(db)

    body_parts_pool = ["Chest", "Back", "Shoulders", "Legs", "Arms", "Core"]
    fitness_levels = ["Beginner", "Intermediate", "Expert"]

    failures: List[str] = []
    t0 = time.perf_counter()

    for i in range(1, args.iterations + 1):
        try:
            if args.randomize:
                target_parts = random.sample(body_parts_pool, k=random.choice([1, 2, 3]))
                duration = random.choice([30, 45, 60, 75])
                weight = random.choice([55.0, 65.0, 75.0, 85.0, 95.0])
                level = random.choice(fitness_levels)
            else:
                target_parts = ["Chest", "Back"]
                duration = 60
                weight = 75.0
                level = "Intermediate"

            workout: Dict[str, Any] = gen.generate_structured_workout(
                user_id=args.user_id,
                target_body_parts=target_parts,
                duration_minutes=duration,
                user_weight_kg=weight,
                include_warmup=True,
                include_stretches=True,
                fitness_level=level,
            )

            workout_id = workout.get("workout_id")
            phases = workout.get("phases", {})

            if not workout_id or "main_course" not in phases:
                raise ValueError(f"Invalid workout shape in iter {i}: keys={list(workout.keys())}")

            # Log the first main_course exercise if present
            main_exs = phases.get("main_course", {}).get("exercises", [])
            if main_exs:
                ex0 = main_exs[0]
                exercise_id = ex0.get("exercise_id")
                if exercise_id:
                    logger.log_exercise_realtime(
                        user_id=args.user_id,
                        workout_id=workout_id,
                        exercise_id=exercise_id,
                        exercise_title=ex0.get("title", "Stress Test"),
                        phase="main_course",
                        planned_sets=3,
                        completed_sets=3,
                        planned_reps=10,
                        actual_reps=[10, 10, 10],
                        weight_used_kg=20.0,
                        duration_minutes=10.0,
                        calories_burned=50.0,
                        difficulty_rating=6,
                        notes=f"iter={i}",
                    )

        except Exception as e:
            failures.append(f"iter={i} {type(e).__name__}: {e}")

    elapsed = time.perf_counter() - t0
    print(f"\nModule stress test done. iterations={args.iterations} elapsed_s={elapsed:.2f}")
    print(f"failures={len(failures)}")
    if failures:
        print("Sample failures:")
        for f in failures[:10]:
            print(" -", f)
        raise SystemExit("FAIL")
    print("PASS")

    db.close()


if __name__ == "__main__":
    main()