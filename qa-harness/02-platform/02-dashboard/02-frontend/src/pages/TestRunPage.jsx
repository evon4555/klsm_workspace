import { useState, useEffect, useCallback, useMemo } from 'react'
import { Alert, Typography, Divider, Tag, Modal, Button, Space } from 'antd'

import KpiCards from '../components/KpiCards'
import RunControls from '../components/RunControls'
import ResultsTable from '../components/ResultsTable'
import ErrorAnalysis from '../components/ErrorAnalysis'
import LiveLog from '../components/LiveLog'
import {
  listRuns, startRun, getRunDetail, rerunFailed, connectWebSocket,
  getEvidenceStatus, rerunScenario, fetchPackageExecutions,
} from '../api'

const { Title, Text } = Typography

export default function TestRunPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const packageId = useMemo(() => {
    if (typeof window === 'undefined') return null
    const raw = new URLSearchParams(window.location.search).get('package')
    if (!raw) return null
    const first = raw.replace(/\\/g, '/').split('/', 1)[0]
    return first === projectKey ? raw : null
  }, [projectKey])
  const [runs, setRuns] = useState([])
  const [currentRun, setCurrentRun] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [packageExec, setPackageExec] = useState(null)
  const [logLines, setLogLines] = useState([])
  const [isRunning, setIsRunning] = useState(false)
  const [evidence, setEvidence] = useState({ cases: {} })
  const [runError, setRunError] = useState('')
  const [logMode, setLogMode] = useState('inline')
  const [rerunLogOpen, setRerunLogOpen] = useState(false)
  const [rerunLogTitle, setRerunLogTitle] = useState('Rerun Log')

  // Per-case "synced to the Kasi workbook" status; refreshed on mount and
  // whenever an evidence sync finishes (RunControls calls onSyncDone).
  const fetchEvidence = useCallback(async () => {
    try { setEvidence(await getEvidenceStatus(projectKey)) } catch { /* ignore */ }
  }, [projectKey])

  const fetchRuns = useCallback(async () => {
    const data = await listRuns(projectKey)
    setRuns(data)
    if (data.length > 0) {
      const latest = data[0]
      setCurrentRun(latest)
      if (latest.status !== 'running') {
        const detail = await getRunDetail(latest.id)
        setScenarios(detail.scenarios || [])
      }
    } else if (data.length === 0) {
      setCurrentRun(null)
      setScenarios([])
    }
  }, [projectKey])

  const refreshRunDetail = useCallback(async (runId) => {
    if (!runId) return null
    const detail = await getRunDetail(runId)
    setCurrentRun(detail)
    setScenarios(detail.scenarios || [])
    return detail
  }, [])

  const waitForRunDone = useCallback((runId, onLine, timeoutMs = 15 * 60 * 1000) => {
    return new Promise((resolve) => {
      let done = false
      let ws = null
      const finish = () => {
        if (done) return
        done = true
        if (ws) ws.close()
        clearTimeout(timer)
        resolve()
      }
      const timer = setTimeout(finish, timeoutMs)
      ws = connectWebSocket(runId, onLine, finish)
    })
  }, [])

  useEffect(() => {
    setRunError('')
    setLogLines([])
    fetchRuns()
    fetchEvidence()
  }, [fetchRuns, fetchEvidence])

  useEffect(() => {
    if (!packageId) {
      setPackageExec(null)
      return
    }
    let cancelled = false
    fetchPackageExecutions(packageId)
      .then((data) => { if (!cancelled) setPackageExec(data) })
      .catch(() => { if (!cancelled) setPackageExec(null) })
    return () => { cancelled = true }
  }, [packageId])

  const handleSelectRun = async (runId) => {
    const detail = await getRunDetail(runId)
    setCurrentRun(detail)
    setScenarios(detail.scenarios || [])
    setLogLines([])
  }

  const handleRun = async (features, env, names = null) => {
    setIsRunning(true)
    setRunError('')
    setLogLines([])
    setLogMode('inline')
    setRerunLogOpen(false)
    setScenarios([])

    const result = await startRun(features, env, projectKey, names, packageId)
    if (result?.error || !result?.id) {
      setIsRunning(false)
      setRunError(result?.error || 'Could not start test run.')
      return
    }
    const { id } = result
    setCurrentRun({ id, status: 'running', total: 0, passed: 0, failed: 0, skipped: 0 })

    connectWebSocket(
      id,
      (line) => setLogLines(prev => [...prev, line]),
      async () => {
        setIsRunning(false)
        const detail = await getRunDetail(id)
        setCurrentRun(detail)
        setScenarios(detail.scenarios || [])
        fetchRuns()
      }
    )
  }

  const handleRerun = async () => {
    if (!currentRun) return
    setIsRunning(true)
    setRunError('')
    setLogMode('rerun')
    setRerunLogOpen(true)
    setRerunLogTitle('Rerun Failed / Errored Log')
    setLogLines(['Starting failed/errored-case rerun...'])
    const sourceRunId = currentRun.parent_run_id || currentRun.id

    let result
    try {
      result = await rerunFailed(currentRun.id)
    } catch (e) {
      setIsRunning(false)
      setRunError(`Could not rerun failed/errored scenarios: ${e.message || e}`)
      setLogLines(prev => [...prev, `Request failed: ${e.message || e}`])
      return
    }
    if (result?.error || !result?.id) {
      setIsRunning(false)
      setRunError(result?.error || 'Could not rerun failed/errored scenarios.')
      setLogLines(prev => [...prev, result?.error || 'Could not rerun failed/errored scenarios.'])
      return
    }
    const { id } = result
    try {
      setLogLines([`Started failed/errored-case rerun #${id} from full run #${sourceRunId}`])
      await waitForRunDone(id, (line) => setLogLines(prev => [...prev, line]))
      await refreshRunDetail(sourceRunId)
      await fetchEvidence()
      fetchRuns()
      setLogLines(prev => [...prev, `Rerun #${id} finished. Full run #${sourceRunId} refreshed.`])
      return result
    } catch (e) {
      setRunError(`Rerun finished but refresh failed: ${e.message || e}`)
      return { error: e.message || String(e), id }
    } finally {
      setIsRunning(false)
    }
  }

  const handleScenarioRerun = async (scenario) => {
    if (!currentRun) return { error: 'No full run is selected.' }
    setIsRunning(true)
    setRunError('')
    setLogMode('rerun')
    setRerunLogOpen(true)
    setRerunLogTitle(`Rerun Log - ${scenario.case_id || 'Scenario'}`)
    setLogLines([`Starting single-case rerun: ${scenario.case_id || scenario.name}`])
    const sourceRunId = currentRun.parent_run_id || currentRun.id
    let result
    try {
      result = await rerunScenario(scenario.id)
    } catch (e) {
      setIsRunning(false)
      setRunError(`Could not rerun this scenario: ${e.message || e}`)
      setLogLines(prev => [...prev, `Request failed: ${e.message || e}`])
      return { error: e.message || String(e) }
    }
    if (result?.error || !result?.id) {
      setIsRunning(false)
      setRunError(result?.error || 'Could not rerun this scenario.')
      setLogLines(prev => [...prev, result?.error || 'Could not rerun this scenario.'])
      return result || { error: 'Could not rerun this scenario.' }
    }
    const { id } = result
    const caseLabel = scenario.case_id || scenario.name
    try {
      setLogLines([`Started single-case rerun #${id} from full run #${sourceRunId}: ${caseLabel}`])
      await waitForRunDone(id, (line) => setLogLines(prev => [...prev, line]))
      await refreshRunDetail(sourceRunId)
      await fetchEvidence()
      fetchRuns()
      setLogLines(prev => [...prev, `Rerun #${id} finished. Full run #${sourceRunId} refreshed.`])
      return result
    } catch (e) {
      setRunError(`Scenario rerun finished but refresh failed: ${e.message || e}`)
      return { error: e.message || String(e), id }
    } finally {
      setIsRunning(false)
    }
  }

  const problemCount = (currentRun?.failed || 0) + (currentRun?.errored || 0)
  const hasFailed = problemCount > 0
  const packageCompleteRun = packageExec?.latest_package_complete_run
  const packageSnapshot = packageExec?.current_snapshot
  const packageGate = packageExec?.execution_gate
  const selectedPackageRun = packageExec?.runs?.find(r => r.id === currentRun?.id)
  const selectedRunScope = selectedPackageRun
    ? [
        `#${selectedPackageRun.id}`,
        (selectedPackageRun.scope_kind || 'unknown').replace(/_/g, ' '),
        `${selectedPackageRun.scope_matched || 0}/${packageExec.case_count || 0} matched`,
      ].join(' / ')
    : (currentRun?.id && packageExec ? `#${currentRun.id} / not linked to this package` : null)
  const packageSummaryRows = packageExec
    ? [
        `Scope: ${packageExec.case_count || 0} signed case(s)`,
        `Gate: ${[
          packageCompleteRun ? `latest package-complete #${packageCompleteRun.id}` : 'no package-complete run yet',
          packageSnapshot?.dashboard_run_id ? `snapshot #${packageSnapshot.dashboard_run_id}` : 'no promoted snapshot',
          packageGate?.snapshot_status ? `snapshot ${packageGate.snapshot_status}` : null,
        ].filter(Boolean).join(' / ')}`,
        selectedRunScope ? `Selected run: ${selectedRunScope}` : null,
      ].filter(Boolean)
    : []

  return (
    <div style={{ maxWidth: 1400 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
          Test Run
        </Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Execute and monitor Behave + Playwright test suites for <Tag style={{ marginInline: 4 }}>{projectName}</Tag>
        </Text>
      </div>

      {runError && (
        <Alert type="error" showIcon message={runError} style={{ marginBottom: 16 }} closable onClose={() => setRunError('')} />
      )}

      {packageId && (
        <Alert
          type={packageGate?.snapshot_status === 'stale' ? 'warning' : 'info'}
          showIcon
          message="Package execution context"
          description={
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <span><code>{packageId}</code></span>
              {packageSummaryRows.length > 0
                ? packageSummaryRows.map(row => <span key={row}>{row}</span>)
                : <span>Loading package execution status...</span>}
              {packageCompleteRun && (
                <Button size="small" onClick={() => handleSelectRun(packageCompleteRun.id)}>
                  View package-complete run #{packageCompleteRun.id}
                </Button>
              )}
            </Space>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <KpiCards run={currentRun} />

      <RunControls
        onRun={handleRun}
        onRerun={handleRerun}
        isRunning={isRunning}
        hasFailed={hasFailed}
        runs={runs}
        currentRunId={currentRun?.id}
        onSelectRun={handleSelectRun}
        onSyncDone={fetchEvidence}
        activeProject={activeProject}
        activeProjectKey={projectKey}
        packageId={packageId}
        packageExecution={packageExec}
      />

      <Divider style={{ margin: '16px 0' }} />

      <ResultsTable
        scenarios={scenarios}
        evidenceStatus={evidence}
        activeProject={activeProject}
        onRerunScenario={handleScenarioRerun}
      />

      {problemCount > 0 && (
        <ErrorAnalysis runId={currentRun.id} />
      )}

      {logMode === 'inline' && <LiveLog lines={logLines} />}

      <Modal
        title={rerunLogTitle}
        open={logMode === 'rerun' && rerunLogOpen}
        onCancel={() => setRerunLogOpen(false)}
        footer={null}
        width={920}
        destroyOnHidden={false}
      >
        <LiveLog
          lines={logLines}
          embedded
          emptyText="Waiting for rerun output..."
        />
      </Modal>
    </div>
  )
}
