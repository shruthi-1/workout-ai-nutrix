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
| `docs/NEXT_STEPS_ML_IMPLEMENTATION_REPORT.md` | Detailed organisational roadmap for evolving FitGen AI into a data-driven personalisation platform (Phases 1–3) |
| `docs/API_DOCUMENTATION.md` | REST endpoint reference |
| `docs/performance_test_report.md` | Soak and stress test results (200-iteration run) |
| `IMPLEMENTATION_SUMMARY.md` | v6.0 feature summary |

---

## Generating the ML report PDF

### Locally (requires pandoc and a LaTeX engine)

```bash
# Install pandoc and a minimal LaTeX engine on macOS (Homebrew)
brew install pandoc
brew install --cask mactex-no-gui   # or: brew install basictex

# Install on Ubuntu/Debian
sudo apt-get install pandoc texlive-latex-recommended texlive-latex-extra \
    texlive-fonts-recommended texlive-fonts-extra

# Generate the PDF
pandoc \
  docs/NEXT_STEPS_ML_IMPLEMENTATION_REPORT.md \
  --pdf-engine=pdflatex \
  --toc \
  --toc-depth=3 \
  --variable geometry:margin=2.5cm \
  --variable fontsize=11pt \
  --variable colorlinks=true \
  --variable linkcolor=blue \
  --variable urlcolor=blue \
  --highlight-style=tango \
  -o docs/NEXT_STEPS_ML_IMPLEMENTATION_REPORT.pdf
```

The output PDF is written to `docs/NEXT_STEPS_ML_IMPLEMENTATION_REPORT.pdf`.

### Via GitHub Actions (automated)

The workflow `.github/workflows/build-ml-report-pdf.yml` runs automatically:

- **On push** whenever `docs/NEXT_STEPS_ML_IMPLEMENTATION_REPORT.md` or the
  workflow file itself is changed.
- **Manually** via *Actions → Build ML Report PDF → Run workflow*.

After the job completes, download the generated PDF from the **Artifacts**
section of the workflow run (retained for 90 days).
