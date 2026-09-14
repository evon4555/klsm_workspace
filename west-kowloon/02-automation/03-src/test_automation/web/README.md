# web

Page objects and browser UI helpers live here.

This package should model UI pages, components, selectors, and user-facing
browser actions. It should not contain API-first or API+UI orchestration files.

Current page objects:

```text
antank_login_page.py
antank_program_page.py
menpiao_page.py
website_forgot_password_page.py
website_guest_page.py
website_login_page.py
website_registration_page.py
```

If a module creates orders through API, refreshes browser state, writes evidence
screenshots, and then checks the UI, put it under `..\flows` instead.
