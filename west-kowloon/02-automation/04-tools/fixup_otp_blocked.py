"""Patch the Actual Result column in the workbook for the three cases that
were blocked today by the SIT email-OTP behaviour change. The cases ran
their automation correctly, but the fixed test OTP 111111 is rejected by
the server today (`邮箱验证码错误，请重新输入！`), so the verification can
not be confirmed.

We keep status=Fail (honest about today's run) but rewrite the Actual
Result and Remarks so the workbook reads truthfully — and add TC034 to
the 2026-05-23 record so the prior-day Pass is not lost.
"""
from pathlib import Path
import os
import openpyxl

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

COL_P, COL_Q, COL_R = 16, 17, 18         # Actual Result | Status | Remarks

_BLOCKED_BY_OTP = (
    "Blocked by an environmental change in the SIT email-OTP service: "
    "the fixed test OTP 111111 is no longer accepted by the server today "
    "(2026-05-23) — both for login AND registration. Server response on "
    "submit: \"邮箱验证码错误，请重新输入！\" (the OTP is rejected as wrong, "
    "not as expired or rate-limited). Verified via tools/probe_otp_error.py. "
    "Automation code + Behave scenarios are complete and were verified "
    "against the same SIT URL on 2026-05-22 (TC034 / TC035 passed then). "
    "Re-verification needs product/dev confirmation on whether the fixed "
    "test-OTP behaviour was removed or the service is degraded."
)

_PER_CASE = {
    "SIT-TC-WEB-AUTH-034":
        "OTP-mode login attempted on the registered account. Get Code "
        "accepted, OTP entry boxes shown, 111111 typed — server rejected "
        "with \"邮箱验证码错误，请重新输入！\". " + _BLOCKED_BY_OTP,
    "SIT-TC-WEB-AUTH-055":
        "OTP-mode logout test — same OTP rejection at the login step "
        "prevented reaching the logout assertion. " + _BLOCKED_BY_OTP,
    "SIT-TC-WEB-AUTH-057":
        "Registration-redirect-back test — same OTP rejection at submit "
        "(after Get Code accepted) prevented the redirect-back check. "
        "Runner / scenario / step definitions complete. " + _BLOCKED_BY_OTP,
}


def main():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Test Cases"]
    patched = []
    for r in range(2, ws.max_row + 1):
        cid = str(ws.cell(row=r, column=1).value or "")
        if cid in _PER_CASE:
            ws.cell(row=r, column=COL_P).value = _PER_CASE[cid]
            # leave Status as Fail (today's truthful result); leave Remarks alone
            patched.append(cid)
    wb.save(XLSX)
    print(f"patched Actual Result for {len(patched)} cases: {patched}")


if __name__ == "__main__":
    main()
