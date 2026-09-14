"""Probe Aliyun corporate email (阿里邮箱企业版) inbox to identify the OTP
email pattern for SIT.

Reads credentials from env vars (never CLI args, never logged):
  ALIMAIL_USER     default 'evan.wang@antank.com'
  ALIMAIL_PASSWORD required (use the 客户端独立密码 / app-specific password
                   from your Aliyun mailbox security settings)

Lists the last 10 messages in INBOX with sender / subject / date / body
preview, plus a heuristic 'has 6-digit code' flag — that's the candidate
OTP email. Once you see what the OTP email looks like, the production
poller in tools/imap_otp_poller.py (TODO) can target the exact sender +
subject pattern.

Run:
    [Environment]::SetEnvironmentVariable('ALIMAIL_PASSWORD','<app password>','User')
    # reopen shell OR use the registry-fallback below
    python tools/alimail_probe.py
"""
from __future__ import annotations
import email
import imaplib
import os
import re
import sys
from email.header import decode_header

HOST = "imap.qiye.aliyun.com"
PORT = 993
USER = os.environ.get("ALIMAIL_USER", "evan.wang@antank.com")


def _read_pw_from_user_env_if_missing() -> str | None:
    pw = os.environ.get("ALIMAIL_PASSWORD")
    if pw:
        return pw
    # Windows-only fallback: read directly from HKCU\Environment so the
    # current shell doesn't need to be reopened after setx-style writes.
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            v, _ = winreg.QueryValueEx(k, "ALIMAIL_PASSWORD")
            return v
    except Exception:
        return None


def _decode(s) -> str:
    if not s:
        return ""
    parts = decode_header(s)
    out = []
    for chunk, enc in parts:
        if isinstance(chunk, bytes):
            try:
                out.append(chunk.decode(enc or "utf-8", errors="replace"))
            except LookupError:
                out.append(chunk.decode("utf-8", errors="replace"))
        else:
            out.append(chunk)
    return "".join(out)


def _body_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "")
            if "attachment" in disp.lower():
                continue
            if ctype == "text/plain":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    return payload.decode(charset, errors="replace")
                except LookupError:
                    return payload.decode("utf-8", errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                html = payload.decode(charset, errors="replace")
                # crude tag strip for preview
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    payload = msg.get_payload(decode=True) or b""
    charset = msg.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def main():
    pw = _read_pw_from_user_env_if_missing()
    if not pw:
        sys.exit("ERROR: ALIMAIL_PASSWORD not set. See module docstring.")

    print(f"connecting imaps://{HOST}:{PORT} as {USER} ...")
    M = imaplib.IMAP4_SSL(HOST, PORT)
    try:
        try:
            M.login(USER, pw)
        except imaplib.IMAP4.error as exc:
            sys.exit(f"LOGIN FAILED: {exc}. If 2FA is on you must use the "
                     f"客户端独立密码 (Aliyun mailbox → 安全设置 → 客户端独立密码).")

        print("login OK; SELECT INBOX")
        typ, data = M.select("INBOX")
        if typ != "OK":
            sys.exit(f"SELECT INBOX failed: {typ} {data}")
        total = int(data[0])
        print(f"INBOX total messages: {total}")

        last = max(1, total - 9)
        typ, msg_nums = M.fetch(",".join(str(n) for n in range(last, total + 1)),
                                "(RFC822)")
        print(f"\n--- last {total - last + 1} messages (newest at bottom) ---")
        idx = 0
        # IMAP returns alternating tuples + parens; pick the (resp, msg) tuples
        for item in msg_nums:
            if not isinstance(item, tuple):
                continue
            idx += 1
            raw = item[1]
            try:
                msg = email.message_from_bytes(raw)
            except Exception as exc:
                print(f"\n[#{idx}] parse failed: {exc}")
                continue
            sender = _decode(msg.get("From"))
            subj = _decode(msg.get("Subject"))
            date = msg.get("Date") or ""
            body = _body_text(msg)
            body_oneline = re.sub(r"\s+", " ", body)[:200]
            six = re.findall(r"(?<!\d)(\d{6})(?!\d)", body)
            has6 = "  ⭐ 6-digit code candidate(s): " + ", ".join(six[:3]) if six else ""
            print(f"\n[#{idx}] {date}")
            print(f"  From   : {sender}")
            print(f"  Subject: {subj}")
            print(f"  Body   : {body_oneline}{has6}")
    finally:
        try:
            M.close()
        except Exception:
            pass
        M.logout()


if __name__ == "__main__":
    main()
