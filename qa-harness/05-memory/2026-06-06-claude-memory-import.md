# Claude Memory Import

Date: 2026-06-06

Reason: the project was previously operated with Claude, and important working
memory lived under `C:\Users\klsm\.claude`. The QA harness should not depend on
hidden assistant state, so relevant Markdown memory was copied into the
workspace.

Imported source:

```text
C:\Users\klsm\.claude\projects\C--Users-klsm\memory
C:\Users\klsm\.claude\plans
```

Destination:

```text
D:\Workspace\qa-harness\05-memory\claude-import
```

Imported scope:

- Claude memory Markdown files
- Claude plan Markdown files
- manifest with source paths, sizes, and SHA-256 hashes

Excluded scope:

- credentials
- cache
- telemetry
- shell snapshots
- raw JSONL conversation history
- paste cache

Conversion status:

- Harness architecture, pipeline, change management, rule promotion, source
  authority, evidence rules, and smoke requirements are already represented in
  `01-system`, `02-platform`, `04-docs`, or dated `05-memory` entries.
- West Kowloon-specific source authority, OTP, PRD layout, HK verification, and
  auth automation details remain available in the imported Claude memory and
  should be promoted only when still current and project-owned.
- Retired environment facts such as old `D:\TestAutomation2`, TA2 credentials,
  and older Docker/WSL notes are kept for audit history but should not override
  the current Windows-native harness docs.

Rule: future assistants should check `05-memory\claude-import\memory\MEMORY.md`
when a fact seems missing from the new workspace memory, then promote only the
still-current part into a first-class harness or project document.
