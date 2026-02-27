# FitGen AI — Workout & Nutrition Service

FitGen AI is a FastAPI-based service that generates personalised workout plans,
logs exercise sessions in real time, and provides calorie-burn analytics.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set MongoDB URI (skip to use without a database)
export MONGODB_ATLAS_URI="mongodb+srv://..."

# 3. Start the API server
uvicorn api_service_v6:app --reload

# 4. Open interactive docs
open http://localhost:8000/docs
```

---

## Running the existing tests

```bash
pytest test_v6_features.py -v
```

---

## Automated benchmark runner

`tools/run_benchmark_tests.py` repeats the test suite *N* times, collects
timing and pass/fail metrics, detects flaky tests, and writes machine-readable
JSON + human-readable Markdown reports to the `reports/` directory.

### Usage

```bash
# Run 500 iterations (default)
python -m tools.run_benchmark_tests

# Run 10 iterations (quick check)
python -m tools.run_benchmark_tests --iterations 10

# Custom target, seed, and output directory
python -m tools.run_benchmark_tests \
    --iterations 500 \
    --target test_v6_features.py \
    --seed 123 \
    --output-dir reports
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--iterations N` | `500` | Number of times to run the test suite |
| `--target PATH` | `test_v6_features.py` | pytest path / marker expression |
| `--seed INT` | `42` | Value for `PYTHONHASHSEED` in each iteration |
| `--parallel` | off | Pass `-n auto` to pytest (requires `pytest-xdist`) |
| `--output-dir DIR` | `reports` | Directory for output files |
| `--report-prefix STR` | `test_run` | Filename prefix for report files |

### Output files

After a run the `reports/` directory will contain:

| File | Description |
|------|-------------|
| `reports/test_run_500.json` | Machine-readable full report (meta, summary, timing, per-test counts, flaky list, all iterations) |
| `reports/test_run_500.md` | Human-readable Markdown report with ASCII timing histogram and flaky-test guidance |

---

## CI / GitHub Actions

The `.github/workflows/benchmark.yml` workflow can be triggered:

- **Manually** via *Actions → Benchmark Tests → Run workflow*  
  (configurable `iterations`, `target`, `seed` inputs)
- **On schedule** every Sunday at 02:00 UTC

The workflow uploads both the JSON and Markdown reports as downloadable build
artefacts (retained 30 days).

---

## Documentation

| File | Contents |
|------|----------|
| `docs/ml-models-and-suitability.md` | Inventory and suitability review of every ML/analytics algorithm in the codebase |
| `docs/API_DOCUMENTATION.md` | REST endpoint reference |
| `docs/performance_test_report.md` | Soak and stress test results (200-iteration run) |
| `IMPLEMENTATION_SUMMARY.md` | v6.0 feature summary |
