"""AUTH-009 API-first UI validation reference.

Scenario: SIT-TC-WEB-AUTH-009 Registered user logs in via email and password.

Best-practice split:
  1. API owns the workflow assertions:
     getLogonInfo -> getMemberInfo -> getPersonalInfo.
  2. UI only validates the final user-visible state:
     the same session opens #/my/profile and shows the logged-in email.

The one unavoidable UI step is session bootstrap. The site protects password
login with an image captcha, so authed_http refreshes storage_state.json through
the existing Playwright login crawler when needed. After that, requests and
Playwright reuse the same cookie jar.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

_AUTOMATION = Path(__file__).resolve().parents[3]
_STATE_PATH = _AUTOMATION / "07-artifacts" / "api_smoke" / "storage_state.json"
_ARTIFACT_DIR = _AUTOMATION / "07-artifacts" / "api_first_ui"


def _env_value(key: str) -> str:
    value = os.environ.get(key)
    if value:
        return value.strip()

    env_name = os.environ.get("ENV", "sit")
    env_file = _AUTOMATION / "06-envs" / f".env.{env_name}"
    if not env_file.exists():
        return ""

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, raw_value = line.partition("=")
        if name.strip() == key:
            return raw_value.strip().strip("'\"")
    return ""


def _context_options(**kwargs: Any) -> dict[str, Any]:
    user = os.environ.get("WK_BASIC_AUTH_USER")
    password = os.environ.get("WK_BASIC_AUTH_PASS")
    if user and password:
        kwargs["http_credentials"] = {"username": user, "password": password}
    return kwargs


@pytest.fixture(scope="module")
def expected_email() -> str:
    email = _env_value("TA_WEBSITE_USERNAME")
    if not email or email == "your-test-account@example.com":
        pytest.skip("TA_WEBSITE_USERNAME is not configured")
    return email


def _same_email(left: str | None, right: str | None) -> bool:
    return bool(left and right and left.strip().casefold() == right.strip().casefold())


def _email_visible_in_text(email: str, text: str) -> bool:
    if not email or not text:
        return False
    haystack = text.casefold()
    if email.casefold() in haystack:
        return True
    if "@" not in email:
        return email.casefold() in haystack
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        summary_mask = f"{name[:1]}*@{domain}"
        profile_mask = f"{name[:1]}***@{domain}"
    else:
        summary_mask = f"{name[:2]}***{name[-1:]}@{domain}"
        profile_mask = f"{name[:3]}***@{domain}"
    candidates = {name, summary_mask, profile_mask}
    return any(candidate and candidate.casefold() in haystack for candidate in candidates)


def _request_json(session, method: str, url: str, *, endpoint: str, **kwargs) -> dict[str, Any]:
    resp = session.request(method, url, timeout=10, **kwargs)
    assert resp.status_code == 200, (
        f"{endpoint}: expected HTTP 200, got {resp.status_code}. "
        f"Body head: {resp.text[:300]!r}"
    )
    try:
        body = resp.json()
    except ValueError as exc:
        pytest.fail(f"{endpoint}: response is not JSON: {exc}; body={resp.text[:300]!r}")

    assert body.get("errcode") == "0000", (
        f"{endpoint}: expected errcode '0000', got {body.get('errcode')!r}. "
        f"Body head: {resp.text[:300]!r}"
    )
    assert body.get("data") is not None, f"{endpoint}: response data is empty: {body!r}"
    return body


def _profile_text(page) -> str:
    return page.evaluate(
        """() => {
            const text = document.body ? document.body.innerText || "" : "";
            const values = Array.from(document.querySelectorAll("input, textarea"))
              .map((el) => el.value || "")
              .filter(Boolean)
              .join("\\n");
            return `${text}\\n${values}`;
        }"""
    )


def test_sit_tc_web_auth_009_api_chain_then_ui_profile(
    authed_http,
    base_url: str,
    expected_email: str,
) -> None:
    """API chains the identity flow; UI verifies the final profile state."""
    logon = _request_json(
        authed_http,
        "POST",
        base_url + "/ucenter/rest/getLogonInfo.xhtml",
        endpoint="ucenter.rest.getLogonInfo",
    )
    logon_data = logon["data"]
    logon_id = logon_data.get("id")
    logon_email = logon_data.get("email")
    assert isinstance(logon_id, int) and logon_id > 0, logon_data
    assert _same_email(logon_email, expected_email), (
        f"configured email {expected_email!r} != API logon email {logon_email!r}"
    )

    member = _request_json(
        authed_http,
        "GET",
        base_url + "/thvendor/member/info/getMemberInfo.xhtml",
        endpoint="thvendor.member.info.getMemberInfo",
    )
    member_data = member["data"]
    assert int(member_data.get("memberId")) == int(logon_id), (
        f"member API identity mismatch: logon id={logon_id}, "
        f"memberId={member_data.get('memberId')}"
    )
    assert _same_email(member_data.get("email"), logon_email), (
        f"member API email mismatch: logon={logon_email!r}, "
        f"member={member_data.get('email')!r}"
    )

    _request_json(
        authed_http,
        "GET",
        base_url + "/thvendor/member/info/getPersonalInfo.xhtml",
        endpoint="thvendor.member.info.getPersonalInfo",
    )

    if not _STATE_PATH.exists():
        pytest.skip(f"no storage_state.json at {_STATE_PATH}")

    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = _ARTIFACT_DIR / "SIT-TC-WEB-AUTH-009-profile.png"
    result_path = _ARTIFACT_DIR / "SIT-TC-WEB-AUTH-009-api-first-ui.json"

    target = base_url + "/websitehtml/index.html#/my/profile"
    final_url = ""
    page_text = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**_context_options(
            storage_state=str(_STATE_PATH),
            ignore_https_errors=True,
            viewport={"width": 1366, "height": 768},
        ))
        page = context.new_page()
        try:
            page.goto(target, wait_until="commit", timeout=30000)
            try:
                page.wait_for_load_state("load", timeout=15000)
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                pass

            try:
                page.wait_for_function(
                    """(email) => {
                        if (location.hash.includes("/login")) return true;
                        const body = document.body ? document.body.innerText || "" : "";
                        const values = Array.from(document.querySelectorAll("input, textarea"))
                          .map((el) => el.value || "")
                          .join("\\n");
                        return `${body}\\n${values}`.toLowerCase()
                          .includes(String(email).toLowerCase());
                    }""",
                    arg=expected_email,
                    timeout=15000,
                )
            except PlaywrightTimeoutError:
                pass

            final_url = page.url
            page_text = _profile_text(page)
            page.screenshot(path=str(screenshot_path), full_page=False)
        finally:
            context.close()
            browser.close()

    result_path.write_text(
        json.dumps(
            {
                "case_id": "SIT-TC-WEB-AUTH-009",
                "pattern": "api-first-ui-validation",
                "api_member_id": logon_id,
                "api_email": logon_email,
                "ui_url": final_url,
                "screenshot": str(screenshot_path),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    assert "#/login" not in final_url, (
        f"UI session was rejected and redirected to login: {final_url}"
    )
    assert "#/my" in final_url, f"expected member area URL, got {final_url}"
    assert _email_visible_in_text(expected_email, page_text), (
        "profile UI did not expose the same email returned by the API. "
        f"url={final_url}; text_head={page_text[:300]!r}"
    )
