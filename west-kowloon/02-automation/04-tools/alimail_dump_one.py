"""Dump the latest OTP email's full HTML, fall back from buggy SEARCH FROM
on Aliyun IMAP by pulling last N messages and filtering in Python."""
import os, imaplib, email, re
HOST="imap.qiye.aliyun.com"; PORT=993; USER="evan.wang@antank.com"
def pw():
    p = os.environ.get("ALIMAIL_PASSWORD")
    if p: return p
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        return winreg.QueryValueEx(k, "ALIMAIL_PASSWORD")[0]

M = imaplib.IMAP4_SSL(HOST, PORT); M.login(USER, pw())
typ, data = M.select("INBOX"); total = int(data[0])
last_n = 30
first = max(1, total - last_n + 1)
typ, raw = M.fetch(",".join(str(i) for i in range(first, total+1)), "(RFC822)")
hits = []
for item in raw:
    if not isinstance(item, tuple): continue
    msg = email.message_from_bytes(item[1])
    if "public@antank.com" not in (msg.get("From") or ""):
        continue
    # Subject often comes RFC-2047 encoded for non-ASCII; decode it
    from email.header import decode_header
    raw_subj = msg.get("Subject") or ""
    subj = ""
    for chunk, enc in decode_header(raw_subj):
        if isinstance(chunk, bytes):
            try: subj += chunk.decode(enc or "utf-8", errors="replace")
            except LookupError: subj += chunk.decode("utf-8", errors="replace")
        else:
            subj += chunk
    if "验证码" not in subj:
        continue
    body_html = ""
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        if part.get_content_type() == "text/html":
            body_html = (part.get_payload(decode=True) or b"").decode(
                part.get_content_charset() or "utf-8", errors="replace")
            break
    hits.append((msg.get("Date"), body_html))
print(f"OTP emails found: {len(hits)}")
if hits:
    # take latest
    date, html = hits[-1]
    print(f"latest date: {date}")
    print(f"html length: {len(html)}")
    print("--- FULL HTML ---")
    print(html)
M.logout()
