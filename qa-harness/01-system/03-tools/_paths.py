"""Path helpers for qa-harness tools.

Tools should not hard-code an install drive. By default we derive the harness
root from this file's location. Set QA_HARNESS_ROOT to override when needed.
"""
from __future__ import annotations

import os
from pathlib import Path


def _looks_like_repo_root(path: Path) -> bool:
    return (
        (path / "01-system").is_dir()
        and (path / "02-platform").is_dir()
        and (path / "03-context").is_dir()
    )


def _candidate_roots() -> list[Path]:
    starts = [Path.cwd().absolute(), Path.cwd().resolve(),
              Path(__file__).absolute(), Path(__file__).resolve()]
    candidates: list[Path] = []
    for start in starts:
        candidates.append(start)
        candidates.extend(start.parents)
    return candidates


def repo_root() -> Path:
    override = os.getenv("QA_HARNESS_ROOT")
    if override:
        return Path(override).expanduser().resolve()

    for candidate in _candidate_roots():
        if _looks_like_repo_root(candidate):
            return candidate.resolve()

    raise RuntimeError(
        "Cannot locate qa-harness repo root. Set QA_HARNESS_ROOT to the "
        "physical workspace harness root."
    )


def westk_root() -> Path:
    override = os.getenv("QA_WESTK_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    candidate = repo_root().parent / "west-kowloon"
    if candidate.is_dir():
        return candidate.resolve()
    raise RuntimeError("Cannot locate West Kowloon root. Set QA_WESTK_ROOT.")
