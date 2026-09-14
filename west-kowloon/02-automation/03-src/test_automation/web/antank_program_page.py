from __future__ import annotations

from datetime import datetime

from playwright.sync_api import Page, Frame


class AntankProgramPage:
    """Hybrid page object for 项目 (Program) management in 门票票务系统.

    Hybrid pattern used here:
      - create_via_api()          → API call via page.request (fast, no UI)
      - navigate_to_programs()    → UI navigation via page.goto + iframe
      - is_program_visible(name)  → UI assertion via Playwright locator

    Why hybrid?
      Creating data via API is fast and reliable.
      Asserting via UI proves the user actually sees the data — end-to-end confidence.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")
        self._api = page.request   # Playwright APIRequestContext — shares session cookie with browser
        self._frame: Frame | None = None
        self.last_created_name: str | None = None   # set by create_via_api(), read by steps

    # ── API layer ─────────────────────────────────────────────────────────────

    def create_via_api(self) -> str:
        """Create a no-seat program via API POST. Returns the program name.

        Uses page.request (Playwright's built-in HTTP client) — same session
        cookie as the browser, so no separate auth step is needed after login.
        The timestamp suffix ensures each test run creates a uniquely named program.
        """
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        program_name = f"test no seat project {ts}"

        resp = self._api.post(
            f"{self._base_url}/theatre/home/program/op/save.xhtml",
            # Playwright encodes this dict as application/x-www-form-urlencoded
            form={
                "defaultLang": "en",
                "supportLang": "en",
                "cnName": program_name,      # display name — this is what we search for in UI
                "briefName": ts,
                "stadiumId": "69844",
                "venueId": "1708",
                "durationType": "period",
                "startTime": "2026-03-18 00:00:00",
                "endTime": "2026-03-18 23:59:59",
                "minPrice": "0",
                "maxPrice": "1",
                "showMode": "calendar",
                "saleType": "sale",
                "available": "Y",
                "supportSeat": "N",          # no-seat project
                "multiGroupCheck": "N",
                "allowInvoice": "N",
                "pushInvoice": "N",
                "consumerInvoiceTime": "paid",
                "bizScenario": "program",
                "blackLimit": "Y",
                "category": "",
                "smallCategory": "",
                "tag": "",
                "approvalNum": "",
                "programCode": "",
                "certLevel": "",
                "productType": "",
            },
        )
        data = resp.json()
        if not data.get("success") and "program" not in str(data):
            raise RuntimeError(f"create_via_api failed — response: {data}")

        self.last_created_name = program_name
        print(f"  [program] created via API: {program_name}")
        return program_name

    # ── UI layer ──────────────────────────────────────────────────────────────

    def navigate_to_programs(self) -> None:
        """Navigate the browser to the programs list page (UI step).

        Opens 门票票务系统 from the home page (same flow as MenpiaoPage.open())
        then waits for the iframe to load. The default view of the menpiao SPA
        is the programs list, so no additional click is needed.
        """
        # Click 门票票务系统 on the home page to enter the menpiao iframe
        self._page.wait_for_load_state("networkidle", timeout=15000)
        self._page.get_by_text("门票票务系统", exact=True).first.click()
        self._page.wait_for_selector("iframe", timeout=15000)
        self._frame = self._wait_for_menpiao_frame(timeout_ms=30000)
        self._frame.wait_for_load_state("networkidle", timeout=30000)
        self._page.wait_for_timeout(2000)

    def is_program_visible(self, program_name: str) -> bool:
        """Assert that a program with the given name is visible in the list (UI assertion).

        Looks for the exact program name text anywhere inside the menpiao iframe.
        Returns True if found within the timeout, False otherwise.
        NOTE: if the list is paginated, you may need to add search/filter logic here.
        """
        try:
            self.frame.get_by_text(program_name, exact=False).wait_for(
                state="visible", timeout=15000
            )
            return True
        except Exception:
            return False

    # ── internals ─────────────────────────────────────────────────────────────

    def _wait_for_menpiao_frame(self, timeout_ms: int = 30000) -> Frame:
        interval = 1000
        elapsed = 0
        while elapsed < timeout_ms:
            frames = [
                f for f in self._page.frames
                if f.url.startswith(f"{self._base_url}/menpiao/")
            ]
            if frames:
                return frames[0]
            self._page.wait_for_timeout(interval)
            elapsed += interval
        raise TimeoutError("menpiao iframe did not appear within timeout")

    @property
    def frame(self) -> Frame:
        if self._frame is None:
            raise RuntimeError("call navigate_to_programs() before accessing the frame")
        return self._frame
