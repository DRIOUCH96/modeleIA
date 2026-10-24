import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_SCRIPT = PROJECT_ROOT / "scripts" / "check_quality.py"
QUALITY_CONFIG = PROJECT_ROOT / "config" / "quality_gate.yaml"
REAL_METRICS = PROJECT_ROOT / "model" / "metrics.json"
INSUFFICIENT_METRICS = (
    PROJECT_ROOT / "tests" / "fixtures" / "metrics_insufficient.json"
)


def run_quality_gate(metrics_path: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"

    return subprocess.run(
        [
            sys.executable,
            str(QUALITY_SCRIPT),
            "--metrics",
            str(metrics_path),
            "--config",
            str(QUALITY_CONFIG),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        check=False,
    )


def test_real_metrics_pass_quality_gate():
    result = run_quality_gate(REAL_METRICS)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Barrière qualité : OK" in result.stdout


def test_insufficient_metrics_are_rejected_without_overwriting_real_metrics():
    real_metrics_before = REAL_METRICS.read_bytes()

    result = run_quality_gate(INSUFFICIENT_METRICS)

    assert result.returncode == 1
    assert "Barrière qualité : ÉCHEC" in result.stdout
    assert "F1 insuffisant" in result.stdout
    assert "Test trop petit" in result.stdout
    assert REAL_METRICS.read_bytes() == real_metrics_before