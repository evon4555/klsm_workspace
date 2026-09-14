from __future__ import annotations

import json
import os
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunSummary:
    started_at: str
    finished_at: str
    duration_seconds: float
    env: str
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int


def write_summary(path: str | os.PathLike[str], summary: RunSummary) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(summary), ensure_ascii=False, indent=2), encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
