# West Kowloon Automation Tools

This folder owns concrete West Kowloon automation scripts.

Examples:

- evidence generation and xlsx writeback helpers
- Antank UI/API probes
- Aliyun IMAP OTP helpers
- ZenTao delivery and diagnostic scripts
- HAR/API discovery scripts
- West Kowloon end-to-end shell smoke

New West Kowloon scripts should be added here first. Promote a script to the
platform only after it is reusable for another project without Antank, West
Kowloon, concrete account, concrete URL, or ZenTao-product assumptions.

This folder is for scripts you run directly for delivery, diagnostics, or
maintenance. Reusable modules imported by tests should live under
`..\03-src\test_automation`.

Current script groups:

```text
evidence/writeback   update_evidence.py, sync_md_results.py, fixup_*.py
api discovery        crawl_api_endpoints.py, discover_api_endpoints.py, record_har.py
mail/OTP             imap_otp_poller.py, alimail_*.py
Zentao               zentao_*.py, smoke_zentao*.py, self_test_open_bug.py
probes               probe_*.py and other short diagnostics
shell smoke          full_flow.sh
```
