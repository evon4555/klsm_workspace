import { useState, useEffect, useMemo } from 'react'
import {
  Typography, Card, Row, Col, Statistic, Table, Tag, Button, Input, InputNumber,
  Space, Divider, Badge, Tabs, Alert, Tooltip, Spin, Select,
} from 'antd'
import {
  ThunderboltOutlined, PlayCircleOutlined, StopOutlined, ClockCircleOutlined, TeamOutlined,
  DashboardOutlined, WarningOutlined,
  ApiOutlined, LinkOutlined, ReloadOutlined,
  BarChartOutlined, LineChartOutlined, SettingOutlined, HistoryOutlined, EyeOutlined,
} from '@ant-design/icons'
import { requestJson } from '../apiClient'

const { Title, Text, Paragraph } = Typography

const PERFORMANCE_MODE_OPTIONS = [
  { value: 'mixed', label: 'Mixed' },
  { value: 'login', label: 'Login only' },
  { value: 'business', label: 'Business mix' },
  { value: 'order_create', label: 'Business: order create' },
  { value: 'order_cancel', label: 'Business: order cancel' },
  { value: 'linked_ticket', label: 'Linked Ticket cart' },
]

const DEFAULT_MODE_VALUES = ['mixed', 'login', 'business', 'order_create', 'order_cancel']
const MODE_LABEL_BY_VALUE = Object.fromEntries(
  PERFORMANCE_MODE_OPTIONS.map((option) => [option.value, option.label]),
)

const LOCUST_FILE_MODE_MAP = {
  'tests/performance/locustfile.py': DEFAULT_MODE_VALUES,
  'tests/performance/business_create_order.py': ['order_create'],
  'tests/performance/linked_ticket.py': ['linked_ticket'],
}

function normalizeLocustFile(file) {
  return (file || '').replace(/\\/g, '/')
}

function allowedModesForLocustFile(file, apiModes = {}) {
  const normalized = normalizeLocustFile(file)
  const fromApi = apiModes?.[normalized]
  if (Array.isArray(fromApi) && fromApi.length) {
    return fromApi.filter((mode) => MODE_LABEL_BY_VALUE[mode])
  }
  if (LOCUST_FILE_MODE_MAP[normalized]) {
    return LOCUST_FILE_MODE_MAP[normalized]
  }

  const filename = normalized.split('/').pop()?.toLowerCase() || ''
  if (filename.includes('create_order') || filename.includes('create-order')) return ['order_create']
  if (filename.includes('cancel_order') || filename.includes('cancel-order')) return ['order_cancel']
  return DEFAULT_MODE_VALUES
}

function modeLabel(mode) {
  return MODE_LABEL_BY_VALUE[mode] || mode || 'Mixed'
}

function locustFileName(file) {
  return normalizeLocustFile(file).split('/').pop() || file || '-'
}

function formatDateTime(iso) {
  if (!iso) return '-'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return String(iso).replace('T', ' ').slice(0, 19)
  return date.toLocaleString()
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function fetchServiceStatus(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/perf/services${qs}`)
}

async function fetchPerfStatus(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/perf/status${qs}`)
}

async function fetchGrafanaPanels(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/perf/grafana/panels${qs}`)
}

async function fetchPerfReport(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/perf/report${qs}`)
}

async function fetchPerfMetrics(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/perf/metrics${qs}`)
}

async function fetchPerfLocustFiles(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/perf/locustfiles${qs}`)
}

async function fetchPerfRuns(project, limit = 50) {
  const qs = new URLSearchParams()
  if (project) qs.set('project', project)
  qs.set('limit', String(limit))
  return requestJson(`/api/perf/runs?${qs.toString()}`)
}

async function fetchPerfRunDetail(runId, project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/perf/runs/${runId}${qs}`)
}

async function startPerfTest(config) {
  return requestJson('/api/perf/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
}

async function stopPerfTest() {
  return requestJson('/api/perf/stop', { method: 'POST' })
}

// ---------------------------------------------------------------------------
// SVG Mini Charts
// ---------------------------------------------------------------------------

function TimeSeriesChart({ data, width = 500, height = 100, color = '#1677ff', label = '', unit = '' }) {
  if (!data || data.length < 2) return <Text type="secondary" style={{ fontSize: 12 }}>No data</Text>

  const values = data.map(d => d.value)
  const min = Math.min(...values) * 0.9
  const max = Math.max(...values) * 1.1 || 1
  const range = max - min || 1
  const step = width / (data.length - 1)

  const points = values.map((v, i) => ({
    x: i * step,
    y: height - 10 - ((v - min) / range) * (height - 20),
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height} L 0 ${height} Z`
  const lastVal = values[values.length - 1]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <Text type="secondary" style={{ fontSize: 11 }}>{label}</Text>
        <Text strong style={{ fontSize: 13, color }}>{lastVal?.toFixed(1)}{unit}</Text>
      </div>
      <svg width={width} height={height} style={{ display: 'block' }}>
        <path d={areaPath} fill={color} opacity={0.08} />
        <path d={linePath} fill="none" stroke={color} strokeWidth={1.5} />
        <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r={3} fill={color} />
      </svg>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Service Status Indicator
// ---------------------------------------------------------------------------

function ServiceBadge({ name, connected, url, icon }) {
  return (
    <Tooltip title={`${url} — ${connected ? 'Connected' : 'Not reachable'}`}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '6px 12px', borderRadius: 6,
        background: connected ? '#f6ffed' : '#fff2f0',
        border: `1px solid ${connected ? '#b7eb8f' : '#ffccc7'}`,
      }}>
        {icon}
        <Text strong style={{ fontSize: 12 }}>{name}</Text>
        <Badge status={connected ? 'success' : 'error'} />
      </div>
    </Tooltip>
  )
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function PerformanceTestPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const [services, setServices] = useState(null)
  const [runStatus, setRunStatus] = useState(null)
  const [report, setReport] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [grafana, setGrafana] = useState(null)
  const [locustfiles, setLocustfiles] = useState([])
  const [locustfileModes, setLocustfileModes] = useState({})
  const [perfRuns, setPerfRuns] = useState([])
  const [selectedRunDetail, setSelectedRunDetail] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [testRunning, setTestRunning] = useState(false)
  const [runError, setRunError] = useState('')

  // Config state
  const [host, setHost] = useState('https://anticket.lengliwh.com')
  const [locustfile, setLocustfile] = useState('')
  const [mode, setMode] = useState('mixed')
  const [users, setUsers] = useState(100)
  const [spawnRate, setSpawnRate] = useState(10)
  const [spawnPeriod, setSpawnPeriod] = useState(1)  // seconds; effective rate = spawnRate / spawnPeriod
  const [duration, setDuration] = useState('60s')

  const loadPerfHistory = async (selectLatest = false) => {
    const history = await fetchPerfRuns(projectKey, 50)
    const runs = history?.runs || []
    setPerfRuns(runs)
    if (selectLatest && runs.length) {
      const detail = await fetchPerfRunDetail(runs[0].id, projectKey)
      if (!detail?.error) {
        setSelectedRunDetail(detail)
      }
    }
    return runs
  }

  const handleViewHistoryRun = async (runId) => {
    setHistoryLoading(true)
    try {
      const detail = await fetchPerfRunDetail(runId, projectKey)
      if (!detail?.error) {
        setSelectedRunDetail(detail)
      }
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    setRunError('')
    setLocustfiles([])
    setLocustfileModes({})
    setLocustfile('')
    setSelectedRunDetail(null)
    Promise.all([
      fetchServiceStatus(projectKey),
      fetchPerfStatus(projectKey),
      fetchPerfReport(projectKey),
      fetchPerfMetrics(projectKey),
      fetchGrafanaPanels(projectKey),
      fetchPerfLocustFiles(projectKey),
      fetchPerfRuns(projectKey, 50),
    ]).then(async ([s, status, r, m, g, lf, history]) => {
      setServices(s)
      setRunStatus(status)
      setReport(r)
      setMetrics(m)
      setGrafana(g)
      const availableLocustFiles = lf?.files || []
      setLocustfiles(availableLocustFiles)
      setLocustfileModes(lf?.modes || {})
      setLocustfile((current) => (availableLocustFiles.includes(current) ? current : (availableLocustFiles[0] || '')))
      const runs = history?.runs || []
      setPerfRuns(runs)
      if (runs.length) {
        const detail = await fetchPerfRunDetail(runs[0].id, projectKey)
        if (!detail?.error) {
          setSelectedRunDetail(detail)
        }
      } else {
        setSelectedRunDetail(null)
      }
      setTestRunning(status?.status === 'running')
    }).finally(() => setLoading(false))
  }, [projectKey])

  useEffect(() => {
    if (!locustfile) return
    const allowedModes = allowedModesForLocustFile(locustfile, locustfileModes)
    if (!allowedModes.includes(mode)) {
      setMode(allowedModes[0] || 'mixed')
    }
  }, [locustfile, locustfileModes, mode])

  useEffect(() => {
    if (!testRunning) return undefined

    const timer = setInterval(async () => {
      const [status, liveMetrics, latestReport] = await Promise.all([
        fetchPerfStatus(projectKey),
        fetchPerfMetrics(projectKey),
        fetchPerfReport(projectKey),
      ])

      setRunStatus(status)
      setMetrics(liveMetrics)
      setReport(latestReport)

      if (status?.status !== 'running') {
        setTestRunning(false)
        loadPerfHistory(true).catch(() => {})
      }
    }, 3000)

    return () => clearInterval(timer)
  }, [testRunning, projectKey])

  const handleStartTest = async () => {
    setRunError('')
    if (!locustfile || locustfiles.length === 0) {
      setRunError(`No Locust performance script is configured for ${projectName}. Add a .py file under ${projectKey}/02-automation/02-tests/performance.`)
      setTestRunning(false)
      return
    }
    setTestRunning(true)
    const effectiveRate = spawnRate / spawnPeriod
    const selectedMode = allowedModesForLocustFile(locustfile, locustfileModes).includes(mode)
      ? mode
      : allowedModesForLocustFile(locustfile, locustfileModes)[0]
    const result = await startPerfTest({ project: projectKey, host, locustfile, mode: selectedMode, users, spawn_rate: effectiveRate, duration })
    if (result.error) {
      setRunError(result.error)
      setTestRunning(false)
      return
    }
    // Poll for completion (simplified — real impl would use WebSocket)
    const status = await fetchPerfStatus(projectKey)
    setRunStatus(status)
    loadPerfHistory(true).catch(() => {})
  }

  const handleStopTest = async () => {
    setRunError('')
    // UX: disable the Stop button immediately so the user sees the click
    // landed (otherwise they wait for the 3s status poller and think nothing
    // happened). The actual subprocess kill is async on the backend.
    setTestRunning(false)
    const result = await stopPerfTest()
    if (result.error) {
      setRunError(result.error)
      // backend rejected the stop — re-enable the button
      setTestRunning(true)
      return
    }
    // Force a fresh status fetch ~1s later (don't wait for the 3s poller).
    setTimeout(async () => {
      const status = await fetchPerfStatus(projectKey)
      setRunStatus(status)
      setTestRunning(status?.status === 'running')
      loadPerfHistory(true).catch(() => {})
    }, 1000)
  }

  const handleRefresh = async () => {
    setLoading(true)
    setRunError('')
    const [s, status, r, m, g, lf, history] = await Promise.all([
      fetchServiceStatus(projectKey), fetchPerfStatus(projectKey), fetchPerfReport(projectKey), fetchPerfMetrics(projectKey), fetchGrafanaPanels(projectKey),
      fetchPerfLocustFiles(projectKey),
      fetchPerfRuns(projectKey, 50),
    ])
    setServices(s)
    setRunStatus(status)
    setReport(r)
    setMetrics(m)
    setGrafana(g)
    const availableLocustFiles = lf?.files || []
    setLocustfiles(availableLocustFiles)
    setLocustfileModes(lf?.modes || {})
    setLocustfile((current) => (availableLocustFiles.includes(current) ? current : (availableLocustFiles[0] || '')))
    const runs = history?.runs || []
    setPerfRuns(runs)
    if (runs.length && !selectedRunDetail) {
      const detail = await fetchPerfRunDetail(runs[0].id, projectKey)
      if (!detail?.error) setSelectedRunDetail(detail)
    } else if (!runs.length) {
      setSelectedRunDetail(null)
    }
    setTestRunning(status?.status === 'running')
    setLoading(false)
  }

  const handleLocustFileChange = (file) => {
    const allowedModes = allowedModesForLocustFile(file, locustfileModes)
    setLocustfile(file)
    if (!allowedModes.includes(mode)) {
      setMode(allowedModes[0] || 'mixed')
    }
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>
  }

  const summary = report?.summary || {}
  const endpoints = report?.endpoints || []
  const reportTs = report?.timeseries || {}
  const liveTs = metrics || {}
  const ts = testRunning ? {
    rps: liveTs.rps || reportTs.rps || [],
    response_time: liveTs.response_time || reportTs.response_time || [],
    error_rate: liveTs.error_rate || reportTs.error_rate || [],
    users: liveTs.users || reportTs.users || [],
  } : reportTs
  const hasLocustFiles = locustfiles.length > 0
  const availableModeValues = hasLocustFiles ? allowedModesForLocustFile(locustfile, locustfileModes) : []
  const selectedMode = availableModeValues.includes(mode) ? mode : (availableModeValues[0] || 'mixed')
  const selectedModeOptions = PERFORMANCE_MODE_OPTIONS.filter((option) => availableModeValues.includes(option.value))
  const isRunTargetLocked = selectedModeOptions.length <= 1
  const isStandaloneCreateOrder = normalizeLocustFile(locustfile).endsWith('/business_create_order.py')
  const isLinkedTicket = normalizeLocustFile(locustfile).endsWith('/linked_ticket.py')
  const currentSummary = testRunning ? {
    ...summary,
    rps: ts.rps?.[ts.rps.length - 1]?.value ?? summary.rps,
    avg_response_time: ts.response_time?.[ts.response_time.length - 1]?.value ?? summary.avg_response_time,
    error_rate: ts.error_rate?.[ts.error_rate.length - 1]?.value ?? summary.error_rate,
    virtual_users: ts.users?.[ts.users.length - 1]?.value ?? summary.virtual_users,
  } : summary

  const endpointColumns = [
    {
      title: 'Method',
      dataIndex: 'method',
      width: 80,
      render: (m) => <Tag color={m === 'GET' ? 'green' : 'blue'}>{m}</Tag>,
    },
    { title: 'Endpoint', dataIndex: 'endpoint', render: (v) => <Text code style={{ fontSize: 12 }}>{v}</Text> },
    { title: 'Requests', dataIndex: 'requests', width: 90, render: (v) => v?.toLocaleString() },
    {
      title: 'Avg (ms)',
      dataIndex: 'avg_response_time',
      width: 90,
      render: (v) => <Text style={{ color: v > 500 ? '#ff4d4f' : v > 200 ? '#faad14' : '#52c41a', fontWeight: 500 }}>{v}</Text>,
      sorter: (a, b) => a.avg_response_time - b.avg_response_time,
    },
    {
      title: 'P95 (ms)',
      dataIndex: 'p95',
      width: 90,
      render: (v) => <Text style={{ color: v > 1000 ? '#ff4d4f' : v > 500 ? '#faad14' : '#52c41a', fontWeight: 500 }}>{v}</Text>,
    },
    {
      title: 'P99 (ms)',
      dataIndex: 'p99',
      width: 90,
      render: (v) => <Text style={{ color: v > 2000 ? '#ff4d4f' : v > 1000 ? '#faad14' : '#52c41a', fontWeight: 500 }}>{v}</Text>,
    },
    { title: 'RPS', dataIndex: 'rps', width: 70 },
    {
      title: 'Error %',
      dataIndex: 'error_rate',
      width: 90,
      render: (v) => (
        <Tag color={v > 5 ? 'red' : v > 1 ? 'orange' : 'green'} style={{ borderRadius: 4 }}>
          {v}%
        </Tag>
      ),
    },
  ]

  const perfRunColumns = [
    {
      title: 'Run',
      dataIndex: 'id',
      width: 80,
      render: (id) => <Text strong>#{id}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 95,
      render: (status) => {
        const color = status === 'passed' ? 'green' : status === 'failed' ? 'red' : status === 'running' ? 'blue' : 'default'
        return <Tag color={color}>{String(status || '').toUpperCase()}</Tag>
      },
    },
    {
      title: 'Script',
      dataIndex: 'locustfile',
      width: 220,
      render: (file) => (
        <Tooltip title={file || '-'}>
          <Text code style={{ fontSize: 12 }}>{locustFileName(file)}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Target',
      key: 'target',
      width: 190,
      render: (_, r) => (
        <Space size={4} wrap>
          <Tag color="geekblue">{modeLabel(r.mode)}</Tag>
          <Tag>{r.users || 0} users</Tag>
          <Tag>{r.spawn_rate || 0}/s</Tag>
          <Tag>{r.duration || '-'}</Tag>
        </Space>
      ),
    },
    {
      title: 'Requests',
      dataIndex: 'total_requests',
      width: 105,
      render: (v) => (v || 0).toLocaleString(),
    },
    {
      title: 'Failures',
      dataIndex: 'total_failures',
      width: 105,
      render: (v) => <Text type={(v || 0) > 0 ? 'danger' : undefined}>{(v || 0).toLocaleString()}</Text>,
    },
    {
      title: 'Error %',
      dataIndex: 'error_rate',
      width: 90,
      render: (v) => <Tag color={(v || 0) > 5 ? 'red' : (v || 0) > 0 ? 'orange' : 'green'}>{v || 0}%</Tag>,
    },
    {
      title: 'Avg / RPS',
      key: 'perf',
      width: 125,
      render: (_, r) => <Text>{r.avg_response_time || 0} ms / {r.rps || 0}</Text>,
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      width: 190,
      render: formatDateTime,
    },
    {
      title: '',
      key: 'action',
      width: 90,
      render: (_, r) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewHistoryRun(r.id)}
        >
          View
        </Button>
      ),
    },
  ]

  const grafanaPanels = grafana?.panels || []
  const grafanaDashUrl = grafana?.dashboard_url || ''
  const selectedHistoryEndpoints = selectedRunDetail?.endpoints || []
  const selectedHistorySummary = selectedRunDetail?.summary || {}
  const historyCard = (
    <Card
      title={<><HistoryOutlined /> Run History</>}
      size="small"
      style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
    >
      <Table
        rowKey="id"
        dataSource={perfRuns}
        columns={perfRunColumns}
        size="small"
        loading={historyLoading}
        pagination={{ pageSize: 8, showSizeChanger: false }}
        onRow={(record) => ({ onClick: () => handleViewHistoryRun(record.id) })}
      />
      {selectedRunDetail && (
        <>
          <Divider />
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col xs={12} md={6}>
              <Statistic title={`Run #${selectedRunDetail.id} Requests`} value={(selectedHistorySummary.total_requests || 0).toLocaleString()} />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Failures" value={(selectedHistorySummary.total_failures || 0).toLocaleString()} valueStyle={{ color: (selectedHistorySummary.total_failures || 0) > 0 ? '#ff4d4f' : '#52c41a' }} />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Avg Response" value={selectedHistorySummary.avg_response_time || 0} suffix="ms" />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="RPS" value={selectedHistorySummary.rps || 0} />
            </Col>
          </Row>
          <Table
            dataSource={selectedHistoryEndpoints.map((e, i) => ({ ...e, key: i }))}
            columns={endpointColumns}
            size="small"
            pagination={false}
          />
        </>
      )}
    </Card>
  )

  return (
    <div style={{ maxWidth: 1400 }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
            Performance Test
            <Tag style={{ marginLeft: 8 }}>{projectName}</Tag>
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Load testing with Locust + metrics from Prometheus + Grafana
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>Refresh</Button>
        </Space>
      </div>

      {/* Service Status Bar */}
      {services && (
        <div style={{ marginBottom: 20 }}>
          <Space wrap size={8}>
            <ServiceBadge
              name="Prometheus"
              connected={services.prometheus?.connected}
              url={services.prometheus?.url}
              icon={<BarChartOutlined style={{ color: '#e6522c' }} />}
            />
            <ServiceBadge
              name="Grafana"
              connected={services.grafana?.connected}
              url={services.grafana?.url}
              icon={<LineChartOutlined style={{ color: '#f46800' }} />}
            />
            {!services.prometheus?.connected && !services.grafana?.connected && (
              <Alert
                type="info"
                message="Services not connected - showing demo data. Configure via environment variables."
                showIcon
                style={{ borderRadius: 6 }}
              />
            )}
          </Space>
        </div>
      )}

      {(runError || runStatus?.error) && (
        <Alert
          type="error"
          message="Performance test error"
          description={runError || runStatus?.error}
          showIcon
          style={{ marginBottom: 20, borderRadius: 8 }}
        />
      )}

      {runStatus && (() => {
        const hasErrors = runStatus.status === 'completed' && (runStatus.total_failures || 0) > 0
        const alertType = runStatus.status === 'running' ? 'info'
          : runStatus.status === 'completed' ? (hasErrors ? 'warning' : 'success')
          : runStatus.status === 'stopped' ? 'warning'
          : (runStatus.status === 'failed' || runStatus.status === 'error') ? 'error'
          : 'info'
        const msg = hasErrors
          ? `Run completed with ${runStatus.total_failures.toLocaleString()} failed requests (${runStatus.error_rate}% error rate)`
          : `Run status: ${runStatus.status}`
        return (
          <Alert
            type={alertType}
            message={msg}
            description={
              runStatus.config
                ? `${modeLabel(runStatus.config.mode)} target, ${runStatus.config.users} users, ${runStatus.config.spawn_rate}/s effective, ${runStatus.config.duration}, host ${runStatus.config.host}, locust file ${runStatus.config.locustfile || 'not selected'}`
                : 'No performance run started yet.'
            }
            showIcon
            style={{ marginBottom: 20, borderRadius: 8 }}
          />
        )
      })()}

      {!hasLocustFiles && (
        <Alert
          type="warning"
          message="No Locust performance script configured for this project"
          description={`Add a .py entry file under ${projectKey}/02-automation/02-tests/performance, then click Refresh.`}
          showIcon
          style={{ marginBottom: 20, borderRadius: 8 }}
        />
      )}

      <Tabs
        defaultActiveKey="run"
        items={[
          {
            key: 'overview',
            label: <><DashboardOutlined /> Overview</>,
            children: (
              <>
                {/* KPI Cards */}
                <Row gutter={16} style={{ marginBottom: 24 }}>
                  <Col xs={12} sm={6}>
                    <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <Statistic
                        title="Total Requests"
                        value={summary.total_requests?.toLocaleString() || '—'}
                        prefix={<ThunderboltOutlined style={{ color: '#1677ff' }} />}
                      />
                    </Card>
                  </Col>
                  <Col xs={12} sm={6}>
                    <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <Statistic
                        title="Avg Response Time"
                        value={summary.avg_response_time || '—'}
                        suffix="ms"
                        valueStyle={{ color: (summary.avg_response_time || 0) > 500 ? '#ff4d4f' : '#52c41a' }}
                        prefix={<ClockCircleOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col xs={12} sm={6}>
                    <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <Statistic
                        title="Throughput"
                        value={summary.rps || '—'}
                        suffix="req/s"
                        prefix={<TeamOutlined style={{ color: '#722ed1' }} />}
                      />
                    </Card>
                  </Col>
                  <Col xs={12} sm={6}>
                    <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <Statistic
                        title="Error Rate"
                        value={summary.error_rate ?? '—'}
                        suffix="%"
                        valueStyle={{ color: (summary.error_rate || 0) > 5 ? '#ff4d4f' : '#52c41a' }}
                        prefix={<WarningOutlined />}
                      />
                    </Card>
                  </Col>
                </Row>

                {/* Real-time Charts */}
                <Row gutter={16} style={{ marginBottom: 24 }}>
                  <Col xs={24} lg={12}>
                    <Card size="small" title="Response Time" style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <TimeSeriesChart data={ts.response_time} color="#1677ff" label="Avg Response Time" unit="ms" />
                    </Card>
                  </Col>
                  <Col xs={24} lg={12}>
                    <Card size="small" title="Throughput (RPS)" style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <TimeSeriesChart data={ts.rps} color="#52c41a" label="Requests / Second" unit="" />
                    </Card>
                  </Col>
                </Row>
                <Row gutter={16} style={{ marginBottom: 24 }}>
                  <Col xs={24} lg={12}>
                    <Card size="small" title="Error Rate" style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <TimeSeriesChart data={ts.error_rate} color="#ff4d4f" label="Error %" unit="%" />
                    </Card>
                  </Col>
                  <Col xs={24} lg={12}>
                    <Card size="small" title="Virtual Users" style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <TimeSeriesChart data={ts.users} color="#722ed1" label="Active Users" unit="" />
                    </Card>
                  </Col>
                </Row>

                {/* Endpoint Details */}
                <Card
                  title={<><ApiOutlined /> Endpoint Performance</>}
                  size="small"
                  style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
                >
                  <Table
                    dataSource={endpoints.map((e, i) => ({ ...e, key: i }))}
                    columns={endpointColumns}
                    size="small"
                    pagination={false}
                  />
                </Card>
              </>
            ),
          },
          {
            key: 'run',
            label: <><PlayCircleOutlined /> Run Test</>,
            children: (
              <>
                <Card
                  title={<><SettingOutlined /> Load Test Configuration</>}
                  style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
                >
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Locust File</Text>
                    <Select
                      value={locustfile}
                      onChange={handleLocustFileChange}
                      showSearch
                      disabled={!hasLocustFiles}
                      placeholder="No Locust file available"
                      style={{ width: '100%' }}
                      options={locustfiles.map((file) => ({ value: file, label: file }))}
                    />
                  </Col>
                  <Col span={7}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Target Host</Text>
                    <Input
                      value={host}
                      onChange={(e) => setHost(e.target.value)}
                      placeholder="https://anticket.lengliwh.com"
                      prefix={<LinkOutlined />}
                    />
                  </Col>
                  <Col span={4}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Run Target</Text>
                    <Select
                      value={selectedMode}
                      onChange={setMode}
                      disabled={!hasLocustFiles || isRunTargetLocked}
                      style={{ width: '100%' }}
                      options={selectedModeOptions}
                    />
                  </Col>
                  <Col span={2}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Virtual Users</Text>
                    <InputNumber value={users} onChange={setUsers} min={1} max={10000} style={{ width: '100%' }} />
                  </Col>
                  <Col span={3}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Duration</Text>
                    <Input value={duration} onChange={(e) => setDuration(e.target.value)} placeholder="60s" />
                  </Col>
                </Row>

                <Divider />

                <Row gutter={16}>
                  <Col span={8}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                      Spawn Rate <Text type="secondary" style={{ fontSize: 11 }}>(users per period)</Text>
                    </Text>
                    <Space.Compact style={{ width: '100%' }}>
                      <InputNumber
                        value={spawnRate}
                        onChange={setSpawnRate}
                        min={0.1}
                        max={1000}
                        step={0.01}
                        style={{ width: '60%' }}
                      />
                      <Select
                        value={spawnPeriod}
                        onChange={setSpawnPeriod}
                        style={{ width: '40%' }}
                        options={[
                          { value: 1, label: '/ 1s' },
                          { value: 2, label: '/ 2s' },
                          { value: 5, label: '/ 5s' },
                          { value: 10, label: '/ 10s' },
                        ]}
                      />
                    </Space.Compact>
                  </Col>
                  <Col span={16}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Test Scenarios</Text>
                    <div style={{ padding: '8px 12px', background: '#fafafa', borderRadius: 6, fontSize: 12 }}>
                      {!hasLocustFiles && (
                        <Tag color="red">No Locust file configured</Tag>
                      )}
                      {hasLocustFiles && isRunTargetLocked && (
                        <Tag color="gold">Run target locked by selected file</Tag>
                      )}
                      {hasLocustFiles && isLinkedTicket && (<>
                        <Tag color="green">Get Cart Number</Tag>
                        <Tag color="green">Add Show Item</Tag>
                        <Tag color="green">Add Seat Item</Tag>
                        <Tag color="purple">Cancel linked tickets</Tag>
                        <Tag color="default">CSV recycle</Tag>
                      </>)}
                      {hasLocustFiles && !isLinkedTicket && selectedMode === 'login' && (<>
                        <Tag color="blue">SSO getCaptchaId</Tag>
                        <Tag color="blue">SSO captcha image</Tag>
                        <Tag color="blue">SSO doubleCheck</Tag>
                        <Tag color="blue">SSO login</Tag>
                      </>)}
                      {hasLocustFiles && !isLinkedTicket && selectedMode === 'business' && (<>
                        <Tag color="green">GET /mainframe/index.html</Tag>
                        <Tag color="green">GET /menpiao/index.html</Tag>
                        <Tag color="default">Business mix</Tag>
                      </>)}
                      {hasLocustFiles && !isLinkedTicket && selectedMode === 'order_create' && isStandaloneCreateOrder && (<>
                        <Tag color="green">POST /show/order/create target</Tag>
                        <Tag color="blue">SETUP session bootstrap</Tag>
                        <Tag color="default">No setup rows in stats</Tag>
                      </>)}
                      {hasLocustFiles && !isLinkedTicket && selectedMode === 'order_create' && !isStandaloneCreateOrder && (<>
                        <Tag color="green">POST /show/order/create</Tag>
                        <Tag color="default">SETUP ticket context</Tag>
                        <Tag color="purple">CLEANUP cancel order</Tag>
                      </>)}
                      {hasLocustFiles && !isLinkedTicket && selectedMode === 'order_cancel' && (<>
                        <Tag color="purple">GET /show/order/cancelOrder</Tag>
                        <Tag color="default">SETUP create order</Tag>
                        <Tag color="default">SETUP ticket context</Tag>
                      </>)}
                      {hasLocustFiles && !isLinkedTicket && selectedMode === 'mixed' && (<>
                        <Tag color="green">Business pages</Tag>
                        <Tag color="blue">Startup SSO</Tag>
                        <Tag color="blue">SSO probe</Tag>
                        <Tag color="purple">Program write if logged in</Tag>
                      </>)}
                    </div>
                  </Col>
                </Row>

                <div style={{ marginTop: 24 }}>
                  <Space>
                    <Button
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      size="large"
                      loading={testRunning}
                      disabled={testRunning || !hasLocustFiles}
                      onClick={handleStartTest}
                      style={{ borderRadius: 8 }}
                    >
                      {testRunning ? 'Running...' : 'Start Load Test'}
                    </Button>
                    <Button
                      danger
                      icon={<StopOutlined />}
                      size="large"
                      disabled={!testRunning}
                      onClick={handleStopTest}
                      style={{ borderRadius: 8 }}
                    >
                      Stop
                    </Button>
                  </Space>
                  <Text type="secondary" style={{ marginLeft: 16, fontSize: 12 }}>
                    {hasLocustFiles
                      ? `${modeLabel(selectedMode)} target, ${users} users, ramp up ${spawnRate} ${spawnPeriod === 1 ? 'per second' : `every ${spawnPeriod}s`} (${(spawnRate / spawnPeriod).toFixed(2)}/s effective), run for ${duration}, locust file ${locustfile}`
                      : `No runnable Locust script for ${projectName}`}
                  </Text>
                </div>

                {testRunning && (
                  <Alert
                    style={{ marginTop: 16, borderRadius: 8 }}
                    type="info"
                    showIcon
                    message="Load test is running..."
                    description="Locust is executing the performance test. The dashboard is polling live metrics and will switch to the parsed report when the run finishes."
                  />
                )}

                <Divider />

                <Title level={5}>Architecture</Title>
                {(() => {
                  const boxStyle = {
                    border: '1px solid #4a4a6a',
                    borderRadius: 6,
                    padding: '10px 8px',
                    background: '#252540',
                    color: '#d4d4d4',
                    textAlign: 'center',
                    fontSize: 13,
                    minHeight: 56,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                  }
                  const arrowRow = {
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    textAlign: 'center',
                    color: '#7a7a9a',
                    fontSize: 16,
                    lineHeight: '20px',
                  }
                  const sublabel = { fontSize: 11, color: '#9b9bb4' }
                  return (
                    <div style={{ padding: 16, background: '#1a1a2e', borderRadius: 8 }}>
                      <div style={{
                        border: '1px dashed #4a4a6a',
                        borderRadius: 8,
                        padding: 12,
                      }}>
                        <Text style={{ color: '#9b9bb4', fontSize: 12, display: 'block', marginBottom: 10 }}>
                          QA Dashboard — Performance Test Page
                        </Text>
                        <Row gutter={12}>
                          <Col span={8}><div style={boxStyle}>Config &amp; Run Control</div></Col>
                          <Col span={8}><div style={boxStyle}>Charts &amp; Metrics</div></Col>
                          <Col span={8}><div style={boxStyle}>Grafana Panels<div style={sublabel}>(iframe embed)</div></div></Col>
                        </Row>
                      </div>

                      <div style={arrowRow}><span>▼</span><span>▼</span><span>▼</span></div>

                      <div style={{
                        textAlign: 'center',
                        color: '#9b9bb4',
                        fontSize: 12,
                        padding: '6px 0',
                        border: '1px dashed #4a4a6a',
                        borderRadius: 6,
                        background: '#1f1f38',
                      }}>
                        FastAPI Backend
                      </div>

                      <div style={arrowRow}><span>▼</span><span>▼</span><span>▼</span></div>

                      <Row gutter={12} align="middle">
                        <Col span={7}>
                          <div style={boxStyle}>
                            <strong>Locust</strong>
                            <div style={sublabel}>(Python) · port 9646</div>
                          </div>
                        </Col>
                        <Col span={1} style={{ textAlign: 'center', color: '#7a7a9a', fontSize: 16 }}>▶</Col>
                        <Col span={7}>
                          <div style={boxStyle}>
                            <strong>Prometheus</strong>
                            <div style={sublabel}>:9090</div>
                          </div>
                        </Col>
                        <Col span={1} style={{ textAlign: 'center', color: '#7a7a9a', fontSize: 16 }}>◀</Col>
                        <Col span={8}>
                          <div style={boxStyle}>
                            <strong>Grafana</strong>
                            <div style={sublabel}>:3000</div>
                          </div>
                        </Col>
                      </Row>
                    </div>
                  )
                })()}
                </Card>
                {historyCard}
              </>
            ),
          },
          {
            key: 'history',
            label: <><HistoryOutlined /> Run History</>,
            children: historyCard,
          },
          {
            key: 'grafana',
            label: <><LineChartOutlined /> Grafana</>,
            children: (
              <Card
                title="Grafana Dashboard"
                extra={
                  grafanaDashUrl ? (
                    <a href={grafanaDashUrl} target="_blank" rel="noreferrer">
                      <Button size="small" icon={<LinkOutlined />}>Open in Grafana</Button>
                    </a>
                  ) : null
                }
                style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
              >
                {services?.grafana?.connected ? (
                  <div>
                    {grafanaDashUrl ? (
                      <iframe
                        src={grafanaDashUrl}
                        width="100%"
                        height="600"
                        frameBorder="0"
                        style={{ borderRadius: 8, border: '1px solid #f0f0f0' }}
                      />
                    ) : (
                      <Alert
                        type="warning"
                        message="Set GRAFANA_DASHBOARD_UID environment variable to embed a dashboard"
                        showIcon
                      />
                    )}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: 60 }}>
                    <LineChartOutlined style={{ fontSize: 48, color: '#f46800', marginBottom: 16 }} />
                    <Title level={5}>Grafana Not Connected</Title>
                    <Paragraph type="secondary">
                      Start Grafana on <Text code>localhost:3000</Text> and configure:
                    </Paragraph>
                    <div style={{ textAlign: 'left', maxWidth: 500, margin: '0 auto' }}>
                      <pre style={{
                        background: '#1a1a2e', color: '#d4d4d4', padding: 16, borderRadius: 8,
                        fontSize: 12, lineHeight: 1.8,
                      }}>
{`# Environment variables for FastAPI:
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=your-service-account-token
GRAFANA_DASHBOARD_UID=your-dashboard-uid

# Grafana config (grafana.ini):
[security]
allow_embedding = true
cookie_samesite = none

# Prometheus data source in Grafana:
# URL: http://localhost:9090`}
                      </pre>
                    </div>
                  </div>
                )}
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}
