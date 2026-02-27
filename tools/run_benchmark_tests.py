#!/usr/bin/env python3
"""
FitGen AI - Automated Test Benchmark Runner
Runs the test suite N times (default 500), collects metrics, and writes
machine-readable JSON + human-readable Markdown reports.

Usage:
    python -m tools.run_benchmark_tests [options]
    python tools/run_benchmark_tests.py [options]

Options:
    --iterations N      Number of iterations to run (default: 500)
    --target PATH       pytest target path/marker expression (default: test_v6_features.py)
    --seed INT          Random seed passed to tests via PYTHONHASHSEED (default: 42)
    --parallel          Run pytest with -n auto (requires pytest-xdist)
    --output-dir DIR    Directory for report files (default: reports)
    --report-prefix STR Prefix for report filenames (default: test_run)

Examples:
    python -m tools.run_benchmark_tests --iterations 10
    python -m tools.run_benchmark_tests --iterations 500 --target test_v6_features.py
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_pytest() -> str:
    """Return the pytest executable, falling back to 'python -m pytest'."""
    for candidate in ("pytest", "py.test"):
        result = subprocess.run(
            [candidate, "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate
    return f"{sys.executable} -m pytest"


def _run_single_iteration(
    pytest_cmd: str,
    target: str,
    seed: int,
    parallel: bool,
    xml_path: str,
) -> Tuple[bool, float, str, str, Dict[str, str]]:
    """
    Execute one pytest run.

    Returns:
        (passed, duration_seconds, stdout, stderr, test_outcomes)
        where test_outcomes maps test_id -> "passed" | "failed" | "error" | "skipped"
    """
    cmd: List[str] = []
    if pytest_cmd.startswith(sys.executable):
        cmd = [sys.executable, "-m", "pytest"]
    else:
        cmd = [pytest_cmd]

    cmd += [
        target,
        f"--junitxml={xml_path}",
        "-q",
        "--tb=short",
        "--no-header",
    ]
    if parallel:
        cmd += ["-n", "auto"]

    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)

    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
    )
    duration = time.perf_counter() - t0

    passed = proc.returncode == 0
    test_outcomes = _parse_junitxml(xml_path)

    return passed, duration, proc.stdout, proc.stderr, test_outcomes


def _parse_junitxml(xml_path: str) -> Dict[str, str]:
    """
    Parse a JUnit XML file and return a dict of {test_id: outcome}.
    outcome is one of: "passed", "failed", "error", "skipped".
    """
    outcomes: Dict[str, str] = {}
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # Handle both <testsuites><testsuite> and bare <testsuite>
        suites = root.findall(".//testcase")
        for tc in suites:
            classname = tc.get("classname", "")
            name = tc.get("name", "")
            test_id = f"{classname}::{name}" if classname else name

            if tc.find("failure") is not None:
                outcomes[test_id] = "failed"
            elif tc.find("error") is not None:
                outcomes[test_id] = "error"
            elif tc.find("skipped") is not None:
                outcomes[test_id] = "skipped"
            else:
                outcomes[test_id] = "passed"
    except Exception:
        pass
    return outcomes


def _detect_flaky(per_test_history: Dict[str, List[str]]) -> List[Dict]:
    """
    Identify tests that both passed and failed across iterations.

    Returns a list of dicts with test_id, fail_count, pass_count, flake_rate.
    """
    flaky = []
    for test_id, results in per_test_history.items():
        passes = results.count("passed")
        fails = results.count("failed") + results.count("error")
        total = len(results)
        if passes > 0 and fails > 0:
            flaky.append(
                {
                    "test_id": test_id,
                    "pass_count": passes,
                    "fail_count": fails,
                    "total_seen": total,
                    "flake_rate": round(fails / total, 4),
                }
            )
    return sorted(flaky, key=lambda x: x["flake_rate"], reverse=True)


def _percentile(data: List[float], pct: float) -> float:
    """Return the pct-th percentile of sorted data (0-100)."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (k - lo)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

MAX_CAPTURED_FAILURES = 10  # keep stdout/stderr for at most this many failures


def _build_json_report(
    args: argparse.Namespace,
    iterations_data: List[Dict],
    per_test_history: Dict[str, List[str]],
    durations: List[float],
    flaky_tests: List[Dict],
) -> Dict:
    passes = sum(1 for it in iterations_data if it["passed"])
    fails = len(iterations_data) - passes

    timing_stats: Dict = {}
    if durations:
        timing_stats = {
            "mean_s": round(statistics.mean(durations), 4),
            "median_s": round(statistics.median(durations), 4),
            "p95_s": round(_percentile(durations, 95), 4),
            "min_s": round(min(durations), 4),
            "max_s": round(max(durations), 4),
            "stdev_s": round(statistics.stdev(durations), 4) if len(durations) > 1 else 0.0,
        }

    return {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "iterations": args.iterations,
            "target": args.target,
            "seed": args.seed,
            "parallel": args.parallel,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "summary": {
            "total_iterations": len(iterations_data),
            "passed_iterations": passes,
            "failed_iterations": fails,
            "pass_rate": round(passes / len(iterations_data), 4) if iterations_data else 0.0,
        },
        "timing": timing_stats,
        "flaky_tests": flaky_tests,
        "per_test_summary": {
            test_id: {
                "passed": results.count("passed"),
                "failed": results.count("failed"),
                "error": results.count("error"),
                "skipped": results.count("skipped"),
            }
            for test_id, results in per_test_history.items()
        },
        "iterations": iterations_data,
    }


def _ascii_histogram(durations: List[float], bins: int = 10, width: int = 40) -> str:
    """Return a simple ASCII histogram of durations."""
    if not durations:
        return "(no data)"
    lo, hi = min(durations), max(durations)
    if lo == hi:
        return f"All durations: {lo:.3f}s"
    bin_size = (hi - lo) / bins
    counts = [0] * bins
    for d in durations:
        idx = min(int((d - lo) / bin_size), bins - 1)
        counts[idx] += 1
    max_count = max(counts)
    lines = []
    for i, count in enumerate(counts):
        lo_b = lo + i * bin_size
        hi_b = lo_b + bin_size
        bar = "#" * int(count / max_count * width) if max_count else ""
        lines.append(f"  [{lo_b:6.3f}s – {hi_b:6.3f}s] {bar} ({count})")
    return "\n".join(lines)


def _build_markdown_report(report: Dict, args: argparse.Namespace) -> str:
    meta = report["meta"]
    summary = report["summary"]
    timing = report.get("timing", {})
    flaky = report.get("flaky_tests", [])
    per_test = report.get("per_test_summary", {})
    iterations = report.get("iterations", [])

    durations = [it["duration_s"] for it in iterations if "duration_s" in it]

    lines: List[str] = []
    lines.append("# FitGen AI — Benchmark Test Run Report")
    lines.append("")
    lines.append(f"**Generated:** {meta['generated_at']}  ")
    lines.append(f"**Iterations:** {meta['iterations']}  ")
    lines.append(f"**Target:** `{meta['target']}`  ")
    lines.append(f"**Random seed (PYTHONHASHSEED):** {meta['seed']}  ")
    lines.append(f"**Parallel:** {meta['parallel']}  ")
    lines.append(f"**Python:** {meta['python_version']} on {meta['platform']}  ")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## How the benchmark was run")
    lines.append("")
    lines.append("```")
    lines.append(f"python -m tools.run_benchmark_tests \\")
    lines.append(f"    --iterations {meta['iterations']} \\")
    lines.append(f"    --target {meta['target']} \\")
    lines.append(f"    --seed {meta['seed']}")
    if meta["parallel"]:
        lines.append("    --parallel")
    lines.append("```")
    lines.append("")
    lines.append(
        "Each iteration invokes `pytest` as a subprocess with `--junitxml` output. "
        "The XML is parsed to extract per-test outcomes and detect flaky tests. "
        "Timing is measured with `time.perf_counter()` around the subprocess call."
    )
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total iterations | {summary['total_iterations']} |")
    lines.append(f"| ✅ Passed | {summary['passed_iterations']} |")
    lines.append(f"| ❌ Failed | {summary['failed_iterations']} |")
    lines.append(
        f"| Pass rate | {summary['pass_rate'] * 100:.1f}% |"
    )
    lines.append("")

    if timing:
        lines.append("## Timing statistics (wall-clock per iteration)")
        lines.append("")
        lines.append("| Stat | Value |")
        lines.append("|------|-------|")
        lines.append(f"| Mean | {timing['mean_s']:.3f}s |")
        lines.append(f"| Median | {timing['median_s']:.3f}s |")
        lines.append(f"| P95 | {timing['p95_s']:.3f}s |")
        lines.append(f"| Min | {timing['min_s']:.3f}s |")
        lines.append(f"| Max | {timing['max_s']:.3f}s |")
        lines.append(f"| Std Dev | {timing['stdev_s']:.3f}s |")
        lines.append("")
        lines.append("### Duration distribution")
        lines.append("")
        lines.append("```")
        lines.append(_ascii_histogram(durations))
        lines.append("```")
        lines.append("")

    if per_test:
        lines.append("## Per-test pass/fail summary")
        lines.append("")
        lines.append("| Test | Passed | Failed | Error | Skipped |")
        lines.append("|------|--------|--------|-------|---------|")
        for test_id, counts in sorted(per_test.items()):
            lines.append(
                f"| `{test_id}` | {counts['passed']} | {counts['failed']} "
                f"| {counts['error']} | {counts['skipped']} |"
            )
        lines.append("")

    lines.append("## Flaky tests")
    lines.append("")
    if flaky:
        lines.append(
            "The following tests produced **both pass and fail outcomes** across iterations:"
        )
        lines.append("")
        lines.append("| Test | Pass | Fail | Flake rate |")
        lines.append("|------|------|------|-----------|")
        for ft in flaky:
            lines.append(
                f"| `{ft['test_id']}` | {ft['pass_count']} | {ft['fail_count']} "
                f"| {ft['flake_rate'] * 100:.1f}% |"
            )
        lines.append("")
        lines.append("### Recommended actions for flaky tests")
        lines.append("")
        lines.append(
            "1. **Add determinism:** Ensure the test does not rely on random state, "
            "ordering of dict keys, or external I/O without mocking."
        )
        lines.append(
            "2. **Isolate setup/teardown:** Check for shared mutable state between tests "
            "(class-level or module-level variables)."
        )
        lines.append(
            "3. **Increase precision tolerance:** If the test compares floating-point values, "
            "use `pytest.approx()` or `math.isclose()`."
        )
        lines.append(
            "4. **Mock external services:** Database or network calls should be mocked "
            "so results are reproducible."
        )
    else:
        lines.append("✅ No flaky tests detected across all iterations.")
    lines.append("")

    # Failed iteration samples
    failed_iters = [it for it in iterations if not it["passed"]]
    if failed_iters:
        lines.append("## Sample failure output (first 3 failed iterations)")
        lines.append("")
        for it in failed_iters[:3]:
            lines.append(f"### Iteration {it['iteration']} (duration: {it['duration_s']:.3f}s)")
            lines.append("")
            captured = it.get("captured_output", "")
            if captured:
                lines.append("```")
                lines.append(captured[:2000])
                lines.append("```")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Next steps")
    lines.append("")

    if summary["failed_iterations"] > 0:
        fail_pct = (1 - summary["pass_rate"]) * 100
        lines.append(f"⚠️  **{summary['failed_iterations']} iteration(s) failed** ({fail_pct:.1f}% failure rate).")
        lines.append("")
        lines.append(
            "- Review the *Sample failure output* section above for root causes."
        )
        lines.append(
            "- Run a single failing iteration with verbose output: "
            f"`pytest {meta['target']} -v --tb=long`"
        )
        lines.append(
            "- Consider adding more targeted unit tests for failing modules."
        )
    else:
        lines.append("✅ All iterations passed — the test suite is stable.")
        lines.append("")

    if flaky:
        lines.append("- Address flaky tests listed above before adding new features.")
    else:
        lines.append(
            "- Consider expanding test coverage for calorie calculator edge cases, "
            "workout generation with unusual parameters, and API endpoint contracts."
        )
    lines.append(
        "- For regression safety, run `python -m tools.run_benchmark_tests --iterations 100` "
        "as a pre-merge check."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="FitGen AI – automated test benchmark runner (N iterations)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=500,
        help="Number of times to run the test suite",
    )
    parser.add_argument(
        "--target",
        default="test_v6_features.py",
        help="pytest target (path, file, or marker expression)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Value for PYTHONHASHSEED passed to each iteration",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Pass -n auto to pytest (requires pytest-xdist)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to write JSON and Markdown report files",
    )
    parser.add_argument(
        "--report-prefix",
        default="test_run",
        help="Filename prefix for output report files",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pytest_cmd = _find_pytest()
    print(f"[benchmark] pytest command : {pytest_cmd}")
    print(f"[benchmark] target         : {args.target}")
    print(f"[benchmark] iterations     : {args.iterations}")
    print(f"[benchmark] seed           : {args.seed}")
    print(f"[benchmark] parallel       : {args.parallel}")
    print(f"[benchmark] output dir     : {output_dir}")
    print()

    iterations_data: List[Dict] = []
    per_test_history: Dict[str, List[str]] = {}
    durations: List[float] = []
    captured_failure_count = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(1, args.iterations + 1):
            xml_path = os.path.join(tmpdir, f"iter_{i}.xml")

            passed, duration, stdout, stderr, test_outcomes = _run_single_iteration(
                pytest_cmd=pytest_cmd,
                target=args.target,
                seed=args.seed,
                parallel=args.parallel,
                xml_path=xml_path,
            )

            durations.append(duration)

            # Accumulate per-test history
            for test_id, outcome in test_outcomes.items():
                per_test_history.setdefault(test_id, []).append(outcome)

            # Build iteration record
            record: Dict = {
                "iteration": i,
                "passed": passed,
                "duration_s": round(duration, 4),
                "test_outcomes": test_outcomes,
            }

            # Capture stdout/stderr for failures (bounded)
            if not passed and captured_failure_count < MAX_CAPTURED_FAILURES:
                combined = (stdout + stderr).strip()
                record["captured_output"] = combined[:4096]
                captured_failure_count += 1

            iterations_data.append(record)

            # Progress indicator
            status = "✅" if passed else "❌"
            print(
                f"  {status} [{i:>{len(str(args.iterations))}}/{args.iterations}] "
                f"{duration:.3f}s",
                flush=True,
            )

    print()

    # Detect flaky tests
    flaky_tests = _detect_flaky(per_test_history)
    if flaky_tests:
        print(f"[benchmark] ⚠️  {len(flaky_tests)} flaky test(s) detected:")
        for ft in flaky_tests:
            print(
                f"  {ft['test_id']}  pass={ft['pass_count']} fail={ft['fail_count']} "
                f"flake_rate={ft['flake_rate']*100:.1f}%"
            )
    else:
        print("[benchmark] ✅ No flaky tests detected.")

    # Build reports
    json_report = _build_json_report(
        args, iterations_data, per_test_history, durations, flaky_tests
    )
    md_report = _build_markdown_report(json_report, args)

    # Write JSON
    json_filename = f"{args.report_prefix}_{args.iterations}.json"
    json_path = output_dir / json_filename
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(json_report, fh, indent=2)
    print(f"[benchmark] JSON report    : {json_path}")

    # Write Markdown
    md_filename = f"{args.report_prefix}_{args.iterations}.md"
    md_path = output_dir / md_filename
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md_report)
    print(f"[benchmark] Markdown report: {md_path}")

    summary = json_report["summary"]
    passes = summary["passed_iterations"]
    total = summary["total_iterations"]
    print(f"\n[benchmark] Done — {passes}/{total} iterations passed.")

    return 0 if summary["failed_iterations"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
