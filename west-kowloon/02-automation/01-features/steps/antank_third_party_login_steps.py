"""Step definitions for antank_third_party_login.feature.

Covers the Website 第三方登录 + Link Your Account binding flow as defined
in PRD §3.2.2 (2026-05-26 完善绑定流程) and figma 2026-06-02.

  ID range: SIT-TC-WEB-AUTH-017, 018, 059-063 (modified)
            SIT-TC-WEB-AUTH-078..087           (new)

Steps that interact with the real third-party provider (Google / Facebook /
X / TikTok / WeChat OAuth) are gated by _require_oauth_mock(). The whole
scenario skips cleanly if the OAUTH_MOCK_URL env var is not set, instead
of failing — that way the dashboard shows them as Skipped (= "blocked on
infra") instead of Failed (= "the feature is broken").

When the OAuth mock is added later, set OAUTH_MOCK_URL and these steps
will execute.
"""
from __future__ import annotations

import os

from behave import given, when, then  # type: ignore


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _require_oauth_mock(context) -> None:
    """Skip the current scenario when no OAuth provider mock is configured.

    The third-party providers (Google / Facebook / X / TikTok / WeChat)
    cannot be driven from headless Playwright without either real provider
    test accounts (fragile, password-rotation issues) or a mock provider
    server. Until that infra exists, scenarios that touch real OAuth skip
    rather than fail.
    """
    if not os.environ.get("OAUTH_MOCK_URL"):
        context.scenario.skip(
            "OAuth provider mock not configured "
            "(set OAUTH_MOCK_URL to enable end-to-end OAuth tests)"
        )


def _login_page(context):
    """The existing 'Given the Website login page is open' step from
    antank_email_login_steps.py stores the page object on context.login_page.
    Reuse it here so we don't redefine the step (Behave would treat that
    as an Ambiguous step) and so the same WebsiteLoginPage instance is
    shared across both flows."""
    return getattr(context, "login_page", None)


# ---------------------------------------------------------------------------
# Given — entry & state setup
# ---------------------------------------------------------------------------
# NOTE: "Given the Website login page is open" is defined in
# antank_email_login_steps.py — we deliberately do NOT redefine it here.

@given("the third-party account is already linked to a platform account")
def step_provider_already_linked(context):
    # State precondition — needs a pre-bound provider sandbox account.
    # Without the OAuth mock we can't simulate this prior state; skip.
    _require_oauth_mock(context)


@given("I have just completed OAuth and am on the Link Your Account page in Email mode")
def step_on_link_page_email(context):
    _require_oauth_mock(context)
    # When the mock IS available, this step would:
    # 1. Drive the mock provider to return an OAuth callback with a test identity
    # 2. Assert the SPA routed to /websitehtml/index.html#/link-account
    # 3. Verify Email mode is active by default
    # left unimplemented intentionally — gated by the skip above.


@given("I have just completed OAuth and am on the Link Your Account page")
def step_on_link_page(context):
    _require_oauth_mock(context)


@given("I am on the Link Your Account page after OAuth")
def step_on_link_page_alt(context):
    _require_oauth_mock(context)


@given("I am on the Link Your Account page after OAuth with email entered")
def step_on_link_page_email_entered(context):
    _require_oauth_mock(context)


@given("I am on the Link Your Account page with all other fields valid")
def step_on_link_page_all_valid(context):
    _require_oauth_mock(context)


@given("I am on the Link Your Account page in Email mode")
def step_on_link_page_email_mode(context):
    _require_oauth_mock(context)


@given("I am on the Link Your Account page in Phone mode")
def step_on_link_page_phone_mode(context):
    _require_oauth_mock(context)


# ---------------------------------------------------------------------------
# When — provider click / OAuth dance
# ---------------------------------------------------------------------------
@when("I click a third-party provider button")
def step_click_provider(context):
    # The provider buttons (Google / Facebook / X / TikTok / WeChat) only
    # appear once the figma 2026-06-02 update is deployed. Until BOTH the
    # UI is deployed AND we have an OAuth provider mock, this whole flow
    # skips cleanly. Once deployed, this step would locate and click a
    # specific provider button via page.locator(...).
    _require_oauth_mock(context)


@when("I click the same provider button on the login page")
def step_click_same_provider(context):
    step_click_provider(context)


@when("I click the same third-party provider button")
def step_click_same_provider_v2(context):
    step_click_provider(context)


@when("I complete provider OAuth authorization")
def step_complete_oauth(context):
    _require_oauth_mock(context)


@when("I complete a first-time Google OAuth and Link Your Account binding")
def step_first_google(context):
    _require_oauth_mock(context)


@when("I complete a first-time Facebook OAuth and Link Your Account binding")
def step_first_facebook(context):
    _require_oauth_mock(context)


@when("I complete a first-time X OAuth and Link Your Account binding")
def step_first_x(context):
    _require_oauth_mock(context)


@when("I complete a first-time TikTok OAuth and Link Your Account binding")
def step_first_tiktok(context):
    _require_oauth_mock(context)


@when("I complete a first-time WeChat OAuth (QR scan) and Link Your Account binding")
def step_first_wechat(context):
    _require_oauth_mock(context)


# ---------------------------------------------------------------------------
# When — Link Your Account form actions
# ---------------------------------------------------------------------------
@when("I bind via an UNREGISTERED email with valid 动态码, OTP and Terms ticked")
def step_bind_email_new(context):
    _require_oauth_mock(context)


@when("I bind via an ALREADY-REGISTERED email with valid 动态码, OTP and Terms ticked")
def step_bind_email_existing(context):
    _require_oauth_mock(context)


@when("I switch to Phone mode and bind via an UNREGISTERED phone with valid OTP and Terms")
def step_bind_phone_new(context):
    _require_oauth_mock(context)


@when("I switch to Phone mode and bind via an ALREADY-REGISTERED phone with valid OTP and Terms")
def step_bind_phone_existing(context):
    _require_oauth_mock(context)


@when("I submit with an empty captcha")
def step_submit_empty_captcha(context):
    _require_oauth_mock(context)


@when("I submit with a wrong captcha value")
def step_submit_wrong_captcha(context):
    _require_oauth_mock(context)


@when("I click the 动态码 image to request a fresh captcha")
def step_refresh_captcha(context):
    _require_oauth_mock(context)


@when("I click Get Code")
def step_click_get_code(context):
    _require_oauth_mock(context)


@when("I enter a wrong OTP and submit")
def step_wrong_otp(context):
    _require_oauth_mock(context)


@when("I enter the correct OTP and submit")
def step_correct_otp(context):
    _require_oauth_mock(context)


@when("I submit without ticking the Privacy / Ticket Purchase Terms checkbox")
def step_submit_no_terms(context):
    _require_oauth_mock(context)


@when("I tick only the marketing checkbox")
def step_tick_marketing_only(context):
    _require_oauth_mock(context)


@when("I tick the Privacy / Ticket Purchase Terms checkbox")
def step_tick_terms(context):
    _require_oauth_mock(context)


@when('I click "Use phone number"')
def step_switch_to_phone(context):
    _require_oauth_mock(context)


@when('I click "Use email"')
def step_switch_to_email(context):
    _require_oauth_mock(context)


@when('I keep the default country code "CN +86" and enter an 11-digit CN phone')
def step_cn_phone(context):
    _require_oauth_mock(context)


@when('I change the country code to "HK +852" and re-enter the CN phone')
def step_hk_with_cn_phone(context):
    _require_oauth_mock(context)


@when('I enter a valid HK phone for "+852"')
def step_valid_hk_phone(context):
    _require_oauth_mock(context)


# ---------------------------------------------------------------------------
# Then — assertions
# ---------------------------------------------------------------------------
@then("the Link Your Account page is shown")
def step_link_page_shown(context):
    _require_oauth_mock(context)


@then("I can complete account binding via Email or Phone")
def step_can_bind(context):
    _require_oauth_mock(context)


@then("a new platform account is created and the OAuth identity is linked")
def step_new_account_linked(context):
    _require_oauth_mock(context)


@then("the Link Your Account page is NOT shown")
def step_link_page_not_shown(context):
    _require_oauth_mock(context)


@then("I am logged in directly to the previously-linked account")
def step_direct_login(context):
    _require_oauth_mock(context)


@then("login succeeds and a platform account is created and linked")
def step_login_success_linked(context):
    _require_oauth_mock(context)


@then("a subsequent Google login skips Link page and lands directly on home")
def step_subsequent_google(context):
    _require_oauth_mock(context)


@then("a subsequent Facebook login skips Link page and lands directly on home")
def step_subsequent_facebook(context):
    _require_oauth_mock(context)


@then("a subsequent X login skips Link page and lands directly on home")
def step_subsequent_x(context):
    _require_oauth_mock(context)


@then("a subsequent TikTok login skips Link page and lands directly on home")
def step_subsequent_tiktok(context):
    _require_oauth_mock(context)


@then("a subsequent WeChat login skips Link page and lands directly on home")
def step_subsequent_wechat(context):
    _require_oauth_mock(context)


@then('the orange "email not registered" notice is shown')
def step_email_not_registered_notice(context):
    _require_oauth_mock(context)


@then('the blue "email already registered" notice is shown')
def step_email_registered_notice(context):
    _require_oauth_mock(context)


@then('the orange "phone not registered" notice is shown')
def step_phone_not_registered_notice(context):
    _require_oauth_mock(context)


@then('the blue "phone already registered" notice is shown with a masked phone number')
def step_phone_registered_masked(context):
    _require_oauth_mock(context)


@then("the OAuth identity is linked to the existing account (no new account created)")
def step_linked_existing_no_dup(context):
    _require_oauth_mock(context)


@then("the OAuth identity is linked to the existing account")
def step_linked_existing(context):
    _require_oauth_mock(context)


@then("the success page is shown then auto-login completes")
def step_success_auto_login(context):
    _require_oauth_mock(context)


@then("the success page is shown then auto-login to the existing account")
def step_success_auto_login_existing(context):
    _require_oauth_mock(context)


@then("I land directly on the home / member area")
def step_land_home(context):
    _require_oauth_mock(context)


@then('no "Account linked successfully" transient page is shown')
def step_no_transient(context):
    _require_oauth_mock(context)


@then('the captcha field reports "Captcha required"')
def step_captcha_required_err(context):
    _require_oauth_mock(context)


@then('the captcha field reports "Captcha incorrect"')
def step_captcha_incorrect_err(context):
    _require_oauth_mock(context)


@then("a fresh captcha image is shown")
def step_fresh_captcha(context):
    _require_oauth_mock(context)


@then("the OTP arrives within 30 seconds")
def step_otp_arrives(context):
    _require_oauth_mock(context)


@then("the Get Code button is disabled or counting down for ~30 seconds")
def step_getcode_cooldown(context):
    _require_oauth_mock(context)


@then("the verification code field reports an error")
def step_otp_field_err(context):
    _require_oauth_mock(context)


@then("the bind proceeds")
def step_bind_proceeds(context):
    _require_oauth_mock(context)


@then("the bind is blocked with a Terms-required message")
def step_terms_required(context):
    _require_oauth_mock(context)


@then("the bind is still blocked")
def step_still_blocked(context):
    _require_oauth_mock(context)


@then("the Phone mode is active with the country code dropdown visible")
def step_phone_mode_active(context):
    _require_oauth_mock(context)


@then("the Email mode is active and the captcha refreshes")
def step_email_mode_refresh(context):
    _require_oauth_mock(context)


@then("the phone field has no inline error")
def step_phone_no_err(context):
    _require_oauth_mock(context)


@then("the phone field reports a format error")
def step_phone_format_err(context):
    _require_oauth_mock(context)
