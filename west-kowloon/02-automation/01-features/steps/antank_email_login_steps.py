"""
Step definitions for antank_email_login.feature.

Converts manual test case SIT-TC-WEB-AUTH-009 ("Successful password-mode
login") from the Kasi requirement package into a pure-UI Playwright test.

Uses Playwright (context.page) which is set up in environment.py
before_scenario(). The 动态码 image captcha is solved by OCR with retry
inside WebsiteLoginPage (same approach as antank_login_page.py).

Test data (the registered Website account) lives in config/users.yml under
<env>.website_user and is read via get_user().
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from behave import given, when, then

from test_automation.config import get_settings, get_user
from test_automation.web import WebsiteLoginPage

# Allow `from imap_otp_poller import ...` from 01-features/steps/*.py — the
# poller lives in tools/ and reads ALIMAIL_PASSWORD from env (or HKCU
# fallback on Windows so the dashboard backend can pick it up without
# restart).
_TOOLS_DIR = Path(__file__).resolve().parents[2] / "04-tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# Folder where the success screenshot is stored (created on demand).
# __file__ = .../west-kowloon/02-automation/01-features/steps/antank_email_login_steps.py
_SCREENSHOT_DIR = Path(__file__).resolve().parents[2] / "07-artifacts" / "screenshots"


@given("the Website login page is open")
def step_open_login_page(context):
    """Manual step 1 — open the login page (email/password mode is the default tab)."""
    settings = get_settings()
    context.login_page = WebsiteLoginPage(context.page, str(settings.antank_url))
    context.login_page.open()


@when("I enter the registered email and password")
def step_enter_credentials(context):
    """Manual step 3 (part) — fill the registered email + password in the UI."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    context.login_page.fill_credentials(user.username, user.password)


@when("I submit the login form, solving the 动态码 captcha")
def step_submit_with_captcha(context):
    """Manual step 3 (动态码) + step 4 — OCR-solve the image captcha and click
    "Log in"; the captcha is retried automatically if OCR misreads it."""
    context.login_page.submit_with_captcha()


@then("login succeeds and the home page is shown")
def step_assert_logged_in(context):
    """Expected result — login succeeds and the authenticated home page loads."""
    assert context.login_page.is_logged_in(), \
        "Expected to leave the #/login route after a successful login"
    assert context.login_page.is_home_page(), \
        "Expected the authenticated home page to be shown after login"


@then("a screenshot of the logged-in page is saved")
def step_save_screenshot(context):
    """Save a screenshot of the final logged-in page into artifacts/screenshots/."""
    _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = _SCREENSHOT_DIR / f"email_login_success_{timestamp}.png"
    context.login_page.save_screenshot(str(path))
    print(f"  [screenshot] logged-in page saved -> {path}")


# --- TC010 / TC012  negative login -------------------------------------------

_WRONG_PASSWORD = "WrongPass@000000"
_UNKNOWN_EMAIL = "no.such.user.2026@126.com"


@when("I submit the login form with a wrong password")
def step_login_wrong_password(context):
    """TC010 — registered email + wrong password (动态码 OCR-solved with retry)."""
    user = get_user("website_user", get_settings().env)
    context.login_error = context.login_page.attempt_login(user.username, _WRONG_PASSWORD)


@when("I submit the login form with an unregistered email")
def step_login_unknown_account(context):
    """TC012 — an email that is not registered, with any password."""
    context.login_error = context.login_page.attempt_login(_UNKNOWN_EMAIL, _WRONG_PASSWORD)


# Per 2026-06-10 PRD §用户邮箱/手机+密码登录 (updated 2026-06-12), wrong-password
# AND unknown-account must both surface the SAME generic error so the response
# does not leak whether the account exists. The PRD-cited wording is
# "用户名或密码错误" / "用戶名或密碼錯誤" / "Username or password incorrect"; SIT
# in practice serves variants like "Incorrect username or password!" (different
# word order, trailing !). The check below accepts any of these surface forms
# but still rejects account-enumeration leaks via the second assertion.
_GENERIC_LOGIN_ERROR_LEAK_HINTS = (
    "not registered", "not found", "does not exist", "未注册", "未註冊",
    "go register", "去注册", "去註冊",
)


def _matches_generic_login_error(msg: str) -> bool:
    """True if the error string is plausibly the PRD-mandated generic error."""
    if not msg:
        return False
    if "用户名或密码" in msg or "用戶名或密碼" in msg:
        return True
    lower = msg.lower()
    if "username" in lower and "password" in lower and (
            "incorrect" in lower or "error" in lower or "wrong" in lower):
        return True
    return False


@then("login is rejected and the user stays unauthenticated")
def step_assert_login_rejected(context):
    """TC010 / TC012 expected result — login rejected, still on #/login.

    UPDATED 2026-06-12 per 2026-06-10 PRD: both wrong-password (TC010) and
    unknown-account (TC012) MUST surface the same generic "Username or
    password incorrect" wording (one of 3 languages). The product MUST NOT
    differentiate "account does not exist" vs "wrong password" — no
    account-enumeration leak.
    """
    assert context.login_error, "Expected a rejection message"
    assert not context.login_page.is_logged_in(), \
        "Expected to stay unauthenticated on the #/login route"
    print(f"  [login rejected] message -> {context.login_error!r}")
    msg = str(context.login_error)
    assert _matches_generic_login_error(msg), (
        f"2026-06-10 PRD: expected the generic 'Username or password "
        f"incorrect' wording (zh-CN / zh-HK / en variant). Got: {msg!r}")
    leak = next((h for h in _GENERIC_LOGIN_ERROR_LEAK_HINTS if h.lower() in msg.lower()), None)
    assert leak is None, (
        f"2026-06-10 PRD: response leaks account state ({leak!r}); must use "
        f"the generic wording instead. Got: {msg!r}")
    print(f"  [PRD-2026-06-10] generic wording accepted (no enumeration leak)")


# --- TC031  password login requires the 动态码 -------------------------------

@when("I submit valid credentials with a missing or wrong 动态码")
def step_login_missing_captcha(context):
    """TC031 — valid email + password but a wrong 动态码 (the server rejects
    it; an empty 动态码 is blocked client-side with no message)."""
    user = get_user("website_user", get_settings().env)
    context.login_error = context.login_page.submit_login_with_captcha_value(
        user.username, user.password, "0000")


@then("login is blocked with a captcha error")
def step_assert_login_captcha_error(context):
    """TC031 expected result — login blocked, a 动态码/captcha error shown."""
    assert context.login_error, "Expected a captcha error message"
    assert not context.login_page.is_logged_in(), "Expected login to be blocked"
    print(f"  [TC031] captcha error -> {context.login_error!r}")


# --- TC026  duplicate submit / loading state ---------------------------------

@when("I fill the login form and click submit repeatedly")
def step_login_duplicate_submit(context):
    """TC026 — fill the form, then click submit several times in quick
    succession; sample the submit control's disabled/loading state."""
    user = get_user("website_user", get_settings().env)
    context.login_page.fill_credentials(user.username, user.password)
    btn = context.page.locator(".submit-btn").first
    context.tc026_disabled_seen = False
    for _ in range(8):
        try:
            btn.click(timeout=1000, no_wait_after=True)
        except Exception:
            pass
        cls = (btn.get_attribute("class") or "").lower()
        if btn.is_disabled() or "loading" in cls or "disabled" in cls:
            context.tc026_disabled_seen = True
            break
        context.page.wait_for_timeout(120)


@then("the submit control shows a loading or disabled state")
def step_assert_loading_state(context):
    """TC026 expected result — the submit control disables / shows loading so
    repeated clicks cannot double-submit."""
    assert context.tc026_disabled_seen, \
        "Expected the submit button to enter a disabled/loading state on submit"
    print("  [TC026] submit control entered a disabled/loading state")


# --- TC032  OTP-mode login requires the 动态码 -------------------------------

@when("I request an OTP-login code with a missing 动态码")
def step_otp_request_no_captcha(context):
    """TC032 — switch to OTP mode, request the code with an empty 动态码."""
    user = get_user("website_user", get_settings().env)
    context.login_page.switch_to_otp_mode()
    context.login_error = context.login_page.request_verification_code(
        user.username, captcha="")


@then("the OTP code is not sent and a captcha error is shown")
def step_assert_otp_captcha_error(context):
    """TC032 expected result — the OTP entry boxes do NOT appear without a
    valid 动态码 (the code request is blocked)."""
    assert not context.login_page.otp_boxes_present(), \
        "Expected the OTP entry boxes NOT to appear without a valid 动态码"
    print(f"  [TC032] OTP code not sent; message -> {context.login_error!r}")


# --- TC034 / TC035  OTP-mode login -------------------------------------------

@when("I log in through OTP mode with the registered email")
def step_otp_login_registered(context):
    """TC034 — OTP-mode login. SIT removed the fixed OTP 111111 (since
    2026-05-23) and now sends a real OTP to the registered email; we
    IMAP-poll that inbox for it."""
    from imap_otp_poller import fetch_latest_otp, wait_for_otp_throttle
    user = get_user("website_user", get_settings().env)
    context.login_page.switch_to_otp_mode()
    wait_for_otp_throttle(user.username)
    since = datetime.now(timezone.utc) - timedelta(seconds=10)
    err = context.login_page.request_verification_code(user.username)
    assert not err, f"Expected the OTP request to succeed, got {err!r}"
    real_otp = fetch_latest_otp(since=since, timeout=45.0)
    context.login_page.fill_otp(real_otp)


@when("I log in through OTP mode with a brand-new email")
def step_otp_login_new_email(context):
    """TC035 — OTP-mode login with a never-registered email; the first OTP
    login is expected to auto-create the account.

    OTP delivery limitation: SIT removed the fixed test OTP (111111) on
    2026-05-23. Probed 2026-06-09: plus-addressed evan.wang aliases are
    rejected by the SIT login-form's email-format regex, so the only
    "brand-new" email we can submit is from an uncontrolled domain whose
    inbox we cannot poll. End-to-end pass requires a SIT fixed-OTP backdoor
    or a controlled catch-all domain.
    """
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    context.tc035_email = f"fake_{stamp}@126.com"
    context.login_page.switch_to_otp_mode()
    err = context.login_page.request_verification_code(context.tc035_email)
    assert not err, f"Expected the OTP request to succeed, got {err!r}"
    context.login_page.fill_otp("111111")


# --- TC048 / 049 / 050  password-login error matrix --------------------------

def _run_login_matrix(context, attempts):
    """Submit each (label, email, password, captcha) password-mode login and
    record (label, error, logged_in). captcha "ocr" → OCR-solve a correct
    动态码; any other value is typed verbatim as a wrong 动态码."""
    lp = context.login_page
    context.matrix = []
    for label, email, pwd, cap in attempts:
        if cap == "ocr":
            err = lp.attempt_login(email, pwd)
        else:
            err = lp.submit_login_with_captcha_value(email, pwd, cap)
        context.matrix.append((label, err, lp.is_logged_in()))


@when("I submit password-mode logins each with one field wrong")
def step_login_one_field_wrong(context):
    """TC048 — exactly one of email / password / 动态码 wrong per attempt."""
    user = get_user("website_user", get_settings().env)
    _run_login_matrix(context, [
        ("wrong email", _UNKNOWN_EMAIL, user.password, "ocr"),
        ("wrong password", user.username, _WRONG_PASSWORD, "ocr"),
        ("wrong 动态码", user.username, user.password, "0000"),
    ])


@when("I submit password-mode logins each with two fields wrong")
def step_login_two_fields_wrong(context):
    """TC049 — exactly two of email / password / 动态码 wrong per attempt."""
    user = get_user("website_user", get_settings().env)
    _run_login_matrix(context, [
        ("email + password wrong", _UNKNOWN_EMAIL, _WRONG_PASSWORD, "ocr"),
        ("email + 动态码 wrong", _UNKNOWN_EMAIL, user.password, "0000"),
        ("password + 动态码 wrong", user.username, _WRONG_PASSWORD, "0000"),
    ])


@when("I submit a password-mode login with all three fields wrong")
def step_login_all_fields_wrong(context):
    """TC050 — email / password / 动态码 all wrong in one attempt."""
    _run_login_matrix(context, [
        ("email + password + 动态码 all wrong",
         _UNKNOWN_EMAIL, _WRONG_PASSWORD, "0000"),
    ])


@then("every wrong-field login attempt is blocked")
def step_assert_matrix_blocked(context):
    """TC048-050 expected result — every attempt is rejected with an error and
    no authenticated session is created."""
    assert context.matrix, "No login attempts were recorded"
    for label, err, logged_in in context.matrix:
        assert err and not logged_in, (
            f"Attempt '{label}' was not blocked — error={err!r}, "
            f"loggedIn={logged_in}")
        print(f"  [matrix] {label}: blocked -> {err!r}")


# --- TC055  OTP-mode active logout -------------------------------------------

def _registered_area_reachable(page) -> bool:
    """True only if the registered-only personal centre stayed open — the
    SPA did not redirect the #/my/profile route away to #/login or #/."""
    return "#/my/profile" in page.url


@when("I switch to OTP mode and submit with a wrong verification code")
def step_otp_login_wrong_otp(context):
    """TC051 (SIT 3-field variant) — fill correct email + 动态码, request
    OTP from inbox, then fill a deliberately WRONG OTP and submit. SIT OTP
    mode has no password field, so the original 4-field "any-one-wrong"
    matrix collapses to checking the OTP value itself; wrong-captcha is
    TC032's territory, wrong-email is TC012's territory.
    """
    from imap_otp_poller import wait_for_otp_throttle
    user = get_user("website_user", get_settings().env)
    lp = context.login_page
    lp.switch_to_otp_mode()
    wait_for_otp_throttle(user.username)
    err = lp.request_verification_code(user.username)
    assert not err, f"Get Code should succeed with correct inputs; got {err!r}"
    # fill_otp auto-submits once all 6 digits are typed (it waits 3s internally).
    lp.fill_otp("000000")
    context.tc051_logged_in = lp.is_logged_in()


@then("the OTP-mode login is blocked")
def step_assert_otp_login_blocked(context):
    """TC051/052/053 expected — wrong inputs are rejected; no authenticated
    session is created."""
    # Each scenario sets its own "logged_in" attribute; collect whichever ran.
    logged_in = (
        getattr(context, "tc051_logged_in", None)
        or getattr(context, "tc052_logged_in", None)
        or getattr(context, "tc053_logged_in", None)
    )
    assert not logged_in, "Expected OTP-mode login to be blocked"
    print(f"  [OTP-matrix] login blocked as expected")


# --- TC052  email + OTP both wrong ------------------------------------------

@when("I switch to OTP mode and submit with a wrong email and wrong verification code")
def step_otp_login_email_and_otp_wrong(context):
    """TC052 (SIT 3-field variant) — real 动态码 + unregistered email +
    wrong OTP. The Get Code may succeed (OTP sent to nowhere) or fail
    immediately; either way the user must not end up logged in.
    """
    lp = context.login_page
    lp.switch_to_otp_mode()
    wrong_email = "no.such.user.tc052@126.com"
    err = lp.request_verification_code(wrong_email)
    if not err:
        # Get Code accepted (system sent OTP to a nonexistent address).
        # Submit a wrong 6-digit value anyway.
        lp.fill_otp("000000")
    context.tc052_logged_in = lp.is_logged_in()


# --- TC053  all three fields wrong ------------------------------------------

@when("I switch to OTP mode and submit with all three OTP-mode fields wrong")
def step_otp_login_all_three_wrong(context):
    """TC053 (= TC054 in 3-field SIT UI) — wrong 动态码 forces Get Code to
    fail before the OTP entry step is reachable. Adding a wrong email and
    a (would-be) wrong OTP on top can only confirm the block.
    """
    lp = context.login_page
    lp.switch_to_otp_mode()
    wrong_email = "no.such.user.tc053@126.com"
    err = lp.request_verification_code(wrong_email, captcha="0000")
    # captcha wrong → request_verification_code returns an error and never
    # advances to OTP entry. Therefore the user is definitely not logged in.
    context.tc053_logged_in = lp.is_logged_in()


@when("I log in through OTP mode and then log out")
def step_otp_login_then_logout(context):
    """TC055 — log in via OTP mode (real OTP from inbox), confirm the
    personal centre is reachable, then actively log out and re-check."""
    from imap_otp_poller import fetch_latest_otp, wait_for_otp_throttle
    settings = get_settings()
    user = get_user("website_user", settings.env)
    base = str(settings.antank_url).rstrip("/")
    profile_url = f"{base}/websitehtml/index.html#/my/profile"
    lp = context.login_page
    lp.switch_to_otp_mode()
    wait_for_otp_throttle(user.username)
    since = datetime.now(timezone.utc) - timedelta(seconds=10)
    err = lp.request_verification_code(user.username)
    assert not err, f"Expected the OTP request to succeed, got {err!r}"
    real_otp = fetch_latest_otp(since=since, timeout=45.0)
    lp.fill_otp(real_otp)
    context.page.wait_for_timeout(1500)
    assert lp.is_logged_in(), "Expected OTP-mode login to succeed"
    context.page.goto(profile_url, timeout=60000)
    context.page.wait_for_timeout(2500)
    context.tc055_before = _registered_area_reachable(context.page)
    lp.logout()
    context.page.goto(profile_url, timeout=60000)
    context.page.wait_for_timeout(2500)
    context.tc055_after = _registered_area_reachable(context.page)


@then("the registered-only area is no longer accessible after OTP logout")
def step_assert_otp_logout_protected(context):
    """TC055 expected result — reachable before logout, protected after."""
    assert context.tc055_before, \
        "Expected the personal centre to be reachable while logged in via OTP"
    assert not context.tc055_after, (
        "Expected the personal centre to be protected after OTP-mode logout "
        f"(url={context.page.url})")
    print("  [TC055] OTP-mode logout cleared registered-only access")
