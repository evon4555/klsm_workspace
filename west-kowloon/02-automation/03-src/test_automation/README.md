# test_automation

Project-specific reusable automation package for West Kowloon.

```text
test_automation\
  web\     Page objects: classes that model pages, components, selectors, and UI actions.
  flows\   Business flow runners: API+UI orchestration and reusable scenario logic.
```

Rules:

- `web\` should not contain API orchestration modules.
- `flows\` may call API clients, page objects, Playwright, and artifact writers.
- Runnable test files still belong in `01-features` or `02-tests`, not here.
