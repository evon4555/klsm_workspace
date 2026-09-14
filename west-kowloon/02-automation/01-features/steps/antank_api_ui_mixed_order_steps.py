from __future__ import annotations

from pathlib import Path

from behave import given, then, when

from test_automation.config import get_settings, get_user
from test_automation.flows.order_cancel_api_ui_mixed import run_order_cancel_api_ui_mixed


_ROOT = Path(__file__).resolve().parents[2]
_SHOT_DIR = _ROOT / "07-artifacts" / "screenshots" / "api_ui_mixed" / "order_cancel"


@given("a registered Website user is available for API+UI mixed ticketing validation")
def step_registered_user_available(context):
    settings = get_settings()
    context.order_cancel_base_url = str(settings.antank_url)
    context.order_cancel_user = get_user("website_user", settings.env)


@when("I create and cancel a show order through the official APIs")
def step_create_and_cancel_order(context):
    context.order_cancel_result = run_order_cancel_api_ui_mixed(
        context.browser,
        context.order_cancel_base_url,
        context.order_cancel_user.username,
        context.order_cancel_user.password,
        _SHOT_DIR,
    )


@then("the browser UI check confirms the same order is cancelled")
def step_assert_order_cancelled(context):
    result = context.order_cancel_result
    assert result.trade_no, "Expected a tradeNo from order/create"
    assert result.pay_status == "cancel_user", (
        f"Expected payStatus cancel_user, got {result.pay_status!r}"
    )
    assert result.cancel_list_after_cancel is True, "Expected order in cancel list"
    assert result.new_list_after_cancel is False, "Expected order removed from new list"
    print(
        "  [API+UI mixed order] "
        f"tradeNo={result.trade_no}, payStatus={result.pay_status}, "
        f"programId={result.program_id}"
    )
