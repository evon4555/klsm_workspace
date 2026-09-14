import { useState, useEffect, useMemo, useRef } from 'react'
import { Button, Select, Card, Row, Col, Typography, Divider } from 'antd'
import {
  PlayCircleOutlined, ReloadOutlined, HistoryOutlined, SyncOutlined,
} from '@ant-design/icons'
import { listFeatures, startSyncEvidence, getSyncStatus } from '../api'

const { Text } = Typography

function runExecuted(run) {
  return run?.executed ?? ((run?.passed || 0) + (run?.failed || 0) + (run?.errored || 0))
}

function runCollected(run) {
  return run?.collected ?? run?.total ?? 0
}

const NON_RUNNABLE_TAGS = ['@na', '@needs-oauth-mock']

function isRunnableScenario(scenario) {
  const tags = scenario?.tags || []
  return !tags.some((tag) => NON_RUNNABLE_TAGS.includes(tag))
}

function featureGroupLabel(feature) {
  const fallback = feature?.feature || feature?.file || 'Feature'
  const raw = String(fallback)
    .replace(/^01-features\//, '')
    .replace(/\.feature$/, '')
    .replace(/[_-]+/g, ' ')
    .trim()
  return raw.replace(/\b\w/g, c => c.toUpperCase())
}

/**
 * Test-run controls: pick the environment + scope, then run.
 *
 * Scope is a multi-select dropdown of runnable test-case groups (one per
 * feature file). The dropdown scrolls, so it never overflows the row no
 * matter how many groups exist; selected groups show as selected pills in the box.
 * Empty selection = run all.
 * The Run button label always states what will run, so a click is never a
 * surprise. A scoped run executes only the chosen feature files, so results
 * contain no other test-case noise.
 *
 * "Sync -> xlsx" runs tools/update_evidence.py on the backend for the SAME
 * scope, refreshing the Kasi workbook's result columns + embedded step
 * screenshots. It is scope-aware so a single test-case group syncs quickly
 * (a full sync is ~30 min and trips the SIT OTP rate limit).
 */
export default function RunControls({
  onRun,
  onRerun,
  isRunning,
  hasFailed,
  runs,
  currentRunId,
  onSelectRun,
  onSyncDone,
  activeProject,
  activeProjectKey = 'west-kowloon',
}) {
  const [env, setEnv] = useState('sit')
  const [features, setFeatures] = useState([])
  const [selected, setSelected] = useState([])   // feature-file paths
  const [syncing, setSyncing] = useState(false)
  const [syncMsg, setSyncMsg] = useState('')
  const [syncOk, setSyncOk] = useState(null)      // null / true / false
  const pollRef = useRef(null)

  useEffect(() => {
    setSelected([])
    listFeatures(activeProjectKey).then(data => setFeatures(data.features || [])).catch(() => setFeatures([]))
  }, [activeProjectKey])

  // Poll the evidence-sync status until it finishes, mirroring the tail of
  // update_evidence.py's stdout into the status line.
  const pollSync = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      let st
      try { st = await getSyncStatus() } catch { return }
      const tail = (st.log || []).slice(-1)[0] || ''
      if (st.running) {
        setSyncMsg(tail || 'Syncing...')
        return
      }
      clearInterval(pollRef.current)
      pollRef.current = null
      setSyncing(false)
      setSyncOk(st.exit_code === 0)
      setSyncMsg(st.exit_code === 0
        ? `Synced to xlsx OK - ${st.scope}`
        : `Sync failed (exit ${st.exit_code}) - is the .xlsx open in Excel? ${tail}`)
      // Refresh the Test Results table's "Sync to Excel" column.
      onSyncDone?.()
    }, 4000)
  }

  // On mount: if a sync is already running (e.g. page was reloaded), re-attach.
  useEffect(() => {
    getSyncStatus().then(st => {
      if (st.running) { setSyncing(true); setSyncMsg('Syncing...'); pollSync() }
    }).catch(() => {})
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  // One runnable test-case group per feature file. The visible name comes
  // from the Feature metadata, not raw Behave execution tags.
  const testCaseGroups = useMemo(() => features.map(f => {
    const runnableScenarios = (f.scenarios || []).filter(isRunnableScenario)
    if (runnableScenarios.length === 0) return null
    const name = featureGroupLabel(f)
    return { name, value: f.file, count: runnableScenarios.length }
  }).filter(Boolean), [features])

  const options = testCaseGroups.map(m => ({ label: `${m.name} (${m.count})`, value: m.value }))
  const allValues = testCaseGroups.map(m => m.value)

  // Scope label: nothing / everything selected -> "All";
  // one test-case group -> its name; otherwise -> "N test cases".
  const scopeLabel = useMemo(() => {
    if (selected.length === 0 || selected.length === testCaseGroups.length) return 'All'
    if (selected.length === 1)
      return testCaseGroups.find(m => m.value === selected[0])?.name || '1 test case'
    return `${selected.length} test cases`
  }, [selected, testCaseGroups])

  const handleRun = () => onRun(selected.length ? selected : null, env)

  const handleSync = async () => {
    setSyncMsg('Starting sync...')
    setSyncOk(null)
    setSyncing(true)
    try {
      await startSyncEvidence(selected.length ? selected : null, env, activeProjectKey)
      pollSync()
    } catch {
      setSyncing(false)
      setSyncOk(false)
      setSyncMsg('Could not reach the backend to start the sync.')
    }
  }

  return (
    <Card
      size="small"
      style={{
        borderRadius: 12,
        border: 'none',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        marginBottom: 16,
      }}
    >
      <Row gutter={[12, 12]} align="middle">
        <Col>
          <Text type="secondary" style={{ fontSize: 13, marginRight: 8 }}>
            Project
          </Text>
          <Text strong style={{ marginRight: 12 }}>
            {activeProject?.name || activeProjectKey}
          </Text>
        </Col>
        <Col>
          <Select
            value={env}
            onChange={setEnv}
            style={{ width: 110 }}
            options={[
              { value: 'local', label: 'Local' },
              { value: 'sit', label: 'SIT' },
              { value: 'uat', label: 'UAT' },
            ]}
          />
        </Col>
        <Col>
          <Text type="secondary" style={{ fontSize: 13, marginRight: 8 }}>
            Test Case
          </Text>
          <Select
            mode="multiple"
            allowClear
            showSearch
            optionFilterProp="label"
            placeholder="All test cases"
            value={selected}
            onChange={setSelected}
            options={options}
            maxTagCount="responsive"
            style={{ minWidth: 240, maxWidth: 360 }}
            popupMatchSelectWidth={false}
            popupRender={(menu) => (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between',
                              padding: '4px 8px' }}>
                  <Button type="link" size="small"
                    onClick={() => setSelected(allValues)}>
                    Select all
                  </Button>
                  <Button type="link" size="small"
                    onClick={() => setSelected([])}>
                    Clear
                  </Button>
                </div>
                <Divider style={{ margin: '4px 0' }} />
                {menu}
              </>
            )}
          />
        </Col>
        <Col>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            loading={isRunning}
            disabled={testCaseGroups.length === 0}
            onClick={handleRun}
            style={{ borderRadius: 6 }}
          >
            {`Run: ${scopeLabel}`}
          </Button>
        </Col>
        <Col>
          <Button
            icon={<ReloadOutlined />}
            disabled={!hasFailed || isRunning}
            onClick={onRerun}
            style={{ borderRadius: 6 }}
          >
            Rerun Failed
          </Button>
        </Col>
        <Col>
          <Button
            icon={<SyncOutlined spin={syncing} />}
            loading={syncing}
            disabled={testCaseGroups.length === 0}
            onClick={handleSync}
            style={{ borderRadius: 6 }}
            title="Run update_evidence.py for the selected scope - refreshes the Kasi workbook result columns + embedded step screenshots"
          >
            {syncing ? 'Syncing...' : `Sync -> xlsx: ${scopeLabel}`}
          </Button>
        </Col>
        <Col flex="auto" style={{ textAlign: 'right' }}>
          {runs.length > 0 && (
            <Select
              value={currentRunId}
              onChange={onSelectRun}
              style={{ width: 420 }}
              placeholder="View past run..."
              suffixIcon={<HistoryOutlined />}
              options={runs.map((r) => ({
                value: r.id,
                label: `Run #${r.id} - ${r.status.toUpperCase()} (${r.env}) - ${runExecuted(r)}/${runCollected(r)} executed/collected`,
              }))}
            />
          )}
        </Col>
      </Row>

      {syncMsg && (
        <Row style={{ marginTop: 8 }}>
          <Col flex="auto">
            <Text
              type={syncOk === false ? 'danger' : 'secondary'}
              style={{ fontSize: 12, fontFamily: 'monospace' }}
            >
              {syncing ? '[sync] ' : (syncOk ? '[ok] ' : '[warn] ')}{syncMsg}
            </Text>
          </Col>
        </Row>
      )}
      {testCaseGroups.length === 0 && (
        <Row style={{ marginTop: 8 }}>
          <Col flex="auto">
            <Text type="secondary" style={{ fontSize: 12 }}>
              No runnable feature files found for {activeProject?.name || activeProjectKey}.
            </Text>
          </Col>
        </Row>
      )}
    </Card>
  )
}
