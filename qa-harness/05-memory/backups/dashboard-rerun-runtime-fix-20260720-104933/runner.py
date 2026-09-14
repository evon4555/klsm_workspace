"""
Behave subprocess runner — starts behave as a child process and streams output.

Responsibilities:
  1. Build the behave CLI command from the requested tags/env/names
  2. Launch it as an async subprocess (non-blocking)
  3. Read stdout line-by-line and broadcast to WebSocket subscribers
  4. Parse the JSON results file after completion

The JSON results file (artifacts/run_{id}.json) is created by behave's
built-in JSON formatter (--format json --outfile ...).
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


DEFAULT_DASHBOARD_TAGS = "not @na and not @needs-oauth-mock"


class BehaveRunner:
    """Manages Behave subprocess lifecycle and log streaming."""

    def __init__(
        self,
        project_root: str,
        features_dir: str | Path = "features",
        artifacts_dir: str | Path = "artifacts",
    ):
        self.project_root = Path(project_root)
        self.features_dir = Path(features_dir)
        if not self.features_dir.is_absolute():
            self.features_dir = self.project_root / self.features_dir
        self.artifacts_dir = Path(artifacts_dir)
        if not self.artifacts_dir.is_absolute():
            self.artifacts_dir = self.project_root / self.artifacts_dir
        # Per-run log buffers: run_id → list of log lines
        self.logs: dict[int, list[str]] = {}
        # Per-run WebSocket subscribers: run_id → list of asyncio.Queue
        self._subscribers: dict[int, list[asyncio.Queue]] = {}

    def subscribe(self, run_id: int, queue: asyncio.Queue):
        """Register a WebSocket client to receive live log lines for a run."""
        self._subscribers.setdefault(run_id, []).append(queue)

    def unsubscribe(self, run_id: int, queue: asyncio.Queue):
        """Remove a WebSocket client subscription."""
        if run_id in self._subscribers:
            self._subscribers[run_id] = [
                q for q in self._subscribers[run_id] if q is not queue
            ]

    async def _broadcast(self, run_id: int, message):
        """Send a message (log line or None sentinel) to all subscribers."""
        for queue in self._subscribers.get(run_id, []):
            await queue.put(message)

    async def run_behave(
        self,
        run_id: int,
        tags: Optional[str] = None,
        env: str = "local",
        names: Optional[list[str]] = None,
        features: Optional[list[str]] = None,
    ) -> tuple[int, list[dict]]:
        """Run behave and return (exit_code, parsed_scenarios).

        Args:
            run_id: Database ID for this run (used for log file naming).
            tags:   Behave tag expression, e.g. "@hybrid" or "@api,@antank".
            env:    Environment name — sets the ENV variable for behave.
            names:  Scenario names to re-run (regex-matched via --name flag).

        Returns:
            (exit_code, scenarios) where scenarios is a list of dicts with keys:
            feature, name, status, duration_s, error_msg, tags.
        """
        results_file = self.artifacts_dir / f"run_{run_id}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)

        # Build the behave command.
        # We use two formatters:
        #   --format json --outfile <file>   → machine-readable results (parsed after run)
        #   --format pretty --no-capture     → human-readable stdout (streamed to WebSocket)
        cmd = [
            sys.executable, "-m", "behave",     # python -m behave (reliable on all platforms)
            "--format", "json", "--outfile", str(results_file),
            "--format", "pretty",
            "--no-skipped",
            "--no-capture",
        ]

        effective_tags = tags or DEFAULT_DASHBOARD_TAGS
        if effective_tags:
            cmd.extend(["--tags", effective_tags])

        if names:
            # --name uses regex matching; escape special chars in scenario names
            for name in names:
                cmd.extend(["--name", re.escape(name)])

        # Restrict the run to the selected feature files (positional paths
        # override behave.ini's `paths = features`). This keeps the JSON
        # results free of other modules' scenarios.
        if features:
            cmd.extend(self._normalize_feature_paths(features))
        else:
            try:
                cmd.append(str(self.features_dir.relative_to(self.project_root)))
            except ValueError:
                cmd.append(str(self.features_dir))

        # Pass the environment selection to behave via ENV variable
        env_vars = dict(os.environ)
        env_vars["ENV"] = env
        env_vars.setdefault("QA_PROJECT_AUTOMATION_ROOT", str(self.project_root))
        env_vars.setdefault("QA_WORKSPACE_ROOT", str(self.project_root.parent.parent))
        env_vars.setdefault("QA_HARNESS_ROOT", str(Path(__file__).resolve().parents[3]))
        env_vars["PYTHONPATH"] = self._pythonpath(env_vars.get("PYTHONPATH"))
        # Force UTF-8 output on Windows (prevents GBK garbled Chinese)
        env_vars["PYTHONIOENCODING"] = "utf-8"
        env_vars["PYTHONUTF8"] = "1"
        # Signal to features/environment.py that this run is already being
        # recorded by the dashboard (don't double-record).
        env_vars["BEHAVE_DASHBOARD_RUN_ID"] = str(run_id)

        self.logs[run_id] = []

        # Launch behave as an async subprocess so we don't block the FastAPI event loop
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,   # merge stderr into stdout
            cwd=str(self.project_root),
            env=env_vars,
        )

        # Stream stdout line-by-line to subscribers (WebSocket clients)
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip("\n").rstrip("\r")
            self.logs[run_id].append(text)
            await self._broadcast(run_id, text)

        exit_code = await process.wait()

        # Signal that the run is complete (None = sentinel value)
        await self._broadcast(run_id, None)

        # Parse the JSON results file produced by behave
        scenarios = []
        if results_file.exists():
            try:
                raw = results_file.read_text(encoding="utf-8")
                data = json.loads(raw) if raw.strip() else []
                scenarios = self._parse_results(data)
            except Exception as exc:
                print(f"[runner] failed to parse results for run {run_id}: {exc}")

        return exit_code, scenarios

    def _pythonpath(self, current: str | None) -> str:
        """Build the PYTHONPATH needed by dashboard-launched Behave runs."""
        platform_root = Path(__file__).resolve().parents[2]
        required = [
            platform_root / "01-automation" / "02-src",
            self.project_root / "03-src",
        ]
        parts: list[str] = []
        for path in required:
            if path.exists():
                parts.append(str(path))
        if current:
            parts.extend(p for p in current.split(os.pathsep) if p)

        deduped: list[str] = []
        seen = set()
        for part in parts:
            key = str(Path(part)).lower()
            if key not in seen:
                seen.add(key)
                deduped.append(part)
        return os.pathsep.join(deduped)

    def _normalize_feature_paths(self, features: list[str]) -> list[str]:
        """Return behave positional paths relative to project_root.

        The dashboard used to send values like ``features/foo.feature``. The
        numbered West Kowloon layout now sends ``01-features/foo.feature``.
        Accept both so old browser state cannot create
        ``features/01-features/...`` paths and trigger Behave ConfigError.
        """
        normalized: list[str] = []
        for raw in features:
            value = str(raw).replace("\\", "/").lstrip("./")
            candidates = [value]
            if value.startswith("features/"):
                candidates.append(value.removeprefix("features/"))
            if not value.startswith("01-features/"):
                candidates.append(f"01-features/{value}")

            chosen = None
            for candidate in candidates:
                path = Path(candidate)
                full = path if path.is_absolute() else self.project_root / path
                if full.exists():
                    try:
                        chosen = str(full.relative_to(self.project_root))
                    except ValueError:
                        chosen = str(full)
                    break
            normalized.append(chosen or value)
        return normalized

    @staticmethod
    def _parse_results(data: list[dict]) -> list[dict]:
        """Convert behave JSON output into a flat list of scenario dicts.

        Behave JSON structure:
          [ { "name": "Feature...", "elements": [ { "name": "Scenario...", "steps": [...] } ] } ]

        Each step has a "result" dict with "status" (passed/failed/skipped) and "duration" (seconds).
        """
        scenarios = []

        for feature in data:
            feature_name = feature.get("name", "")

            for element in feature.get("elements", []):
                if element.get("keyword") not in ("Scenario", "Scenario Outline"):
                    continue

                steps = element.get("steps", [])
                duration = sum(
                    (s.get("result") or {}).get("duration", 0) for s in steps
                )

                # Per-step status. behave emits EVERY discovered step into the
                # JSON, but a step that never executed — because the scenario
                # was excluded by the tag filter, or the scenario was skipped —
                # carries no "result". That is NOT the same as an undefined
                # step (a step with no matching step definition, which behave
                # explicitly marks with result.status == "undefined").
                statuses = []
                for s in steps:
                    result = s.get("result")
                    if isinstance(result, dict) and result.get("status"):
                        statuses.append(result["status"])
                    else:
                        statuses.append("not_run")

                # Determine overall scenario status from its steps. A scenario
                # is "passed" ONLY when every step is passed / skipped / not-run.
                # Any failed, errored, or undefined step rules that out — and an
                # unrecognised status fails safe (never reported as passed), so
                # a scenario that errored after a few passing steps is never
                # mislabelled green.
                GOOD = {"passed", "skipped", "untested", "not_run"}
                if not statuses:
                    status = "skipped"
                elif "error" in statuses:
                    status = "error"
                elif "undefined" in statuses:
                    status = "undefined"        # a real missing step definition
                elif "failed" in statuses:
                    status = "failed"
                elif "passed" in statuses and all(s in GOOD for s in statuses):
                    status = "passed"
                elif all(s in ("skipped", "untested", "not_run") for s in statuses):
                    status = "skipped"
                else:
                    status = "failed"           # unknown status — fail safe

                # Extract the first error message (if any step failed)
                error_msg = None
                for step in steps:
                    result = step.get("result") or {}
                    if result.get("status") == "failed":
                        error_msg = result.get("error_message", "")
                        break

                # Tags can be strings ("@web") or objects ({"name": "@web"})
                raw_tags = element.get("tags", [])
                tag_list = []
                for t in raw_tags:
                    if isinstance(t, str):
                        tag_list.append(t)
                    elif isinstance(t, dict):
                        tag_list.append(t.get("name", ""))

                scenarios.append({
                    "feature": feature_name,
                    "name": element.get("name", ""),
                    "status": status,
                    "duration_s": round(duration, 3),
                    "error_msg": error_msg,
                    "tags": ",".join(tag_list),
                })

        return scenarios
