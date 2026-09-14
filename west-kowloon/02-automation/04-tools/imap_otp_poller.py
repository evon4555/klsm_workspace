"""Poll the Aliyun corporate mailbox for the latest OTP email from SIT.

Usage in test code:
    from tools.imap_otp_poller import fetch_latest_otp
    sent_at = datetime.utcnow()
    # ... click "Get Code" on the website ...
    otp = fetch_latest_otp(since=sent_at)
    page.fill_otp(otp)

Configuration (env vars):
    ALIMAIL_USER       default 'evan.wang@antank.com'
    ALIMAIL_PASSWORD   required (Aliyun 客户端独立密码)

Filter is fixed to:
    From    contains  'public@antank.com'
    Subject contains  '验证码'
OTP is extracted by regex '验证码[:：]\\s*(\\d{6})'.
SIT-side validity per email body: 20 minutes.
"""
from __future__ import annotations

import email
import imaplib
import os
import re
import time
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Optional

HOST = "imap.qiye.aliyun.com"
PORT = 993
USER = os.environ.get("ALIMAIL_USER", "evan.wang@antank.com")

_OTP_RE = re.compile(r"验证码[:：]\s*(\d{6})")
_SUBJECT_KEYWORD = "验证码"
_SENDER_KEYWORD = "public@antank.com"

# --- per-process throttle so we don't hit Aliyun's 30s server-side OTP
# rate limit when running multiple OTP-touching tests back-to-back.
_LAST_OTP_REQUEST: dict = {}
_OTP_THROTTLE_SECONDS = 35     # 30s window + 5s safety


def wait_for_otp_throttle(email: str) -> None:
    """Sleep if needed so the next OTP request to `email` is safely past
    the 30s server window. Records the request time after the wait."""
    last = _LAST_OTP_REQUEST.get(email)
    if last:
        wait = _OTP_THROTTLE_SECONDS - (time.time() - last)
        if wait > 0:
            print(f"  [otp throttle] sleeping {wait:.1f}s before next OTP to "
                  f"{email} (server limit: 1 per 30s)", flush=True)
            time.sleep(wait + 0.5)
    _LAST_OTP_REQUEST[email] = time.time()


class OTPNotFound(Exception):
    pass


def _pw() -> str:
    p = os.environ.get("ALIMAIL_PASSWORD")
    if p:
        return p
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, "ALIMAIL_PASSWORD")[0]
    except Exception:                                       # noqa: BLE001
        raise RuntimeError(
            "ALIMAIL_PASSWORD not set — write your Aliyun 客户端独立密码 "
            "(NOT the web login password) into the user env var."
        )


def _decode_subject(raw: str) -> str:
    out = ""
    for chunk, enc in decode_header(raw or ""):
        if isinstance(chunk, bytes):
            try:
                out += chunk.decode(enc or "utf-8", errors="replace")
            except LookupError:
                out += chunk.decode("utf-8", errors="replace")
        else:
            out += chunk
    return out


def _body_html(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    return payload.decode(charset, errors="replace")
                except LookupError:
                    return payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            return payload.decode("utf-8", errors="replace")
    return ""


def _scan_inbox(since: Optional[datetime] = None,
                last_n: int = 30) -> list[tuple[datetime, str]]:
    """Return [(received_dt, otp_code)] for OTP emails newer than `since`,
    newest last. Scans last_n messages (cheap; Aliyun SEARCH FROM/SUBJECT
    is fussy so we filter in Python)."""
    M = imaplib.IMAP4_SSL(HOST, PORT)
    try:
        M.login(USER, _pw())
        typ, data = M.select("INBOX")
        total = int(data[0])
        first = max(1, total - last_n + 1)
        typ, raw = M.fetch(
            ",".join(str(i) for i in range(first, total + 1)), "(RFC822)")
        out: list[tuple[datetime, str]] = []
        for item in raw:
            if not isinstance(item, tuple):
                continue
            try:
                msg = email.message_from_bytes(item[1])
            except Exception:                                # noqa: BLE001
                continue
            if _SENDER_KEYWORD not in (msg.get("From") or ""):
                continue
            if _SUBJECT_KEYWORD not in _decode_subject(msg.get("Subject")):
                continue
            try:
                dt = parsedate_to_datetime(msg.get("Date"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:                                # noqa: BLE001
                dt = datetime.now(timezone.utc)
            if since and dt < since:
                continue
            m = _OTP_RE.search(_body_html(msg))
            if not m:
                continue
            out.append((dt, m.group(1)))
        out.sort(key=lambda t: t[0])
        return out
    finally:
        try:
            M.close()
        except Exception:
            pass
        try:
            M.logout()
        except Exception:
            pass


def fetch_latest_otp(since: Optional[datetime] = None,
                     timeout: float = 45.0,
                     interval: float = 4.0) -> str:
    """Retry-poll for the newest OTP delivered AFTER `since`. Returns the
    6-digit code or raises OTPNotFound if no match within `timeout`.

    Mail delivery to Aliyun usually arrives in <10s; default budget 45s is
    generous to absorb cold-start + propagation.
    """
    if since is None:
        # default: only accept OTPs received within the last 5 minutes
        from datetime import timedelta
        since = datetime.now(timezone.utc) - timedelta(minutes=5)
    elif since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    deadline = time.time() + timeout
    last_err = "no email matched filter"
    while time.time() < deadline:
        try:
            hits = _scan_inbox(since=since)
            if hits:
                # newest hit
                return hits[-1][1]
        except Exception as exc:                             # noqa: BLE001
            last_err = f"IMAP error: {exc}"
        time.sleep(interval)
    raise OTPNotFound(
        f"no OTP email (from {_SENDER_KEYWORD}, subject contains "
        f"'{_SUBJECT_KEYWORD}', after {since.isoformat()}) within "
        f"{timeout:.0f}s — last error: {last_err}"
    )


if __name__ == "__main__":
    # CLI: print the latest OTP from the last 5 minutes (one-shot, no retry)
    hits = _scan_inbox()
    if not hits:
        print("(no OTP emails matched filter in last 30 messages)")
    else:
        for dt, code in hits:
            print(f"  {dt.isoformat()}  OTP={code}")
