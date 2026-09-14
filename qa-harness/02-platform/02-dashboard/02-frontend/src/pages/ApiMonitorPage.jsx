import { useEffect, useState, useCallback } from 'react'
import {
  Typography, Card, Row, Col, Table, Tag, Badge, Statistic, Space,
  Button, Empty, Divider, Alert, Tooltip, Radio, Segmented,
} from 'antd'
import {
  ApiOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  GlobalOutlined,
  MinusCircleOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { ExperimentOutlined, WarningOutlined } from '@ant-design/icons'
import {
  ResponsiveContainer, ComposedChart, LineChart, Line, Area, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip, Legend,
} from 'recharts'
import {
  fetchApiMonitorEndpoints, fetchApiMonitorLayers, fetchApiMonitorTrends,
  fetchApiMonitorSmokeRun, startApiMonitorSmokeRun,
} from '../api'

const { Title, Text, Paragraph } = Typography

const STATUS_MAP = {
  up:       { status: 'success', text: 'UP' },
  degraded: { status: 'warning', text: 'SLOW' },
  down:     { status: 'error',   text: 'DOWN' },
  skipped:  { status: 'default', text: 'SKIP' },
}

const columns = [
  {
    title: 'Status',
    dataIndex: 'status',
    width: 80,
    render: (s) => {
      const badge = STATUS_MAP[s] || { status: 'default', text: s || '—' }
      return <Badge status={badge.status} text={<Text strong style={{ fontSize: 12 }}>{badge.text}</Text>} />
    },
  },
  { title: 'Name', dataIndex: 'name', render: (v) => <Text code style={{ fontSize: 12 }}>{v}</Text> },
  {
    title: 'Endpoint',
    key: 'endpoint',
    render: (_, r) => (
      <Space size={4}>
        <Tag color={r.method === 'GET' ? 'green' : 'blue'} style={{ fontSize: 10 }}>{r.method}</Tag>
        <Text code style={{ fontSize: 12 }}>{r.path}</Text>
        {r.auth_required && <Tag color="gold" style={{ fontSize: 10 }}>AUTH</Tag>}
      </Space>
    ),
  },
  {
    title: 'Code',
    dataIndex: 'actual_status_code',
    width: 70,
    render: (v) => v == null ? <Text type="secondary">—</Text> : <Text>{v}</Text>,
  },
  {
    title: 'Latency',
    dataIndex: 'latency_ms',
    width: 100,
    render: (v) => v == null ? <Text type="secondary">—</Text> : (
      <Text style={{ color: v > 1000 ? '#ff4d4f' : v > 500 ? '#faad14' : '#52c41a', fontWeight: 500 }}>
        {Math.round(v)}ms
      </Text>
    ),
  },
  {
    title: 'Group',
    dataIndex: 'group',
    width: 100,
    render: (v) => v ? <Tag>{v}</Tag> : null,
  },
  {
    title: 'Notes',
    dataIndex: 'notes',
    ellipsis: true,
    render: (v, r) => (
      <Space size={4}>
        {r.body_warning && (
          <Tooltip title={`Body warning: ${r.body_warning}`}>
            <WarningOutlined style={{ color: '#faad14' }} />
          </Tooltip>
        )}
        {v && <Tooltip title={v}><Text type="secondary" style={{ fontSize: 12 }}>{v}</Text></Tooltip>}
      </Space>
    ),
  },
]

const LAYER_DESCRIPTIONS = {
  api_smoke: 'Pure single-API monitoring: status code and latency checks, runs fast on a schedule.',
  api_contract: 'Pure API contract checks: response shape and schema validation.',
  api_functional: 'Pure API functional checks: multi-step API journeys and cross-response assertions.',
  ui_smoke: 'UI smoke and UI state-flow checks for user-facing guards and no-save behavior.',
  api_ui_mixed: 'API + UI mixed checks: API chain first, final state asserted on the UI.',
  smoke:     'Monitoring — is the endpoint up? status code + latency, runs fast on a schedule.',
}

const LAYER_LABELS = {
  api_smoke: 'API Smoke',
  api_contract: 'API Contract',
  api_functional: 'API Functional',
  ui_smoke: 'UI Smoke',
  api_ui_mixed: 'API + UI Mixed',
  smoke: 'Smoke',
}

// Trend window options: label shown, hours sent to backend
const TREND_WINDOWS = [
  { label: '24h',  hours: 24 },
  { label: '7d',   hours: 168 },
  { label: '30d',  hours: 720 },
]

function formatTrendTick(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  // Short label: "05-29 12:51"
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

function mergeTrendSeries(summary, latency) {
  // Two backend series share ran_at; zip them by index (both sorted asc same way).
  const out = []
  const n = Math.max(summary?.length || 0, latency?.length || 0)
  for (let i = 0; i < n; i += 1) {
    const s = summary?.[i] || {}
    const l = latency?.[i] || {}
    out.push({
      ran_at: s.ran_at || l.ran_at,
      tick: formatTrendTick(s.ran_at || l.ran_at),
      up: s.up ?? 0,
      degraded: s.degraded ?? 0,
      down: s.down ?? 0,
      skipped: s.skipped ?? 0,
      avg_latency_ms: l.avg_latency_ms ?? null,
    })
  }
  return out
}

export default function ApiMonitorPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const projectRoot = activeProject?.root || `D:\\Workspace\\${projectKey}`
  const projectRootPath = projectRoot.replace(/\//g, '\\')
  const automationRoot = `${projectRootPath}\\02-automation`
  const endpointDataDir = `${automationRoot}\\02-tests\\api\\data`
  const smokeResultsPath = `${automationRoot}\\07-artifacts\\api_smoke\\latest.json`
  const smokeCommand = `cd ${automationRoot}
D:\\Workspace\\qa-harness\\02-platform\\01-automation\\.venv\\Scripts\\python.exe -m pytest 02-tests\\api\\api_smoke -v`
  const discoverCommand = `cd ${automationRoot}
python 04-tools\\discover_api_endpoints.py --probe --update`
  const [data, setData] = useState(null)
  const [layers, setLayers] = useState(null)
  const [trends, setTrends] = useState(null)
  const [trendHours, setTrendHours] = useState(168)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [smokeRun, setSmokeRun] = useState(null)
  const [smokeRunError, setSmokeRunError] = useState(null)

  const load = useCallback(async (hours = trendHours) => {
    setLoading(true)
    setError(null)
    try {
      const [payload, layerPayload, trendPayload] = await Promise.all([
        fetchApiMonitorEndpoints(projectKey),
        fetchApiMonitorLayers(projectKey),
        fetchApiMonitorTrends(hours, null, projectKey),
      ])
      setData(payload)
      setLayers(layerPayload)
      setTrends(trendPayload)
    } catch (exc) {
      setError(String(exc))
    } finally {
      setLoading(false)
    }
  }, [trendHours, projectKey])

  useEffect(() => { load(trendHours) }, [load, trendHours])

  useEffect(() => {
    let cancelled = false
    fetchApiMonitorSmokeRun(projectKey)
      .then((payload) => {
        if (!cancelled) setSmokeRun(payload)
      })
      .catch(() => {
        if (!cancelled) setSmokeRun(null)
      })
    return () => { cancelled = true }
  }, [projectKey])

  const smokeRunning = Boolean(smokeRun?.running || smokeRun?.status === 'running')

  useEffect(() => {
    if (!smokeRunning) return undefined
    let cancelled = false
    const poll = async () => {
      try {
        const payload = await fetchApiMonitorSmokeRun(projectKey)
        if (cancelled) return
        setSmokeRun(payload)
        if (!payload?.running) {
          await load(trendHours)
        }
      } catch (exc) {
        if (!cancelled) setSmokeRunError(String(exc))
      }
    }
    const id = window.setInterval(poll, 2000)
    poll()
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [smokeRunning, load, trendHours, projectKey])

  const handleRunApiSmoke = async () => {
    setSmokeRunError(null)
    try {
      const payload = await startApiMonitorSmokeRun('sit', projectKey)
      setSmokeRun(payload)
      if (!payload?.running) {
        await load(trendHours)
      }
    } catch (exc) {
      setSmokeRunError(String(exc))
    }
  }

  const trendPoints = trends ? mergeTrendSeries(trends.summary, trends.latency) : []
  const hasTrendData = trendPoints.length > 0

  const summary = data?.summary || { total: 0, up: 0, degraded: 0, down: 0, skipped: 0 }
  const endpoints = (data?.endpoints || []).map((e, i) => ({ key: `${e.name}-${i}`, ...e }))
  const hasData = endpoints.length > 0
  const note = data?._note
  const apiError = data?._error
  const ranAt = data?.ran_at ? new Date(data.ran_at).toLocaleString() : null
  const smokeLogTail = smokeRun?.log?.slice(-8) || []
  const showSmokeRunStatus = smokeRun && smokeRun.status && smokeRun.status !== 'idle'
  const smokeRunAlertType = smokeRunning ? 'info' : smokeRun?.exit_code === 0 ? 'success' : 'error'

  return (
    <div style={{ maxWidth: 1400 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
            API Monitor
            <Text type="secondary" style={{ fontSize: 13, marginLeft: 12 }}>· {projectName}</Text>
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            {data?.website_url || 'Smoke results for project public APIs'}
            {ranAt && <span style={{ marginLeft: 12 }}>last run: {ranAt}</span>}
          </Text>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleRunApiSmoke}
            loading={smokeRunning}
          >
            Run API Smoke
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => load(trendHours)} loading={loading}>Refresh</Button>
        </Space>
      </div>

      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} closable />}
      {apiError && <Alert type="error" message={apiError} style={{ marginBottom: 16 }} closable />}
      {smokeRunError && <Alert type="error" message={smokeRunError} style={{ marginBottom: 16 }} closable />}
      {showSmokeRunStatus && (
        <Alert
          type={smokeRunAlertType}
          showIcon
          message={
            smokeRunning
              ? 'API smoke is running'
              : `API smoke ${smokeRun.status}`
          }
          description={
            <div>
              <Text type="secondary">
                {smokeRun.started_at ? `started: ${new Date(smokeRun.started_at).toLocaleString()}` : ''}
                {smokeRun.finished_at ? ` | finished: ${new Date(smokeRun.finished_at).toLocaleString()}` : ''}
                {smokeRun.exit_code != null ? ` | exit: ${smokeRun.exit_code}` : ''}
              </Text>
              {smokeLogTail.length > 0 && (
                <pre style={{ background: '#f5f5f5', padding: 8, marginTop: 8, marginBottom: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
{smokeLogTail.join('\n')}
                </pre>
              )}
            </div>
          }
          style={{ marginBottom: 16 }}
        />
      )}
      {note && !hasData && (
        <Alert
          type="info"
          showIcon
          message="No smoke run on record yet"
          description={
            <>
              Run it once and the dashboard will pick up the result automatically:
              <pre style={{ background: '#f5f5f5', padding: 8, marginTop: 8, fontSize: 12 }}>
                {smokeCommand}
              </pre>
            </>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Summary cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="Monitored APIs"
              value={summary.total}
              prefix={<GlobalOutlined style={{ color: '#1677ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="Healthy"
              value={summary.up}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="Slow / Degraded"
              value={summary.degraded}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="Down"
              value={summary.down}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Trends — historical up/down/degraded + avg latency over time */}
      <Card
        title={
          <Space size={12}>
            <span><LineChartOutlined /> Trends</span>
            <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
              {trends ? `${trends.run_count} run${trends.run_count === 1 ? '' : 's'} in selected window` : 'loading…'}
            </Text>
          </Space>
        }
        extra={
          <Segmented
            size="small"
            options={TREND_WINDOWS.map(w => w.label)}
            value={TREND_WINDOWS.find(w => w.hours === trendHours)?.label || '7d'}
            onChange={(label) => {
              const next = TREND_WINDOWS.find(w => w.label === label)
              if (next) setTrendHours(next.hours)
            }}
          />
        }
        style={{ marginBottom: 24 }}
        styles={{ body: { paddingTop: 12, paddingBottom: 12 } }}
      >
        {!hasTrendData ? (
          <Empty
            description={
              trends?.run_count === 0
                ? `No runs in the selected window. Try a longer window, or run: pytest 02-tests/api/api_smoke -v`
                : 'No trend data yet'
            }
            style={{ padding: 24 }}
          />
        ) : trendPoints.length === 1 ? (
          <Alert
            type="info"
            showIcon
            message="Only 1 run in the selected window — a trend needs at least 2 points."
            description={`Latest run at ${trendPoints[0].tick}: ${trendPoints[0].up} up, ${trendPoints[0].down} down, avg ${trendPoints[0].avg_latency_ms ?? '—'} ms. Trend chart will appear once a second run is recorded.`}
            style={{ margin: 12 }}
          />
        ) : (
          <Row gutter={16}>
            <Col xs={24} md={14}>
              <Text type="secondary" style={{ fontSize: 12, paddingLeft: 12 }}>
                Endpoint status counts (stacked) — {trends.run_count} runs
              </Text>
              <ResponsiveContainer width="100%" height={220}>
                <ComposedChart data={trendPoints} margin={{ top: 16, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="tick" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <ReTooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="up"       stackId="s" fill="#52c41a" name="Up" />
                  <Bar dataKey="degraded" stackId="s" fill="#faad14" name="Slow" />
                  <Bar dataKey="down"     stackId="s" fill="#ff4d4f" name="Down" />
                  <Bar dataKey="skipped"  stackId="s" fill="#bfbfbf" name="Skipped" />
                </ComposedChart>
              </ResponsiveContainer>
            </Col>
            <Col xs={24} md={10}>
              <Text type="secondary" style={{ fontSize: 12, paddingLeft: 12 }}>
                Average latency across all monitored endpoints (ms)
              </Text>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trendPoints} margin={{ top: 16, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="tick" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} unit=" ms" />
                  <ReTooltip />
                  <Line
                    type="monotone"
                    dataKey="avg_latency_ms"
                    name="Avg latency"
                    stroke="#1677ff"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </Col>
          </Row>
        )}
      </Card>

      {/* Layer summary — pytest results per L0/L1/L2/L3 */}
      {layers && layers.layers && layers.layers.length > 0 && (
        <Card
          title={<><ExperimentOutlined /> Test Layers</>}
          style={{ marginBottom: 24 }}
          styles={{ body: { paddingTop: 12, paddingBottom: 12 } }}
        >
          <Row gutter={16}>
            {layers.layers.map((l) => {
              const ok = l.failed === 0
              const color = ok ? '#52c41a' : '#ff4d4f'
              return (
                <Col xs={24} sm={12} key={l.name}>
                  <Tooltip title={LAYER_DESCRIPTIONS[l.name] || l.name}>
                    <div style={{ padding: 12 }}>
                      <Text type="secondary" style={{ fontSize: 12, textTransform: 'uppercase' }}>
                        {LAYER_LABELS[l.name] || l.name}
                      </Text>
                      <div style={{ fontSize: 28, fontWeight: 600, color }}>
                        {l.passed}/{l.total}
                      </div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {l.failed > 0 ? `${l.failed} failed` : 'all pass'}
                        {l.skipped > 0 ? ` · ${l.skipped} skipped` : ''}
                      </Text>
                    </div>
                  </Tooltip>
                </Col>
              )
            })}
          </Row>
        </Card>
      )}

      {/* Endpoint table */}
      <Card title={<><ApiOutlined /> Endpoint Status</>} styles={{ body: { padding: hasData ? 0 : 24 } }}>
        {hasData ? (
          <Table
            dataSource={endpoints}
            columns={columns}
            size="small"
            pagination={{ pageSize: 25, hideOnSinglePage: true }}
            rowKey="key"
          />
        ) : (
          <Empty description="No endpoints to display" />
        )}
      </Card>

      <Divider />
      <Paragraph type="secondary" style={{ fontSize: 12 }}>
        Endpoint registry lives under <Text code>{endpointDataDir}</Text>.
        Smoke results JSON: <Text code>{smokeResultsPath}</Text>.
        To re-discover endpoints after a new website deploy:{' '}
        <Text code>{discoverCommand}</Text>.
      </Paragraph>
    </div>
  )
}
