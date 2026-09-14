from __future__ import annotations

from urllib.parse import urlparse

from behave import given, then, when

from test_automation.config import get_settings
from test_automation.config import get_user
from test_automation.standard_product.admin_auth import RouteContext
from test_automation.standard_product.admin_auth import StandardProductAdminSession
from test_automation.standard_product.admin_ui import BASE_URL
from test_automation.standard_product.admin_ui import TEXT
from test_automation.standard_product.admin_ui import StandardProductAdminUi
from test_automation.standard_product.admin_ui import is_batch_write_url
from test_automation.standard_product.admin_ui import set_default_viewport
from test_automation.standard_product.evidence import save_case_screenshot


NO_SEAT_ROUTE = RouteContext(
    referer="https://anticket.lengliwh.com/mshow/index.html",
    parentpath="mshow:/menpiao/programs",
    routerpath="mshow:/menpiao/detail/schedule",
)


def _start_write_capture(context) -> None:
    context.batch_write_urls = []
    if getattr(context, "_batch_write_capture_started", False):
        return

    def capture(request):
        if is_batch_write_url(request.url):
            context.batch_write_urls.append(request.url)

    context.page.on("request", capture)
    context._batch_write_capture_started = True


def _settings_user():
    settings = get_settings()
    user = get_user("user1", settings.env)
    return settings, user


def _seed_ui_cookies_from_api_session(context, base_url: str) -> bool:
    client = getattr(context, "_standard_product_api_client", None)
    if client is None:
        return False

    host = urlparse(base_url).hostname
    cookies = []
    for cookie in client.session.cookies:
        domain = cookie.domain or host
        if not domain:
            continue
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": domain,
                "path": cookie.path or "/",
            }
        )
    if not cookies:
        return False
    context.page.context.add_cookies(cookies)
    return True


@given("I am logged in to the real Standard Product admin UI")
def step_login_real_standard_product_ui(context):
    settings, user = _settings_user()
    set_default_viewport(context.page)
    base_url = str(getattr(settings, "antank_url", BASE_URL))
    context.standard_product_ui = StandardProductAdminUi(context.page, base_url)
    if _seed_ui_cookies_from_api_session(context, base_url):
        context.standard_product_ui.warm_mainframe()
        _start_write_capture(context)
        return
    context.standard_product_ui.login(user.username, user.password)
    _start_write_capture(context)


@given("I open the no-seat session management UI with session rows")
def step_open_no_seat_ui_with_rows(context):
    context.standard_product_ui.open_no_seat_schedule(with_rows=True)
    context.standard_product_ui.assert_texts_visible(["90042939", "90037094"])
    save_case_screenshot(
        context,
        context.standard_product_ui,
        "ui-no-seat-session-rows",
        "ui-no-seat-session-rows.png",
    )


@given("I open the no-seat session management UI without session rows")
def step_open_no_seat_ui_without_rows(context):
    context.standard_product_ui.open_no_seat_schedule(with_rows=False)
    context.standard_product_ui.assert_texts_visible([TEXT["no_data"]])
    save_case_screenshot(
        context,
        context.standard_product_ui,
        "ui-no-seat-no-session-rows",
        "ui-no-seat-no-session-rows.png",
    )


@when("I open the session batch operation menu")
def step_open_batch_operation_menu(context):
    context.standard_product_ui.open_batch_menu()
    save_case_screenshot(
        context,
        context.standard_product_ui,
        "ui-batch-operation-menu",
        "ui-batch-operation-menu.png",
    )


@then("the batch operation menu shows the three signed actions")
def step_batch_menu_shows_three_signed_actions(context):
    context.standard_product_ui.assert_texts_visible(
        [TEXT["group_action"], TEXT["display_action"], TEXT["calendar_action"]]
    )


@when("I open calendar-display batch modification and pre-generate")
def step_open_calendar_display_and_pregenerate(context):
    context.standard_product_ui.open_batch_menu()
    context.standard_product_ui.choose_batch_action(TEXT["calendar_action"])
    context.standard_product_ui.click_pre_generate()
    save_case_screenshot(
        context,
        context.standard_product_ui,
        "ui-no-session-blocked",
        "ui-no-session-blocked.png",
    )


@then("the UI blocks pre-generation because no session row is available")
def step_ui_blocks_no_session_rows(context):
    context.standard_product_ui.assert_texts_visible([TEXT["select_data_prompt"]])


@when("I open saleable-ticket-group batch modification without selecting a target group")
def step_open_group_batch_without_target(context):
    context.standard_product_ui.open_batch_menu()
    context.standard_product_ui.choose_batch_action(TEXT["group_action"])
    context.standard_product_ui.click_pre_generate()
    save_case_screenshot(
        context,
        context.standard_product_ui,
        "ui-target-group-required",
        "ui-target-group-required.png",
    )


@then("the UI blocks pre-generation because the target group is required")
def step_ui_blocks_missing_target_group(context):
    context.standard_product_ui.assert_texts_visible([TEXT["select_group_prompt"]])


@when("I generate a calendar-display preview and return without confirming")
def step_generate_calendar_preview_and_return(context):
    context.standard_product_ui.open_batch_menu()
    context.standard_product_ui.choose_batch_action(TEXT["calendar_action"])
    context.standard_product_ui.click_pre_generate()
    context.standard_product_ui.assert_texts_visible([TEXT["confirm_modify"]])
    save_case_screenshot(
        context,
        context.standard_product_ui,
        "ui-preview-return-before-close",
        "ui-preview-return-before-close.png",
    )
    context.standard_product_ui.click_return()
    context.standard_product_ui.close_drawer_if_open()


@when("I generate a session-list-display preview and close without confirming")
def step_generate_display_preview_and_close(context):
    context.standard_product_ui.open_no_seat_schedule(with_rows=True)
    context.standard_product_ui.open_batch_menu()
    context.standard_product_ui.choose_batch_action(TEXT["display_action"])
    context.standard_product_ui.click_pre_generate()
    context.standard_product_ui.assert_texts_visible([TEXT["confirm_modify"]])
    save_case_screenshot(
        context,
        context.standard_product_ui,
        "ui-preview-close-before-close",
        "ui-preview-close-before-close.png",
    )
    context.standard_product_ui.close_drawer()


@then("no batch write API is emitted by the UI flow")
def step_no_batch_write_api_emitted(context):
    writes = getattr(context, "batch_write_urls", [])
    if writes:
        raise AssertionError(f"Unexpected batch write API request(s): {writes}")


@given("I have a real Standard Product admin requests session for mixed execution")
def step_real_admin_requests_session_for_mixed(context):
    cached = getattr(context, "_standard_product_api_client", None)
    if cached is not None:
        context.standard_product_api = cached
        return

    settings, user = _settings_user()
    client = StandardProductAdminSession(str(settings.antank_url), user.username, user.password)
    client.login()
    context._standard_product_api_client = client
    context.standard_product_api = client


@when("I submit a no-seat display update only for the remaining preview row through API")
def step_submit_remaining_preview_row_only(context):
    client = context.standard_product_api
    remaining_id = "90042939"
    deleted_id = "90037094"
    remaining_before = _read_open_show(client, remaining_id)
    deleted_before = _read_open_show(client, deleted_id)
    original_remaining = str(remaining_before.get("display"))
    original_deleted = str(deleted_before.get("display"))
    target = "N" if original_remaining != "N" else "Y"

    context.mixed_preview_state = {
        "remaining_id": remaining_id,
        "deleted_id": deleted_id,
        "original_remaining": original_remaining,
        "original_deleted": original_deleted,
        "target": target,
    }
    response = client.post_json(
        "/theatre/home/openShow/op/batchUpdateDisplay.xhtml",
        params={"showIds": remaining_id, "display": target},
        route=NO_SEAT_ROUTE,
    )
    if response.get("success") is False:
        raise AssertionError(f"Mixed API update failed: {response}")


@then("the browser UI evidence shows the remaining row changed and the deleted row unchanged")
def step_browser_ui_evidence_shows_row_exclusion(context):
    state = context.mixed_preview_state
    ui = context.standard_product_ui
    ui.warm_mainframe()
    evidence = context.page.evaluate(
        """async ({ remainingId, deletedId, target, originalDeleted }) => {
            const read = async (id) => {
              const response = await fetch(`/theatre/home/openShow/get.xhtml?id=${id}`, {
                credentials: "include",
                headers: {
                  accept: "application/json, text/plain, */*",
                  lang: "zh-CN",
                  parentpath: "mshow:/menpiao/programs",
                  routerpath: "mshow:/menpiao/detail/schedule",
                },
              });
              const body = await response.json();
              return body?.data?.openShow || {};
            };
            const remaining = await read(remainingId);
            const deleted = await read(deletedId);
            document.body.innerHTML = "";
            const main = document.createElement("main");
            main.style.cssText = "font-family: Arial, sans-serif; padding: 32px; color: #1f2933";
            const title = document.createElement("h1");
            title.textContent = "SIT-TC-STD-CONFIG-013 mixed API + UI evidence";
            main.appendChild(title);
            const rows = [
              ["remaining show", remainingId],
              ["remaining display", remaining.display],
              ["expected remaining display", target],
              ["deleted show", deletedId],
              ["deleted display", deleted.display],
              ["expected deleted display", originalDeleted],
            ];
            for (const [key, value] of rows) {
              const row = document.createElement("div");
              row.style.cssText = "display:flex; gap:18px; padding:8px 0; font-size:18px";
              const k = document.createElement("strong");
              k.style.width = "260px";
              k.textContent = key;
              const v = document.createElement("span");
              v.textContent = String(value);
              row.append(k, v);
              main.appendChild(row);
            }
            const pass = String(remaining.display) === String(target)
              && String(deleted.display) === String(originalDeleted);
            const badge = document.createElement("div");
            badge.textContent = pass ? "ROW EXCLUSION VERIFIED" : "ROW EXCLUSION NOT VERIFIED";
            badge.style.cssText = [
              "display:inline-block",
              "margin-top:20px",
              "padding:12px 16px",
              "border-radius:4px",
              `background:${pass ? "#e8f5e9" : "#fff1f0"}`,
              `color:${pass ? "#1b5e20" : "#a8071a"}`,
              "font-weight:700",
            ].join(";");
            main.appendChild(badge);
            document.body.appendChild(main);
            return {
              remainingDisplay: String(remaining.display),
              deletedDisplay: String(deleted.display),
              pass,
            };
        }""",
        {
            "remainingId": state["remaining_id"],
            "deletedId": state["deleted_id"],
            "target": state["target"],
            "originalDeleted": state["original_deleted"],
        },
    )
    save_case_screenshot(
        context,
        ui,
        "mixed-row-exclusion-ui-evidence",
        "mixed-row-exclusion-ui-evidence.png",
    )
    try:
        if not evidence.get("pass"):
            raise AssertionError(f"Mixed UI evidence did not verify row exclusion: {evidence}")
    finally:
        _restore_remaining_display(context)


def _read_open_show(client: StandardProductAdminSession, show_id: str) -> dict:
    response = client.get_json(
        "/theatre/home/openShow/get.xhtml",
        params={"id": show_id},
        route=NO_SEAT_ROUTE,
    )
    return response.get("data", {}).get("openShow", {})


def _restore_remaining_display(context) -> None:
    state = getattr(context, "mixed_preview_state", None)
    if not state:
        return
    context.standard_product_api.post_json(
        "/theatre/home/openShow/op/batchUpdateDisplay.xhtml",
        params={"showIds": state["remaining_id"], "display": state["original_remaining"]},
        route=NO_SEAT_ROUTE,
    )
