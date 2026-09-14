"""Step definitions for scenarios that are documented but not yet runnable
end-to-end because they need infrastructure the harness doesn't yet host:

  - **Lockout flow (TC011)** — needs DB / backend hook to put the account
    into the locked state on demand.
  - **Forgot-password direct-reset OTP flow (TC073)** — needs the existing
    IMAP+captcha path wired end-to-end with new-password set + login-back
    assertion across two browser sessions.
  - **Multi-tab session (TC075/076)** — needs Playwright multi-page wiring
    + matching same-origin storage assertions.

Today every step here skips cleanly with a reason; the scenarios show up
in dashboard as Skipped (not Undefined / not Failed). When the infra is
ready, replace `_skip_deferred()` with real implementation.

Naming convention: the file is `antank_deferred_steps.py` (not bound to
one feature) — Behave's step registry is global, so any antank_*.feature
that mentions these step phrases will resolve here.
"""
from __future__ import annotations

from behave import given, when, then  # type: ignore


def _skip(context, reason: str) -> None:
    """Skip the current scenario with a recognisable reason so the dashboard
    bucket is Skipped (not Failed / Errored). Mirrors the @needs-oauth-mock
    pattern used by antank_third_party_login_steps.py."""
    context.scenario.skip(reason)


# ---------------------------------------------------------------------------
# Lockout flow (antank_email_login.feature — TC077)
# ---------------------------------------------------------------------------
@given("a registered account has been driven to locked state per TC011")
def step_account_locked(context):
    _skip(context,
          "Lockout setup requires a backend hook / DB seed that the harness "
          "does not yet host. Implement by either: (a) calling a SIT admin API "
          "that flips the lock flag, or (b) running TC011 inline N times to "
          "trigger the lockout naturally.")


@when("the configured unlock condition is satisfied")
def step_unlock_condition(context):
    _skip(context, "see preceding @given — lockout fixture not yet implemented")


@when("I log in with the valid credentials of that account")
def step_login_valid_post_unlock(context):
    _skip(context, "see preceding @given — lockout fixture not yet implemented")


@then("the login succeeds")
def step_login_succeeds_generic(context):
    _skip(context, "see preceding @given — lockout fixture not yet implemented")


@then("the failed-login counter is reset")
def step_fail_counter_reset(context):
    _skip(context,
          "Asserting the counter reset needs a backend introspection endpoint "
          "(e.g. GET /admin/account/<id>/lockout-state) — not exposed today.")


# ---------------------------------------------------------------------------
# Forgot-password direct-reset OTP flow (antank_forgot_password.feature — TC073)
# ---------------------------------------------------------------------------
@given("an active registered account with a known old password")
def step_active_account_known_pwd(context):
    _skip(context,
          "Direct-reset E2E needs a pristine test account whose password we "
          "control end-to-end (so we can verify old-password-rejects-after-reset). "
          "Add a per-test account allocator before enabling this scenario.")


@when("I complete the direct-reset flow with email + 动态码 + OTP from IMAP + a new password")
def step_direct_reset_complete(context):
    _skip(context,
          "Pieces already exist (WebsiteForgotPasswordPage + imap_otp_poller) "
          "but they aren't yet stitched into a 'set new password' end-to-end. "
          "Implement: open forgot-password → email → OCR captcha → fetch OTP "
          "→ submit OTP → fill new-password → confirm.")


@then("no temp-password email is sent at any step")
def step_no_temp_pwd_email(context):
    _skip(context,
          "Needs an IMAP scan for any temp-password email (subject pattern) "
          "AFTER the direct-reset flow completes — to assert the flow never "
          "fell back to the legacy temp-password path.")


@then("the old password is rejected on login")
def step_old_pwd_rejected(context):
    _skip(context, "see preceding @when — full direct-reset wiring needed first")


@then("the new password is accepted on login")
def step_new_pwd_accepted(context):
    _skip(context, "see preceding @when — full direct-reset wiring needed first")


# ---------------------------------------------------------------------------
# Multi-tab session (antank_session_ui.feature — TC075 / TC076)
# ---------------------------------------------------------------------------
@given("a logged-in session on browser tab 1")
def step_tab1_logged_in(context):
    _skip(context,
          "Multi-tab scenarios need two Playwright pages within the same "
          "BrowserContext (so cookies are shared). The existing fixtures open "
          "one page per scenario; lift that to context.tab1 / context.tab2 "
          "in environment.py before enabling.")


@when("I open tab 2 to the same site root URL")
def step_open_tab2(context):
    _skip(context, "see preceding @given — multi-tab fixture needed first")


@then("tab 2 is authenticated without re-prompting")
def step_tab2_authed(context):
    _skip(context, "see preceding @given — multi-tab fixture needed first")


@when("I log out on tab 1")
def step_logout_tab1(context):
    _skip(context, "see preceding @given — multi-tab fixture needed first")


@when("I trigger a registered-only action on tab 2")
def step_protected_action_tab2(context):
    _skip(context, "see preceding @given — multi-tab fixture needed first")


@then("tab 2 either blocks the action or redirects to login")
def step_tab2_blocked_or_redirected(context):
    _skip(context, "see preceding @given — multi-tab fixture needed first")
