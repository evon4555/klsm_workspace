import { Row, Col, Card, Statistic, Badge, Progress, Tooltip } from 'antd'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'

const cardBase = {
  borderRadius: 12,
  border: 'none',
  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
}

export default function KpiCards({ run }) {
  if (!run) {
    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card style={cardBase}>
            <span style={{ color: '#999' }}>No test runs yet. Click "Run Tests" to start.</span>
          </Card>
        </Col>
      </Row>
    )
  }

  const statusBadge = {
    running: { status: 'processing', text: 'Running...' },
    passed:  { status: 'success',    text: 'Passed' },
    failed:  { status: 'error',      text: 'Failed' },
    error:   { status: 'warning',    text: 'Error' },
  }

  const badge = statusBadge[run.status] || { status: 'default', text: run.status }
  const executed = run.executed ?? ((run.passed || 0) + (run.failed || 0) + (run.errored || 0))
  const collected = run.collected ?? run.total ?? 0
  const skipped = run.skipped || 0
  const passRate = executed > 0 ? Math.round(((run.passed || 0) / executed) * 100) : 0
  const prColor = passRate >= 80 ? '#52c41a' : passRate >= 60 ? '#faad14' : '#ff4d4f'

  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      {/* Pass Rate Ring */}
      <Col xs={12} sm={5}>
        <Card style={{ ...cardBase, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Progress
              type="circle"
              percent={passRate}
              size={56}
              strokeColor="#fff"
              trailColor="rgba(255,255,255,0.2)"
              format={(p) => <span style={{ color: '#fff', fontSize: 14, fontWeight: 700 }}>{p}%</span>}
            />
            <div>
              <div style={{ color: 'rgba(255,255,255,0.85)', fontSize: 12 }}>
                <Badge {...badge} /> Full run #{run.id}
              </div>
              <div style={{ color: '#fff', fontSize: 18, fontWeight: 700 }}>
                {executed} <span style={{ fontSize: 11, fontWeight: 400 }}>executed</span>
              </div>
              <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 11 }}>
                {collected} collected / {skipped} skipped
              </div>
            </div>
          </div>
        </Card>
      </Col>

      {/* Passed */}
      <Col xs={12} sm={5}>
        <Card style={cardBase}>
          <Statistic
            title="Passed"
            value={run.passed}
            valueStyle={{ color: '#52c41a' }}
            prefix={<CheckCircleOutlined />}
          />
        </Card>
      </Col>

      {/* Failed — real assertion mismatch (likely product bug) */}
      <Col xs={12} sm={4}>
        <Card style={cardBase}>
          <Tooltip title="Test ran and assertion did not match — typically a product behavior gap.">
            <Statistic
              title="Failed"
              value={run.failed}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
          </Tooltip>
        </Card>
      </Col>

      {/* Errored — test crashed before assertion (likely test/infra problem) */}
      <Col xs={12} sm={4}>
        <Card style={cardBase}>
          <Tooltip title="Test crashed before its assertion ran — Playwright timeout, undefined step, fixture exception. Usually a test/infra problem, not a product bug.">
            <Statistic
              title="Errored"
              value={run.errored ?? 0}
              valueStyle={{ color: '#faad14' }}
              prefix={<WarningOutlined />}
            />
          </Tooltip>
        </Card>
      </Col>

      {/* Skipped */}
      <Col xs={12} sm={3}>
        <Card style={cardBase}>
          <Statistic
            title="Skipped"
            value={run.skipped}
            valueStyle={{ color: '#8c8c8c' }}
            prefix={<MinusCircleOutlined />}
          />
        </Card>
      </Col>

      {/* Pass Rate Bar */}
      <Col xs={24} sm={3}>
        <Card style={cardBase}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>Pass Rate</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: prColor }}>{passRate}%</div>
            <Progress
              percent={passRate}
              showInfo={false}
              strokeColor={prColor}
              size="small"
              style={{ marginTop: 4 }}
            />
          </div>
        </Card>
      </Col>
    </Row>
  )
}
