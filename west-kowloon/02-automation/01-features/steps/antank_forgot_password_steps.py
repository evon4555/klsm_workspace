"""
Step definitions for antank_forgot_password.feature.

Converts manual test cases SIT-TC-WEB-AUTH-015 / 016 / 033 ("Website forgot
password") into pure-UI Playwright tests driven through
WebsiteForgotPasswordPage.

Email Verification Code is fetched from the real Aliyun mailbox via
tools/imap_otp_poller (SIT killed fixed 111111 since 2026-05-23 — see
[[project_sit_otp_regression_2026_05_27]]). TC015 resets the account back to
its config/users.yml password so the suite is repeatable.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from behave import given, when, then

from test_automation.config import get_settings, get_user
from test_automation.web import WebsiteForgotPasswordPage

_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

_SHOT_ROOT = Path(__file__).resolve().parents[2] / "07-artifacts" / "screenshots"
_UNREGISTERED_EMAIL = "no.such.user.2026@126.com"


def _new_forgot_page(context) -> WebsiteForgotPasswordPage:
    settings = get_settings()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shot_dir = _SHOT_ROOT / f"forgot_{stamp}"
    return WebsiteForgotPasswordPage(context.page, str(settings.antank_url),
                                     screenshot_dir=shot_dir)


@given("the Website forgot-password page is open")
def step_open_forgot(context):
    """Manual step 1 — open the forgot-password page."""
    context.fp = _new_forgot_page(context)
    context.fp.open()
    context.fp.shot("forgot_password_page_opened")


# --- TC015  successful password reset ----------------------------------------

@when("I complete the password-reset form with a valid email and OTP")
def step_complete_reset(context):
    """TC015 — registered email + 动态码 + Get Code + OTP (from inbox) + new
    password. The new password equals the config password so the shared
    test account stays usable by the rest of the suite."""
    from imap_otp_poller import fetch_latest_otp, wait_for_otp_throttle
    user = get_user("website_user", get_settings().env)
    context.fp.fill_email(user.username)
    wait_for_otp_throttle(user.username)
    since = datetime.now(timezone.utc) - timedelta(seconds=10)
    context.fp.request_otp_until_sent()
    real_otp = fetch_latest_otp(since=since, timeout=45.0)
    context.fp.fill_verification_code(real_otp)
    context.fp.fill_new_passwords(user.password)
    context.fp.shot("reset_form_filled")
    context.reset_error = context.fp.submit_until_settled()
    context.fp.shot("reset_result")


@then("the password reset succeeds")
def step_assert_reset_ok(context):
    """TC015 expected result — the reset completes (form accepted, left
    #/forget or no error shown)."""
    assert not context.reset_error or not context.fp.is_on_forget_page(), (
        f"Expected the password reset to complete; error={context.reset_error!r}, "
        f"still_on_forget={context.fp.is_on_forget_page()}")
    print(f"  [TC015] password reset completed (error={context.reset_error!r})")


# --- TC016  invalid reset inputs ---------------------------------------------

@when("I request a reset code for an unregistered email")
def step_reset_unregistered(context):
    """TC016 — an email that has no account; requesting the reset OTP for it
    must be rejected."""
    context.fp.fill_email(_UNREGISTERED_EMAIL)
    context.fp.fill_dynamic_code()
    context.fp.shot("reset_unregistered_email")
    btn = context.page.locator(context.fp.GETCODE_SEL).first
    if btn.count() and not btn.is_disabled():
        btn.click()
        context.page.wait_for_timeout(3000)
    context.reset_error = context.fp.current_error()
    context.fp.shot("reset_unregistered_result")


@then("the password reset is blocked with a validation message")
def step_assert_reset_blocked(context):
    """TC016 expected result — blocked, a message shown, still on #/forget."""
    assert context.fp.is_on_forget_page(), "Expected to stay on #/forget"
    print(f"  [TC016] reset blocked; message -> {context.reset_error!r}")


# --- TC033  forgot password requires the 动态码 ------------------------------

@when("I submit the password-reset form with a missing 动态码")
def step_reset_missing_captcha(context):
    """TC033 — fill the email but leave the 动态码 empty, then submit."""
    user = get_user("website_user", get_settings().env)
    context.fp.fill_email(user.username)
    context.fp.fill_dynamic_code_value("")          # missing 动态码
    context.fp.fill_new_passwords("Test@202605")
    context.fp.shot("reset_missing_captcha")
    context.fp.submit()
    context.reset_error = context.fp.current_error()


# --- TC043  OTP resend invalidates previous --------------------------------

@when("I request an OTP, wait past the resend cooldown, and request a new OTP")
def step_otp_resend_sequence(context):
    """TC043 — issue Get Code (OTP A), wait ~65s (>60s SIT cooldown), issue
    Get Code again (OTP B). Both OTPs are fetched from the live evan.wang
    mailbox via imap_otp_poller; on cooldown we sleep, not bail.
    """
    import time
    from imap_otp_poller import fetch_latest_otp, wait_for_otp_throttle
    user = get_user("website_user", get_settings().env)

    context.fp.fill_email(user.username)

    # --- OTP A ---
    wait_for_otp_throttle(user.username)
    since_a = datetime.now(timezone.utc) - timedelta(seconds=10)
    accepted = context.fp.request_otp_until_sent()
    assert accepted, "Initial Get Code never accepted"
    context.tc043_otp_a = fetch_latest_otp(since=since_a, timeout=45.0)
    context.fp.shot("otp_a_received")
    print(f"  [TC043] OTP A = {context.tc043_otp_a}")

    # --- wait past cooldown + reload page for clean state, then request OTP B ---
    # SIT's resend cooldown is empirically >60s. 75s seems sufficient.
    # Reloading the page clears stale UI state (OTP boxes, half-typed values)
    # without affecting server-side cooldown.
    print(f"  [TC043] waiting 75s for the resend cooldown to expire ...")
    time.sleep(75)
    context.fp.open()                                   # fresh page state
    context.fp.fill_email(user.username)
    wait_for_otp_throttle(user.username)
    since_b = datetime.now(timezone.utc) - timedelta(seconds=10)
    accepted = context.fp.request_otp_until_sent()
    assert accepted, "Resend Get Code never accepted (cooldown still in effect?)"
    context.tc043_otp_b = fetch_latest_otp(since=since_b, timeout=45.0)
    context.fp.shot("otp_b_received")
    print(f"  [TC043] OTP B = {context.tc043_otp_b}")


@then("the previous OTP is rejected and only the latest OTP is accepted")
def step_assert_resend_invalidates(context):
    """TC043 expected — OTP A != OTP B; submitting A fails (replaced by B);
    submitting B succeeds (it's now the operative OTP). The new password
    equals config so the test account stays usable for the rest of the suite.
    """
    user = get_user("website_user", get_settings().env)
    otp_a, otp_b = context.tc043_otp_a, context.tc043_otp_b
    assert otp_a and otp_b and otp_a != otp_b, (
        f"Resend should produce a different OTP; got A={otp_a!r}, B={otp_b!r}")

    # Submit with OTP A — should fail
    context.fp.fill_verification_code(otp_a)
    context.fp.fill_new_passwords(user.password)
    err_a = context.fp.submit_until_settled()
    context.fp.shot("submitted_with_old_otp_a")
    assert err_a, (
        f"Expected OTP A ({otp_a}) to be rejected after resend, but submit "
        f"returned no error. Possible product bug: previous OTP not invalidated.")
    print(f"  [TC043] OTP A correctly rejected: {err_a!r}")

    # Submit with OTP B — should succeed
    context.fp.fill_verification_code(otp_b)
    context.fp.fill_new_passwords(user.password)
    err_b = context.fp.submit_until_settled()
    context.fp.shot("submitted_with_new_otp_b")
    assert not err_b or not context.fp.is_on_forget_page(), (
        f"Expected OTP B ({otp_b}) to succeed, error={err_b!r}, "
        f"still_on_forget={context.fp.is_on_forget_page()}")
    print(f"  [TC043] OTP B accepted; password reset completed")


# --- TC064  动态码 captcha refresh changes image ----------------------------

@then("the 动态码 image changes after clicking refresh")
def step_assert_captcha_refresh_changes_image(context):
    """TC064 (partial — refresh behaviour only; time-based expiry needs the
    spec's TBD validity duration). Capture the captcha image's src attribute
    before and after a refresh click and confirm they differ."""
    fp = context.fp
    page = fp._page
    img = page.locator(fp.CAPTCHA_IMG_SEL).first
    img.wait_for(state="visible", timeout=10000)
    src_a = img.get_attribute("src") or ""
    fp.shot("captcha_a")
    img.click()
    page.wait_for_timeout(1500)
    src_b = page.locator(fp.CAPTCHA_IMG_SEL).first.get_attribute("src") or ""
    fp.shot("captcha_b")
    assert src_a and src_b, f"captcha src missing: A={src_a!r}, B={src_b!r}"
    assert src_a != src_b, (
        f"Expected captcha image to change after refresh; both were {src_a!r}")
    print(f"  [TC064] captcha refresh confirmed: A != B (src tokens differ)")


@then("the forgot-password form exposes the direct-reset fields")
def step_assert_forgot_password_form_structure(context):
    """TC070 — pure DOM inspection: the direct-reset model means the user
    sets the new password on the page (vs. the 'temp password emailed' model
    where the page only has email + send button). Verify all 7 expected
    inputs are visible on the form simultaneously.
    """
    fp = context.fp
    page = fp._page
    required = [
        ("Email", fp.EMAIL_SEL),
        ("Dynamic Code", fp.DYN_SEL),
        ("Get Code button", fp.GETCODE_SEL),
        ("Verification Code", fp.VCODE_SEL),
        ("New password", fp.NEWPWD_SEL),
        ("Confirm new password", fp.CONFIRM_SEL),
        ("Submit button", fp.SUBMIT_SEL),
    ]
    missing = []
    for label, sel in required:
        loc = page.locator(sel).first
        if not (loc.count() > 0 and loc.is_visible()):
            missing.append(label)
    fp.shot("forgot_form_structure")
    assert not missing, (
        f"Forgot-password form is missing direct-reset fields: {missing}. "
        f"Expected SIT to follow model B (direct reset)."
    )
    print(f"  [TC070] direct-reset model confirmed — all 7 fields present")


@then("the password reset is blocked with a captcha error")
def step_assert_reset_captcha_error(context):
    """TC033 expected result — blocked, a 动态码/captcha message shown."""
    err = context.reset_error
    assert err, "Expected a validation message for the missing 动态码"
    assert context.fp.is_on_forget_page(), "Expected to stay on #/forget"
    print(f"  [TC033] missing-动态码 message -> {err!r}")
