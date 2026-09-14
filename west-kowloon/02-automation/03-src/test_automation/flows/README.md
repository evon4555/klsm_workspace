# flows

Reusable business flow runners live here.

Use this folder for code that coordinates more than one layer, for example:

- API setup plus final UI assertion.
- API business-chain execution plus screenshot artifact creation.
- Shared scenario logic called by Behave steps, pytest tests, or delivery tools.

Current files:

```text
auth009_api_first.py          AUTH-009 API-first login/profile validation.
order_cancel_api_ui_mixed.py  Ticketing order create/cancel API chain with final UI proof.
```

Do not put page-object classes here. Page objects stay in `..\web`.
