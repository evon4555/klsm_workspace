import { useState, useEffect } from 'react'
import {
  Typography, Card, Row, Col, Statistic, Progress, Table, Tag, Badge, Space, Spin, Tooltip,
} from 'antd'
import {
  ExperimentOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  FireOutlined,
} from '@ant-design/icons'
import { fetchTrends, fetchFlakyTests } from '../api'

const { Title, Text } = Typography

function runExecuted(run) {
  return run?.executed ?? ((run?.passed || 0) + (run?.failed || 0) + (run?.errored || 0))
}

function runCollected(run) {
  return run?.collected ?? run?.total ?? 0
}

// ---------------------------------------------------------------------------
// Simple SVG-based mini charts (no external chart library dependency issues)
// ---------------------------------------------------------------------------

/** Sparkline — a small inline line chart */
function Sparkline({ data, width = 280, height = 60, color = '#1677ff', areaColor = 'rgba(22,119,255,0.08)' }) {
  if (!data || data.length < 2) return null
  const min = Math.min(...data) * 0.9
  const max = Math.max(...data) * 1.1 || 1
  const range = max - min || 1
  const step = width / (data.length - 1)

  const points = data.map((v, i) => ({
    x: i * step,
    y: height - ((v - min) / range) * height,
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height} L 0 ${height} Z`

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <path d={areaPath} fill={areaColor} />
      <path d={linePath} fill="none" stroke={color} strokeWidth={2} />
      {/* Last point dot */}
      <circle
        cx={points[points.length - 1].x}
        cy={points[points.length - 1].y}
        r={3}
        fill={color}
      />
    </svg>
  )
}

/** Bar chart with stacked executed statuses plus skipped collected scenarios. */
function StackedBarChart({ runs, width = 560, height = 160 }) {
  if (!runs || runs.length === 0) return null
  const maxTotal = Math.max(...runs.map(r => runCollected(r))) || 1
  const barWidth = Math.max(12, Math.min(28, (width - 40) / runs.length - 4))
  const gap = 4

  return (
    <svg width={width} height={height + 30} style={{ display: 'block' }}>
      {runs.map((r, i) => {
        const x = i * (barWidth + gap) + 20
        const scale = (height - 10) / maxTotal
        const passH = (r.passed || 0) * scale
        const failH = (r.failed || 0) * scale
        const errorH = (r.errored || 0) * scale
        const skipH = (r.skipped || 0) * scale
        let y = height

        return (
          <g key={r.id}>
            {/* Passed (green) */}
            <rect x={x} y={y - passH} width={barWidth} height={passH} fill="#52c41a" rx={2} />
            {/* Failed (red) */}
            <rect x={x} y={y - passH - failH} width={barWidth} height={failH} fill="#ff4d4f" rx={2} />
            {/* Errored (gold) */}
            <rect x={x} y={y - passH - failH - errorH} width={barWidth} height={errorH} fill="#faad14" rx={2} />
            {/* Skipped (gray) */}
            <rect x={x} y={y - passH - failH - errorH - skipH} width={barWidth} height={skipH} fill="#d9d9d9" rx={2} />
            {/* Label */}
            <text
              x={x + barWidth / 2}
              y={height + 16}
              textAnchor="middle"
              fontSize={9}
              fill="#8c8c8c"
            >
              #{r.id}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

/** Donut chart for error categories */
function DonutChart({ data, size = 160 }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>No errors</Text>
      </div>
    )
  }

  const total = data.reduce((s, d) => s + d.count, 0)
  const colors = ['#722ed1', '#fa8c16', '#f5222d', '#13c2c2', '#1890ff', '#eb2f96', '#faad14', '#52c41a', '#8c8c8c']
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 10
  const inner = r * 0.6

  let startAngle = -Math.PI / 2
  const slices = data.map((d, i) => {
    const angle = (d.count / total) * 2 * Math.PI
    const endAngle = startAngle + angle
    const largeArc = angle > Math.PI ? 1 : 0

    const x1 = cx + r * Math.cos(startAngle)
    const y1 = cy + r * Math.sin(startAngle)
    const x2 = cx + r * Math.cos(endAngle)
    const y2 = cy + r * Math.sin(endAngle)
    const ix1 = cx + inner * Math.cos(endAngle)
    const iy1 = cy + inner * Math.sin(endAngle)
    const ix2 = cx + inner * Math.cos(startAngle)
    const iy2 = cy + inner * Math.sin(startAngle)

    const path = [
      `M ${x1} ${y1}`,
      `A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${ix1} ${iy1}`,
      `A ${inner} ${inner} 0 ${largeArc} 0 ${ix2} ${iy2}`,
      'Z',
    ].join(' ')

    startAngle = endAngle

    return (
      <path key={i} d={path} fill={colors[i % colors.length]} opacity={0.85}>
        <title>{d.category}: {d.count} ({Math.round(d.count / total * 100)}%)</title>
      </path>
    )
  })

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <svg width={size} height={size}>
        {slices}
        <text x={cx} y={cy - 6} textAnchor="middle" fontSize={20} fontWeight={700} fill="#262626">{total}</text>
        <text x={cx} y={cy + 12} textAnchor="middle" fontSize={10} fill="#8c8c8c">total errors</text>
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {data.map((d, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <span style={{
              width: 10, height: 10, borderRadius: 2,
              background: colors[i % colors.length], display: 'inline-block',
            }} />
            <Text style={{ fontSize: 12 }}>{d.category}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>({d.count})</Text>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Flakiness history dots — shows pass/fail pattern */
function FlakeHistory({ history }) {
  return (
    <Space size={2}>
      {history.map((s, i) => (
        <Tooltip key={i} title={`Run ${i + 1}: ${s}`}>
          <span
            style={{
              display: 'inline-block',
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: s === 'passed' ? '#52c41a' : s === 'failed' ? '#ff4d4f' : '#d9d9d9',
            }}
          />
        </Tooltip>
      ))}
    </Space>
  )
}

// ---------------------------------------------------------------------------
// Main Dashboard Page
// ---------------------------------------------------------------------------

export default function DashboardPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const [trends, setTrends] = useState(null)
  const [flaky, setFlaky] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetchTrends(20, projectKey),
      fetchFlakyTests(15, projectKey),
    ]).then(([t, f]) => {
      setTrends(t)
      setFlaky(f)
    }).finally(() => setLoading(false))
  }, [projectKey])

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>
  }

  const runs = trends?.runs || []
  const summary = trends?.summary || {}
  const errorCats = trends?.error_categories || []
  const flakyTests = flaky?.flaky_tests || []

  const passRates = runs.map(r => r.pass_rate)
  const avgDurations = runs.map(r => r.avg_duration)

  // Latest run for quick glance
  const latest = runs.length > 0 ? runs[runs.length - 1] : null

  // Pass rate color
  const prColor = summary.overall_pass_rate >= 80 ? '#52c41a'
    : summary.overall_pass_rate >= 60 ? '#faad14' : '#ff4d4f'

  // Recent runs table columns
  const recentColumns = [
    {
      title: 'Run',
      dataIndex: 'id',
      width: 70,
      render: (v) => <Text strong>#{v}</Text>,
    },
    {
      title: 'Date',
      dataIndex: 'started_at',
      width: 140,
      render: (v) => v ? new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—',
    },
    {
      title: 'Env',
      dataIndex: 'env',
      width: 70,
      render: (v) => <Tag>{(v || '').toUpperCase()}</Tag>,
    },
    {
      title: 'Scope',
      key: 'scope',
      width: 130,
      render: (_, r) => {
        const executed = runExecuted(r)
        const collected = runCollected(r)
        return (
          <Tooltip title="Executed excludes skipped/NA scenarios. Collected is every Behave scenario discovered in the feature files.">
            <div>
              <Text strong>{executed}</Text>
              <Text type="secondary"> / {collected}</Text>
              <div style={{ fontSize: 11, color: '#8c8c8c' }}>
                executed / collected
              </div>
            </div>
          </Tooltip>
        )
      },
    },
    {
      title: 'Result',
      key: 'result',
      width: 145,
      render: (_, r) => (
        <Space size={4} wrap>
          <Tag color="green" style={{ margin: 0 }}>{r.passed || 0} passed</Tag>
          <Tag color={(r.failed || 0) > 0 ? 'red' : 'default'} style={{ margin: 0 }}>{r.failed || 0} failed</Tag>
          {(r.errored || 0) > 0 && <Tag color="gold" style={{ margin: 0 }}>{r.errored} errored</Tag>}
          <Tag style={{ margin: 0 }}>{r.skipped || 0} skipped</Tag>
        </Space>
      ),
    },
    {
      title: 'Exec Pass Rate',
      dataIndex: 'pass_rate',
      width: 160,
      render: (v) => (
        <Space>
          <Progress
            percent={v}
            size="small"
            style={{ width: 80 }}
            strokeColor={v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f'}
            showInfo={false}
          />
          <Text style={{
            color: v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f',
            fontWeight: 600, fontSize: 13,
          }}>
            {v}%
          </Text>
        </Space>
      ),
      sorter: (a, b) => a.pass_rate - b.pass_rate,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 80,
      render: (s) => {
        const c = { passed: 'green', failed: 'red', error: 'orange' }
        return <Tag color={c[s] || 'default'}>{(s || '').toUpperCase()}</Tag>
      },
    },
  ]

  // Flaky tests table
  const flakyColumns = [
    {
      title: 'Test',
      key: 'test',
      render: (_, r) => (
        <div>
          <Text strong style={{ fontSize: 13 }}>{r.name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>{r.feature}</Text>
        </div>
      ),
    },
    {
      title: 'Flakiness',
      dataIndex: 'flakiness_rate',
      width: 100,
      render: (v) => (
        <Text style={{
          color: v >= 40 ? '#ff4d4f' : v >= 20 ? '#faad14' : '#52c41a',
          fontWeight: 600,
        }}>
          {v}%
        </Text>
      ),
      sorter: (a, b) => a.flakiness_rate - b.flakiness_rate,
      defaultSortOrder: 'descend',
    },
    {
      title: 'Flips',
      dataIndex: 'flips',
      width: 60,
      render: (v) => <Badge count={v} style={{ backgroundColor: v >= 5 ? '#ff4d4f' : '#faad14' }} />,
    },
    {
      title: 'History',
      dataIndex: 'history',
      width: 140,
      render: (h) => <FlakeHistory history={h} />,
    },
    {
      title: 'Last',
      dataIndex: 'last_status',
      width: 70,
      render: (s) => (
        <Tag color={s === 'passed' ? 'green' : 'red'} style={{ borderRadius: 4 }}>
          {(s || '').toUpperCase()}
        </Tag>
      ),
    },
  ]

  return (
    <div style={{ maxWidth: 1400 }}>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, fontWeight: 600 }}>Dashboard</Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Test automation overview for <Tag style={{ marginInline: 4 }}>{projectName}</Tag>
        </Text>
      </div>

      {/* KPI Cards Row */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <Statistic
              title="Total Runs"
              value={summary.total_runs || 0}
              prefix={<ExperimentOutlined style={{ color: '#1677ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <Progress
                type="circle"
                percent={summary.overall_pass_rate || 0}
                size={64}
                strokeColor={prColor}
                format={(p) => <span style={{ fontSize: 14, fontWeight: 700 }}>{p}%</span>}
              />
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>Executed Pass Rate</Text>
                <div style={{ fontSize: 11, color: '#8c8c8c' }}>
                  {summary.total_passed || 0} / {summary.total_scenarios_executed || 0} executed
                </div>
                <div style={{ fontSize: 11, color: '#bfbfbf' }}>
                  {summary.total_scenarios_collected || 0} collected incl. skipped
                </div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <Statistic
              title="Avg Executed / Run"
              value={summary.avg_executed_per_run ?? summary.avg_scenarios_per_run ?? 0}
              prefix={<RiseOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <Statistic
              title="Flaky Tests"
              value={flakyTests.length}
              valueStyle={{ color: flakyTests.length > 3 ? '#ff4d4f' : '#faad14' }}
              prefix={<WarningOutlined />}
              suffix={<Text type="secondary" style={{ fontSize: 12 }}>detected</Text>}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {/* Pass Rate Trend */}
        <Col xs={24} lg={12}>
          <Card
            title="Executed Pass Rate Trend"
            size="small"
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', height: '100%' }}
          >
            <div style={{ padding: '8px 0' }}>
              <Sparkline
                data={passRates}
                width={520}
                height={80}
                color="#52c41a"
                areaColor="rgba(82,196,26,0.08)"
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {runs.length > 0 ? `Run #${runs[0].id}` : ''}
                </Text>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {runs.length > 0 ? `Run #${runs[runs.length - 1].id}` : ''}
                </Text>
              </div>
            </div>
          </Card>
        </Col>

        {/* Duration Trend */}
        <Col xs={24} lg={12}>
          <Card
            title="Avg Duration Trend (seconds)"
            size="small"
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', height: '100%' }}
          >
            <div style={{ padding: '8px 0' }}>
              <Sparkline
                data={avgDurations}
                width={520}
                height={80}
                color="#722ed1"
                areaColor="rgba(114,46,209,0.08)"
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {runs.length > 0 ? `Run #${runs[0].id}` : ''}
                </Text>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {latest ? `Latest: ${latest.avg_duration}s` : ''}
                </Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Test Count Growth + Error Category */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={14}>
          <Card
            title="Run Scope Mix"
            size="small"
            extra={
              <Space size={12}>
                <span style={{ fontSize: 11 }}><span style={{ display: 'inline-block', width: 8, height: 8, background: '#52c41a', borderRadius: 2, marginRight: 4 }} />Passed</span>
                <span style={{ fontSize: 11 }}><span style={{ display: 'inline-block', width: 8, height: 8, background: '#ff4d4f', borderRadius: 2, marginRight: 4 }} />Failed</span>
                <span style={{ fontSize: 11 }}><span style={{ display: 'inline-block', width: 8, height: 8, background: '#faad14', borderRadius: 2, marginRight: 4 }} />Errored</span>
                <span style={{ fontSize: 11 }}><span style={{ display: 'inline-block', width: 8, height: 8, background: '#d9d9d9', borderRadius: 2, marginRight: 4 }} />Skipped</span>
              </Space>
            }
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', height: '100%' }}
          >
            <StackedBarChart runs={runs} width={560} height={140} />
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card
            title="Error Distribution"
            size="small"
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', height: '100%' }}
          >
            <DonutChart data={errorCats} size={140} />
          </Card>
        </Col>
      </Row>

      {/* Recent Runs + Flaky Tests */}
      <Row gutter={16}>
        <Col xs={24} lg={14}>
          <Card
            title="Recent Runs"
            size="small"
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
          >
            <Table
              dataSource={[...runs].reverse().slice(0, 10)}
              columns={recentColumns}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card
            title={<><FireOutlined style={{ color: '#ff4d4f' }} /> Flaky Tests</>}
            size="small"
            extra={
              <Text type="secondary" style={{ fontSize: 11 }}>
                {flaky?.runs_analyzed || 0} runs analyzed
              </Text>
            }
            style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
          >
            {flakyTests.length > 0 ? (
              <Table
                dataSource={flakyTests.slice(0, 8)}
                columns={flakyColumns}
                rowKey={(r) => `${r.feature}-${r.name}`}
                size="small"
                pagination={false}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#52c41a' }}>
                <CheckCircleOutlined style={{ fontSize: 32, marginBottom: 8 }} />
                <div>No flaky tests detected</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
