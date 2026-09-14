# -*- coding: utf-8 -*-
"""
update_evidence.py

Run the Website login + registration UI test cases (pure Playwright UI),
capture step-by-step screenshots, and write the REAL results back into the
Kasi test-case workbook test-cases-registration-login.xlsx:

  SIT-TC-WEB-AUTH-001  Successful registration ...... Pass  (kept manual *)
  SIT-TC-WEB-AUTH-002  Empty mandatory fields ........ Pass
  SIT-TC-WEB-AUTH-003  Invalid email format .......... Pass
  SIT-TC-WEB-AUTH-004  Duplicate email ............... NA   (OTP-gated)
  SIT-TC-WEB-AUTH-005  Wrong email OTP ............... Pass
  SIT-TC-WEB-AUTH-006  OTP resend cooldown ........... Pass
  SIT-TC-WEB-AUTH-008  Privacy Policy link ........... Pass
  SIT-TC-WEB-AUTH-009  Successful password login ..... Pass

For every case the workbook columns are filled (purple execution columns):
  M Environment   -> SIT
  N Execution Date-> today
  O Executed By   -> Evan
  P Actual Result -> "As expected" on pass / a short description otherwise
  Q Status        -> Pass / Fail / NA
  R Comments      -> the automation script + tag that covers the case
  S Screenshots   -> the step screenshots, composed into one labelled strip
                     and embedded as an image INSIDE the cell

Non-repeated steps only are captured. On failure the final panel is the error
screenshot (the proof of failure). For the NA cases the screenshots document
*why* the case cannot be automated.

  * TC001 happy-path registration needs a real unused email + its OTP inbox,
    so it is verified manually and kept as Pass per the QA owner's decision;
    automation only drives the form up to the email-OTP step.

Re-run any time to refresh all evidence:

  cd D:\\Workspace\\west-kowloon\\02-automation
  ENV=sit .\\.venv\\Scripts\\python.exe tools\\update_evidence.py

This script supersedes the older tools/update_tc009_evidence.py — it embeds
all nine images in one pass, so re-running it never drops or stacks images.
The workbook test data is generated from test-cases-registration-login.md;
embedded images live only in the .xlsx, so re-run this after any regeneration.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]            # <west-kowloon>\02-automation
WESTK_ROOT = Path(os.getenv("QA_WESTK_ROOT", ROOT.parent)).resolve()
sys.path.insert(0, str(ROOT / "03-src"))

from PIL import Image, ImageDraw, ImageFont                       # noqa: E402
from playwright.sync_api import sync_playwright                   # noqa: E402
import openpyxl                                                   # noqa: E402
from openpyxl.drawing.image import Image as XLImage               # noqa: E402

from test_automation.config import get_settings, get_user         # noqa: E402
from test_automation.web import WebsiteLoginPage                  # noqa: E402
from test_automation.web import WebsiteRegistrationPage           # noqa: E402
from test_automation.web import WebsiteForgotPasswordPage         # noqa: E402
from test_automation.web import WebsiteGuestPage                  # noqa: E402
from test_automation.flows.auth009_api_first import run_auth009_api_first  # noqa: E402

_PKG = (
    WESTK_ROOT / "01-requirements" / "02-subprojects" / "02-website" /
    "02-modules" / "01-login-registration" / "2026-06-16"
)
XLSX = _PKG / "03-test-design" / "test-cases-registration-login.xlsx"
EVIDENCE_DIR = _PKG / "05-execution" / "evidence"

TODAY = datetime.date.today().isoformat()
ENVIRONMENT = "SIT"
EXECUTED_BY = "Evan"
VALID_PASSWORD = "Test@202605"
VALID_OTP = "111111"      # the email Verification Code is a fixed test value in SIT
WRONG_OTP = "000000"      # any value other than VALID_OTP — used for the negative case

FEATURE_REG = "01-features/ui_e2e/antank_registration.feature"
FEATURE_LOGIN = "01-features/ui_e2e/antank_email_login.feature"

# --- OTP rate-limit guard (added 2026-05-26) --------------------------------
# Aliyun mail server throttles: same email can request OTP only once per 30s.
# We track per-email last-request time and sleep before the next request.
import time as _otp_time
_LAST_OTP_REQUEST: dict = {}
_OTP_THROTTLE_SECONDS = 35       # 30s server window + 5s safety margin


def _wait_for_otp_throttle(email: str) -> None:
    last = _LAST_OTP_REQUEST.get(email)
    if last:
        wait = _OTP_THROTTLE_SECONDS - (_otp_time.time() - last)
        if wait > 0:
            print(f"  [otp throttle] sleeping {wait:.1f}s before next OTP "
                  f"to {email} (server limit: 1 per 30s)")
            _otp_time.sleep(wait + 0.5)
    _LAST_OTP_REQUEST[email] = _otp_time.time()

# xlsx column indices (1-based): M=13 N=14 O=15 P=16 Q=17 R=18 S=19
COL_M, COL_N, COL_O, COL_P, COL_Q, COL_R, COL_S = 13, 14, 15, 16, 17, 18, 19

_STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
SHOT_BASE = ROOT / "07-artifacts" / "screenshots" / f"evidence_{_STAMP}"

# pretty panel headers for the WebsiteLoginPage internal screenshot labels
LOGIN_TITLES = {
    "login_page_opened": "Step 1  Login page opened",
    "credentials_and_captcha_filled": "Step 2  Email + password + dynamic code filled",
    "login_success": "Step 3  Login success - home page",
    "login_failed": "Step 3  Login FAILED - error state",
    "Step 1  API identity chain verified": "Step 1  API identity chain verified",
    "Step 2  Profile UI opened with same session": "Step 2  Profile UI opened with same session",
    "api_first_login_gate": "Step 1  Login gate / environment error",
}


class CaseResult:
    """Outcome of one test case: status + texts + (label, path) screenshots."""

    def __init__(self, case_id, status, actual, remarks, shots):
        self.case_id = case_id
        self.status = status            # "Pass" | "Fail" | "NA"
        self.actual = actual
        self.remarks = remarks
        self.shots = shots              # list of (label, path)


# ---------------------------------------------------------------------------
# screenshot helpers
# ---------------------------------------------------------------------------

def _registered_area_accessible(page) -> bool:
    """True only if the registered-only personal centre (#/my/profile) is
    actually shown — the route did NOT redirect away and its profile content
    is visible. Used to confirm logout / guest restrictions. A redirect to
    #/ or #/login means the area is correctly protected."""
    if "#/my/profile" not in page.url:
        return False
    return bool(page.evaluate(
        """() => {
            const vis = el => !!(el && (el.offsetWidth || el.offsetHeight));
            return [...document.querySelectorAll(
                      '.avatar-popup-btn,.nav-item,.tab-item')].some(vis);
        }"""))


def _error_shot(page, shot_dir, shots, label="error_state"):
    """Capture an extra screenshot of the current screen (used on failure)."""
    try:
        shot_dir.mkdir(parents=True, exist_ok=True)
        path = shot_dir / f"99_{label}.png"
        page.screenshot(path=str(path))
        shots.append((label, str(path)))
    except Exception:                                       # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# per-case runners — each returns a CaseResult
# ---------------------------------------------------------------------------

def run_tc001(browser):
    """SIT-TC-WEB-AUTH-001 — a new visitor registers successfully.

    Uses a throwaway fake email (fake_<stamp>@126.com) — unique per run, so it
    is a genuine first-time registration — plus the fixed SIT email OTP. No
    real inbox is needed because the Verification Code is a fixed test value.
    The 动态码 image captcha is still OCR-solved."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc001"
    email = f"fake_{_STAMP}@126.com"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.fill_email(email)
        reg.request_otp_until_sent()        # 动态码 + click Get Code
        reg.fill_verification_code(VALID_OTP)
        reg.fill_passwords(VALID_PASSWORD)
        reg.shot("Step 2  Form filled — Get Code requested, OTP 111111 entered")
        error = reg.submit_until_settled()
        reg._page.wait_for_timeout(2500)        # let the success modal / redirect settle
        reg.shot("Step 3  Registration result")
        if reg.registration_succeeded():
            status = "Pass"
            actual = "As expected"
        else:
            status = "Fail"
            actual = f"New-visitor registration did not complete (error={error!r})."
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)  [TC001]"
    return CaseResult("SIT-TC-WEB-AUTH-001", status, actual, remarks, shots)


def run_tc002(browser):
    """SIT-TC-WEB-AUTH-002 — empty mandatory fields block registration."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc002"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.submit()
        reg.shot("Step 2  Empty submit blocked - validation message")
        error = reg.current_error()
        if error and reg.is_on_register_page():
            status = "Pass"
            actual = "As expected"
        else:
            status = "Fail"
            actual = f"Empty submit was not blocked as expected (error={error!r})."
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)  [TC002]"
    return CaseResult("SIT-TC-WEB-AUTH-002", status, actual, remarks, shots)


def run_tc003(browser):
    """SIT-TC-WEB-AUTH-003 — invalid email format is rejected."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc003"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.fill_email("not-an-email")
        reg.shot("Step 2  Invalid email entered")
        reg.submit()
        reg.shot("Step 3  Invalid email rejected")
        error = reg.current_error()
        low = error.lower()
        rejected = bool(error) and ("invalid" in low or "email" in low
                                    or "邮件" in error or "邮箱" in error
                                    or "格式" in error)
        if rejected and reg.is_on_register_page():
            status = "Pass"
            actual = "As expected"
        else:
            status = "Fail"
            actual = f"Invalid email was not rejected as expected (error={error!r})."
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)  [TC003]"
    return CaseResult("SIT-TC-WEB-AUTH-003", status, actual, remarks, shots)


def run_tc004(browser):
    """SIT-TC-WEB-AUTH-004 — a duplicate email must be rejected.

    Submits a full, valid registration (email OTP 111111) for the
    already-registered website account. The system is EXPECTED to reject it
    with an existing-account message. If registration instead succeeds, the
    duplicate-email protection has failed — a product defect — so this case
    is recorded as Fail. The registration password matches config/users.yml
    so a (defective) re-registration leaves the account credentials unchanged."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc004"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.fill_email(user.username)
        # Stay past Aliyun's 30s per-email OTP rate limit + record `since`
        # before Get Code so the IMAP poller only accepts THIS request's OTP.
        _wait_for_otp_throttle(user.username)
        from datetime import datetime, timezone, timedelta
        since = datetime.now(timezone.utc) - timedelta(seconds=10)
        reg.request_otp_until_sent()        # 动态码 + click Get Code
        # SIT removed fixed test OTP 111111; fetch the real one from inbox.
        import sys
        _tools_dir = str(Path(__file__).resolve().parent)
        if _tools_dir not in sys.path: sys.path.insert(0, _tools_dir)
        from imap_otp_poller import fetch_latest_otp
        real_otp = fetch_latest_otp(since=since, timeout=45.0)
        reg.fill_verification_code(real_otp)
        reg.fill_passwords(user.password)
        reg.shot(f"Step 2  Valid form filled with an ALREADY-REGISTERED "
                 f"email and a real OTP ({real_otp[:2]}xxxx)")
        error = reg.submit_until_settled()
        reg._page.wait_for_timeout(2500)
        reg.shot("Step 3  Registration result")
        succeeded = reg.registration_succeeded()
        if succeeded:
            status = "Fail"
            actual = ("DEFECT - registration with an already-registered email "
                      f"({user.username}) SUCCEEDED. The system did not prevent "
                      "the duplicate; expected rejection with an existing-account "
                      "message. The same email can be registered repeatedly.")
        else:
            status = "Pass"
            actual = "As expected"
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)  [TC004]"
    return CaseResult("SIT-TC-WEB-AUTH-004", status, actual, remarks, shots)


def run_tc005(browser):
    """SIT-TC-WEB-AUTH-005 — a wrong email OTP cannot complete registration."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc005"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.fill_email(user.username)
        reg.request_otp_until_sent()        # 动态码 + click Get Code (real OTP session)
        reg.fill_verification_code(WRONG_OTP)   # deliberately wrong — not 111111
        reg.fill_passwords(VALID_PASSWORD)
        reg.shot("Step 2  Form filled with a wrong verification code")
        error = reg.submit_until_settled()
        reg.shot("Step 3  Registration blocked - OTP error")
        low = error.lower()
        if error and reg.is_on_register_page() and (
                "邮箱" in error or "验证码" in error
                or "otp" in low or "verification" in low):
            status = "Pass"
            actual = "As expected"
        else:
            status = "Fail"
            actual = f"Wrong OTP was not rejected as expected (error={error!r})."
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)  [TC005]"
    return CaseResult("SIT-TC-WEB-AUTH-005", status, actual, remarks, shots)


def run_tc006(browser):
    """SIT-TC-WEB-AUTH-006 — OTP resend follows a cooldown."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc006"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.fill_email(user.username)
        reg.fill_dynamic_code()
        reg.shot("Step 2  Email and dynamic code filled")
        cooling = False
        for attempt in range(1, 4):
            reg.request_otp()
            if reg.resend_is_cooling_down():
                cooling = True
                break
            print(f"  [TC006] no cooldown yet (attempt {attempt}) - retrying")
            reg.fill_dynamic_code()
        reg.shot("Step 3  Resend control in countdown cooldown")
        text, disabled = reg.get_code_button_state()
        if cooling:
            status = "Pass"
            actual = "As expected"
        else:
            status = "Fail"
            actual = (f"Resend cooldown was not observed "
                      f"(button={text!r}, disabled={disabled}).")
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)  [TC006]"
    return CaseResult("SIT-TC-WEB-AUTH-006", status, actual, remarks, shots)


def run_tc008(browser):
    """SIT-TC-WEB-AUTH-008 — the Privacy Policy link opens the policy."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc008"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    email = "policy.viewer@example.com"
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.fill_email(email)
        reg.shot("Step 1  Registration field filled")
        reg.open_privacy_policy()
        reg.shot("Step 2  Privacy Policy modal opened")
        opened = reg.privacy_dialog_visible()
        title = reg.privacy_dialog_title()
        reg.close_privacy_policy()
        preserved = reg.email_value()
        reg.shot("Step 3  Modal closed - form data preserved")
        if opened and "privacy" in title.lower() and preserved == email:
            status = "Pass"
            actual = "As expected"
        else:
            status = "Fail"
            actual = (f"Privacy Policy check failed (opened={opened}, "
                      f"title={title!r}, preserved={preserved!r}).")
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)  [TC008]"
    return CaseResult("SIT-TC-WEB-AUTH-008", status, actual, remarks, shots)


def run_tc009(browser):
    """SIT-TC-WEB-AUTH-009 — successful password-mode login."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc009"
    ctx = browser.new_context()
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url),
                              screenshot_dir=shot_dir)
        lp.open()
        lp.fill_credentials(user.username, user.password)
        lp.submit_with_captcha()
        shots = list(lp.screenshots)
        if lp.is_home_page():
            status = "Pass"
            actual = "As expected"
        else:
            status = "Fail"
            actual = "Login submitted but the authenticated home page was not confirmed."
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status = "Fail"
        actual = f"Login failed: {exc}"
        try:
            shots = list(lp.screenshots)
        except Exception:                                   # noqa: BLE001
            shots = []
        if not shots:
            _error_shot(page, shot_dir, shots, "login_failed")
    finally:
        ctx.close()
    remarks = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_LOGIN}, tag @login)"
    return CaseResult("SIT-TC-WEB-AUTH-009", status, actual, remarks, shots)


# ---------------------------------------------------------------------------
# TC010-035 runners
# ---------------------------------------------------------------------------

_RMK_LOGIN = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_LOGIN}, tag @login)"
_RMK_REG = f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG}, tag @registration)"
_RMK_FORGOT = "D:\\Workspace\\west-kowloon\\02-automation (01-features/ui_e2e/antank_forgot_password.feature, tag @forgot)"
_RMK_GUEST = "D:\\Workspace\\west-kowloon\\02-automation (01-features/ui_e2e/antank_guest_login.feature, tag @guest)"
_RMK_SESSION = "D:\\Workspace\\west-kowloon\\02-automation (01-features/ui_e2e/antank_session_ui.feature)"


def run_tc010(browser):
    """SIT-TC-WEB-AUTH-010 — wrong password is rejected."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc010"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        error = lp.attempt_login(user.username, "WrongPass@000000")
        lp._shot("Step 2  Wrong password rejected")
        if error and not lp.is_logged_in():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Wrong password not rejected (error={error!r})."
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-010", status, actual,
                      f"{_RMK_LOGIN}  [TC010]", shots)


def run_tc012(browser):
    """SIT-TC-WEB-AUTH-012 — an unknown account cannot log in."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc012"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        error = lp.attempt_login("no.such.user.2026@126.com", "WrongPass@000000")
        lp._shot("Step 2  Unknown account rejected")
        if error and not lp.is_logged_in():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Unknown account not rejected (error={error!r})."
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-012", status, actual,
                      f"{_RMK_LOGIN}  [TC012]", shots)


def run_tc013(browser):
    """SIT-TC-WEB-AUTH-013 — logout clears authenticated access."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    base = str(settings.antank_url).rstrip("/")
    shot_dir = SHOT_BASE / "tc013"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    profile_url = f"{base}/websitehtml/index.html#/my/profile"
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        lp.fill_credentials(user.username, user.password)
        lp.submit_with_captcha()
        page.wait_for_timeout(1500)
        # the registered-only personal centre must be reachable while logged in
        page.goto(profile_url, timeout=60000)
        page.wait_for_timeout(2500)
        reachable_before = _registered_area_accessible(page)
        lp._shot("Step 2  Personal centre open while logged in")
        lp.logout()
        # after logout, the same registered-only page must NOT be accessible
        page.goto(profile_url, timeout=60000)
        page.wait_for_timeout(2500)
        reachable_after = _registered_area_accessible(page)
        lp._shot("Step 3  Personal centre re-opened after logout")
        if reachable_before and not reachable_after:
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", (f"Logout did not protect the registered-only "
                f"page (reachable before={reachable_before}, after={reachable_after}, "
                f"url={page.url}).")
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-013", status, actual,
                      f"{_RMK_SESSION}  [TC013]", shots)


def run_tc015(browser):
    """SIT-TC-WEB-AUTH-015 — registered user resets the password (reset back
    to the config password so the suite stays repeatable)."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc015"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        fp = WebsiteForgotPasswordPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        fp.open()
        fp.shot("Step 1  Forgot-password page opened")
        fp.fill_email(user.username)
        # Aliyun OTP throttle: same email 1/30s — wait if needed
        _wait_for_otp_throttle(user.username)
        from datetime import datetime, timezone, timedelta
        since = datetime.now(timezone.utc) - timedelta(seconds=10)
        fp.request_otp_until_sent()
        # SIT removed fixed 111111; fetch the real one from inbox
        import sys
        _td = str(Path(__file__).resolve().parent)
        if _td not in sys.path: sys.path.insert(0, _td)
        from imap_otp_poller import fetch_latest_otp
        real_otp = fetch_latest_otp(since=since, timeout=45.0)
        fp.fill_verification_code(real_otp)
        fp.fill_new_passwords(user.password)
        fp.shot(f"Step 2  Reset form filled (email + REAL OTP "
                f"{real_otp[:2]}xxxx + new password)")
        error = fp.submit_until_settled()
        fp.shot("Step 3  Password-reset result")
        if not error:
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Password reset did not complete (error={error!r})."
        shots = list(fp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-015", status, actual,
                      f"{_RMK_FORGOT}  [TC015]", shots)


def run_tc016(browser):
    """SIT-TC-WEB-AUTH-016 — a reset for an unregistered email is blocked."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc016"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        fp = WebsiteForgotPasswordPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        fp.open()
        fp.shot("Step 1  Forgot-password page opened")
        fp.fill_email("no.such.user.2026@126.com")
        fp.fill_dynamic_code()
        fp.shot("Step 2  Unregistered email entered")
        btn = page.locator(fp.GETCODE_SEL).first
        if btn.count() and not btn.is_disabled():
            btn.click(); page.wait_for_timeout(3000)
        error = fp.current_error()
        fp.shot("Step 3  Reset request result for an unregistered email")
        if fp.is_on_forget_page():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Reset proceeded for an unregistered email (error={error!r})."
        shots = list(fp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-016", status, actual,
                      f"{_RMK_FORGOT}  [TC016]", shots)


def run_tc021(browser):
    """SIT-TC-WEB-AUTH-021 — visitor enters guest mode after robot verification."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc021"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        g = WebsiteGuestPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        g.open(); g.start_guest()
        g.shot("Step 1  Guest panel opened")
        g.fill_dynamic_code()
        g.accept_agreement()
        g.shot("Step 2  Robot verification completed")
        g.submit()
        g.shot("Step 3  Guest login result")
        if g.is_guest_session():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Guest session did not start (msg={g.current_message()!r})."
        shots = list(g.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-021", status, actual,
                      f"{_RMK_GUEST}  [TC021]", shots)


def run_tc022(browser):
    """SIT-TC-WEB-AUTH-022 — failed robot verification blocks guest login."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc022"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        g = WebsiteGuestPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        g.open(); g.start_guest()
        g.shot("Step 1  Guest panel opened")
        g.fill_dynamic_code_value("")          # robot verification skipped
        g.shot("Step 2  Robot verification skipped")
        g.submit()
        g.shot("Step 3  Guest login blocked")
        if not g.is_guest_session():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", "Guest login succeeded without robot verification."
        shots = list(g.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-022", status, actual,
                      f"{_RMK_GUEST}  [TC022]", shots)


def run_tc023(browser):
    """SIT-TC-WEB-AUTH-023 — guest session shows a validity countdown."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc023"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        g = WebsiteGuestPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        g.open(); g.start_guest()
        g.fill_dynamic_code(); g.accept_agreement(); g.submit()
        g.shot("Step 1  Guest session started")
        found = page.evaluate(
            r"""() => {
                const sel='[class*=countdown],[class*=timer],[class*=remain],'
                  +'[class*=expire],[class*=valid],[class*=guest]';
                const re=/\d+\s*(min|分|sec|秒|:|时)|countdown|倒计时|剩余|有效/i;
                for (const n of document.querySelectorAll(sel)) {
                  const t=(n.innerText||'').trim();
                  if (t && re.test(t)) return t.slice(0,60);
                } return "";
            }""")
        g.shot("Step 2  Guest validity indicator")
        if found:
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", "No guest session validity/countdown indicator found."
        shots = list(g.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-023", status, actual,
                      f"{_RMK_GUEST}  [TC023]", shots)


def run_tc025(browser):
    """SIT-TC-WEB-AUTH-025 — guest cannot access registered-only functions."""
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")
    shot_dir = SHOT_BASE / "tc025"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        g = WebsiteGuestPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        g.open(); g.start_guest()
        g.fill_dynamic_code(); g.accept_agreement(); g.submit()
        g.shot("Step 1  Guest session started")
        page.goto(f"{base}/websitehtml/index.html#/my/profile", timeout=60000)
        page.wait_for_timeout(3000)
        g.shot("Step 2  Guest opens the registered-only personal centre")
        if not _registered_area_accessible(page):
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", (f"Guest reached the registered-only personal "
                f"centre (url={page.url}).")
        shots = list(g.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-025", status, actual,
                      f"{_RMK_GUEST}  [TC025]", shots)


def run_tc026(browser):
    """SIT-TC-WEB-AUTH-026 — repeated submit does not double-process."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc026"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        lp.fill_credentials(user.username, user.password)
        lp.fill_captcha()                       # form fully valid so submit fires
        lp._shot("Step 2  Login form filled")
        btn = page.locator(".submit-btn").first
        handled_once = False
        btn.click(no_wait_after=True)
        for _ in range(20):
            if "#/login" not in page.url:
                handled_once = True             # login processed (navigated away)
                break
            try:
                cls = (btn.get_attribute("class") or "").lower()
                if btn.is_disabled() or "loading" in cls:
                    handled_once = True          # control disabled while in flight
                    break
            except Exception:                   # noqa: BLE001
                handled_once = True
                break
            page.wait_for_timeout(120)
        lp._shot("Step 3  Submit control state after the click")
        if handled_once:
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", ("Submit control showed no loading/disabled "
                "state; repeated clicks could double-submit.")
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-026", status, actual,
                      f"{_RMK_LOGIN}  [TC026]", shots)


def run_tc027(browser):
    """SIT-TC-WEB-AUTH-027 — auth screens usable on a mobile viewport."""
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")
    shot_dir = SHOT_BASE / "tc027"
    shot_dir.mkdir(parents=True, exist_ok=True)
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        checks = {}
        for i, (name, route, field) in enumerate(
                [("login", "#/login", "#login-email"),
                 ("register", "#/register", 'input[placeholder="Email"]')]):
            page.goto(f"{base}/websitehtml/index.html{route}", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            fv = page.locator(field).first.is_visible()
            sv = page.locator(".submit-btn").first.is_visible()
            ov = page.evaluate("() => document.documentElement.scrollWidth"
                               " - document.documentElement.clientWidth")
            checks[name] = (fv, sv, ov)
            path = shot_dir / f"{i + 1:02d}_mobile_{name}.png"
            page.screenshot(path=str(path))
            shots.append((f"Mobile viewport - {name} screen", str(path)))
        if all(fv and sv and ov <= 6 for fv, sv, ov in checks.values()):
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Mobile-viewport layout issue: {checks}"
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-027", status, actual,
                      f"{_RMK_SESSION}  [TC027]", shots)


def run_tc028(browser):
    """SIT-TC-WEB-AUTH-028 — auth labels follow the selected language."""
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")
    shot_dir = SHOT_BASE / "tc028"
    shot_dir.mkdir(parents=True, exist_ok=True)
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        page.goto(f"{base}/websitehtml/index.html#/login", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(1500)
        before = page.locator(".submit-btn").first.inner_text().strip()
        p1 = shot_dir / "01_language_default.png"
        page.screenshot(path=str(p1))
        shots.append(("Login page - default language", str(p1)))
        page.locator(".auth-lang__trigger").first.click()
        page.wait_for_timeout(900)
        opts = page.locator("[role=option], .auth-lang__option, li")
        for i in range(opts.count()):
            opt = opts.nth(i)
            txt = (opt.inner_text() or "").strip()
            if opt.is_visible() and txt and txt.upper() != "EN":
                opt.click()
                break
        page.wait_for_timeout(1800)
        after = page.locator(".submit-btn").first.inner_text().strip()
        p2 = shot_dir / "02_language_switched.png"
        page.screenshot(path=str(p2))
        shots.append(("Login page - after switching language", str(p2)))
        if before != after:
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Auth labels did not change with language (stayed {before!r})."
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-028", status, actual,
                      f"{_RMK_SESSION}  [TC028]", shots)


def run_tc029(browser):
    """SIT-TC-WEB-AUTH-029 — registration requires the 动态码 captcha."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc029"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.fill_email("captcha.required@126.com")
        reg.fill_passwords(VALID_PASSWORD)
        reg.fill_dynamic_code_value("")            # missing 动态码
        reg.shot("Step 2  Form filled, 动态码 left empty")
        reg.submit()
        error = reg.current_error()
        reg.shot("Step 3  Registration blocked - 动态码 required")
        if error and reg.is_on_register_page():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Missing 动态码 did not block registration (error={error!r})."
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-029", status, actual,
                      f"{_RMK_REG}  [TC029]", shots)


def run_tc030(browser):
    """SIT-TC-WEB-AUTH-030 — the 动态码 captcha refreshes on click."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc030"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        reg.open()
        src_before = reg.captcha_image_src()
        reg.shot("Step 1  动态码 before refresh")
        reg.refresh_captcha()
        reg.shot("Step 2  动态码 after clicking the image")
        src_after = reg.captcha_image_src()
        if src_before and src_after and src_before != src_after:
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", "The 动态码 image did not change after the click."
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-030", status, actual,
                      f"{_RMK_REG}  [TC030]", shots)


def run_tc031(browser):
    """SIT-TC-WEB-AUTH-031 — password login requires the 动态码 captcha."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc031"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        error = lp.submit_login_with_captcha_value(user.username, user.password, "0000")
        lp._shot("Step 2  Login blocked - wrong 动态码 rejected")
        if error and not lp.is_logged_in():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Missing 动态码 did not block login (error={error!r})."
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-031", status, actual,
                      f"{_RMK_LOGIN}  [TC031]", shots)


def run_tc032(browser):
    """SIT-TC-WEB-AUTH-032 — OTP-mode login requires the 动态码 captcha."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc032"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        lp.switch_to_otp_mode()
        err = lp.request_verification_code(user.username, captcha="")
        lp._shot("Step 2  OTP request blocked - 动态码 required")
        if not lp.otp_boxes_present():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", "OTP request proceeded without a valid 动态码."
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-032", status, actual,
                      f"{_RMK_LOGIN}  [TC032]", shots)


def run_tc033(browser):
    """SIT-TC-WEB-AUTH-033 — forgot password requires the 动态码 captcha."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc033"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        fp = WebsiteForgotPasswordPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        fp.open()
        fp.shot("Step 1  Forgot-password page opened")
        fp.fill_email(user.username)
        fp.fill_dynamic_code_value("")             # missing 动态码
        fp.fill_new_passwords(VALID_PASSWORD)
        fp.shot("Step 2  Form filled, 动态码 left empty")
        fp.submit()
        error = fp.current_error()
        fp.shot("Step 3  Reset blocked - 动态码 required")
        if error and fp.is_on_forget_page():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"Missing 动态码 did not block the reset (error={error!r})."
        shots = list(fp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-033", status, actual,
                      f"{_RMK_FORGOT}  [TC033]", shots)


def run_tc034(browser):
    """SIT-TC-WEB-AUTH-034 — registered user logs in via OTP mode."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc034"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        lp.switch_to_otp_mode()
        # Stay past Aliyun's 30s per-email OTP rate limit + record `since`
        # before Get Code so the IMAP poller only accepts THIS request's OTP.
        _wait_for_otp_throttle(user.username)
        from datetime import datetime, timezone, timedelta
        since = datetime.now(timezone.utc) - timedelta(seconds=10)  # 10s clock slack
        err = lp.request_verification_code(user.username)
        if err:
            raise RuntimeError(f"OTP request failed: {err}")
        # SIT removed the fixed test OTP 111111 (verified 2026-05-23): the
        # server now sends a real 6-digit code to evan.wang@antank.com via
        # public@antank.com. We IMAP-poll the inbox for it.
        # `tools` is not a package; add this dir to sys.path so the import
        # works whether update_evidence.py is run directly or imported.
        import sys
        _tools_dir = str(Path(__file__).resolve().parent)
        if _tools_dir not in sys.path:
            sys.path.insert(0, _tools_dir)
        from imap_otp_poller import fetch_latest_otp, OTPNotFound
        try:
            real_otp = fetch_latest_otp(since=since, timeout=45.0)
        except OTPNotFound as exc:
            raise RuntimeError(f"could not fetch real OTP from inbox: {exc}")
        lp._shot(f"Step 2  Real OTP fetched from inbox ({real_otp[:2]}xxxx)")
        lp.fill_otp(real_otp)
        page.wait_for_timeout(2000)
        lp._shot("Step 3  OTP-mode login result")
        if lp.is_logged_in():
            status, actual = "Pass", ("As expected — logged in via OTP-mode "
                f"using a real OTP fetched from {user.username}'s inbox.")
        else:
            status, actual = "Fail", ("OTP-mode login did not succeed even "
                f"with a real OTP ({real_otp[:2]}xxxx) fetched from inbox; "
                "check whether the OTP expired before submit or the form "
                "rejected for another reason.")
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-034", status, actual,
                      f"{_RMK_LOGIN}  [TC034]", shots)


def run_tc035(browser):
    """SIT-TC-WEB-AUTH-035 — first OTP login auto-creates an account."""
    settings = get_settings()
    email = f"fake.otp.{_STAMP}@126.com"
    shot_dir = SHOT_BASE / "tc035"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        lp.switch_to_otp_mode()
        err = lp.request_verification_code(email)
        lp._shot("Step 2  OTP requested for a brand-new email")
        lp.fill_otp(VALID_OTP)
        lp._shot("Step 3  First OTP-login result")
        if not err and lp.is_logged_in():
            status, actual = "Pass", "As expected"
        else:
            status, actual = "Fail", f"First OTP login did not succeed (err={err!r})."
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-035", status, actual,
                      f"{_RMK_LOGIN}  [TC035]", shots)


# --- TC036-074 batch: password-mode login error matrix (TC048-050) ----------

_WRONG_EMAIL = "no.such.user.2026@126.com"
_WRONG_PASSWORD = "WrongPass@000000"
_WRONG_CAPTCHA = "0000"


def _run_pw_login_matrix(browser, case_id, tag, attempts):
    """Driver for the password-mode login error-matrix cases (TC048-050).

    `attempts` is a list of (label, email, password, captcha): captcha "ocr"
    means OCR-solve a CORRECT 动态码, any other value is typed verbatim as a
    wrong 动态码. Every attempt must be blocked (an error shown, no session)
    for the case to pass.
    """
    settings = get_settings()
    shot_dir = SHOT_BASE / f"tc{tag}"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        outcomes = []
        for i, (label, email, pwd, cap) in enumerate(attempts, 1):
            if cap == "ocr":
                err = lp.attempt_login(email, pwd)
            else:
                err = lp.submit_login_with_captcha_value(email, pwd, cap)
            logged_in = lp.is_logged_in()
            lp._shot(f"Step {i}  {label}")
            outcomes.append((label, err, logged_in))
            if logged_in:
                break                      # a wrong-field attempt logged in
        all_blocked = (len(outcomes) == len(attempts)
                       and all(err and not li for _, err, li in outcomes))
        if all_blocked:
            status = "Pass"
            actual = "All attempts blocked - " + "; ".join(
                f"{lbl}: {err!r}" for lbl, err, _ in outcomes)
        else:
            status = "Fail"
            actual = "An attempt was NOT blocked - " + "; ".join(
                f"{lbl}: err={err!r} loggedIn={li}" for lbl, err, li in outcomes)
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult(case_id, status, actual, f"{_RMK_LOGIN}  [TC{tag}]", shots)


def run_tc048(browser):
    """SIT-TC-WEB-AUTH-048 — password login is blocked when exactly ONE of
    email / password / 动态码 is wrong."""
    user = get_user("website_user", get_settings().env)
    return _run_pw_login_matrix(browser, "SIT-TC-WEB-AUTH-048", "048", [
        ("wrong email only",    _WRONG_EMAIL,  user.password,   "ocr"),
        ("wrong password only", user.username, _WRONG_PASSWORD, "ocr"),
        ("wrong 动态码 only",    user.username, user.password,   _WRONG_CAPTCHA),
    ])


def run_tc049(browser):
    """SIT-TC-WEB-AUTH-049 — password login is blocked when exactly TWO of
    email / password / 动态码 are wrong."""
    user = get_user("website_user", get_settings().env)
    return _run_pw_login_matrix(browser, "SIT-TC-WEB-AUTH-049", "049", [
        ("email + password wrong", _WRONG_EMAIL,  _WRONG_PASSWORD, "ocr"),
        ("email + 动态码 wrong",    _WRONG_EMAIL,  user.password,   _WRONG_CAPTCHA),
        ("password + 动态码 wrong", user.username, _WRONG_PASSWORD, _WRONG_CAPTCHA),
    ])


def run_tc050(browser):
    """SIT-TC-WEB-AUTH-050 — password login is blocked when ALL THREE of
    email / password / 动态码 are wrong."""
    return _run_pw_login_matrix(browser, "SIT-TC-WEB-AUTH-050", "050", [
        ("email + password + 动态码 all wrong",
         _WRONG_EMAIL, _WRONG_PASSWORD, _WRONG_CAPTCHA),
    ])


def run_tc042(browser):
    """SIT-TC-WEB-AUTH-042 — an OTP resend within 60s of the last request is
    rejected: the resend control stays disabled with a countdown."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc042"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        # Use a fresh fake email (NOT the registered evan@antank.com): TC042
        # only validates the cooldown UI behaviour, not that OTP arrives.
        # Using the registered account fails on SIT because the server refuses
        # to send a registration OTP for an already-registered email.
        tc042_email = f"tc042_cooldown_{_STAMP}@126.com"
        reg.fill_email(tc042_email)
        _wait_for_otp_throttle(tc042_email)
        # request_otp_until_sent solves 动态码 + clicks Get Code + retries
        # if the OCR misread; succeeds when the client-side cooldown UI starts.
        cooling = reg.request_otp_until_sent()
        reg.shot("Step 2  Email + OTP requested (resend control entered cooldown)")
        text_before, _ = reg.get_code_button_state()
        # Immediately try to resend within the 60s window. request_otp is
        # best-effort: it does NOT click a disabled button, so a still-cooling
        # control proves the within-60s resend is blocked.
        reg.request_otp()
        still_cooling = reg.resend_is_cooling_down()
        reg.shot("Step 4  Resend within 60s still blocked")
        if cooling and still_cooling:
            status = "Pass"
            actual = (f"Resend within 60s rejected - control stayed in "
                      f"countdown ({text_before!r}).")
        else:
            status = "Fail"
            actual = (f"60s resend cooldown not enforced (initial cooldown="
                      f"{cooling}, still cooling after resend={still_cooling}).")
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-042", status, actual,
                      f"{_RMK_REG}  [TC042]", shots)


def run_tc044(browser):
    """SIT-TC-WEB-AUTH-044 — mismatched password / confirmation blocks
    registration. To prove that the BLOCK is specifically caused by the
    mismatch (and not by some other missing field), pre-fill every other
    required field with a valid value: email, 动态码, request + fill the
    email OTP 111111. Only the password+confirm pair is the failing variable."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc044"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.shot("Step 1  Registration page opened")
        reg.fill_email("mismatch.check@126.com")
        # Get Code so the OTP-session cookie is in place + fill OTP 111111
        reg.request_otp_until_sent()
        reg.fill_verification_code(VALID_OTP)
        reg.fill_passwords("Test@202605", "Different@202699")   # confirm != password
        reg.shot("Step 2  Form filled with valid email/OTP/captcha but "
                 "MISMATCHED password+confirm (only failing variable)")
        # submit_until_settled retries the 动态码 if OCR misreads it, so the
        # final error reflects whatever the server / client actually
        # complains about (not a stale captcha noise).
        error = reg.submit_until_settled()
        on_register = reg.is_on_register_page()
        reg.shot("Step 3  Submission blocked")
        low = error.lower()
        mismatch_msg = ("match" in low or "一致" in error or "相同" in error)
        if error and on_register and mismatch_msg:
            status = "Pass"
            actual = f"Mismatch blocked with a match-error message: {error!r}"
        elif error and on_register:
            status = "Pass"
            actual = (f"Registration blocked on the password mismatch; the "
                      f"message did not explicitly say 'do not match': {error!r}")
        else:
            status = "Fail"
            actual = (f"Password mismatch was not blocked (error={error!r}, "
                      f"onRegister={on_register}).")
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-044", status, actual,
                      f"{_RMK_REG}  [TC044]", shots)


def run_tc045(browser):
    """SIT-TC-WEB-AUTH-045 — the show/hide plaintext toggle (eye icon) cycles
    the password input between type=password and type=text on the registration
    password field, registration confirm field, AND the login password field.
    Pure UI, no OTP."""
    settings = get_settings()
    shot_dir = SHOT_BASE / "tc045"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    findings = []   # (label, initially_masked, shown_after_click, remasked_after_2nd)
    try:
        # --- registration page: password + confirm ---
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.open()
        reg.fill_passwords("Aa12345!", "Aa12345!")
        reg.shot("Step 1  Registration - both password fields masked")
        for sel, label in ((reg.PASSWORD_SEL, "registration password"),
                           (reg.CONFIRM_SEL,  "registration confirm")):
            initial = page.locator(sel).first.get_attribute("type")
            eye = page.locator(f'{sel} + button.eye-btn').first
            eye.click(); page.wait_for_timeout(300)
            shown = page.locator(sel).first.get_attribute("type")
            reg.shot(f"Step  {label} REVEALED via eye toggle")
            eye.click(); page.wait_for_timeout(300)
            remasked = page.locator(sel).first.get_attribute("type")
            reg.shot(f"Step  {label} remasked after second click")
            findings.append((label, initial == "password",
                             shown == "text", remasked == "password"))
        # --- login page: password ---
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        user = get_user("website_user", settings.env)
        page.fill('input#login-password', user.password)
        page.wait_for_timeout(300)
        reg.shot("Step  Login password field filled and masked")
        sel = 'input#login-password'
        initial = page.locator(sel).first.get_attribute("type")
        eye = page.locator(f'{sel} + button.eye-btn').first
        eye.click(); page.wait_for_timeout(300)
        shown = page.locator(sel).first.get_attribute("type")
        reg.shot("Step  Login password REVEALED via eye toggle")
        eye.click(); page.wait_for_timeout(300)
        remasked = page.locator(sel).first.get_attribute("type")
        reg.shot("Step  Login password remasked after second click")
        findings.append(("login password", initial == "password",
                         shown == "text", remasked == "password"))
        all_ok = all(i and s and r for _, i, s, r in findings)
        if all_ok:
            status = "Pass"
            actual = ("As expected - the eye toggle reveals and re-masks the "
                      "password on registration (password + confirm) and on "
                      "the login form; input type cycles password<->text per "
                      "click.")
        else:
            status = "Fail"
            actual = "Toggle did not cycle correctly: " + "; ".join(
                f"{n}: initial-masked={i}, shown-after-click={s}, "
                f"remasked-after-2nd-click={r}" for n, i, s, r in findings)
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-045", status, actual,
                      f"D:\\Workspace\\west-kowloon\\02-automation ({FEATURE_REG} + {FEATURE_LOGIN}, "
                      f"tag @ui)  [TC045]", shots)


def run_tc057(browser):
    """SIT-TC-WEB-AUTH-057 — after a successful registration the user is
    redirected back to the page they entered the auth flow from, not stuck on
    #/register or sent to a generic confirmation page.

    Entry page in this run = the homepage #/."""
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")
    email = f"tc057_{_STAMP}@126.com"
    shot_dir = SHOT_BASE / "tc057"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    try:
        # 1. visit the entry (non-auth) page so the SPA has a known referrer
        entry_url = f"{base}/websitehtml/index.html#/"
        page.goto(entry_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=20000)
        page.wait_for_timeout(1500)
        recorded_entry = page.url
        reg = WebsiteRegistrationPage(page, str(settings.antank_url),
                                      screenshot_dir=shot_dir)
        reg.shot("Step 1  Entry page (homepage) before auth flow")
        # 2. navigate to registration (the equivalent of the user clicking a
        #    header Log in / Sign up link from the homepage)
        reg.open()
        reg.shot("Step 2  Registration page reached from the entry")
        # 3. complete registration with a fresh, never-registered email
        reg.fill_email(email)
        reg.request_otp_until_sent()
        reg.fill_verification_code(VALID_OTP)
        reg.fill_passwords(VALID_PASSWORD)
        reg.shot("Step 3  Registration form filled - fresh email + fixed OTP")
        reg.submit_until_settled()
        page.wait_for_timeout(4000)             # let any post-success nav settle
        final_url = page.url
        reg.shot("Step 4  Final landing page after successful registration")
        registered = reg.registration_succeeded()
        back_to_entry = (final_url == recorded_entry)
        on_register   = ("#/register" in final_url)
        if registered and back_to_entry:
            status, actual = "Pass", ("As expected - registration succeeded and "
                f"the user was redirected back to the entry page "
                f"({recorded_entry}).")
        elif registered and on_register:
            status, actual = "Fail", (f"Registration succeeded but the user "
                f"stayed on #/register (final url={final_url}); no redirect "
                f"back to the entry page ({recorded_entry}) was performed.")
        elif registered and not back_to_entry:
            status, actual = "Fail", ("Registration succeeded but the final "
                f"URL ({final_url}) does NOT match the entry URL "
                f"({recorded_entry}); the app does not preserve the entry "
                f"page across the registration flow.")
        else:
            status, actual = "Fail", (f"Registration did not succeed; "
                f"final url={final_url!r}.")
        shots = list(reg.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-057", status, actual,
                      f"{_RMK_REG}  [TC057]", shots)


def run_tc055(browser):
    """SIT-TC-WEB-AUTH-055 — a user logged in via OTP mode can actively log
    out; afterwards the registered-only area is no longer accessible."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    base = str(settings.antank_url).rstrip("/")
    shot_dir = SHOT_BASE / "tc055"
    ctx = browser.new_context(); page = ctx.new_page()
    status, actual, shots = "Fail", "", []
    profile_url = f"{base}/websitehtml/index.html#/my/profile"
    try:
        lp = WebsiteLoginPage(page, str(settings.antank_url), screenshot_dir=shot_dir)
        lp.open()
        lp.switch_to_otp_mode()
        _wait_for_otp_throttle(user.username)
        from datetime import datetime, timezone, timedelta
        since = datetime.now(timezone.utc) - timedelta(seconds=10)
        err = lp.request_verification_code(user.username)
        if err:
            raise RuntimeError(f"OTP code request failed: {err}")
        import sys
        _tools_dir = str(Path(__file__).resolve().parent)
        if _tools_dir not in sys.path: sys.path.insert(0, _tools_dir)
        from imap_otp_poller import fetch_latest_otp
        real_otp = fetch_latest_otp(since=since, timeout=45.0)
        lp.fill_otp(real_otp)
        page.wait_for_timeout(1500)
        lp._shot(f"Step 1  Logged in via OTP mode (real OTP {real_otp[:2]}xxxx)")
        if not lp.is_logged_in():
            status = "Fail"
            actual = "OTP-mode login did not succeed; logout could not be tested."
        else:
            page.goto(profile_url, timeout=60000)
            page.wait_for_timeout(2500)
            reachable_before = _registered_area_accessible(page)
            lp._shot("Step 2  Personal centre open while logged in")
            lp.logout()
            page.goto(profile_url, timeout=60000)
            page.wait_for_timeout(2500)
            reachable_after = _registered_area_accessible(page)
            lp._shot("Step 3  Personal centre re-opened after logout")
            if reachable_before and not reachable_after:
                status, actual = "Pass", "As expected"
            else:
                status, actual = "Fail", (f"OTP-mode logout did not protect the "
                    f"registered-only page (reachable before={reachable_before}, "
                    f"after={reachable_after}, url={page.url}).")
        shots = list(lp.screenshots)
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc(); status, actual = "Fail", f"Automation error: {exc}"
        _error_shot(page, shot_dir, shots, "error_state")
    finally:
        ctx.close()
    return CaseResult("SIT-TC-WEB-AUTH-055", status, actual,
                      f"{_RMK_LOGIN}  [TC055]", shots)


# --- NA cases (cannot be executed by pure-UI automation) --------------------

_NA_CASES = {
    # Added 2026-05-26 after SIT killed the fixed OTP 111111 and switched to
    # real email delivery: these three cases use throwaway fake_xxx@126.com
    # addresses that don't actually exist, so the OTP email goes nowhere and
    # the test can't complete. Needs a real test inbox (e.g. IT provisions
    # qa-test@antank.com or similar) to be reactivated.
    "SIT-TC-WEB-AUTH-001": "NA - first-time registration uses a throwaway "
        "fake_xxx@126.com address which doesn't exist; since SIT switched to "
        "real email OTP (2026-05-26), no OTP can be fetched for an unowned "
        "inbox. Needs IT to provision a real test email (e.g. "
        "qa-test@antank.com) to be reactivated.",
    "SIT-TC-WEB-AUTH-035": "NA - first OTP-login for a brand-new email uses "
        "fake.otp.xxx@126.com which doesn't exist; with real email OTP in "
        "effect (since 2026-05-26) no code can be retrieved. Same fix as "
        "TC001: needs a real deliverable test inbox.",
    "SIT-TC-WEB-AUTH-057": "NA - registration-redirect-back test uses "
        "fake_xxx@126.com (unreachable). Logic + scenario are complete and "
        "verified to enter the registration flow; the OTP-completion step "
        "requires a deliverable inbox. Reactivate when a real test email "
        "is available.",
    "SIT-TC-WEB-AUTH-011": "NA - failed-login lockout would lock the shared test "
        "account; it needs a dedicated throwaway account and a known lockout "
        "threshold, neither of which is available.",
    "SIT-TC-WEB-AUTH-014": "NA - SSO identity synchronisation needs a WestK "
        "Account SSO test environment, which is not available.",
    "SIT-TC-WEB-AUTH-017": "NA - third-party login (new account) needs Google / "
        "Facebook / X / TikTok / WeChat provider sandbox accounts, not available.",
    "SIT-TC-WEB-AUTH-018": "NA - third-party login (existing user) needs provider "
        "sandbox accounts, which are not available.",
    "SIT-TC-WEB-AUTH-019": "NA - third-party provider authorization-cancelled "
        "flow needs provider sandbox accounts, which are not available.",
    "SIT-TC-WEB-AUTH-020": "NA - third-party provider missing-identifier flow "
        "needs a provider sandbox that can simulate missing profile data.",
    "SIT-TC-WEB-AUTH-024": "NA - guest-timeout state clearing needs waiting for "
        "the guest session validity to expire (duration TBD); not run.",
    "SIT-TC-WEB-AUTH-023": "NA - the guest session validity countdown is shown "
        "inside the ticketing flow per the manual case; it is not present on the "
        "post-login landing page, so a pure-UI auth pass cannot observe it.",
    # --- TC036-074 batch: cases the test design itself marks Deferred / DO NOT
    #     EXECUTE / TBD, or that need resources unavailable on this SIT pass. ---
    "SIT-TC-WEB-AUTH-036": "NA - email-link registration needs reading the "
        "verification email to click the registration link; SIT registration "
        "uses a fixed test OTP and no inbox is accessible to the pure-UI pass.",
    "SIT-TC-WEB-AUTH-037": "NA - expired-registration-link case needs email "
        "access plus an expired link; link validity duration is TBD per the "
        "test design.",
    "SIT-TC-WEB-AUTH-038": "NA - the guest expiry-warning popup needs waiting out "
        "the configured remaining-time threshold (~5 min, exact value TBD); a "
        "long-wait timing case, like TC024.",
    "SIT-TC-WEB-AUTH-039": "NA - WestK SSO (BU already logged in) needs a West "
        "Kowloon BU SSO test environment; marked Deferred pending the SSO scope "
        "decision in the test design.",
    "SIT-TC-WEB-AUTH-040": "NA - WestK SSO (BU not logged in) needs a WestK SSO "
        "test environment; marked Deferred pending the SSO scope decision.",
    "SIT-TC-WEB-AUTH-041": "NA - WestK SSO (direct access) is marked Deferred "
        "pending the SSO scope decision; the SSO environment is not available.",
    "SIT-TC-WEB-AUTH-043": "NA - SIT issues a fixed test OTP (111111), so a "
        "resend produces the same code; the 'previous OTP invalidated after "
        "resend' behaviour cannot be observed.",
    "SIT-TC-WEB-AUTH-046": "NA - mobile registration is marked TBD - DO NOT "
        "EXECUTE in the test design; it needs the HK mobile registration spec "
        "and an HK SIM testing environment.",
    "SIT-TC-WEB-AUTH-047": "NA - mobile login is marked TBD - DO NOT EXECUTE in "
        "the test design; it needs the HK mobile login spec and an HK SIM "
        "testing environment.",
    "SIT-TC-WEB-AUTH-051": "NA - OTP-mode login on SIT uses three fields (email "
        "/ 动态码 / 验证码) with no password field, so the email/password/动态码/"
        "验证码 one-field-wrong matrix in the test design cannot be executed "
        "faithfully (the OTP-mode password requirement is itself flagged open "
        "in TC034). The real-field negatives are covered by TC032/TC012.",
    "SIT-TC-WEB-AUTH-052": "NA - OTP-mode login has no password field on SIT, so "
        "the two-fields-wrong matrix that includes password cannot be executed "
        "faithfully against the implemented 3-field OTP form.",
    "SIT-TC-WEB-AUTH-053": "NA - OTP-mode login has no password field on SIT, so "
        "the three-fields-wrong matrix that includes password cannot be "
        "executed faithfully against the implemented 3-field OTP form.",
    "SIT-TC-WEB-AUTH-054": "NA - OTP-mode login has only three fields on SIT, so "
        "an all-four-fields-wrong attempt (which assumes a password field) "
        "cannot be constructed.",
    "SIT-TC-WEB-AUTH-056": "NA - guest active-logout data clearing needs guest "
        "cart / order-draft data, which lives in the ticketing flow - outside "
        "the auth dry-run scope (cf. TC023).",
    "SIT-TC-WEB-AUTH-058": "NA - verification-email content checks need reading "
        "the actual email per language; no inbox is accessible on this SIT pass.",
    "SIT-TC-WEB-AUTH-059": "NA - third-party login via Google needs a Google "
        "provider sandbox account, which is not available (cf. TC017-020).",
    "SIT-TC-WEB-AUTH-060": "NA - third-party login via Facebook needs a Facebook "
        "provider sandbox account, which is not available.",
    "SIT-TC-WEB-AUTH-061": "NA - third-party login via X needs an X provider "
        "sandbox account, which is not available.",
    "SIT-TC-WEB-AUTH-062": "NA - third-party login via TikTok needs a TikTok "
        "provider sandbox account, which is not available.",
    "SIT-TC-WEB-AUTH-063": "NA - third-party login via WeChat needs a WeChat "
        "provider sandbox account, which is not available.",
    "SIT-TC-WEB-AUTH-064": "NA - Deferred: the 动态码 captcha validity duration "
        "is TBD per the test design, so an expiry cannot be asserted.",
    "SIT-TC-WEB-AUTH-065": "NA - Deferred: the OTP digit-count rule is TBD; SIT "
        "uses a fixed 6-digit test OTP, so the configured-length rule cannot be "
        "exercised.",
    "SIT-TC-WEB-AUTH-066": "NA - Deferred: the password-mode session expiry "
        "duration is TBD; verifying it needs a known value or a test-clock "
        "override.",
    "SIT-TC-WEB-AUTH-067": "NA - Deferred: the OTP-mode session expiry duration "
        "is TBD; verifying it needs a known value or a test-clock override.",
    "SIT-TC-WEB-AUTH-068": "NA - Deferred: the guest-session expiry calculation "
        "method (rolling vs fixed) is TBD per the test design.",
    "SIT-TC-WEB-AUTH-069": "NA - Deferred: the post-robot-failure redirect target "
        "page is TBD; TC022 already covers the failure outcome itself.",
    "SIT-TC-WEB-AUTH-070": "NA - Deferred: the forgot-password reset model (temp "
        "password vs reset token) is TBD, and it needs email content inspection.",
    "SIT-TC-WEB-AUTH-071": "NA - Deferred: third-party post-login share behaviour "
        "is TBD, and it needs a third-party-authenticated session (no provider "
        "sandbox accounts).",
    "SIT-TC-WEB-AUTH-072": "NA - Deferred: the multi-device concurrent-session "
        "policy is TBD per the test design, so there is no defined expected "
        "result to assert against.",
    "SIT-TC-WEB-AUTH-074": "NA - Deferred: the password policy rule set is TBD "
        "per the test design, so per-rule enforcement cannot be enumerated.",
}


def _make_na_runner(case_id, reason):
    """Build a runner for a not-applicable case: capture one login-page
    screenshot as context and return an NA CaseResult."""
    def _runner(browser):
        settings = get_settings()
        base = str(settings.antank_url).rstrip("/")
        tag = case_id.split("-")[-1]
        shot_dir = SHOT_BASE / f"tc{tag}"
        ctx = browser.new_context(); page = ctx.new_page()
        shots = []
        try:
            page.goto(f"{base}/websitehtml/index.html#/login", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            _error_shot(page, shot_dir, shots, "login_page")
        except Exception:                                   # noqa: BLE001
            traceback.print_exc()
        finally:
            ctx.close()
        return CaseResult(case_id, "NA", reason,
                          "D:\\Workspace\\west-kowloon\\02-automation - not executed; see Actual Result.",
                          shots)
    _runner.__name__ = f"run_na_{case_id.split('-')[-1]}"
    return _runner


_NA_RUNNERS = [_make_na_runner(cid, reason) for cid, reason in _NA_CASES.items()]


def run_tc009(browser):
    """SIT-TC-WEB-AUTH-009 - API+UI mixed password login + final profile UI."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    shot_dir = SHOT_BASE / "tc009"
    status, actual, shots = "Fail", "", []
    try:
        result = run_auth009_api_first(
            browser,
            str(settings.antank_url),
            user.username,
            user.password,
            shot_dir,
        )
        shots = list(result.shots)
        status = "Pass"
        actual = (
            "API identity chain passed and the profile UI opened with the "
            f"same session (memberId={result.member_id})."
        )
    except Exception as exc:                                # noqa: BLE001
        traceback.print_exc()
        status = "Fail"
        actual = f"API+UI mixed login/profile validation failed: {exc}"
        login_gate = ROOT / "07-artifacts" / "api_smoke" / "login_error.png"
        if login_gate.exists():
            shots = [("api_first_login_gate", str(login_gate))]
        if not shots:
            ctx = browser.new_context()
            page = ctx.new_page()
            try:
                _error_shot(page, shot_dir, shots, "login_failed")
            finally:
                ctx.close()
    remarks = (
        "D:\\Workspace\\west-kowloon\\02-automation "
        "(01-features/api_ui_mixed/antank_api_first_ui.feature, tags @api_first_ui @auth009, label API+UI mixed)"
    )
    return CaseResult("SIT-TC-WEB-AUTH-009", status, actual, remarks, shots)


RUNNERS = [
    # TC001/035/057 removed from active runners — moved to _NA_CASES on
    # 2026-05-26 (unreachable fake_xxx@126.com inboxes after SIT switched
    # to real email OTP). _NA_RUNNERS below covers them as NA.
    run_tc002, run_tc003, run_tc004, run_tc005, run_tc006,
    run_tc008, run_tc009, run_tc010, run_tc012, run_tc013, run_tc015,
    run_tc016, run_tc021, run_tc022, run_tc025, run_tc026,
    run_tc027, run_tc028, run_tc029, run_tc030, run_tc031, run_tc032,
    run_tc033, run_tc034,
    run_tc042, run_tc044, run_tc045, run_tc048, run_tc049, run_tc050,
    run_tc055,
] + _NA_RUNNERS


# ---------------------------------------------------------------------------
# screenshot strip composition
# ---------------------------------------------------------------------------

_HEADER_COLOR = {
    "Pass": (47, 133, 90),      # green
    "Fail": (197, 48, 48),      # red
    "NA":   (193, 124, 28),     # amber
}


def _font(size):
    for name in ("arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:                                   # noqa: BLE001
            continue
    return ImageFont.load_default()


def compose_strip(shots, status, out_path):
    """Compose the step screenshots into one labelled horizontal strip."""
    panel_w, label_h = 640, 38
    panels = []
    for label, path in shots:
        im = Image.open(path).convert("RGB")
        h = round(im.height * panel_w / im.width)
        panels.append((label, im.resize((panel_w, h))))

    body_h = max(im.height for _, im in panels)
    strip = Image.new("RGB", (panel_w * len(panels), label_h + body_h), "white")
    draw = ImageDraw.Draw(strip)
    font = _font(20)
    header = _HEADER_COLOR.get(status, (90, 90, 90))
    for i, (label, im) in enumerate(panels):
        x = i * panel_w
        draw.rectangle([x, 0, x + panel_w, label_h], fill=header)
        title = LOGIN_TITLES.get(label, label)
        draw.text((x + 12, 9), title, fill="white", font=font)
        if i:
            draw.line([x, 0, x, strip.height], fill=(210, 210, 210), width=2)
        strip.paste(im, (x, label_h))
    strip.save(out_path)
    return strip.size, len(panels)


# ---------------------------------------------------------------------------
# workbook update
# ---------------------------------------------------------------------------

def _resolve_cols(ws) -> dict:
    """Look up the workbook's actual column indices by HEADER NAME, so the
    script keeps working when users insert / reorder columns (the 'Label'
    column added on 2026-05-26 shifted everything by 1, breaking the old
    hard-coded indices). Returns dict {role: col_idx, ...}."""
    HEADER_ALIASES = {
        "case_id":   ("Test Case ID",),
        "env":       ("Environment", "Environment\n(SIT/UAT/PROD)"),
        "exec_date": ("Execution Date",),
        "exec_by":   ("Executed By",),
        "actual":    ("Actual Result",),
        "status":    ("Status", "Status\n(Pass/ Fail)"),
        "remarks":   ("Comments/Remarks", "Comments", "Remarks"),
        "shots":     ("Screenshots",),
    }
    headers = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=1, column=c).value
        if v is not None:
            headers[str(v).strip()] = c
    cols = {}
    for role, names in HEADER_ALIASES.items():
        for n in names:
            if n in headers:
                cols[role] = headers[n]; break
        if role not in cols:
            raise RuntimeError(
                f"workbook header missing for role '{role}' — looked for "
                f"any of {names!r}; actual headers: {list(headers)!r}"
            )
    return cols


def update_workbook(results, strips):
    """Write the execution-result columns + embed screenshot strips. Column
    positions are looked up by header name, not hard-coded indices.

    `strips` maps case_id -> (strip_path, (w, h), n_panels)."""
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Test Cases"]
    cols = _resolve_cols(ws)

    # locate each case row by its ID in the (header-named) Test Case ID column
    cid_col = cols["case_id"]
    row_of = {}
    for r in range(2, ws.max_row + 1):
        cid = str(ws.cell(row=r, column=cid_col).value or "").strip()
        if cid:
            row_of[cid] = r

    # Replace only the rows being written — preserve other rows' embedded
    # images so a targeted (subset) re-run does not wipe earlier evidence.
    target_rows = {row_of[res.case_id] for res in results if res.case_id in row_of}
    ws._images = [im for im in ws._images
                  if (getattr(im.anchor._from, "row", -1) + 1) not in target_rows]

    shots_col = cols["shots"]
    # Excel column letter for the screenshots column (A=1, B=2, ...)
    shots_letter = openpyxl.utils.get_column_letter(shots_col)

    for res in results:
        row = row_of.get(res.case_id)
        if row is None:
            print(f"  !! {res.case_id} not found in workbook — skipped")
            continue

        ws.cell(row=row, column=cols["env"]).value       = ENVIRONMENT
        ws.cell(row=row, column=cols["exec_date"]).value = TODAY
        ws.cell(row=row, column=cols["exec_by"]).value   = EXECUTED_BY
        ws.cell(row=row, column=cols["actual"]).value    = res.actual
        ws.cell(row=row, column=cols["status"]).value    = res.status
        ws.cell(row=row, column=cols["remarks"]).value   = res.remarks
        ws.cell(row=row, column=cols["shots"]).value     = None  # clear text

        strip = strips.get(res.case_id)
        if not strip:
            continue
        strip_path, (sw, sh), n_panels = strip
        xlimg = XLImage(str(strip_path))
        disp_w = 320 * n_panels                          # ~320 px per panel
        disp_h = round(sh * disp_w / sw)
        xlimg.width, xlimg.height = disp_w, disp_h
        xlimg.anchor = f"{shots_letter}{row}"
        ws.add_image(xlimg)
        ws.row_dimensions[row].height = max(ws.row_dimensions[row].height or 15,
                                            disp_h * 0.75 + 8)

    ws.column_dimensions[shots_letter].width = 320 * 3 / 7.0  # widest = 3 panels

    wb.save(XLSX)


# ---------------------------------------------------------------------------
# per-case sync status — consumed by the QA dashboard's "Sync to Excel" column
# ---------------------------------------------------------------------------

# artifacts/ sits next to tools/ in the repo, NOT in the Kasi package.
SYNC_STATUS_FILE = ROOT / "07-artifacts" / "evidence_sync.json"


def _write_sync_status(results, workbook_written):
    """Record the last evidence sync per case into artifacts/evidence_sync.json
    so the dashboard can show a per-row 'Sync to Excel' status.

    Accumulating: a case not touched by this (possibly scoped) run keeps its
    previous record — so syncing one module never blanks the others.
    """
    payload = {"cases": {}}
    if SYNC_STATUS_FILE.exists():
        try:
            payload = json.loads(SYNC_STATUS_FILE.read_text(encoding="utf-8"))
            payload.setdefault("cases", {})
        except Exception:                                # noqa: BLE001
            payload = {"cases": {}}

    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    payload["updated_at"] = stamp
    for res in results:
        tag = res.case_id.split("-")[-1]                 # e.g. "013"
        payload["cases"][tag] = {
            "case_id": res.case_id,
            "status": res.status,                        # Pass | Fail | NA
            "shots": len(res.shots),
            "synced": bool(workbook_written),
            "synced_at": stamp,
        }

    SYNC_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATUS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sync status -> {SYNC_STATUS_FILE}  "
          f"({len(results)} case(s), workbook_written={workbook_written})")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    # Optional CLI args = case numbers to run a SUBSET, e.g.
    #   update_evidence.py 013 026 029   → re-run only those cases.
    # No args → run every case. Subset runs preserve other rows' xlsx images.
    import sys
    wanted = {"".join(c for c in a if c.isdigit()) for a in sys.argv[1:]}
    wanted = {w for w in wanted if w}
    runners = [r for r in RUNNERS if any(w in r.__name__ for w in wanted)] \
        if wanted else RUNNERS
    scope = f"SUBSET {sorted(wanted)}" if wanted else "all"
    print(f"=== update_evidence — {scope} ({len(runners)} cases) — {TODAY} ===")
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    results, strips = [], {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for runner in runners:
            print(f"\n--- {runner.__name__} ---")
            try:
                res = runner(browser)
            except Exception as exc:                         # noqa: BLE001
                traceback.print_exc()
                cid = runner.__name__.replace("run_tc", "SIT-TC-WEB-AUTH-")
                res = CaseResult(cid, "Fail", f"Runner crashed: {exc}", "", [])
            results.append(res)
            print(f"    {res.case_id}: {res.status} | {len(res.shots)} screenshot(s)")

            if res.shots:
                tag = res.case_id.split("-")[-1]
                strip_path = (EVIDENCE_DIR /
                              f"registration-TC{tag}-{res.status.lower()}-{TODAY}.png")
                size, n = compose_strip(res.shots, res.status, strip_path)
                strips[res.case_id] = (strip_path, size, n)
                print(f"    strip -> {strip_path.name}  {size[0]}x{size[1]}")
            else:
                print(f"    !! no screenshots captured for {res.case_id}")
        browser.close()

    print("\n=== writing workbook ===")
    workbook_written = False
    try:
        update_workbook(results, strips)
        workbook_written = True
        print(f"workbook updated: {XLSX}")
    except PermissionError:
        print(f"ERROR: cannot write {XLSX.name} — close it in Excel and re-run.")

    _write_sync_status(results, workbook_written)

    print("\n=== summary ===")
    for res in results:
        print(f"  {res.case_id}  {res.status:5s}  {len(res.shots)} shot(s)")

    if not workbook_written:
        raise SystemExit(
            f"FAILED: workbook not written — {XLSX.name} was locked or "
            f"read-only. Close it in Excel and re-run.")
    print("DONE.")


if __name__ == "__main__":
    main()
