import { useState, useEffect } from 'react'
import {
  Typography, Card, Row, Col, Tabs, Button, Space, Tag, Badge, Alert, Spin,
  Select, Slider, InputNumber, Table, Tooltip, Switch, Divider, Input,
} from 'antd'
import {
  FireOutlined, FileTextOutlined, ThunderboltOutlined, ReloadOutlined,
  CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, BugOutlined,
  ExperimentOutlined, ClockCircleOutlined, CloudServerOutlined, SearchOutlined,
} from '@ant-design/icons'
import { requestJson } from '../apiClient'

const { Title, Text, Paragraph } = Typography

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function fetchObsStatus(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : ''
  return requestJson(`/api/observability/status${qs}`)
}

async function fetchFlameGraph(query = 'process_cpu') {
  return requestJson(`/api/observability/flamegraph?query=${encodeURIComponent(query)}`)
}

async function fetchLogs(query = '{job="fastapi-app"}', limit = 100) {
  return requestJson(`/api/observability/logs?query=${encodeURIComponent(query)}&limit=${limit}`)
}

async function injectToxic(proxyName, toxicType, latency, jitter) {
  return requestJson(`/api/observability/toxiproxy/toxic?proxy_name=${proxyName}&toxic_type=${toxicType}&latency=${latency}&jitter=${jitter}`, { method: 'POST' })
}

async function resetToxics() {
  return requestJson('/api/observability/toxiproxy/reset', { method: 'POST' })
}

// ---------------------------------------------------------------------------
// Flame Graph SVG Component
// ---------------------------------------------------------------------------

const FLAME_COLORS = [
  '#ff6b35', '#ff8c42', '#ffa64d', '#ffbd59', '#ffd166',
  '#e85d04', '#f48c06', '#faa307', '#ffba08', '#dc2f02',
  '#d00000', '#e63946', '#f4845f', '#f7a072', '#f8961e',
]

function FlameGraph({ data }) {
  if (!data?.flamebearer) {
    return <Text type="secondary">No flame graph data available</Text>
  }

  const { names, levels, numTicks, maxSelf } = data.flamebearer
  const width = 900
  const rowHeight = 22
  const height = levels.length * rowHeight + 40
  const [tooltip, setTooltip] = useState(null)
  const [selectedFunc, setSelectedFunc] = useState(null)

  // Parse levels — each level is chunks of 4: [x_offset, total, self, name_index, ...]
  const bars = []
  levels.forEach((level, depth) => {
    for (let i = 0; i < level.length; i += 4) {
      const xOffset = level[i]
      const totalSamples = level[i + 1]
      const selfSamples = level[i + 2]
      const nameIdx = level[i + 3]

      if (totalSamples === 0) continue

      const x = (xOffset / numTicks) * width
      const w = Math.max(1, (totalSamples / numTicks) * width)
      const y = height - (depth + 1) * rowHeight - 20
      const name = names[nameIdx] || 'unknown'
      const pct = ((totalSamples / numTicks) * 100).toFixed(1)
      const selfPct = ((selfSamples / numTicks) * 100).toFixed(1)

      // Color based on self time intensity
      const intensity = maxSelf > 0 ? selfSamples / maxSelf : 0
      const colorIdx = Math.min(Math.floor(intensity * FLAME_COLORS.length), FLAME_COLORS.length - 1)
      const color = selfSamples > 0 ? FLAME_COLORS[colorIdx] : '#4a9eff'

      bars.push({
        x, y, w, depth, name, totalSamples, selfSamples, pct, selfPct, color,
        isHot: selfSamples > maxSelf * 0.3,
      })
    }
  })

  return (
    <div style={{ position: 'relative' }}>
      <svg
        width={width}
        height={height}
        style={{ display: 'block', fontFamily: 'monospace', cursor: 'pointer' }}
      >
        {bars.map((bar, i) => (
          <g
            key={i}
            onMouseEnter={() => setTooltip(bar)}
            onMouseLeave={() => setTooltip(null)}
            onClick={() => setSelectedFunc(bar.name === selectedFunc ? null : bar.name)}
          >
            <rect
              x={bar.x}
              y={bar.y}
              width={bar.w}
              height={rowHeight - 2}
              fill={selectedFunc === bar.name ? '#1677ff' : bar.color}
              rx={2}
              opacity={selectedFunc && selectedFunc !== bar.name ? 0.4 : 0.9}
              stroke={bar.isHot ? '#d00000' : 'rgba(255,255,255,0.3)'}
              strokeWidth={bar.isHot ? 1.5 : 0.5}
            />
            {bar.w > 60 && (
              <text
                x={bar.x + 4}
                y={bar.y + 14}
                fontSize={10}
                fill="#fff"
                style={{ pointerEvents: 'none' }}
              >
                {bar.name.length > bar.w / 6.5
                  ? bar.name.slice(0, Math.floor(bar.w / 6.5)) + '...'
                  : bar.name}
              </text>
            )}
          </g>
        ))}
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'absolute',
          top: 8,
          right: 8,
          background: 'rgba(0,0,0,0.88)',
          color: '#fff',
          padding: '10px 14px',
          borderRadius: 8,
          fontSize: 12,
          lineHeight: 1.8,
          maxWidth: 400,
          zIndex: 10,
          pointerEvents: 'none',
        }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4, wordBreak: 'break-all' }}>
            {tooltip.name}
          </div>
          <div>Total: <strong>{tooltip.totalSamples}</strong> samples ({tooltip.pct}%)</div>
          <div>Self: <strong>{tooltip.selfSamples}</strong> samples ({tooltip.selfPct}%)</div>
          {tooltip.isHot && (
            <div style={{ color: '#ff6b35', fontWeight: 700, marginTop: 4 }}>
              HOTSPOT — This function uses significant CPU
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div style={{ marginTop: 8, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <Text type="secondary" style={{ fontSize: 11 }}>Color = self CPU time:</Text>
        <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 12, height: 12, background: '#4a9eff', borderRadius: 2, display: 'inline-block' }} />
          No self time (calling others)
        </span>
        <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 12, height: 12, background: '#ffa64d', borderRadius: 2, display: 'inline-block' }} />
          Moderate
        </span>
        <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 12, height: 12, background: '#d00000', borderRadius: 2, display: 'inline-block' }} />
          Hot (bottleneck)
        </span>
        {selectedFunc && (
          <Tag color="blue" closable onClose={() => setSelectedFunc(null)}>
            Highlight: {selectedFunc}
          </Tag>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Log Viewer Component
// ---------------------------------------------------------------------------

const LEVEL_CONFIG = {
  error: { color: '#ff4d4f', bg: '#fff2f0', icon: <CloseCircleOutlined /> },
  warn:  { color: '#fa8c16', bg: '#fff7e6', icon: <WarningOutlined /> },
  info:  { color: '#1677ff', bg: '#f0f5ff', icon: <CheckCircleOutlined /> },
  debug: { color: '#8c8c8c', bg: '#fafafa', icon: <BugOutlined /> },
}

function LogViewer({ data }) {
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  if (!data?.data?.result) {
    return <Text type="secondary">No log data available</Text>
  }

  // Flatten all log entries
  const entries = []
  for (const stream of data.data.result) {
    const level = stream.stream?.level || 'info'
    for (const [ts, msg] of (stream.values || [])) {
      entries.push({
        timestamp: ts,
        time: new Date(parseInt(ts) / 1_000_000).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        level,
        message: msg,
      })
    }
  }

  entries.sort((a, b) => parseInt(b.timestamp) - parseInt(a.timestamp))

  const filtered = entries.filter(e => {
    if (filter !== 'all' && e.level !== filter) return false
    if (search && !e.message.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const levelCounts = {}
  for (const e of entries) {
    levelCounts[e.level] = (levelCounts[e.level] || 0) + 1
  }

  return (
    <div>
      {/* Toolbar */}
      <div style={{ marginBottom: 12, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <Button
          size="small"
          type={filter === 'all' ? 'primary' : 'default'}
          onClick={() => setFilter('all')}
        >
          All ({entries.length})
        </Button>
        {['error', 'warn', 'info', 'debug'].map(lv => (
          <Button
            key={lv}
            size="small"
            type={filter === lv ? 'primary' : 'default'}
            danger={lv === 'error' && filter === lv}
            onClick={() => setFilter(lv)}
            style={filter !== lv ? { color: LEVEL_CONFIG[lv]?.color } : {}}
          >
            {lv.toUpperCase()} ({levelCounts[lv] || 0})
          </Button>
        ))}
        <Input
          placeholder="Search logs..."
          prefix={<SearchOutlined />}
          size="small"
          value={search}
          onChange={e => setSearch(e.target.value)}
          allowClear
          style={{ width: 200, marginLeft: 'auto' }}
        />
      </div>

      {/* Log entries */}
      <div style={{
        background: '#1a1a2e',
        borderRadius: 8,
        padding: 12,
        maxHeight: 500,
        overflow: 'auto',
        fontFamily: '"Cascadia Code", "Fira Code", "Consolas", monospace',
        fontSize: 12,
        lineHeight: 1.7,
      }}>
        {filtered.slice(0, 200).map((entry, i) => {
          const cfg = LEVEL_CONFIG[entry.level] || LEVEL_CONFIG.info
          return (
            <div
              key={i}
              style={{
                padding: '2px 8px',
                borderRadius: 3,
                background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
              }}
            >
              <span style={{ color: '#6c7086' }}>{entry.time}</span>
              {' '}
              <span style={{
                color: cfg.color,
                fontWeight: entry.level === 'error' ? 700 : 500,
                display: 'inline-block',
                width: 48,
              }}>
                [{entry.level.toUpperCase()}]
              </span>
              {' '}
              <span style={{
                color: entry.level === 'error' ? '#ff6b6b'
                  : entry.level === 'warn' ? '#ffa94d'
                  : '#d4d4d4',
              }}>
                {entry.message}
              </span>
            </div>
          )
        })}
        {filtered.length === 0 && (
          <div style={{ color: '#6c7086', textAlign: 'center', padding: 20 }}>
            No matching log entries
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Chaos Panel Component (Toxiproxy)
// ---------------------------------------------------------------------------

function ChaosPanel({ connected }) {
  const [results, setResults] = useState([])
  const [selectedProxy, setSelectedProxy] = useState('database')
  const [toxicType, setToxicType] = useState('latency')
  const [latency, setLatency] = useState(500)
  const [jitter, setJitter] = useState(100)

  const proxies = [
    { name: 'database', upstream: 'db.internal:5432', description: 'PostgreSQL database' },
    { name: 'redis-cache', upstream: 'redis.internal:6379', description: 'Redis cache' },
    { name: 'payment-api', upstream: 'payment.example.com:443', description: 'Payment gateway' },
    { name: 'auth-service', upstream: 'auth.internal:8080', description: 'Authentication service' },
  ]

  const toxicTypes = [
    { value: 'latency', label: 'Latency', desc: 'Add network delay', icon: <ClockCircleOutlined /> },
    { value: 'bandwidth', label: 'Bandwidth', desc: 'Limit throughput', icon: <ThunderboltOutlined /> },
    { value: 'timeout', label: 'Timeout', desc: 'Drop connection', icon: <CloseCircleOutlined /> },
    { value: 'slow_close', label: 'Slow Close', desc: 'Delay TCP close', icon: <ClockCircleOutlined /> },
  ]

  const handleInject = async () => {
    const result = await injectToxic(selectedProxy, toxicType, latency, jitter)
    setResults(prev => [{
      time: new Date().toLocaleTimeString(),
      action: 'inject',
      proxy: selectedProxy,
      toxic: toxicType,
      detail: `${toxicType} ${latency}ms (jitter: ${jitter}ms)`,
      status: result.status || 'ok',
      ...result,
    }, ...prev])
  }

  const handleReset = async () => {
    const result = await resetToxics()
    setResults(prev => [{
      time: new Date().toLocaleTimeString(),
      action: 'reset',
      proxy: 'all',
      toxic: 'all',
      detail: 'Reset all toxics',
      status: result.status || 'ok',
    }, ...prev])
  }

  return (
    <div>
      <Row gutter={24}>
        {/* Control Panel */}
        <Col span={14}>
          <Card
            title={<><ExperimentOutlined /> Fault Injection</>}
            size="small"
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
          >
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Target Service</Text>
                <Select
                  value={selectedProxy}
                  onChange={setSelectedProxy}
                  style={{ width: '100%' }}
                  options={proxies.map(p => ({
                    value: p.name,
                    label: <><CloudServerOutlined /> {p.name} <Text type="secondary" style={{ fontSize: 11 }}>({p.upstream})</Text></>,
                  }))}
                />
              </Col>
              <Col span={12}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Fault Type</Text>
                <Select
                  value={toxicType}
                  onChange={setToxicType}
                  style={{ width: '100%' }}
                  options={toxicTypes.map(t => ({
                    value: t.value,
                    label: <>{t.icon} {t.label} <Text type="secondary" style={{ fontSize: 11 }}>— {t.desc}</Text></>,
                  }))}
                />
              </Col>
              <Col span={12}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                  Latency: {latency}ms
                </Text>
                <Slider min={10} max={5000} value={latency} onChange={setLatency} />
              </Col>
              <Col span={12}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                  Jitter: {jitter}ms
                </Text>
                <Slider min={0} max={1000} value={jitter} onChange={setJitter} />
              </Col>
            </Row>

            <Divider style={{ margin: '12px 0' }} />

            <Space>
              <Button
                type="primary"
                danger
                icon={<ThunderboltOutlined />}
                onClick={handleInject}
                style={{ borderRadius: 6 }}
              >
                Inject Fault
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={handleReset}
                style={{ borderRadius: 6 }}
              >
                Reset All
              </Button>
            </Space>

            {!connected && (
              <Alert
                type="info"
                message="Demo Mode — Toxiproxy is not running. Actions are simulated."
                showIcon
                style={{ marginTop: 12, borderRadius: 6 }}
              />
            )}
          </Card>
        </Col>

        {/* Service Topology */}
        <Col span={10}>
          <Card
            title="Service Topology"
            size="small"
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
          >
            <div style={{ textAlign: 'center' }}>
              {/* Simple visual topology */}
              <div style={{
                padding: 12, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: 8, color: '#fff', fontWeight: 600, fontSize: 13, marginBottom: 8,
              }}>
                Locust (Load Generator)
              </div>
              <div style={{ fontSize: 20, color: '#bbb' }}>↓</div>
              <div style={{
                padding: 10, background: '#e6f4ff', border: '2px solid #1677ff',
                borderRadius: 8, fontWeight: 600, fontSize: 13, marginBottom: 8,
              }}>
                Your API (FastAPI)
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 4, fontSize: 20, color: '#bbb' }}>
                <span>↙</span><span>↓</span><span>↘</span>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
                {proxies.map(p => (
                  <Tooltip key={p.name} title={`${p.upstream} — ${p.description}`}>
                    <div style={{
                      padding: '6px 12px',
                      borderRadius: 6,
                      fontSize: 11,
                      fontWeight: 600,
                      background: selectedProxy === p.name ? '#fff2f0' : '#f6ffed',
                      border: `1px solid ${selectedProxy === p.name ? '#ffccc7' : '#b7eb8f'}`,
                      cursor: 'pointer',
                    }}
                    onClick={() => setSelectedProxy(p.name)}
                    >
                      {selectedProxy === p.name ? <ThunderboltOutlined style={{ color: '#ff4d4f' }} /> : <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                      {' '}{p.name}
                    </div>
                  </Tooltip>
                ))}
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Action Log */}
      {results.length > 0 && (
        <Card
          title="Action Log"
          size="small"
          style={{ marginTop: 16, borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
        >
          <div style={{
            background: '#1a1a2e', borderRadius: 8, padding: 12,
            fontFamily: 'monospace', fontSize: 12, maxHeight: 200, overflow: 'auto',
          }}>
            {results.map((r, i) => (
              <div key={i} style={{ color: r.action === 'inject' ? '#ff6b6b' : '#52c41a', lineHeight: 1.8 }}>
                <span style={{ color: '#6c7086' }}>[{r.time}]</span>
                {' '}
                {r.action === 'inject' ? '⚡ INJECT' : '🔄 RESET'}
                {' '}
                <span style={{ color: '#d4d4d4' }}>
                  {r.detail} → {r.proxy}
                </span>
                {' '}
                <span style={{ color: r.status === 'demo' ? '#ffa94d' : '#52c41a' }}>
                  [{r.status}]
                </span>
                {r.message && <span style={{ color: '#6c7086' }}> {r.message}</span>}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Service Status Badge
// ---------------------------------------------------------------------------

function StatusBadge({ name, connected, url, icon }) {
  return (
    <Tooltip title={`${url} — ${connected ? 'Connected' : 'Using demo data'}`}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '5px 12px', borderRadius: 6,
        background: connected ? '#f6ffed' : '#f0f5ff',
        border: `1px solid ${connected ? '#b7eb8f' : '#adc6ff'}`,
      }}>
        {icon}
        <Text strong style={{ fontSize: 12 }}>{name}</Text>
        <Badge status={connected ? 'success' : 'processing'} />
        {!connected && <Text type="secondary" style={{ fontSize: 10 }}>demo</Text>}
      </div>
    </Tooltip>
  )
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ObservabilityPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const [status, setStatus] = useState(null)
  const [flameData, setFlameData] = useState(null)
  const [logData, setLogData] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    const [s, f, l] = await Promise.all([
      fetchObsStatus(projectKey),
      fetchFlameGraph(),
      fetchLogs(),
    ])
    setStatus(s)
    setFlameData(f)
    setLogData(l)
    setLoading(false)
  }

  useEffect(() => { loadData() }, [projectKey])

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>
  }

  return (
    <div style={{ maxWidth: 1400 }}>
      {/* Header */}
      <div style={{ marginBottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
            Observability
            <Tag style={{ marginLeft: 8 }}>{projectName}</Tag>
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Pyroscope flame graphs + Loki logs + Toxiproxy chaos engineering
          </Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={loadData}>Refresh</Button>
      </div>

      {/* Service Status */}
      <div style={{ marginBottom: 20 }}>
        <Space wrap size={8}>
          <StatusBadge name="Pyroscope" connected={status?.pyroscope?.connected} url={status?.pyroscope?.url} icon={<FireOutlined style={{ color: '#ff6b35' }} />} />
          <StatusBadge name="Loki" connected={status?.loki?.connected} url={status?.loki?.url} icon={<FileTextOutlined style={{ color: '#f46800' }} />} />
          <StatusBadge name="Toxiproxy" connected={status?.toxiproxy?.connected} url={status?.toxiproxy?.url} icon={<ThunderboltOutlined style={{ color: '#722ed1' }} />} />
        </Space>
      </div>

      {/* Tabs */}
      <Tabs
        defaultActiveKey="flamegraph"
        items={[
          {
            key: 'flamegraph',
            label: <><FireOutlined /> Flame Graph</>,
            children: (
              <Card
                title={
                  <Space>
                    <FireOutlined style={{ color: '#ff6b35' }} />
                    <span>CPU Flame Graph</span>
                    <Tag color="orange">Pyroscope</Tag>
                  </Space>
                }
                extra={
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Click a function to highlight · Wider = more CPU time · Redder = more self time
                  </Text>
                }
                style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
              >
                <FlameGraph data={flameData} />

                <Divider style={{ margin: '16px 0 12px' }} />

                <div style={{ padding: '12px 16px', background: '#f0f5ff', borderRadius: 8, border: '1px solid #adc6ff' }}>
                  <Text strong style={{ fontSize: 13 }}>How to read this flame graph:</Text>
                  <ul style={{ margin: '8px 0 0', paddingLeft: 20, fontSize: 12, color: '#595959', lineHeight: 2 }}>
                    <li><strong>Width</strong> = total CPU time spent in that function (including children)</li>
                    <li><strong>Red/orange bars</strong> = high "self" time — this function is doing the actual work (bottleneck)</li>
                    <li><strong>Blue bars</strong> = low self time — this function mostly calls other functions</li>
                    <li><strong>Bottom → Top</strong> = call stack depth (bottom is the entry point, top is the leaf)</li>
                    <li>Look for <strong>wide red bars</strong> near the top — those are your optimization targets</li>
                  </ul>
                </div>

                {!status?.pyroscope?.connected && (
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginTop: 12, borderRadius: 8 }}
                    message="Demo data — showing simulated flame graph for a FastAPI application"
                    description={
                      <span style={{ fontSize: 12 }}>
                        To connect to real profiling: <Text code>pip install pyroscope-io</Text> and set <Text code>PYROSCOPE_URL=http://localhost:4040</Text>
                      </span>
                    }
                  />
                )}
              </Card>
            ),
          },
          {
            key: 'logs',
            label: <><FileTextOutlined /> Logs</>,
            children: (
              <Card
                title={
                  <Space>
                    <FileTextOutlined style={{ color: '#f46800' }} />
                    <span>Application Logs</span>
                    <Tag color="orange">Loki</Tag>
                  </Space>
                }
                style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
              >
                <LogViewer data={logData} />

                {!status?.loki?.connected && (
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginTop: 12, borderRadius: 8 }}
                    message="Demo data — showing simulated log entries"
                    description={
                      <span style={{ fontSize: 12 }}>
                        To connect: set <Text code>LOKI_URL=http://localhost:3100</Text>. Use <Text code>pip install python-logging-loki</Text> to push logs from your app.
                      </span>
                    }
                  />
                )}
              </Card>
            ),
          },
          {
            key: 'chaos',
            label: <><ThunderboltOutlined /> Chaos Engineering</>,
            children: (
              <div>
                <Alert
                  type="warning"
                  showIcon
                  icon={<ExperimentOutlined />}
                  message="Chaos Engineering — inject network faults to test system resilience"
                  description="Use this during load tests to simulate real-world failure scenarios. Toxiproxy sits between your app and its dependencies (DB, Redis, external APIs) and can inject latency, bandwidth limits, timeouts, and connection drops."
                  style={{ marginBottom: 16, borderRadius: 8 }}
                />
                <ChaosPanel connected={status?.toxiproxy?.connected} />
              </div>
            ),
          },
        ]}
      />
    </div>
  )
}
