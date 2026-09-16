import { useState, useEffect, useMemo, useRef } from 'react'
import { Button, Select, Card, Row, Col, Typography, Divider, Tooltip } from 'antd'
import {
  PlayCircleOutlined, ReloadOutlined, HistoryOutlined, SyncOutlined,
} from '@ant-design/icons'
import { listFeatures, startSyncEvidence, getSyncStatus } from '../api'
import { formatDashboardTime } from '../utils/time.js'

const { Text } = Typography

function formatRunTime(iso) {
  return iso ? formatDashboardTime(iso, { withYear: true }) : 'no time'
}

function runExecuted(run) {
  return run?.executed ?? ((run?.passed || 0) + (run?.failed || 0) + (run?.errored || 0))
}

function runCollected(run) {
  return run?.collected ?? run?.total ?? 0
}

const NON_RUNNABLE_TAGS = ['@na', '@needs-oauth-mock']
const ALL_SCOPE_LABEL = 'All Test Cases'
const TEST_CASE_SCOPE_WIDTH = 180

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
 * matter how many groups exist. Full scope shows a short "All Test Cases"
 * label; partial scope collapses to a compact +N counter in the box.
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
  activeProjectKey = 'west-kowloon',
  packageId = null,
  packageExecution = null,
}) {
  const [env, setEnv] = useState('sit')
  const [features, setFeatures] = useState([])
  const [selected, setSelected] = useState([])   // feature-file paths
  const [syncing, setSyncing] = useState(false)
  const [syncMsg, setSyncMsg] = useState('')
  const [syncOk, setSyncOk] = useState(null)      // null / true / false
  const [runKindFilter, setRunKindFilter] = useState('all')
  const pollRef = useRef(null)

  useEffect(() => {
    setSelected([])
    listFeatures(activeProjectKey, packageId).then(data => setFeatures(data.features || [])).catch(() => setFeatures([]))
  }, [activeProjectKey, packageId])

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
    return {
      name,
      value: f.file,
      count: runnableScenarios.length,
      scenarioNames: runnableScenarios.map(s => s.name).filter(Boolean),
      caseIds: runnableScenarios.map(s => s.case_id).filter(Boolean),
    }
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

  const scopeDetail = useMemo(() => {
    if (selected.length === 0) {
      return packageId
        ? `All runnable test cases in this package (${packageExecution?.case_count || 'loading'} signed case(s))`
        : 'All runnable test cases'
    }
    const selectedNames = selected
      .map(value => testCaseGroups.find(m => m.value === value))
      .filter(Boolean)
      .map(group => `${group.name} (${group.count})`)
    return selectedNames.length > 0 ? selectedNames.join('\n') : scopeLabel
  }, [selected, testCaseGroups, scopeLabel, packageId, packageExecution?.case_count])

  function selectedGroupsForAction() {
    if (selected.length === 0 || selected.length === testCaseGroups.length) return testCaseGroups
    const selectedSet = new Set(selected)
    return testCaseGroups.filter(group => selectedSet.has(group.value))
  }

  function actionScope() {
    const groups = selectedGroupsForAction()
    const featureFiles = groups.map(group => group.value)
    const scenarioNames = groups.flatMap(group => group.scenarioNames || [])
    return {
      features: packageId ? featureFiles : (selected.length ? selected : null),
      names: packageId ? scenarioNames : null,
    }
  }

  const handleRun = () => {
    const scope = actionScope()
    onRun(scope.features, env, scope.names)
  }

  const handleSync = async () => {
    setSyncMsg('Starting sync...')
    setSyncOk(null)
    setSyncing(true)
    try {
      const scope = actionScope()
      await startSyncEvidence(scope.features, env, activeProjectKey)
      pollSync()
    } catch {
      setSyncing(false)
      setSyncOk(false)
      setSyncMsg('Could not reach the backend to start the sync.')
    }
  }

  const isAllScope = selected.length === 0 || selected.length === testCaseGroups.length
  const runButtonLabel = isAllScope ? 'Run: All' : 'Run: Selected'
  const scopeTitle = selected.length === 0
    ? (packageId ? `Current scope: Package all cases\n${packageId}` : 'Current scope: All runnable test cases')
    : `Current scope:\n${scopeDetail}`
  const selectedRun = useMemo(
    () => (runs || []).find(r => String(r.id) === String(currentRunId)),
    [runs, currentRunId],
  )
  const runHistoryOptions = useMemo(
    () => (runs || []).map((r) => {
      const runType = r.run_kind === 'api' ? 'API' : 'Full'
      const status = String(r.status || 'unknown').toUpperCase()
      const executed = `${runExecuted(r)}/${runCollected(r)} executed`
      const when = formatRunTime(r.finished_at || r.started_at)
      const selectedLabel = `${runType} run #${r.id} - ${executed} - ${when}`
      return {
        value: r.id,
        runKind: r.run_kind === 'api' ? 'api' : 'full',
        label: `${runType} run #${r.id} - ${status} - ${executed} - ${when}`,
        selectedLabel,
        searchText: `${r.id} ${runType} ${r.run_kind || ''} ${status} ${executed} ${when}`.toLowerCase(),
      }
    }),
    [runs],
  )
  const visibleRunHistoryOptions = useMemo(
    () => (
      runKindFilter === 'all'
        ? runHistoryOptions
        : runHistoryOptions.filter(option => option.runKind === runKindFilter)
    ),
    [runHistoryOptions, runKindFilter],
  )
  const visibleRunHistoryValue = visibleRunHistoryOptions.some(
    option => String(option.value) === String(currentRunId),
  ) ? currentRunId : undefined
  const handleRunKindFilter = (nextKind) => {
    setRunKindFilter(nextKind)
  }
  const canRerunFailed = hasFailed && !isRunning && ((selectedRun?.run_kind || 'full') === 'full')

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
          <Tooltip title={scopeTitle}>
            <Select
              mode="multiple"
              allowClear
              showSearch
              optionFilterProp="label"
              placeholder={ALL_SCOPE_LABEL}
              value={selected}
              onChange={setSelected}
              options={options}
              maxTagCount={0}
              maxTagPlaceholder={(omitted) => (
                omitted.length === testCaseGroups.length ? ALL_SCOPE_LABEL : `+${omitted.length}`
              )}
              style={{ width: TEST_CASE_SCOPE_WIDTH }}
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
          </Tooltip>
        </Col>
        <Col>
          <Tooltip title={scopeTitle}>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              loading={isRunning}
              disabled={testCaseGroups.length === 0}
              onClick={handleRun}
              style={{ borderRadius: 6, width: 122 }}
            >
              {runButtonLabel}
            </Button>
          </Tooltip>
        </Col>
        <Col>
          <Tooltip title="Reruns failed or errored cases from the selected full run. The Test Case dropdown does not change this scope.">
            <Button
              icon={<ReloadOutlined />}
              disabled={!canRerunFailed}
              onClick={onRerun}
              style={{ borderRadius: 6 }}
            >
              Rerun Failed
            </Button>
          </Tooltip>
        </Col>
        <Col>
          <Tooltip title={`Sync evidence to xlsx. ${scopeTitle}`}>
            <Button
              icon={<SyncOutlined spin={syncing} />}
              loading={syncing}
              disabled={testCaseGroups.length === 0}
              onClick={handleSync}
              style={{ borderRadius: 6, width: 124 }}
            >
              {syncing ? 'Syncing' : 'Sync xlsx'}
            </Button>
          </Tooltip>
        </Col>
        <Col flex="auto" style={{ textAlign: 'right', minWidth: 520 }}>
          {runs.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8 }}>
              <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>Run Type</Text>
              <Select
                aria-label="Filter runs by type"
                value={runKindFilter}
                onChange={handleRunKindFilter}
                style={{ width: 105, textAlign: 'left' }}
                options={[
                  { value: 'all', label: 'All Runs' },
                  { value: 'api', label: 'API' },
                  { value: 'full', label: 'Full' },
                ]}
              />
              <Tooltip title="Search by run ID, status, or date">
                <Select
                  aria-label="Select a filtered run"
                  value={visibleRunHistoryValue}
                  onChange={onSelectRun}
                  showSearch
                  optionLabelProp="selectedLabel"
                  filterOption={(input, option) => (
                    option?.searchText?.includes(input.trim().toLowerCase())
                  )}
                  style={{ width: 300, textAlign: 'left' }}
                  placeholder={
                    runKindFilter === 'all'
                      ? 'Search run ID, status, or date...'
                      : runKindFilter === 'api'
                        ? 'Select an API run...'
                        : 'Select a Full run...'
                  }
                  notFoundContent="No matching run"
                  suffixIcon={<HistoryOutlined />}
                  options={visibleRunHistoryOptions}
                />
              </Tooltip>
            </div>
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
              No runnable feature files found for {activeProjectKey}.
            </Text>
          </Col>
        </Row>
      )}
    </Card>
  )
}
