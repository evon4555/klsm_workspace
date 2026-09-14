# 2026-07-21 Standard Product Linked Ticket Performance

- Trigger: Standard Product needed a project-local Performance Test linked ticketing scenario.
- Decision: `tests/performance/linked_ticket.py` must live in the selected project's automation tree; Dashboard must not borrow WestK project scripts.
- Runtime auth: use `PERF_STORAGE_STATE` or `PERF_COOKIE` for website/member session, plus Basic Auth env vars when the target is behind nginx auth. Do not persist credentials or cookie values in repo artifacts.
- Runtime data: use `STD_LINKED_TICKET_CSV` for live linked-ticket show and seat data. Multi-user runs need multiple valid rows to avoid data contention.
- Pacing: default wait is 10 seconds via `PERF_LINKED_TICKET_WAIT_SECONDS`; 0-second loops caused same-data "operation too fast" failures.
