from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .admin_auth import RouteContext
from .admin_auth import StandardProductAdminSession


@dataclass(frozen=True)
class ApiRequest:
    method: str
    path: str
    params: dict[str, Any]
    route: RouteContext


@dataclass(frozen=True)
class BatchApiFlow:
    key: str
    read: tuple[ApiRequest, ...]
    write: ApiRequest
    readback: tuple[ApiRequest, ...]
    selected_ids: tuple[str, ...]
    assertion: str
    expected_field: str
    expected_value: str
    setup_param: str | None = None
    setup_value: str | None = None


MSHOW_NEW_SCHEDULE = RouteContext(
    referer="https://anticket.lengliwh.com/mshow/index.html",
    routerpath="mshow:/menpiao/newDetail/newSchedule",
)

SEAT_SCHEDULE = RouteContext(
    referer="https://anticket.lengliwh.com/seatadmin/index.html",
    parentpath="seatadmin:/seat/programs",
    routerpath="seatadmin:/seat/detail/schedule",
)

MSHOW_DETAIL_SCHEDULE = RouteContext(
    referer="https://anticket.lengliwh.com/mshow/index.html",
    parentpath="mshow:/menpiao/programs",
    routerpath="mshow:/menpiao/detail/schedule",
)


SEAT_LIST = ApiRequest(
    "GET",
    "/theatre/home/schedule/list.xhtml",
    {
        "programId": "225198",
        "playTimeFrom": "",
        "playTimeEnd": "",
        "keyword": "",
        "scheduleId": "",
        "status": "",
        "overdue": "",
        "ticketTypeIds": "",
        "pageNo": "1",
        "pageSize": "10",
    },
    SEAT_SCHEDULE,
)

ADMISSION_LIST = ApiRequest(
    "GET",
    "/theatre/home/openShow/listShowByTimeRange.xhtml",
    {
        "programId": "225562",
        "fromDateTime": "",
        "toDateTime": "",
        "keyword": "",
        "isExpired": "N",
        "status": "",
    },
    MSHOW_NEW_SCHEDULE,
)

NO_SEAT_LIST = ApiRequest(
    "GET",
    "/theatre/home/openShow/listShowByTimeRange.xhtml",
    {
        "programId": "223334",
        "fromDateTime": "",
        "toDateTime": "",
        "keyword": "",
        "isExpired": "",
        "status": "",
        "ticketTypeIds": "",
    },
    MSHOW_DETAIL_SCHEDULE,
)


FLOWS: dict[str, BatchApiFlow] = {
    "seat saleable group": BatchApiFlow(
        key="seat saleable group",
        selected_ids=("19839", "19837"),
        assertion="schedule_user_group",
        expected_field="checkIdList",
        expected_value="57689",
        setup_param="groups",
        setup_value="56776",
        read=(SEAT_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/schedule/setting/batchSaveUserGroup.xhtml",
            {"scheduleIds": "19839,19837", "groups": "57689"},
            SEAT_SCHEDULE,
        ),
        readback=(
            ApiRequest(
                "GET",
                "/theatre/home/schedule/setting/getUserGroup.xhtml",
                {"scheduleId": "19839"},
                SEAT_SCHEDULE,
            ),
            ApiRequest(
                "GET",
                "/theatre/home/schedule/setting/getUserGroup.xhtml",
                {"scheduleId": "19837"},
                SEAT_SCHEDULE,
            ),
        ),
    ),
    "admission saleable group": BatchApiFlow(
        key="admission saleable group",
        selected_ids=("90051349", "90051350"),
        assertion="open_show_list_group",
        expected_field="groupIdList",
        expected_value="57689",
        setup_param="groups",
        setup_value="56776",
        read=(ADMISSION_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/openShow/op/batchSaveUserGroup.xhtml",
            {"showIds": "90051349,90051350", "groups": "57689"},
            MSHOW_NEW_SCHEDULE,
        ),
        readback=(ADMISSION_LIST,),
    ),
    "no seat saleable group": BatchApiFlow(
        key="no seat saleable group",
        selected_ids=("90042939", "90037094"),
        assertion="open_show_list_group",
        expected_field="groupIdList",
        expected_value="57689",
        setup_param="groups",
        setup_value="56776",
        read=(NO_SEAT_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/openShow/op/batchSaveUserGroup.xhtml",
            {"showIds": "90042939,90037094", "groups": "57689"},
            MSHOW_DETAIL_SCHEDULE,
        ),
        readback=(NO_SEAT_LIST,),
    ),
    "seat calendar display": BatchApiFlow(
        key="seat calendar display",
        selected_ids=("19839", "19837"),
        assertion="schedule_list_field",
        expected_field="showCalendar",
        expected_value="Y",
        read=(SEAT_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/schedule/op/batchUpdateShowCalendar.xhtml",
            {"scheduleIds": "19839,19837", "showCalendar": "Y"},
            SEAT_SCHEDULE,
        ),
        readback=(SEAT_LIST,),
    ),
    "admission calendar display": BatchApiFlow(
        key="admission calendar display",
        selected_ids=("90051349", "90051350"),
        assertion="open_show_detail_field",
        expected_field="showCalendar",
        expected_value="Y",
        read=(ADMISSION_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/openShow/op/batchUpdateShowCalendar.xhtml",
            {"showIds": "90051349,90051350", "showCalendar": "Y"},
            MSHOW_NEW_SCHEDULE,
        ),
        readback=(
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90051349"}, MSHOW_NEW_SCHEDULE),
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90051350"}, MSHOW_NEW_SCHEDULE),
        ),
    ),
    "no seat calendar display": BatchApiFlow(
        key="no seat calendar display",
        selected_ids=("90042939", "90037094"),
        assertion="open_show_detail_field",
        expected_field="showCalendar",
        expected_value="N",
        read=(NO_SEAT_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/openShow/op/batchUpdateShowCalendar.xhtml",
            {"showIds": "90042939,90037094", "showCalendar": "N"},
            MSHOW_DETAIL_SCHEDULE,
        ),
        readback=(
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90042939"}, MSHOW_DETAIL_SCHEDULE),
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90037094"}, MSHOW_DETAIL_SCHEDULE),
        ),
    ),
    "seat session list display": BatchApiFlow(
        key="seat session list display",
        selected_ids=("19839", "19837"),
        assertion="schedule_list_field",
        expected_field="display",
        expected_value="Y",
        read=(
            ApiRequest(
                "GET",
                "/theatre/home/ticket/program/get.xhtml",
                {"id": "225198"},
                SEAT_SCHEDULE,
            ),
        ),
        write=ApiRequest(
            "POST",
            "/theatre/home/schedule/op/batchUpdateDisplay.xhtml",
            {"scheduleIds": "19839,19837", "display": "Y"},
            SEAT_SCHEDULE,
        ),
        readback=(SEAT_LIST,),
    ),
    "admission session list display": BatchApiFlow(
        key="admission session list display",
        selected_ids=("90051349", "90051350"),
        assertion="open_show_detail_field",
        expected_field="display",
        expected_value="Y",
        read=(ADMISSION_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/openShow/op/batchUpdateDisplay.xhtml",
            {"showIds": "90051349,90051350", "display": "Y"},
            MSHOW_NEW_SCHEDULE,
        ),
        readback=(
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90051349"}, MSHOW_NEW_SCHEDULE),
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90051350"}, MSHOW_NEW_SCHEDULE),
        ),
    ),
    "no seat session list display": BatchApiFlow(
        key="no seat session list display",
        selected_ids=("90042939", "90037094"),
        assertion="open_show_detail_field",
        expected_field="display",
        expected_value="Y",
        read=(NO_SEAT_LIST,),
        write=ApiRequest(
            "POST",
            "/theatre/home/openShow/op/batchUpdateDisplay.xhtml",
            {"showIds": "90042939,90037094", "display": "Y"},
            MSHOW_DETAIL_SCHEDULE,
        ),
        readback=(
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90042939"}, MSHOW_DETAIL_SCHEDULE),
            ApiRequest("GET", "/theatre/home/openShow/get.xhtml", {"id": "90037094"}, MSHOW_DETAIL_SCHEDULE),
        ),
    ),
}


def execute_request(client: StandardProductAdminSession, request: ApiRequest) -> dict[str, Any]:
    if request.method == "GET":
        return client.get_json(request.path, params=request.params, route=request.route)
    if request.method == "POST":
        return client.post_json(request.path, params=request.params, route=request.route)
    raise ValueError(f"Unsupported method: {request.method}")


def request_summary(request: ApiRequest) -> dict[str, Any]:
    return {
        "method": request.method,
        "path": request.path,
        "params": {key: str(value) for key, value in request.params.items()},
    }


def precondition_setup_request(flow: BatchApiFlow) -> ApiRequest | None:
    if flow.setup_param and flow.setup_value is not None:
        if flow.setup_param not in flow.write.params:
            raise AssertionError(
                f"{flow.key} setup_param {flow.setup_param!r} is not present in write params"
            )
        if str(flow.setup_value) == str(flow.expected_value):
            raise AssertionError(
                f"{flow.key} setup_value must differ from expected_value {flow.expected_value!r}"
            )
        params = dict(flow.write.params)
        params[flow.setup_param] = flow.setup_value
        return ApiRequest(flow.write.method, flow.write.path, params, flow.write.route)

    if flow.expected_value not in {"Y", "N"}:
        return None
    if flow.expected_field not in flow.write.params:
        return None
    params = dict(flow.write.params)
    params[flow.expected_field] = "N" if flow.expected_value == "Y" else "Y"
    return ApiRequest(flow.write.method, flow.write.path, params, flow.write.route)


def assert_write_accepted(response: dict[str, Any]) -> None:
    if response.get("success") is False:
        raise AssertionError(f"write API rejected request: {response}")


def assert_readback_contains(flow: BatchApiFlow, responses: list[dict[str, Any]]) -> None:
    observations = readback_observations(flow, responses)
    failed = [item for item in observations if not item["passed"]]
    if failed:
        details = "; ".join(
            f"{item['selected_id']} expected {item['field']} {item['comparison']} "
            f"{item['expected_value']}, actual={item['actual_value']}"
            for item in failed
        )
        raise AssertionError(details)


def assert_precondition_changed_to_target(
    flow: BatchApiFlow,
    before_observations: list[dict[str, Any]],
    after_observations: list[dict[str, Any]],
) -> None:
    """Ensure the scenario proves the update action, not just the final state."""
    before_by_id = {
        item["selected_id"]: item
        for item in before_observations
        if isinstance(item, dict) and item.get("selected_id")
    }
    failures = []
    for after in after_observations:
        selected_id = after.get("selected_id")
        before = before_by_id.get(selected_id)
        if not before:
            failures.append(f"{selected_id}: missing before observation")
            continue
        if before.get("passed"):
            failures.append(
                f"{selected_id}: before already matched target "
                f"{flow.expected_field}={flow.expected_value} ({before.get('actual_value')})"
            )
        if before.get("raw_actual") == after.get("raw_actual"):
            failures.append(
                f"{selected_id}: before and after are identical "
                f"({after.get('actual_value')})"
            )
        if not after.get("passed"):
            failures.append(
                f"{selected_id}: after did not match target "
                f"{flow.expected_field}={flow.expected_value} ({after.get('actual_value')})"
            )
    if failures:
        raise AssertionError("; ".join(failures))


def readback_observations(flow: BatchApiFlow, responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if flow.assertion == "open_show_list_group":
        rows = _rows_by_id(responses, flow.selected_ids)
        expected = int(flow.expected_value)
        out = []
        for selected_id in flow.selected_ids:
            row = rows[selected_id]
            groups = row.get(flow.expected_field) or []
            normalized = {str(item) for item in groups}
            out.append(_observation(
                flow,
                selected_id,
                groups,
                expected in groups or flow.expected_value in normalized,
                "contains",
            ))
        return out

    if flow.assertion == "schedule_user_group":
        if len(responses) < len(flow.selected_ids):
            raise AssertionError(
                f"readback returned {len(responses)} response(s) for {len(flow.selected_ids)} selected id(s)"
            )
        out = []
        for selected_id, response in zip(flow.selected_ids, responses, strict=False):
            check_ids = response.get("data", {}).get(flow.expected_field) or []
            normalized = {str(item) for item in check_ids}
            out.append(_observation(
                flow,
                selected_id,
                check_ids,
                int(flow.expected_value) in check_ids or flow.expected_value in normalized,
                "contains",
            ))
        return out

    if flow.assertion == "schedule_list_field":
        rows = _rows_by_id(responses, flow.selected_ids)
        out = []
        for selected_id in flow.selected_ids:
            row = rows[selected_id]
            actual = row.get(flow.expected_field)
            out.append(_observation(
                flow,
                selected_id,
                actual,
                str(actual) == flow.expected_value,
                "equals",
            ))
        return out

    if flow.assertion == "open_show_detail_field":
        if len(responses) < len(flow.selected_ids):
            raise AssertionError(
                f"readback returned {len(responses)} response(s) for {len(flow.selected_ids)} selected id(s)"
            )
        out = []
        for selected_id, response in zip(flow.selected_ids, responses, strict=False):
            row = response.get("data", {}).get("openShow", {})
            if str(row.get("id")) != selected_id:
                raise AssertionError(f"readback detail id mismatch for {selected_id}: {row}")
            actual = row.get(flow.expected_field)
            out.append(_observation(
                flow,
                selected_id,
                actual,
                str(actual) == flow.expected_value,
                "equals",
            ))
        return out

    text = json.dumps(responses, ensure_ascii=False, sort_keys=True)
    raise AssertionError(f"unsupported readback assertion {flow.assertion!r}: {text[:500]}")


def _observation(
    flow: BatchApiFlow,
    selected_id: str,
    actual: Any,
    passed: bool,
    comparison: str,
) -> dict[str, Any]:
    return {
        "selected_id": selected_id,
        "field": flow.expected_field,
        "expected_value": flow.expected_value,
        "actual_value": _display_value(actual),
        "raw_actual": actual,
        "comparison": comparison,
        "passed": passed,
    }


def _display_value(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return ""
    return str(value)


def _rows_by_id(responses: list[dict[str, Any]], selected_ids: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            row_id = value.get("id")
            if str(row_id) in selected_ids:
                found[str(row_id)] = value
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for response in responses:
        visit(response)

    missing = [selected_id for selected_id in selected_ids if selected_id not in found]
    if missing:
        text = json.dumps(responses, ensure_ascii=False, sort_keys=True)
        raise AssertionError(f"readback missing selected id(s) {missing}: {text[:500]}")
    return found
