# 03-src

Reusable West Kowloon automation code lives here.

This folder is not for runnable test entry points. Put runnable Behave scenarios
under `..\01-features`, runnable pytest and Locust tests under `..\02-tests`,
and one-off delivery or diagnostic utilities under `..\04-tools`.

```text
03-src\
  test_automation\
    web\     Page objects and browser UI helpers only.
    flows\   Reusable business flow runners used by tests, steps, or tools.
```

Import this source package through `PYTHONPATH`:

```powershell
$env:PYTHONPATH = 'D:\Workspace\qa-harness\02-platform\01-automation\02-src;D:\Workspace\west-kowloon\02-automation\03-src'
```
