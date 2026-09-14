from __future__ import annotations

from pathlib import Path

from behave import given, then, when

from test_automation.config import get_settings, get_user
from test_automation.flows.auth009_api_first import run_auth009_api_first


_ROOT = Path(__file__).resolve().parents[2]
_SHOT_DIR = _ROOT / "07-artifacts" / "screenshots" / "api_first_ui" / "tc009"


@given("a registered Website user is available for API-first validation")
def step_registered_user_available(context):
    settings = get_settings()
    context.auth009_base_url = str(settings.antank_url)
    context.auth009_user = get_user("website_user", settings.env)


@when("I validate the login identity chain through API and open the profile UI")
def step_validate_api_chain_then_ui(context):
    context.auth009_result = run_auth009_api_first(
        context.browser,
        context.auth009_base_url,
        context.auth009_user.username,
        context.auth009_user.password,
        _SHOT_DIR,
    )


@then("the API member identity and profile UI show the same registered account")
def step_assert_api_and_ui_same_account(context):
    result = context.auth009_result
    assert result.member_id > 0, f"Expected a positive member id, got {result.member_id}"
    assert result.email.casefold() == context.auth009_user.username.casefold(), (
        f"Expected {context.auth009_user.username!r}, got {result.email!r}"
    )
    assert "#/my" in result.final_url, f"Expected member UI URL, got {result.final_url}"
    print(
        "  [AUTH-009 API+UI mixed] "
        f"member_id={result.member_id}, email={result.email}, url={result.final_url}"
    )
