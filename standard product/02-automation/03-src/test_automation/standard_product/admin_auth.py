from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any

import ddddocr
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

_AES_KEY = "zTw=d0!tD1hGD|B?L`O(6ZS|=wRrGwZy".encode("utf-8")
_OCR = ddddocr.DdddOcr(show_ad=False)


def encrypt_credentials(username: str, password: str) -> str:
    plaintext = json.dumps({"username": username, "password": password}, separators=(",", ":"))
    cipher = AES.new(_AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(plaintext.encode("utf-8"), 16))
    return base64.b64encode(encrypted).decode()


@dataclass(frozen=True)
class RouteContext:
    referer: str
    routerpath: str
    parentpath: str | None = None


class StandardProductAdminSession:
    """Real Standard Product admin API session backed by requests.Session."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.last_response_meta: dict[str, Any] = {}
        self.session.trust_env = os.getenv("TA_USE_SYSTEM_PROXY", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        self.session.headers.update(
            {
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9",
                "cache-control": "no-cache",
                "lang": "zh-CN",
                "pragma": "no-cache",
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0 Safari/537.36"
                ),
            }
        )

    def login(self, max_attempts: int = 5) -> None:
        encrypted = encrypt_credentials(self.username, self.password)
        for attempt in range(max_attempts):
            captcha_id = self._captcha_id()
            captcha = self._captcha(captcha_id)
            payload = {"ecd": encrypted, "captchaId": captcha_id, "captcha": captcha}

            self.session.post(f"{self.base_url}/sso/tbsDoubleCheck.xhtml", data=payload, timeout=20)
            response = self.session.post(
                f"{self.base_url}/sso/login.xhtml",
                data=payload,
                timeout=20,
            )
            body = self._json(response)
            if body.get("success"):
                return
            if attempt == max_attempts - 1:
                raise RuntimeError(f"login failed: {body.get('msg', body)}")

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        route: RouteContext,
    ) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params or {},
            headers=self._route_headers(route, include_origin=False),
            timeout=30,
        )
        self.last_response_meta = {
            "method": "GET",
            "path": path,
            "url": response.url,
            "status_code": response.status_code,
        }
        return self._json(response)

    def post_json(
        self,
        path: str,
        *,
        params: dict[str, Any],
        route: RouteContext,
    ) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}{path}",
            params=params,
            headers=self._route_headers(route, include_origin=True),
            timeout=30,
        )
        self.last_response_meta = {
            "method": "POST",
            "path": path,
            "url": response.url,
            "status_code": response.status_code,
        }
        return self._json(response)

    def _captcha_id(self) -> str:
        response = self.session.get(f"{self.base_url}/sso/getCaptchaId.xhtml", timeout=20)
        data = self._json(response)
        return str(data["data"])

    def _captcha(self, captcha_id: str) -> str:
        response = self.session.get(
            f"{self.base_url}/sso/captcha.xhtml",
            params={"captchaId": captcha_id},
            timeout=20,
        )
        response.raise_for_status()
        return _OCR.classification(response.content)

    def _route_headers(self, route: RouteContext, *, include_origin: bool) -> dict[str, str]:
        headers = {
            "referer": route.referer,
            "routerpath": route.routerpath,
        }
        if route.parentpath:
            headers["parentpath"] = route.parentpath
        if include_origin:
            headers["origin"] = self.base_url
        return headers

    @staticmethod
    def _json(response: requests.Response) -> dict[str, Any]:
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(f"non-json response from {response.url}: {response.text[:300]}") from exc
        if not isinstance(data, dict):
            raise RuntimeError(f"unexpected JSON response from {response.url}: {type(data).__name__}")
        return data
