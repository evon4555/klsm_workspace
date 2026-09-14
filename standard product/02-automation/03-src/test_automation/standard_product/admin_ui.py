from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import ddddocr
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .admin_auth import encrypt_credentials


BASE_URL = "https://anticket.lengliwh.com"

TEXT = {
    "all": "\u5168\u90e8",
    "query": "\u67e5\u8be2",
    "batch": "\u573a\u6b21\u6279\u91cf\u4fee\u6539",
    "group_action": "\u6279\u91cf\u4fee\u6539\u573a\u6b21\u53ef\u552e\u7968\u7ec4",
    "calendar_action": "\u6279\u91cf\u4fee\u6539\u662f\u5426\u5728\u65e5\u5386\u4e0a\u5c55\u793a",
    "display_action": "\u6279\u91cf\u4fee\u6539\u662f\u5426\u5728\u573a\u6b21\u5217\u8868\u4e2d\u663e\u793a",
    "pre_generate": "\u9884\u751f\u6210",
    "return": "\u8fd4\u56de",
    "confirm_modify": "\u786e\u8ba4\u4fee\u6539",
    "select_data_prompt": "\u8bf7\u9009\u62e9\u9700\u8981\u64cd\u4f5c\u7684\u6570\u636e",
    "select_group_prompt": "\u8bf7\u9009\u62e9\u573a\u6b21\u53ef\u552e\u7968\u7ec4",
    "no_data": "\u6682\u65e0\u6570\u636e",
}

NO_SEAT_SCHEDULE_URL = (
    BASE_URL
    + "/mshow/index.html#/menpiao/detail/schedule?"
    + "id=223334&imgUrl=https://imgtest.antank.cn/pic/mall/2c6bcc3348035330.png"
)
EXPECTED_NO_SEAT_ROW_IDS = ("90042939", "90037094")


class StandardProductAdminUi:
    def __init__(self, page: Page, base_url: str = BASE_URL) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    def login(self, username: str, password: str, max_attempts: int = 5) -> None:
        encrypted = encrypt_credentials(username, password)
        for attempt in range(1, max_attempts + 1):
            captcha_id = self.page.request.get(
                f"{self.base_url}/sso/getCaptchaId.xhtml"
            ).json()["data"]
            image = self.page.request.get(
                f"{self.base_url}/sso/captcha.xhtml",
                params={"captchaId": captcha_id},
            ).body()
            captcha = self.ocr.classification(image)
            payload = {"ecd": encrypted, "captchaId": captcha_id, "captcha": captcha}
            self.page.request.post(f"{self.base_url}/sso/tbsDoubleCheck.xhtml", form=payload)
            response = self.page.request.post(f"{self.base_url}/sso/login.xhtml", form=payload)
            body = response.json()
            if body.get("success"):
                return
            if attempt == max_attempts:
                raise RuntimeError(f"UI login failed: {body.get('msg', body)}")

    def warm_mainframe(self) -> None:
        target = f"{self.base_url}/mainframe/index.html#/home"
        try:
            self.page.goto(target, wait_until="domcontentloaded", timeout=45000)
        except PlaywrightTimeoutError as exc:
            if "/mainframe/index.html" not in self.page.url:
                raise AssertionError(f"Mainframe warmup did not reach target URL: {self.page.url!r}") from exc
        self.page.wait_for_timeout(1000)

    def open_no_seat_schedule(self, *, with_rows: bool) -> None:
        last_error: Exception | None = None
        for attempt in range(1, 6):
            self.warm_mainframe()
            try:
                self.page.goto(NO_SEAT_SCHEDULE_URL, wait_until="load", timeout=60000)
                wait_for_network_idle(self.page, 12000)
            except PlaywrightTimeoutError as exc:
                last_error = exc
                if "/mshow/index.html#/menpiao/detail/schedule" not in self.page.url:
                    if attempt == 5:
                        raise AssertionError(
                            f"No-seat schedule navigation did not reach target URL: {self.page.url!r}"
                        ) from exc
                    self.page.wait_for_timeout(1000)
                    continue
            try:
                self._wait_for_schedule_filters(timeout=20000)
                break
            except PlaywrightTimeoutError as exc:
                last_error = exc
                if attempt < 5:
                    try:
                        self._recover_mshow_route()
                    except PlaywrightTimeoutError as recover_exc:
                        last_error = recover_exc
                        self.page.wait_for_timeout(1200)
                    continue
                try:
                    body = self.page.locator("body").inner_text(timeout=5000)
                except PlaywrightTimeoutError:
                    body = ""
                raise AssertionError(
                    f"Schedule page did not expose query filters after retry. "
                    f"URL={self.page.url!r}; body head={body[:800]!r}"
                ) from last_error
        if with_rows:
            self._show_all_rows_with_retry()

    def _recover_mshow_route(self) -> None:
        try:
            self.page.reload(wait_until="domcontentloaded", timeout=45000)
            wait_for_network_idle(self.page, 8000)
            self._wait_for_schedule_filters(timeout=8000)
            return
        except PlaywrightTimeoutError:
            pass
        self.page.goto(f"{self.base_url}/mshow/index.html", wait_until="commit", timeout=30000)
        self.page.wait_for_timeout(800)
        self.page.goto(NO_SEAT_SCHEDULE_URL, wait_until="commit", timeout=30000)
        wait_for_network_idle(self.page, 8000)
        self.page.wait_for_timeout(800)

    def show_all_rows(self) -> None:
        self._wait_for_schedule_filters(timeout=15000)
        count = self.page.get_by_text(TEXT["all"], exact=True).count()
        for index in range(count):
            option = self.page.get_by_text(TEXT["all"], exact=True).nth(index)
            try:
                option.click(timeout=3000)
            except PlaywrightTimeoutError:
                option.click(force=True, timeout=3000)
            self.page.wait_for_timeout(150)
        query = self.page.get_by_role("button", name=TEXT["query"])
        try:
            query.click(timeout=5000)
        except PlaywrightTimeoutError:
            query.click(force=True, timeout=5000)
        self.page.wait_for_timeout(2500)

    def _show_all_rows_with_retry(self) -> None:
        last_body = ""
        for attempt in range(1, 4):
            self.show_all_rows()
            last_body = self.body_text()
            if all(row_id in last_body for row_id in EXPECTED_NO_SEAT_ROW_IDS):
                return
            if attempt < 3:
                try:
                    self._recover_mshow_route()
                    self._wait_for_schedule_filters(timeout=15000)
                except PlaywrightTimeoutError:
                    self.page.wait_for_timeout(1200)
        raise AssertionError(
            f"Expected no-seat session rows were not visible after retry: "
            f"{EXPECTED_NO_SEAT_ROW_IDS}. Body head: {last_body[:800]!r}"
        )

    def _wait_for_schedule_filters(self, timeout: int) -> None:
        self.page.get_by_role("button", name=TEXT["query"]).wait_for(
            state="visible",
            timeout=timeout,
        )

    def open_batch_menu(self) -> None:
        for _ in range(3):
            self.page.evaluate("window.scrollTo(0, 0)")
            button = self.page.get_by_role("button", name=TEXT["batch"]).first
            button.scroll_into_view_if_needed(timeout=5000)
            try:
                button.click(timeout=5000)
            except PlaywrightTimeoutError:
                button.click(force=True, timeout=5000)
            self.page.wait_for_timeout(800)
            if self._has_visible(self.page.get_by_text(TEXT["group_action"], exact=True)):
                return
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)
        body = self.body_text()
        raise AssertionError(f"Batch operation menu did not open. Body head: {body[:800]!r}")

    def choose_batch_action(self, action_text: str) -> None:
        if not self._click_first_visible(self.page.get_by_role("button", name=action_text)):
            if not self._click_first_visible(self.page.get_by_text(action_text, exact=True)):
                body = self.body_text()
                raise AssertionError(f"Visible batch action not found: {action_text!r}. Body head: {body[:800]!r}")
        self.page.wait_for_timeout(900)

    def _click_first_visible(self, locator) -> bool:
        for index in range(locator.count()):
            candidate = locator.nth(index)
            if not candidate.is_visible():
                continue
            try:
                candidate.click(timeout=5000)
            except PlaywrightTimeoutError:
                candidate.click(force=True, timeout=5000)
            return True
        return False

    def _has_visible(self, locator) -> bool:
        return any(locator.nth(index).is_visible() for index in range(locator.count()))

    def click_pre_generate(self) -> None:
        self.page.get_by_role("button", name=TEXT["pre_generate"]).last.click()
        self.page.wait_for_timeout(1000)

    def click_return(self) -> None:
        self.page.get_by_role("button", name=TEXT["return"]).last.click()
        self.page.wait_for_timeout(700)

    def close_drawer(self) -> None:
        close_button = self.page.locator(".el-drawer__close-btn").last
        if close_button.count():
            close_button.click()
        else:
            self.page.keyboard.press("Escape")
        try:
            self.page.locator(".el-drawer:visible").last.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeoutError:
            self.page.wait_for_timeout(700)

    def close_drawer_if_open(self) -> None:
        if self.page.locator(".el-drawer:visible").count():
            self.close_drawer()

    def body_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=5000)

    def assert_texts_visible(self, texts: Iterable[str]) -> None:
        body = self.body_text()
        missing = [text for text in texts if text not in body]
        if missing:
            raise AssertionError(f"UI missing text(s) {missing}. Body head: {body[:800]!r}")

    def screenshot(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(path), full_page=False)


def is_batch_write_url(url: str) -> bool:
    return "batchUpdate" in url or "batchSave" in url


def wait_for_network_idle(page: Page, timeout_ms: int = 10000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeoutError:
        return


def set_default_viewport(page: Page) -> None:
    page.set_default_timeout(45000)
    page.set_default_navigation_timeout(45000)
    if not os.environ.get("TA_KEEP_DEFAULT_VIEWPORT"):
        page.set_viewport_size({"width": 1440, "height": 900})
