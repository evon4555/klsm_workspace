# Standard Product Environment Files

Runtime credentials must be set through environment variables or an ignored
`.env.<env>` file. Do not copy passwords, cookies, tokens, or browser session
values into generated QA artifacts.

Required variables for real API execution:

```text
TA_ANTANK_URL=https://anticket.lengliwh.com
TA_USER1_USERNAME=<admin username>
TA_USER1_PASSWORD=<admin password>
TA_ALLOW_BATCH_MUTATION=1
```

`TA_ALLOW_BATCH_MUTATION=1` is intentionally required before write APIs run.
