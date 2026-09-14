from __future__ import annotations

from behave import given, then, when

from test_automation.config import get_settings
from test_automation.config import get_user
from test_automation.standard_product.admin_auth import StandardProductAdminSession
from test_automation.standard_product.batch_session_api import FLOWS
from test_automation.standard_product.batch_session_api import assert_precondition_changed_to_target
from test_automation.standard_product.batch_session_api import assert_readback_contains
from test_automation.standard_product.batch_session_api import assert_write_accepted
from test_automation.standard_product.batch_session_api import execute_request
from test_automation.standard_product.batch_session_api import precondition_setup_request
from test_automation.standard_product.batch_session_api import readback_observations
from test_automation.standard_product.batch_session_api import request_summary
from test_automation.standard_product.evidence import save_api_evidence_screenshot


@given("I have a real Standard Product admin requests session")
def step_real_admin_requests_session(context):
    cached = getattr(context, "_standard_product_api_client", None)
    if cached is not None:
        context.standard_product_api = cached
        return

    settings = get_settings()
    user = get_user("user1", settings.env)
    client = StandardProductAdminSession(str(settings.antank_url), user.username, user.password)
    client.login()
    context._standard_product_api_client = client
    context.standard_product_api = client


@when('I read the "{flow_key}" source sessions through API')
def step_read_source_sessions(context, flow_key):
    flow = FLOWS[flow_key]
    context.batch_flow = flow
    source_responses = []
    source_requests = []
    for request in flow.read:
        response, exchange = _execute_with_exchange(context, request)
        source_responses.append(response)
        source_requests.append(exchange)

    setup_requests = []
    setup = precondition_setup_request(flow)
    if setup is not None:
        response, exchange = _execute_with_exchange(context, setup)
        assert_write_accepted(response)
        setup_requests.append(exchange)

    before_responses = []
    before_requests = []
    for request in flow.readback:
        response, exchange = _execute_with_exchange(context, request)
        before_responses.append(response)
        before_requests.append(exchange)

    context.batch_read_response = source_responses
    context.batch_before_readback_response = before_responses
    context.batch_api_evidence = {
        "flow_key": flow_key,
        "source_requests": source_requests,
        "setup_requests": setup_requests,
        "before_requests": before_requests,
        "before_observations": readback_observations(flow, before_responses),
    }


@when('I submit the "{flow_key}" batch update through API')
def step_submit_batch_update(context, flow_key):
    flow = FLOWS[flow_key]
    response, exchange = _execute_with_exchange(context, flow.write)
    assert_write_accepted(response)
    context.batch_write_response = response
    evidence = getattr(context, "batch_api_evidence", {})
    evidence["write_exchange"] = exchange
    context.batch_api_evidence = evidence


@then('the "{flow_key}" readback API shows the target value changed from the precondition')
def step_readback_contains_target(context, flow_key):
    flow = FLOWS[flow_key]
    responses = []
    readback_requests = []
    assertion_error = None
    observations = []
    try:
        for request in flow.readback:
            response, exchange = _execute_with_exchange(context, request)
            responses.append(response)
            readback_requests.append(exchange)
        observations = readback_observations(flow, responses)
        assert_readback_contains(flow, responses)
        assert_precondition_changed_to_target(
            flow,
            (getattr(context, "batch_api_evidence", {}) or {}).get("before_observations", []),
            observations,
        )
    except AssertionError as exc:
        assertion_error = exc
    finally:
        evidence = _build_api_evidence(
            context,
            flow_key,
            flow,
            observations,
            readback_requests,
            assertion_error,
        )
        save_api_evidence_screenshot(context, evidence)

    context.batch_readback_response = responses
    if assertion_error:
        raise assertion_error


@given("real endpoint mapping is pending")
def step_real_endpoint_mapping_pending(context):
    raise AssertionError("This step should be skipped by environment.py via @needs_mapping.")


@given("real UI mandatory-field selector mapping is pending")
def step_real_ui_selector_mapping_pending(context):
    raise AssertionError("This step should be skipped by environment.py via @needs_ui_selector.")


def _execute_with_exchange(context, request):
    response = execute_request(context.standard_product_api, request)
    meta = dict(getattr(context.standard_product_api, "last_response_meta", {}) or {})
    exchange = {
        **request_summary(request),
        "url": meta.get("url"),
        "status_code": meta.get("status_code"),
        "response_summary": _response_summary(response),
    }
    return response, exchange


def _response_summary(response: dict) -> dict:
    summary = {}
    for key in ("success", "msg", "message", "code", "status"):
        if key in response:
            summary[key] = response.get(key)
    data = response.get("data")
    if isinstance(data, dict):
        summary["data_keys"] = sorted(str(key) for key in data.keys())[:12]
    elif isinstance(data, list):
        summary["data_count"] = len(data)
    if summary:
        return summary
    return {"top_level_keys": sorted(str(key) for key in response.keys())[:12]}


def _build_api_evidence(context, flow_key, flow, observations, readback_requests, assertion_error):
    state = getattr(context, "batch_api_evidence", {}) or {}
    before = {
        item["selected_id"]: item
        for item in state.get("before_observations", [])
        if isinstance(item, dict) and item.get("selected_id")
    }
    merged_observations = []
    for item in observations:
        merged = dict(item)
        before_item = before.get(item.get("selected_id"))
        merged["before_value"] = before_item.get("actual_value", "") if before_item else ""
        merged["before_raw_actual"] = before_item.get("raw_actual") if before_item else None
        merged["before_matched_target"] = bool(before_item.get("passed")) if before_item else None
        merged["changed_from_before"] = (
            before_item.get("raw_actual") != item.get("raw_actual")
            if before_item else None
        )
        merged_observations.append(merged)

    scenario = getattr(context, "scenario", None)
    write_exchange = state.get("write_exchange") or {}
    write_response = write_exchange.get("response_summary") or {}
    write_response = {
        **write_response,
        "status_code": write_exchange.get("status_code"),
    }
    result = "FAIL" if assertion_error else "PASS"
    return {
        "scenario": getattr(scenario, "name", ""),
        "feature": getattr(getattr(scenario, "feature", None), "name", ""),
        "flow_key": flow_key,
        "selected_ids": list(flow.selected_ids),
        "expected_field": flow.expected_field,
        "expected_value": flow.expected_value,
        "assertion": {
            "result": result,
            "logic": flow.assertion,
            "message": str(assertion_error) if assertion_error else "Precondition differed from target and post-write readback matched expected value.",
        },
        "source_requests": state.get("source_requests", []),
        "setup_requests": state.get("setup_requests", []),
        "before_requests": state.get("before_requests", []),
        "write_request": {
            "method": write_exchange.get("method"),
            "path": write_exchange.get("path"),
            "params": write_exchange.get("params"),
            "url": write_exchange.get("url"),
        },
        "write_response": write_response,
        "readback_requests": readback_requests,
        "observations": merged_observations,
    }
