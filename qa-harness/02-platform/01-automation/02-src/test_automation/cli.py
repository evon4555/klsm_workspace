from __future__ import annotations

import subprocess
import sys
from typing import List

import pytest


def _run_pytest(args: List[str]) -> int:
    return pytest.main(args)


def _run_behave(args: List[str]) -> int:
    """Run Behave as a subprocess so it uses its own CLI entry point."""
    result = subprocess.run(["behave"] + args, check=False)
    return result.returncode


def main_api() -> None:
    """Entry point: ta-run-api — runs all @api-tagged Behave scenarios."""
    raise SystemExit(_run_behave(["--tags=@api"]))


def main_web() -> None:
    """Entry point: ta-run-web — runs all @hybrid and @ui Behave scenarios."""
    raise SystemExit(_run_behave(["--tags=@hybrid,@ui"]))


def main_app() -> None:
    """Entry point: ta-run-app — runs all @app-tagged pytest tests (Appium)."""
    raise SystemExit(_run_pytest(["-m", "app"]))


def main_all() -> None:
    """Entry point: ta-run-all — runs every Behave scenario regardless of tag."""
    raise SystemExit(_run_behave([]))
