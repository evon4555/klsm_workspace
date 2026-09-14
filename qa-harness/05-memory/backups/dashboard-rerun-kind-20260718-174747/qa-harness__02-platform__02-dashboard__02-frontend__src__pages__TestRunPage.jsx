import { useState, useEffect, useCallback } from 'react'
import { Alert, Typography, Divider, Tag } from 'antd'

import KpiCards from '../components/KpiCards'
import RunControls from '../components/RunControls'
import ResultsTable from '../components/ResultsTable'
import ErrorAnalysis from '../components/ErrorAnalysis'
import LiveLog from '../components/LiveLog'
import {
  listRuns, startRun, getRunDetail, rerunFailed, connectWebSocket,
  getEvidenceStatus,
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

  // Per-case "synced to the Kasi workbook" status — refreshed on mount and
  // whenever an evidence sync finishes (RunControls calls onSyncDone).
  const fetchEvidence = useCallback(async () => {
    try { setEvidence(await getEvidenceStatus(projectKey)) } catch { /* ignore */ }
  }, [projectKey])

  const fetchRuns = useCallback(async () => {
    const data = await listRuns(projectKey)
    setRuns(data)
    if (data.length > 0 && !isRunning) {
      const latest = data[0]
      setCurrentRun(latest)
      if (latest.status !== 'running') {
        const detail = await getRunDetail(latest.id)
        setScenarios(detail.scenarios || [])
      }
    } else if (data.length === 0 && !isRunning) {
      setCurrentRun(null)
      setScenarios([])
    }
  }, [isRunning, projectKey])

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
    setLogLines([])
    setScenarios([])

    const result = await rerunFailed(currentRun.id)
    if (result?.error || !result?.id) {
      setIsRunning(false)
      setRunError(result?.error || 'Could not rerun failed scenarios.')
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

      <ResultsTable scenarios={scenarios} evidenceStatus={evidence} activeProject={activeProject} />

      {currentRun?.failed > 0 && (
        <ErrorAnalysis runId={currentRun.id} />
      )}

      <LiveLog lines={logLines} />
    </div>
  )
}
