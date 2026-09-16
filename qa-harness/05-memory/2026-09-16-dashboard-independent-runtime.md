# QA Dashboard Independent Runtime

- **Trigger:** On 2026-09-16, `http://127.0.0.1:8002/` repeatedly became unavailable after a Codex task ended or was interrupted.
- **Finding:** `start-dashboard.bat` runs Uvicorn in the foreground. When it is launched inside a task-owned terminal, closing that terminal also stops the dashboard. The afternoon failures showed no Python/Uvicorn crash or Windows application-crash event.
- **Decision:** Keep the local dashboard independent of agent terminals through the current-user scheduled task `QA Dashboard Local 8002`. It starts at user logon, runs `python -m uvicorn main:app --host 127.0.0.1 --port 8002` from the dashboard backend directory, ignores duplicate starts, and retries failures up to five times at one-minute intervals.
- **Verification:** Confirm a listener on `127.0.0.1:8002`, then call `/api/health` and `/`; both must return HTTP 200. Bypass the local HTTP proxy for loopback checks when necessary.
- **Scope:** Local QA Dashboard runtime on this Windows workstation. `start-dashboard.bat` remains a foreground developer launcher.
