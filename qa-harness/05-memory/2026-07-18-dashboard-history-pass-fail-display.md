# 2026-07-18 Dashboard History Pass/Fail Display

Scope: QA dashboard case-history UI and `/api/history/case/{case_id}`.

Trigger: Execution history was showing raw Behave/platform statuses, which made
the user-facing case timeline confusing.

Decision: The dashboard history timeline shows execution outcomes as only
`Pass` or `Fail`. Raw runner status is retained as technical metadata in the API
or database, but not shown as the timeline's human-facing execution status.
Non-execution states such as `skipped` and `running` are excluded from execution
history counts.

Follow-up correction: The history modal is execution-centric. Screenshot
evidence batches, ZenTao bugs, and current XLSX snapshots must not render as
separate timeline items. Evidence can be attached to a matching run/case record
as metadata or artifacts.
