# 07-artifacts

Generated automation output lives here.

Use this folder for runtime files that can be regenerated:

- screenshots produced during Behave, pytest, or delivery runs
- JSON summaries such as API smoke output
- HAR captures and endpoint discovery output
- performance CSVs and temporary dashboard export files
- browser storage state used by automation

Do not put runnable scripts here. Durable evidence that needs review, audit, or
delivery should be copied or promoted to `..\..\03-evidence`.

Use `..\04-tools\promote_automation_evidence.py` to promote a selected run into
`..\..\03-evidence\automation`. Promotion copies the runtime files, writes a
manifest, and records whether the package is trusted by the Quality Gate.
