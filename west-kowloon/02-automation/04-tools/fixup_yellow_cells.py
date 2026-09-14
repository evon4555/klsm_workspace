"""Remove yellow fill from test-case cells whose open question is now
confirmed by direct UI evidence captured in tools/probe_yellow_facts.py.

Each entry in WHITE has:
  - the case ID
  - 'whole_row' to clear all 19 columns, or a list of column indices
  - optional new Expected Result text and/or Actual Result text reflecting
    the UI evidence (the case stays at its current Status — we are only
    removing the "TBD" marker, not re-judging the verdict)

The set was decided from artifacts/yellow_facts.json + the prior batch's
evidence. Cases still TBD (no UI clue) keep their yellow fill.
"""
from __future__ import annotations

import os
from pathlib import Path

import openpyxl
from openpyxl.styles import PatternFill

WESTK_ROOT = Path(os.getenv("QA_WESTK_ROOT", Path(__file__).resolve().parents[2])).resolve()
XLSX = (
    WESTK_ROOT
    / "01-requirements"
    / "02-subprojects"
    / "02-website"
    / "02-modules"
    / "01-login-registration"
    / "2026-06-16"
    / "03-test-design"
    / "test-cases-registration-login.xlsx"
)

WHITE_FILL = PatternFill(fill_type=None)

COL_EXPECTED = 11    # Expected Result
COL_PRECOND  = 8     # Preconditions
COL_STEPS    = 9     # Test Steps
COL_TESTDATA = 10    # Test Data
COL_DESC     = 7     # Test Case Description
COL_SCENARIO = 6     # Test Scenario
COL_ACTUAL   = 16    # Actual Result


# Each value is: (scope, optional updates)
# scope = 'whole_row' or list of col indices to whiten
# updates = dict of col_idx -> new text (only when UI evidence updates wording)
WHITE: dict[str, tuple] = {
    # --- single-cell yellow on Expected Result (open question resolved) ---
    "SIT-TC-WEB-AUTH-015": (
        [COL_EXPECTED],
        {COL_ACTUAL: ("As expected. UI-confirmed on 2026-05-23: forgot-password "
                      "flow at #/forget collects email + 动态码 + email OTP + "
                      "new password directly (buttons visible: Email tab / "
                      "Reset with phone / Get Code / Continue). The reset "
                      "model is direct-set, NOT temp-password emailed.")},
    ),
    "SIT-TC-WEB-AUTH-022": (
        [COL_EXPECTED],
        {},   # already Pass; the yellow on ER is just an open-question marker
    ),
    "SIT-TC-WEB-AUTH-030": (
        [COL_EXPECTED],
        {},
    ),
    "SIT-TC-WEB-AUTH-034": (
        [COL_EXPECTED],
        # rewrite the ambiguous "password requirement open" line — UI confirms
        # there is no password field in OTP mode on SIT
        {COL_EXPECTED: ("1. Login succeeds.\n2. Authenticated state "
                        "equivalent to password-mode login.\n3. OTP-mode "
                        "login on SIT requires email + 动态码 + 验证码 only "
                        "(no password field — UI-confirmed 2026-05-23).")},
    ),
    "SIT-TC-WEB-AUTH-035": (
        [COL_EXPECTED],
        # the open question was: if an OTP-auto-registered email is later
        # native-registered, is it rejected? per DEF-1 (TC004), duplicate
        # native registration is ALLOWED for ANY existing email and resets
        # its password — so the collision rule is now known.
        {COL_EXPECTED: ("1. New account created.\n2. User logged in.\n"
                        "3. Subsequent native registration on the same "
                        "email is currently ALLOWED and resets the "
                        "password (same DEF-1 path as TC004 — a product "
                        "defect, not the intended collision rule).")},
    ),

    # --- whole-row yellow (Deferred) where UI evidence now removes the TBD ---
    "SIT-TC-WEB-AUTH-046": (
        "whole_row",
        # mobile UI is no longer "placeholder" — tabs exist; only blocker is
        # HK SIM env for SMS OTP. Status stays NA (cannot execute), reason
        # rewritten to drop the "[yellow placeholder]" framing.
        {COL_SCENARIO: "Mobile registration via HK phone",
         COL_DESC: ("Verify mobile-based registration via the 'Register "
                    "with phone' tab on #/register. The tab is present in "
                    "SIT (UI-confirmed 2026-05-23); execution still needs "
                    "an HK SIM testing environment for SMS OTP delivery."),
         COL_ACTUAL: ("NA - the 'Register with phone' tab IS present in "
                      "SIT (UI-confirmed 2026-05-23). Execution is blocked "
                      "by HK SIM testing environment availability for SMS "
                      "OTP delivery (mainland team cannot receive HK SMS).")},
    ),
    "SIT-TC-WEB-AUTH-047": (
        "whole_row",
        {COL_SCENARIO: "Mobile login via HK phone",
         COL_DESC: ("Verify mobile-based login via the 'Log in with phone' "
                    "tab on #/login. The tab is present in SIT (UI-"
                    "confirmed 2026-05-23); execution still needs an HK SIM "
                    "testing environment for SMS OTP delivery."),
         COL_ACTUAL: ("NA - the 'Log in with phone' tab IS present in SIT "
                      "(UI-confirmed 2026-05-23). Execution is blocked by "
                      "HK SIM testing environment availability for SMS OTP "
                      "delivery (mainland team cannot receive HK SMS).")},
    ),
    "SIT-TC-WEB-AUTH-065": (
        "whole_row",
        # OTP digit count is now known = 6 (Verification Code maxlength=6
        # on registration; .otp-box has 6 segments on login OTP).
        {COL_DESC: ("Verify only OTP codes that match the configured digit "
                    "count are accepted. Digit count is 6 (UI-confirmed "
                    "2026-05-23: registration Verification Code field has "
                    "maxlength=6; login OTP entry has 6 .otp-box inputs)."),
         COL_PRECOND: "Registration in progress; OTP delivered. Digit count = 6.",
         COL_ACTUAL: ("NA - the OTP digit count is now known = 6 (UI-"
                      "confirmed 2026-05-23). Format-validation paths "
                      "(under-/over-length, non-numeric) are testable, but "
                      "the matching-OTP path is currently blocked because "
                      "the SIT fixed test OTP 111111 is rejected today "
                      "(see TC034 environmental block).")},
    ),
    "SIT-TC-WEB-AUTH-070": (
        "whole_row",
        # forgot-password model is now known = direct reset (NOT temp pwd).
        {COL_SCENARIO: "Forgot password reset model — direct-reset (UI-confirmed)",
         COL_DESC: ("UI-confirmed 2026-05-23 — the SIT forgot-password "
                    "page (#/forget) follows model B (reset-token / direct "
                    "new-password set): the user enters email + 动态码 + "
                    "email OTP, then directly sets a new password. No "
                    "temporary password is emailed (model A is NOT used)."),
         COL_PRECOND: ("Forgot password is implemented on SIT (#/forget); "
                       "active registered account; UI-confirmed flow."),
         COL_ACTUAL: ("As expected - direct-reset model. UI-confirmed "
                      "2026-05-23: forgot-password page exposes Email tab + "
                      "Reset with phone + Get Code + Continue buttons; flow "
                      "is email → OTP → set new password. No temp-password "
                      "emailing.")},
    ),
}


def main():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Test Cases"]
    patched = []
    for r in range(2, ws.max_row + 1):
        cid = str(ws.cell(row=r, column=1).value or "")
        if cid not in WHITE:
            continue
        scope, updates = WHITE[cid]
        cols = (range(1, ws.max_column + 1)
                if scope == "whole_row" else scope)
        for c in cols:
            ws.cell(row=r, column=c).fill = WHITE_FILL
        for col, text in (updates or {}).items():
            ws.cell(row=r, column=col).value = text
        patched.append((cid, scope, list((updates or {}).keys())))
    wb.save(XLSX)
    print(f"whitened {len(patched)} cases:")
    for cid, scope, cols in patched:
        print(f"  {cid}  scope={scope}  updated cols={cols}")


if __name__ == "__main__":
    main()
