r"""Run the reproducible registration/login AUTH gate.

This script rebuilds the temporary AUTH feature scope from the real
`D:\Workspace\west-kowloon\02-automation\01-features` source files before running
the formal qa-system gate. It avoids relying on a stale copied scope under
artifacts.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKBOOK = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else HERE / "test-cases-registration-login_2026-06-12.xlsx"
)
DETERMINISTIC_GATE = HERE / "_validate_2026_06_15_review_gates.py"

QA_HARNESS_ROOT = Path(r"D:\Workspace\qa-harness")
WESTK_ROOT = Path(r"D:\Workspace\west-kowloon")
FEATURES_ROOT = WESTK_ROOT / "02-automation" / "01-features"
SCOPE_DIR = QA_HARNESS_ROOT / "06-artifacts" / "auth-feature-scope-registration-login"
FORMAL_GATE = QA_HARNESS_ROOT / "01-system" / "03-tools" / "gate.py"
DB = QA_HARNESS_ROOT / "02-platform" / "02-dashboard" / "01-backend" / "dashboard.db"

AUTH_FEATURE_FILES = [
    "api_ui_mixed/antank_api_first_ui.feature",
    "ui_e2e/antank_bind_contact.feature",
    "ui_e2e/antank_change_password.feature",
    "ui_e2e/antank_documented_na.feature",
    "ui_e2e/antank_email_login.feature",
    "ui_e2e/antank_forgot_password.feature",
    "ui_e2e/antank_guest_login.feature",
    "ui_e2e/antank_guest_to_member.feature",
    "ui_e2e/antank_registration.feature",
    "ui_e2e/antank_session_ui.feature",
    "ui_e2e/antank_third_party_login.feature",
]

DELETED_AUTH_IDS = {
    "SIT-TC-WEB-AUTH-036",
    "SIT-TC-WEB-AUTH-037",
    "SIT-TC-WEB-AUTH-046",
    "SIT-TC-WEB-AUTH-047",
    "SIT-TC-WEB-AUTH-064",
    "SIT-TC-WEB-AUTH-065",
    "SIT-TC-WEB-AUTH-068",
    "SIT-TC-WEB-AUTH-069",
    "SIT-TC-WEB-AUTH-070",
    "SIT-TC-WEB-AUTH-071",
    "SIT-TC-WEB-AUTH-072",
    "SIT-TC-WEB-AUTH-074",
}

FORBIDDEN_AUTH_FEATURE_TERMS = [
    "@todo",
    "TODO",
    "todo",
    "pending",
    "Pending",
    "TBD",
    "Deferred",
    "deferred",
    "DEPRECATED",
    "deprecated",
    "placeholder",
]


def run(cmd: list[str], cwd: Path) -> int:
    print("\n> " + " ".join(f'"{x}"' if " " in x else x for x in cmd), flush=True)
    return subprocess.run(cmd, cwd=str(cwd)).returncode


def rebuild_scope() -> None:
    if SCOPE_DIR.exists():
        shutil.rmtree(SCOPE_DIR)
    SCOPE_DIR.mkdir(parents=True)
    for name in AUTH_FEATURE_FILES:
        src = FEATURES_ROOT / name
        if not src.exists():
            raise FileNotFoundError(src)
        dst = SCOPE_DIR / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def audit_auth_features() -> list[str]:
    issues: list[str] = []
    for name in AUTH_FEATURE_FILES:
        path = FEATURES_ROOT / name
        text = path.read_text(encoding="utf-8")
        for case_id in sorted(DELETED_AUTH_IDS):
            if case_id in text:
                issues.append(f"{name}: deleted ID still referenced: {case_id}")
        for term in FORBIDDEN_AUTH_FEATURE_TERMS:
            if term in text:
                issues.append(f"{name}: forbidden maintenance marker: {term}")
    return issues


def main() -> int:
    if not WORKBOOK.exists():
        print(f"missing workbook: {WORKBOOK}", file=sys.stderr)
        return 2
    if not FORMAL_GATE.exists():
        print(f"missing formal gate: {FORMAL_GATE}", file=sys.stderr)
        return 2

    issues = audit_auth_features()
    if issues:
        print("AUTH feature audit failed:")
        for issue in issues:
            print(f"  FAIL: {issue}")
        return 1
    print("AUTH feature audit: PASS", flush=True)

    rebuild_scope()
    print(f"rebuilt scope: {SCOPE_DIR}", flush=True)

    rc = run([sys.executable, str(DETERMINISTIC_GATE), str(WORKBOOK)], HERE)
    if rc != 0:
        return rc

    return run(
        [
            sys.executable,
            str(FORMAL_GATE),
            "--xlsx",
            str(WORKBOOK),
            "--features",
            str(SCOPE_DIR),
            "--db",
            str(DB),
            "--report-dir",
            str(SCOPE_DIR),
        ],
        QA_HARNESS_ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
