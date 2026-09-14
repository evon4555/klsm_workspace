import { useState, useEffect } from 'react'
import { Card, Tag, Collapse, Space, Typography, Badge, Row, Col, Statistic, Spin, Tooltip, Progress } from 'antd'
import {
  BugOutlined,
  AimOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  DisconnectOutlined,
  QuestionCircleOutlined,
  GlobalOutlined,
  LockOutlined,
  DatabaseOutlined,
  ExclamationCircleOutlined,
  ToolOutlined,
  ThunderboltOutlined,
  AlertOutlined,
} from '@ant-design/icons'
import { fetchErrorAnalysis } from '../api'

const { Text, Paragraph } = Typography

// Map category icons
const iconMap = {
  'aim': <AimOutlined />,
  'clock-circle': <ClockCircleOutlined />,
  'close-circle': <CloseCircleOutlined />,
  'disconnect': <DisconnectOutlined />,
  'question-circle': <QuestionCircleOutlined />,
  'global': <GlobalOutlined />,
  'lock': <LockOutlined />,
  'database': <DatabaseOutlined />,
  'exclamation-circle': <ExclamationCircleOutlined />,
}

// Complexity badge colors
const complexityConfig = {
  'Low': { color: '#52c41a', bg: '#f6ffed', border: '#b7eb8f' },
  'Medium': { color: '#fa8c16', bg: '#fff7e6', border: '#ffd591' },
  'High': { color: '#f5222d', bg: '#fff2f0', border: '#ffccc7' },
}

export default function ErrorAnalysis({ runId }) {
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!runId) return
    setLoading(true)
    fetchErrorAnalysis(runId)
      .then(setAnalysis)
      .finally(() => setLoading(false))
  }, [runId])

  if (loading) {
    return (
      <Card style={{ marginTop: 16, borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <Spin />
      </Card>
    )
  }

  if (!analysis || analysis.total_errors === 0) return null

  const { categories, groups, blast_radius, summary } = analysis

  return (
    <Card
      title={
        <Space>
          <BugOutlined style={{ color: '#f5222d' }} />
          <span>Error Analysis</span>
          <Badge
            count={summary.total_failed}
            style={{ backgroundColor: '#ff4d4f' }}
          />
        </Space>
      }
      extra={
        <Space size={16}>
          <Tooltip title="Number of unique error patterns (likely root causes)">
            <Text type="secondary" style={{ fontSize: 12 }}>
              <ThunderboltOutlined /> {summary.unique_root_causes} root cause{summary.unique_root_causes !== 1 ? 's' : ''}
            </Text>
          </Tooltip>
          <Tooltip title="Estimated total fix time">
            <Text type="secondary" style={{ fontSize: 12 }}>
              <ClockCircleOutlined /> Est. {summary.est_total_fix_min}-{summary.est_total_fix_max} min
            </Text>
          </Tooltip>
        </Space>
      }
      style={{
        marginTop: 16,
        borderRadius: 12,
        border: 'none',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      }}
    >
      {/* Summary Row */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <div style={{ padding: '12px 16px', background: '#fafafa', borderRadius: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>Dominant Error Type</Text>
            <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>
              {summary.dominant_category || 'N/A'}
            </div>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {summary.dominant_count} of {summary.total_failed} failures
            </Text>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ padding: '12px 16px', background: '#fafafa', borderRadius: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>Error Deduplication</Text>
            <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>
              {summary.total_failed} errors → {summary.unique_root_causes} root cause{summary.unique_root_causes !== 1 ? 's' : ''}
            </div>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {summary.unique_root_causes < summary.total_failed
                ? `${summary.total_failed - summary.unique_root_causes} duplicate(s) detected`
                : 'All errors are unique'}
            </Text>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ padding: '12px 16px', background: '#fafafa', borderRadius: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>Affected Features</Text>
            <div style={{ marginTop: 4 }}>
              {blast_radius.map((b, i) => (
                <Tag key={i} color={b.error_count >= 3 ? 'red' : b.error_count >= 2 ? 'orange' : 'default'} style={{ marginBottom: 2, borderRadius: 4 }}>
                  {b.feature} ({b.error_count})
                </Tag>
              ))}
            </div>
          </div>
        </Col>
      </Row>

      {/* Error Categories - Collapsible */}
      <Collapse
        bordered={false}
        style={{ background: 'transparent' }}
        items={categories.map((cat) => {
          const cplx = complexityConfig[cat.complexity] || complexityConfig['High']

          return {
            key: cat.id,
            label: (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}>
                <span style={{ color: cat.color, fontSize: 16 }}>
                  {iconMap[cat.icon] || <ExclamationCircleOutlined />}
                </span>
                <Text strong style={{ fontSize: 13 }}>{cat.label}</Text>
                <Badge count={cat.count} style={{ backgroundColor: cat.color }} />
                <Tag
                  style={{
                    background: cplx.bg,
                    color: cplx.color,
                    border: `1px solid ${cplx.border}`,
                    borderRadius: 4,
                    fontSize: 11,
                    marginLeft: 'auto',
                  }}
                >
                  <ToolOutlined /> {cat.complexity} · {cat.est_fix_time}
                </Tag>
                {cat.unique_patterns < cat.count && (
                  <Tooltip title="Multiple tests share the same root cause">
                    <Tag color="purple" style={{ borderRadius: 4, fontSize: 11 }}>
                      <AlertOutlined /> {cat.count} tests, {cat.unique_patterns} root cause{cat.unique_patterns !== 1 ? 's' : ''}
                    </Tag>
                  </Tooltip>
                )}
              </div>
            ),
            children: (
              <div>
                {/* Suggestion */}
                <div style={{
                  padding: '8px 12px',
                  background: '#e6f4ff',
                  borderRadius: 6,
                  marginBottom: 12,
                  border: '1px solid #91caff',
                }}>
                  <Text style={{ fontSize: 12 }}>
                    <ToolOutlined style={{ color: '#1677ff', marginRight: 6 }} />
                    <strong>Suggested Action:</strong> {cat.suggestion}
                  </Text>
                </div>

                {/* Individual errors */}
                {cat.errors.map((err, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '10px 14px',
                      background: '#fff',
                      border: '1px solid #f0f0f0',
                      borderRadius: 6,
                      marginBottom: 8,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <div>
                        <Text strong style={{ fontSize: 13 }}>{err.scenario}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 11 }}>{err.feature} · {err.duration_s?.toFixed(1)}s</Text>
                      </div>
                    </div>
                    <pre style={{
                      fontSize: 11,
                      lineHeight: 1.5,
                      color: '#cf1322',
                      background: '#fff2f0',
                      padding: 10,
                      borderRadius: 4,
                      border: '1px solid #ffccc7',
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      maxHeight: 120,
                      overflow: 'auto',
                    }}>
                      {err.error_preview}
                    </pre>
                  </div>
                ))}
              </div>
            ),
          }
        })}
      />

      {/* Root Cause Groups */}
      {groups.length > 0 && groups.some(g => g.count > 1) && (
        <div style={{ marginTop: 16 }}>
          <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
            <ThunderboltOutlined style={{ color: '#722ed1' }} /> Deduplicated Root Causes
          </Text>
          {groups.filter(g => g.count > 1).map((g, i) => (
            <div
              key={i}
              style={{
                padding: '8px 12px',
                background: '#f9f0ff',
                border: '1px solid #d3adf7',
                borderRadius: 6,
                marginBottom: 6,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text code style={{ fontSize: 11 }}>{g.fingerprint}</Text>
                <Badge count={`${g.count} tests`} style={{ backgroundColor: '#722ed1' }} />
              </div>
              <div style={{ marginTop: 4 }}>
                {g.scenarios.map((s, j) => (
                  <Tag key={j} style={{ fontSize: 11, borderRadius: 4, marginBottom: 2 }}>
                    {s.name}
                  </Tag>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
