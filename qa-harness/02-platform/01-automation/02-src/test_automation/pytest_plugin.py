from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from test_automation.config import get_settings
from test_automation.reporting import RunSummary
from test_automation.reporting import utc_now_iso
from test_automation.reporting import write_summary


@dataclass
class _RunTimes:
    started_at: str


def pytest_configure(config: pytest.Config) -> None:
    config._ta_run_times = _RunTimes(started_at=utc_now_iso())  # type: ignore[attr-defined]


def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: pytest.Config) -> None:
    settings = get_settings()
    started_at = getattr(getattr(config, "_ta_run_times", None), "started_at", utc_now_iso())
    finished_at = utc_now_iso()

    stats = terminalreporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    errors = len(stats.get("error", []))
    total = passed + failed + skipped + errors

    duration_seconds = 0.0
    try:
        duration_seconds = float(getattr(terminalreporter, "_sessionduration", 0.0))
    except Exception:
        duration_seconds = 0.0

    summary = RunSummary(
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        env=settings.env,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=errors,
    )

    out_path = Path(settings.artifacts_dir) / "summary.json"
    write_summary(out_path, summary)
