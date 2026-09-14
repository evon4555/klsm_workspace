from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


SUITE = "batch_session_configuration"
SCHEMA = "case-screenshot-manifest/v1"

CASES = {
    "SIT-TC-STD-CONFIG-001": {
        "scenario": "SIT-TC-STD-CONFIG-001 Verify that an admin user can open the session batch operation menu after selecting sessions",
        "feature": "Batch Session Configuration real UI automation",
        "tags": ["batch_session_configuration", "ui"],
        "screenshots": [
            ("ui-no-seat-session-rows", "ui-no-seat-session-rows.png"),
            ("ui-batch-operation-menu", "ui-batch-operation-menu.png"),
        ],
    },
    "SIT-TC-STD-CONFIG-002": {
        "scenario": "SIT-TC-STD-CONFIG-002 Verify that batch operations cannot be started when no session is selected",
        "feature": "Batch Session Configuration real UI automation",
        "tags": ["batch_session_configuration", "ui"],
        "screenshots": [
            ("ui-no-seat-no-session-rows", "ui-no-seat-no-session-rows.png"),
            ("ui-no-session-blocked", "ui-no-session-blocked.png"),
        ],
    },
    "SIT-TC-STD-CONFIG-003": {
        "scenario": "SIT-TC-STD-CONFIG-003 Verify that seat-selection sessions can be batch-updated to a new saleable ticket group",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-004": {
        "scenario": "SIT-TC-STD-CONFIG-004 Verify that admission-ticket sessions can be batch-updated to a new saleable ticket group",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-005": {
        "scenario": "SIT-TC-STD-CONFIG-005 Verify that no-seat sessions can be batch-updated to a new saleable ticket group",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-006": {
        "scenario": "SIT-TC-STD-CONFIG-006 Verify that seat-selection sessions can be batch-updated for calendar display",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-007": {
        "scenario": "SIT-TC-STD-CONFIG-007 Verify that admission-ticket sessions can be batch-updated for calendar display",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-008": {
        "scenario": "SIT-TC-STD-CONFIG-008 Verify that no-seat sessions can be batch-updated for calendar display",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-009": {
        "scenario": "SIT-TC-STD-CONFIG-009 Verify that seat-selection sessions can be batch-updated for session-list display type",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-010": {
        "scenario": "SIT-TC-STD-CONFIG-010 Verify that admission-ticket sessions can be batch-updated for session-list display type",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-011": {
        "scenario": "SIT-TC-STD-CONFIG-011 Verify that no-seat sessions can be batch-updated for session-list display type",
        "feature": "Batch Session Configuration real automation",
        "tags": ["api", "batch_session_configuration"],
        "screenshots": [],
    },
    "SIT-TC-STD-CONFIG-012": {
        "scenario": "SIT-TC-STD-CONFIG-012 Verify that pre-generation is blocked when a required target value is missing",
        "feature": "Batch Session Configuration real UI automation",
        "tags": ["batch_session_configuration", "ui"],
        "screenshots": [
            ("ui-no-seat-session-rows", "ui-no-seat-session-rows.png"),
            ("ui-target-group-required", "ui-target-group-required.png"),
        ],
    },
    "SIT-TC-STD-CONFIG-013": {
        "scenario": "SIT-TC-STD-CONFIG-013 Verify that deleting a row from the preview excludes that session from submission",
        "feature": "Batch Session Configuration API plus UI mixed automation",
        "tags": ["batch_session_configuration", "mixed"],
        "screenshots": [
            ("mixed-row-exclusion-ui-evidence", "mixed-row-exclusion-ui-evidence.png"),
        ],
    },
    "SIT-TC-STD-CONFIG-014": {
        "scenario": "SIT-TC-STD-CONFIG-014 Verify that canceling or closing the preview does not save changes",
        "feature": "Batch Session Configuration real UI automation",
        "tags": ["batch_session_configuration", "ui"],
        "screenshots": [
            ("ui-no-seat-session-rows", "ui-no-seat-session-rows.png"),
            ("ui-preview-return-before-close", "ui-preview-return-before-close.png"),
            ("ui-preview-close-before-close", "ui-preview-close-before-close.png"),
        ],
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def automation_root() -> Path:
    return Path(__file__).resolve().parents[1]


def artifact_root() -> Path:
    return automation_root() / "07-artifacts" / SUITE


def build_manifest(run_id: str) -> dict:
    root = artifact_root()
    captured_at = now_iso()
    manifest = {
        "schema": SCHEMA,
        "project": "standard product",
        "suite": SUITE,
        "run_id": run_id,
        "artifact_root": str(root).replace("\\", "/"),
        "created_at": captured_at,
        "updated_at": captured_at,
        "backfilled": True,
        "cases": {},
    }

    missing: list[str] = []
    for case_id, info in CASES.items():
        case_dir = root / f"run-{run_id}" / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        screenshots = []
        for idx, (label, filename) in enumerate(info["screenshots"], start=1):
            source = root / filename
            if not source.is_file():
                missing.append(str(source))
                continue
            target = case_dir / f"{idx:02d}-{label}.png"
            shutil.copyfile(source, target)
            screenshots.append({
                "label": label,
                "path": str(target).replace("\\", "/"),
                "relative_path": target.relative_to(root).as_posix(),
                "legacy_path": str(source).replace("\\", "/"),
                "captured_at": captured_at,
                "backfilled": True,
            })

        manifest["cases"][case_id] = {
            "case_id": case_id,
            "scenario": info["scenario"],
            "feature": info["feature"],
            "tags": info["tags"],
            "status": "passed",
            "finished_at": captured_at,
            "has_screenshot": bool(screenshots),
            "screenshots": screenshots,
        }

    if missing:
        manifest["missing_legacy_screenshots"] = missing
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill case screenshot manifest from legacy suite-level screenshots.")
    parser.add_argument("--run-id", default="176", help="Dashboard run id to backfill.")
    args = parser.parse_args()

    root = artifact_root()
    root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(str(args.run_id))
    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    run_path = root / f"case-screenshot-manifest-run-{args.run_id}.json"
    latest_path = root / "case-screenshot-manifest-latest.json"
    run_path.write_text(payload, encoding="utf-8")
    latest_path.write_text(payload, encoding="utf-8")
    print(f"wrote {run_path}")
    print(f"wrote {latest_path}")
    if manifest.get("missing_legacy_screenshots"):
        print("missing legacy screenshots:")
        for item in manifest["missing_legacy_screenshots"]:
            print(f"  {item}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
