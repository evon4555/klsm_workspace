from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import Browser
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


_AUTOMATION = Path(__file__).resolve().parents[3]
_DEFAULT_STATE = _AUTOMATION / "07-artifacts" / "api_smoke" / "storage_state.json"


@dataclass(frozen=True)
class Auth009Result:
    member_id: int
    email: str
    final_url: str
    shots: list[tuple[str, str]]


def _base_url(raw: str) -> str:
    return os.environ.get("WK_API_BASE_URL", raw).rstrip("/")


def _host(base_url: str) -> str:
    return urllib.parse.urlparse(base_url).netloc


def _domain_matches(site_host: str, cookie_domain: str) -> bool:
    domain = (cookie_domain or "").lstrip(".")
    return site_host == domain or site_host.endswith("." + domain)


def _context_options(**kwargs: Any) -> dict[str, Any]:
    user = os.environ.get("WK_BASIC_AUTH_USER")
    password = os.environ.get("WK_BASIC_AUTH_PASS")
    if user and password:
        kwargs["http_credentials"] = {"username": user, "password": password}
    return kwargs


def _new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "qa-harness/auth009-api-first",
        "Accept": "application/json, text/plain, */*",
        "cmpappkey": "ShanghaiCS",
        "lang": "en",
        "Referer": "https://anticket.lengliwh.com/websitehtml/index.html",
    })
    session.verify = False
    return session


def _load_cookies(session: requests.Session, base_url: str, state_path: Path) -> int:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    site_host = _host(base_url)
    session.cookies.clear()
    loaded = 0
    for cookie in state.get("cookies", []):
        domain = cookie.get("domain") or ""
        if not _domain_matches(site_host, domain):
            continue
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=domain,
            path=cookie.get("path", "/"),
        )
        loaded += 1
    return loaded


def _request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    endpoint: str,
    **kwargs: Any,
) -> dict[str, Any]:
    resp = session.request(method, url, timeout=10, **kwargs)
    if resp.status_code != 200:
        raise AssertionError(
            f"{endpoint}: expected HTTP 200, got {resp.status_code}. "
            f"Body head: {resp.text[:300]!r}"
        )
    try:
        body = resp.json()
    except ValueError as exc:
        raise AssertionError(
            f"{endpoint}: response is not JSON: {exc}; body={resp.text[:300]!r}"
        ) from exc

    if body.get("errcode") != "0000":
        raise AssertionError(
            f"{endpoint}: expected errcode '0000', got {body.get('errcode')!r}. "
            f"Body head: {resp.text[:300]!r}"
        )
    if body.get("data") is None:
        raise AssertionError(f"{endpoint}: response data is empty: {body!r}")
    return body


def _session_is_alive(session: requests.Session, base_url: str) -> bool:
    try:
        body = _request_json(
            session,
            "POST",
            base_url + "/ucenter/rest/getLogonInfo.xhtml",
            endpoint="ucenter.rest.getLogonInfo",
        )
        return bool(body.get("data"))
    except Exception:
        return False


def _refresh_state_with_browser(
    browser: Browser,
    base_url: str,
    email: str,
    password: str,
    state_path: Path,
) -> None:
    from test_automation.web.website_login_page import WebsiteLoginPage

    state_path.parent.mkdir(parents=True, exist_ok=True)
    ctx = browser.new_context(**_context_options(
        ignore_https_errors=True,
        viewport={"width": 1366, "height": 768},
    ))
    page = ctx.new_page()
    try:
        login_page = WebsiteLoginPage(page, base_url, screenshot_dir=state_path.parent)
        login_page.open()
        login_page.login(email=email, password=password, max_attempts=8)
        ctx.storage_state(path=str(state_path))
    except Exception:
        shot = state_path.parent / "login_error.png"
        try:
            page.screenshot(path=str(shot), full_page=False, timeout=10000)
        except Exception:
            pass
        raise
    finally:
        ctx.close()


def _refresh_state(
    base_url: str,
    email: str,
    password: str,
    *,
    browser: Browser | None = None,
    state_path: Path = _DEFAULT_STATE,
) -> None:
    if browser is not None:
        _refresh_state_with_browser(browser, base_url, email, password, state_path)
        return

    tools_dir = _AUTOMATION / "04-tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from crawl_api_endpoints import login_and_save_state

    login_and_save_state(base_url, email, password)
    if state_path != _DEFAULT_STATE and _DEFAULT_STATE.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_DEFAULT_STATE, state_path)


def authed_session_from_state(
    base_url: str,
    email: str,
    password: str,
    state_path: Path = _DEFAULT_STATE,
    *,
    browser: Browser | None = None,
) -> requests.Session:
    base_url = _base_url(base_url)
    session = _new_session()

    if not state_path.exists():
        _refresh_state(base_url, email, password, browser=browser, state_path=state_path)

    _load_cookies(session, base_url, state_path)
    if not _session_is_alive(session, base_url):
        _refresh_state(base_url, email, password, browser=browser, state_path=state_path)
        _load_cookies(session, base_url, state_path)
        if not _session_is_alive(session, base_url):
            raise AssertionError("authenticated session is not alive after refresh")

    return session


def _same_email(left: str | None, right: str | None) -> bool:
    return bool(left and right and left.strip().casefold() == right.strip().casefold())


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


def _font(size: int):
    for name in ("arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _mask_email(email: str) -> str:
    if "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked = name[:1] + "*"
    else:
        masked = name[:2] + "***" + name[-1:]
    return f"{masked}@{domain}"


def _email_visible_in_text(email: str, text: str) -> bool:
    if not email or not text:
        return False
    haystack = text.casefold()
    if email.casefold() in haystack:
        return True
    if "@" not in email:
        return email.casefold() in haystack
    name, domain = email.split("@", 1)
    candidates = {
        name,
        _mask_email(email),
        f"{name[:3]}***@{domain}" if len(name) >= 3 else f"{name[:1]}***@{domain}",
    }
    return any(candidate and candidate.casefold() in haystack for candidate in candidates)


def _write_api_summary(path: Path, member_id: int, email: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (960, 540), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(28)
    body_font = _font(22)
    small_font = _font(18)

    draw.rectangle([0, 0, 960, 72], fill=(22, 119, 255))
    draw.text((28, 20), "AUTH-009 API+UI mixed validation", fill="white", font=title_font)

    lines = [
        ("1", "POST /ucenter/rest/getLogonInfo.xhtml", "OK"),
        ("2", "GET  /thvendor/member/info/getMemberInfo.xhtml", "OK"),
        ("3", "GET  /thvendor/member/info/getPersonalInfo.xhtml", "OK"),
    ]
    y = 112
    for idx, endpoint, status in lines:
        draw.ellipse([34, y + 4, 62, y + 32], fill=(82, 196, 26))
        draw.text((43, y + 8), idx, fill="white", font=small_font)
        draw.text((82, y), endpoint, fill=(35, 35, 35), font=body_font)
        draw.text((770, y), status, fill=(82, 196, 26), font=body_font)
        y += 78

    draw.line([28, 372, 932, 372], fill=(220, 220, 220), width=2)
    draw.text((34, 404), f"Member ID: {member_id}", fill=(45, 45, 45), font=body_font)
    draw.text((34, 446), f"Email: {_mask_email(email)}", fill=(45, 45, 45), font=body_font)
    draw.text(
        (34, 492),
        "UI final check must show the same session on #/my/profile.",
        fill=(95, 95, 95),
        font=small_font,
    )
    image.save(path)


def run_auth009_api_first(
    browser: Browser,
    base_url: str,
    email: str,
    password: str,
    screenshot_dir: str | Path,
    *,
    state_path: str | Path = _DEFAULT_STATE,
) -> Auth009Result:
    base_url = _base_url(base_url)
    state_path = Path(state_path)
    screenshot_dir = Path(screenshot_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    session = authed_session_from_state(
        base_url,
        email,
        password,
        state_path,
        browser=browser,
    )

    logon = _request_json(
        session,
        "POST",
        base_url + "/ucenter/rest/getLogonInfo.xhtml",
        endpoint="ucenter.rest.getLogonInfo",
    )
    logon_data = logon["data"]
    logon_id = logon_data.get("id")
    logon_email = logon_data.get("email")
    if not isinstance(logon_id, int) or logon_id <= 0:
        raise AssertionError(f"invalid logon id: {logon_data!r}")
    if not _same_email(logon_email, email):
        raise AssertionError(
            f"configured email {email!r} != API logon email {logon_email!r}"
        )

    member = _request_json(
        session,
        "GET",
        base_url + "/thvendor/member/info/getMemberInfo.xhtml",
        endpoint="thvendor.member.info.getMemberInfo",
    )
    member_data = member["data"]
    if int(member_data.get("memberId")) != int(logon_id):
        raise AssertionError(
            f"member API identity mismatch: logon id={logon_id}, "
            f"memberId={member_data.get('memberId')}"
        )
    if not _same_email(member_data.get("email"), logon_email):
        raise AssertionError(
            f"member API email mismatch: logon={logon_email!r}, "
            f"member={member_data.get('email')!r}"
        )

    _request_json(
        session,
        "GET",
        base_url + "/thvendor/member/info/getPersonalInfo.xhtml",
        endpoint="thvendor.member.info.getPersonalInfo",
    )

    api_summary = screenshot_dir / "01_api_identity_chain.png"
    _write_api_summary(api_summary, int(logon_id), str(logon_email))
    shots = [("Step 1  API identity chain verified", str(api_summary))]

    target = base_url + "/websitehtml/index.html#/my/profile"
    context = browser.new_context(**_context_options(
        storage_state=str(state_path),
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
                """(expectedEmail) => {
                    if (location.hash.includes("/login")) return true;
                    const body = document.body ? document.body.innerText || "" : "";
                    const values = Array.from(document.querySelectorAll("input, textarea"))
                      .map((el) => el.value || "")
                      .join("\\n");
                    return `${body}\\n${values}`.toLowerCase()
                      .includes(String(expectedEmail).toLowerCase());
                }""",
                arg=email,
                timeout=15000,
            )
        except PlaywrightTimeoutError:
            pass

        final_url = page.url
        page_text = _profile_text(page)
        ui_shot = screenshot_dir / "02_profile_ui_same_session.png"
        page.screenshot(path=str(ui_shot), full_page=False)
        shots.append(("Step 2  Profile UI opened with same session", str(ui_shot)))
    finally:
        context.close()

    if "#/login" in final_url:
        raise AssertionError(f"UI session was rejected and redirected to login: {final_url}")
    if "#/my" not in final_url:
        raise AssertionError(f"expected member area URL, got {final_url}")
    if not _email_visible_in_text(email, page_text):
        raise AssertionError(
            "profile UI did not expose the same email returned by the API. "
            f"url={final_url}; text_head={page_text[:300]!r}"
        )

    return Auth009Result(
        member_id=int(logon_id),
        email=str(logon_email),
        final_url=final_url,
        shots=shots,
    )
