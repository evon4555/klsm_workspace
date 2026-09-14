/**
 * API client for the dashboard backend.
 *
 * All fetch calls go to /api/... which Vite proxies to http://localhost:8002
 * (configured in vite.config.js). This avoids CORS issues during development.
 */

/** List workspace projects available to the QA dashboard platform switcher. */
export async function fetchProjects() {
  const res = await fetch('/api/projects')
  if (!res.ok) throw new Error(`Projects: HTTP ${res.status}`)
  return res.json()
}

function projectQuery(project) {
  const qs = new URLSearchParams()
  if (project) qs.set('project', project)
  return qs.toString()
}

/**
 * Start a new behave test run. Returns { id, status }.
 * `features` is an array of feature-file paths (e.g.
 * ["01-features/ui_e2e/antank_registration.feature"]) to restrict the run to
 * those test-case groups, or null/undefined/[] to run every runnable case.
 */
export async function startRun(features, env, project = 'west-kowloon') {
  const res = await fetch('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, features: features && features.length ? features : null, env }),
  })
  return res.json()
}

/** List the 20 most recent runs (newest first). */
export async function listRuns(project = 'west-kowloon') {
  const qs = projectQuery(project)
  const res = await fetch(`/api/runs${qs ? `?${qs}` : ''}`)
  return res.json()
}

/** Get full details (summary + scenario list) for one run. */
export async function getRunDetail(runId) {
  const res = await fetch(`/api/runs/${runId}`)
  return res.json()
}

/** Rerun only the failed scenarios from a previous run. Returns { id, status }. */
export async function rerunFailed(runId) {
  const res = await fetch(`/api/runs/${runId}/rerun`, { method: 'POST' })
  return res.json()
}

/** List all features and available tags from .feature files. */
export async function listFeatures(project = 'west-kowloon') {
  const qs = projectQuery(project)
  const res = await fetch(`/api/features${qs ? `?${qs}` : ''}`)
  return res.json()
}

/**
 * Start an evidence sync: runs tools/update_evidence.py to refresh the Kasi
 * workbook (result columns + embedded step screenshots). `features` scopes the
 * sync to those test-case groups; null/[] syncs every case. Returns immediately;
 * poll getSyncStatus() for progress.
 */
export async function startSyncEvidence(features, env = 'sit', project = 'west-kowloon') {
  const res = await fetch('/api/sync-evidence', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, features: features && features.length ? features : null, env }),
  })
  return res.json()
}

/** Poll the current evidence-sync status + the tail of its log. */
export async function getSyncStatus() {
  const res = await fetch('/api/sync-evidence')
  return res.json()
}

/**
 * Per-case "synced to the Kasi workbook" status, written by
 * tools/update_evidence.py. Shape: { updated_at, cases: { "013": { status,
 * shots, synced, synced_at }, ... } }. The Test Results table joins this by
 * case number to render the "Sync to Excel" column.
 */
export async function getEvidenceStatus(project = 'west-kowloon') {
  const qs = projectQuery(project)
  const res = await fetch(`/api/evidence-status${qs ? `?${qs}` : ''}`)
  return res.json()
}

/**
 * Open a ZenTao bug for one failed scenario. Idempotent: if the scenario
 * already has a bug recorded, returns it instead of creating a duplicate.
 * `fields` is optional: { title, steps, severity, pri, type, product_id }.
 * Returns { bug_id, bug_url, title } on success, { error, ... } on failure.
 */
export async function openBugForScenario(scenarioId, fields = {}) {
  const res = await fetch(`/api/scenarios/${scenarioId}/open-bug`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  })
  return res.json()
}

/**
 * Rerun a single scenario. Spawns a new behave run filtered by the scenario
 * name (env + tags inherited from the source run). Returns { id, status,
 * scenario } so the caller can link to the new run.
 */
export async function rerunScenario(scenarioId) {
  const res = await fetch(`/api/scenarios/${scenarioId}/rerun`, { method: 'POST' })
  return res.json()
}

/**
 * Unified timeline of everything that has happened to one test case:
 * Behave runs from the DB, update_evidence.py screenshot batches, linked
 * ZenTao bugs, and the current xlsx snapshot. caseId may be a full
 * "SIT-TC-...-034" id; bare digits are kept for legacy WEB-AUTH cases.
 */
export async function getCaseHistory(caseId) {
  const res = await fetch(`/api/history/case/${encodeURIComponent(caseId)}`)
  return res.json()
}


/** Fetch pass rate trends, duration trends, and summary stats. */
export async function fetchTrends(limit = 30, project = 'west-kowloon') {
  const qs = new URLSearchParams({ limit: String(limit) })
  if (project) qs.set('project', project)
  const res = await fetch(`/api/stats/trends?${qs.toString()}`)
  return res.json()
}

/** Fetch smart error analysis for a specific run. */
export async function fetchErrorAnalysis(runId) {
  const res = await fetch(`/api/stats/errors/${runId}`)
  return res.json()
}

/** Fetch flaky test detection results. */
export async function fetchFlakyTests(limit = 15, project = 'west-kowloon') {
  const qs = new URLSearchParams({ limit: String(limit) })
  if (project) qs.set('project', project)
  const res = await fetch(`/api/stats/flaky?${qs.toString()}`)
  return res.json()
}

/** Get the latest API smoke run snapshot for the API Monitor page. */
export async function fetchApiMonitorEndpoints(project = 'west-kowloon') {
  const qs = projectQuery(project)
  const res = await fetch(`/api/api-monitor/endpoints${qs ? `?${qs}` : ''}`)
  return res.json()
}

/** Get the per-layer (smoke / contract / hybrid / functional) test counts. */
export async function fetchApiMonitorLayers(project = 'west-kowloon') {
  const qs = projectQuery(project)
  const res = await fetch(`/api/api-monitor/layers${qs ? `?${qs}` : ''}`)
  return res.json()
}

/** Trigger the API smoke pytest layer in the dashboard backend. */
export async function startApiMonitorSmokeRun(env = 'sit', project = 'west-kowloon') {
  const res = await fetch('/api/api-monitor/run-smoke', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ env, project }),
  })
  if (!res.ok) throw new Error(`API smoke trigger failed: HTTP ${res.status}`)
  return res.json()
}

/** Poll the current or most recent API smoke dashboard-trigger status. */
export async function fetchApiMonitorSmokeRun(project = 'west-kowloon') {
  const qs = projectQuery(project)
  const res = await fetch(`/api/api-monitor/run-smoke${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error(`API smoke status failed: HTTP ${res.status}`)
  return res.json()
}

/** Get API monitor trend time-series for the last N hours.
 *  Optionally narrows to one endpoint's per-run latency / status. */
export async function fetchApiMonitorTrends(hours = 168, endpointName = null, project = 'west-kowloon') {
  const qs = new URLSearchParams({ hours: String(hours) })
  if (endpointName) qs.set('endpoint_name', endpointName)
  if (project) qs.set('project', project)
  const res = await fetch(`/api/api-monitor/trends?${qs.toString()}`)
  return res.json()
}

/**
 * Quality System - Package Health.
 * List every requirement package for the selected project with per-stage status.
 * Manual refresh: call this whenever the user clicks the Refresh button.
 */
export async function fetchQualityPackages(project = 'west-kowloon') {
  const res = await fetch(`/api/quality-system/packages?project=${encodeURIComponent(project)}`)
  if (!res.ok) throw new Error(`Quality System packages: HTTP ${res.status}`)
  return res.json()
}

/**
 * Quality System - single package detail.
 * `packageId` is the workspace-relative path with forward slashes, e.g.
 * "west-kowloon/01-requirements/02-subprojects/02-website/02-modules/08-discount/2026-06-25"
 */
export async function fetchQualityPackage(packageId) {
  const path = packageId.split('/').map(encodeURIComponent).join('/')
  const res = await fetch(`/api/quality-system/packages/${path}`)
  if (!res.ok) throw new Error(`Quality System package: HTTP ${res.status}`)
  return res.json()
}

/**
 * Open a workspace file in the OS default application (Word/WPS for .docx,
 * Notepad for .md). Backend uses os.startfile on Windows.
 */
export async function openWorkspaceFile(relPath) {
  const res = await fetch('/api/quality-system/open-file', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: relPath }),
  })
  return res.json()
}

/**
 * Generate a sibling .docx from a .md file (uses md_docx.py to-docx).
 */
export async function generateReviewDocx(relMdPath) {
  const res = await fetch('/api/quality-system/generate-docx', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: relMdPath }),
  })
  return res.json()
}

/**
 * Find dashboard.db test runs that exercised this package's scope. Extracts
 * case IDs from the package's xlsx files and joins to test_scenarios.
 */
export async function fetchPackageExecutions(packageId) {
  const path = packageId.split('/').map(encodeURIComponent).join('/')
  const res = await fetch(`/api/quality-system/packages/${path}/executions`)
  if (!res.ok) throw new Error(`Package executions: HTTP ${res.status}`)
  return res.json()
}

/**
 * Run validate_testcase_xlsx.py on every test-cases-*.xlsx in this package.
 */
export async function validatePackageXlsx(packageId) {
  const path = packageId.split('/').map(encodeURIComponent).join('/')
  const res = await fetch(`/api/quality-system/packages/${path}/validate-xlsx`, {
    method: 'POST',
  })
  return res.json()
}

/**
 * Open a WebSocket connection to stream live logs from a running test.
 *
 * @param {number}   runId     - The run ID to stream logs for
 * @param {function} onMessage - Called with each log line (string)
 * @param {function} onDone    - Called when the run finishes
 * @returns {WebSocket} the socket instance (caller can .close() to disconnect)
 */
export function connectWebSocket(runId, onMessage, onDone) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${window.location.host}/ws/runs/${runId}`)

  ws.onmessage = (event) => {
    // The server sends either plain text (log line) or JSON (control message)
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'done') {
        onDone()
        ws.close()
        return
      }
      if (data.type === 'ping') return   // keep-alive, ignore
    } catch {
      // Not JSON: it is a plain text log line.
    }
    onMessage(event.data)
  }

  ws.onerror = () => ws.close()

  return ws
}
