import { useState, useEffect, useCallback } from 'react'
import { Alert, Typography, Divider, Tag, Modal } from 'antd'

import KpiCards from '../components/KpiCards'
import RunControls from '../components/RunControls'
import ResultsTable from '../components/ResultsTable'
import ErrorAnalysis from '../components/ErrorAnalysis'
import LiveLog from '../components/LiveLog'
import {
  listRuns, startRun, getRunDetail, rerunFailed, connectWebSocket,
  getEvidenceStatus, rerunScenario,
} from '../api'

const { Title, Text } = Typography

export default function TestRunPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const [runs, setRuns] = useState([])
  const [currentRun, setCurrentRun] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [logLines, setLogLines] = useState([])
  const [isRunning, setIsRunning] = useState(false)
  const [evidence, setEvidence] = useState({ cases: {} })
  const [runError, setRunError] = useState('')
  const [logMode, setLogMode] = useState('inline')
  const [rerunLogOpen, setRerunLogOpen] = useState(false)
  const [rerunLogTitle, setRerunLogTitle] = useState('Rerun Log')

  // Per-case "synced to the Kasi workbook" status — refreshed on mount and
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

  const handleSelectRun = async (runId) => {
    const detail = await getRunDetail(runId)
    setCurrentRun(detail)
    setScenarios(detail.scenarios || [])
    setLogLines([])
  }

  const handleRun = async (features, env) => {
    setIsRunning(true)
    setRunError('')
    setLogLines([])
    setLogMode('inline')
    setRerunLogOpen(false)
    setScenarios([])

    const result = await startRun(features, env, projectKey)
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
    setRerunLogTitle('Rerun Failed Log')
    setLogLines(['Starting failed-case rerun...'])
    const sourceRunId = currentRun.parent_run_id || currentRun.id

    let result
    try {
      result = await rerunFailed(currentRun.id)
    } catch (e) {
      setIsRunning(false)
      setRunError(`Could not rerun failed scenarios: ${e.message || e}`)
      setLogLines(prev => [...prev, `Request failed: ${e.message || e}`])
      return
    }
    if (result?.error || !result?.id) {
      setIsRunning(false)
      setRunError(result?.error || 'Could not rerun failed scenarios.')
      setLogLines(prev => [...prev, result?.error || 'Could not rerun failed scenarios.'])
      return
    }
    const { id } = result
    try {
      setLogLines([`Started failed-case rerun #${id} from full run #${sourceRunId}`])
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

  const hasFailed = currentRun?.failed > 0

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
      />

      <Divider style={{ margin: '16px 0' }} />

      <ResultsTable
        scenarios={scenarios}
        evidenceStatus={evidence}
        activeProject={activeProject}
        onRerunScenario={handleScenarioRerun}
      />

      {currentRun?.failed > 0 && (
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
