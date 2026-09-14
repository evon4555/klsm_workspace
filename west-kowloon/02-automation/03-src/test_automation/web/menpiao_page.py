from __future__ import annotations

from playwright.sync_api import Page, Frame


class MenpiaoPage:
    """Page Object for the 门票票务系统 (inside the mainframe iframe).

    After clicking into the system, content is served via an iframe at
    /menpiao/index.html. This class operates on that inner frame.
    """

    SYSTEM_NAME = "门票票务系统"

    def __init__(self, page: Page) -> None:
        self._page = page
        self._frame: Frame | None = None

    def open(self) -> None:
        """Click 门票票务系统 on the home page and wait for the iframe to load."""
        self._page.wait_for_load_state("networkidle", timeout=15000)
        self._page.get_by_text(self.SYSTEM_NAME, exact=True).first.click()
        self._page.wait_for_selector("iframe", timeout=15000)
        self._frame = self._wait_for_menpiao_frame(timeout_ms=30000)
        self._frame.wait_for_load_state("networkidle", timeout=30000)
        self._page.wait_for_timeout(2000)

    def _wait_for_menpiao_frame(self, timeout_ms: int = 30000) -> Frame:
        interval = 1000
        elapsed = 0
        while elapsed < timeout_ms:
            frames = [
                f for f in self._page.frames
                if f.url.startswith("https://anticket.lengliwh.com/menpiao/")
            ]
            if frames:
                return frames[0]
            self._page.wait_for_timeout(interval)
            elapsed += interval
        raise TimeoutError("menpiao iframe did not appear within timeout")

    @property
    def frame(self) -> Frame:
        if self._frame is None:
            raise RuntimeError("call open() before accessing the frame")
        return self._frame

    def get_ticket_list_title(self) -> str:
        """Return the page heading text from the ticket list view."""
        heading = self.frame.locator("h2, h3, .page-title, .list-title").first
        heading.wait_for(timeout=10000)
        return heading.inner_text().strip()

    def ticket_count(self) -> int:
        """Return the number of ticket project cards visible on the list page."""
        self.frame.wait_for_selector(".list-item, .ticket-item, table tbody tr", timeout=10000)
        return self.frame.locator(".list-item, .ticket-item, table tbody tr").count()

    def is_ticket_list_visible(self) -> bool:
        """Return True if the ticket list has loaded with at least one item."""
        try:
            self.frame.wait_for_selector(
                "table tbody tr, .list-item", state="visible", timeout=10000
            )
            return True
        except Exception:
            return False
