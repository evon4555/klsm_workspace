import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import {
  ApiOutlined,
  AuditOutlined,
  BugOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import {
  fetchApiMonitorEndpoints,
  fetchFlakyTests,
  getEvidenceStatus,
  getRunDetail,
  listFeatures,
  listRuns,
} from '../api'

const { Title, Text, Paragraph } = Typography

const STATUS_META = {
  passed: { color: 'green', badge: 'success', label: 'Passed' },
  failed: { color: 'red', badge: 'error', label: 'Failed' },
  error: { color: 'gold', badge: 'warning', label: 'Errored' },
  skipped: { color: 'default', badge: 'default', label: 'Skipped' },
  not_run: { color: 'default', badge: 'default', label: 'Not run' },
}

const DECISION_META = {
  ready: {
    color: '#52c41a',
    tag: 'green',
    icon: <CheckCircleOutlined />,
    title: 'Ready',
    summary: 'No blocking quality signal in the current dashboard data.',
  },
  conditional: {
    color: '#faad14',
    tag: 'gold',
    icon: <WarningOutlined />,
    title: 'Conditional',
    summary: 'Some risks need owner review before release approval.',
  },
  blocked: {
    color: '#ff4d4f',
    tag: 'red',
    icon: <CloseCircleOutlined />,
    title: 'Blocked',
    summary: 'A blocking run, API, defect, or evidence signal requires action.',
  },
}

function asArray(value) {
  return Array.isArray(value) ? value : []
}

function normalizeTag(tag) {
  return String(tag || '').replace(/^@/, '').trim()
}

function caseIdFromText(...parts) {
  const text = parts.flat().filter(Boolean).join(' ')
  const match = text.match(/\b(SIT-TC-[A-Z]+-[A-Z]+-\d{3})\b/i)
  return match ? match[1].toUpperCase() : null
}

function caseShort(caseId) {
  const match = String(caseId || '').match(/-(\d{3})$/)
  return match ? match[1] : null
}

function requirementKey(caseId) {
  if (!caseId) return 'UNTRACEABLE'
  return caseId.replace(/-\d{3}$/, '')
}

function cleanDisplayTitle(value) {
  const text = String(value || '').trim()
  if (!text) return ''
  const slashIndex = text.indexOf(' / ')
  if (slashIndex >= 0) {
    const right = text.slice(slashIndex + 3).trim()
    if (right) return right
  }
  return text
}

function layerForTags(tags) {
  const t = tags.map(normalizeTag).map(s => s.toLowerCase())
  if (t.includes('mixed') || t.includes('api_first_ui') || t.includes('api_ui_mixed')) return 'Mixed'
  const hasApi = t.includes('api')
  const hasUi = t.includes('ui')
  if (hasApi && hasUi) return 'Mixed'
  if (hasApi) return 'API'
  if (hasUi) return 'UI'
  return 'Functional'
}

function mergeLayer(left, right) {
  if (left === right) return left
  const values = new Set([left, right])
  if (values.has('Mixed')) return 'Mixed'
  if (values.has('API') && values.has('UI')) return 'Mixed'
  if (values.has('API')) return 'API'
  if (values.has('UI')) return 'UI'
  return left || right || 'Functional'
}

function businessArea(caseId, featureName) {
  if (/AUTH/i.test(caseId || featureName || '')) return 'Authentication'
  if (/TKT|ticket|order/i.test(caseId || featureName || '')) return 'Ticketing'
  if (/PAY|payment/i.test(caseId || featureName || '')) return 'Payment'
  return 'Product flow'
}

function evidenceForCase(evidence, caseId) {
  const cases = evidence?.cases || {}
  const shortId = caseShort(caseId)
  if (shortId && cases[shortId]) return cases[shortId]
  return Object.values(cases).find(item => item?.case_id === caseId) || null
}

function latestRunTime(run) {
  if (!run) return ''
  return run.finished_at || run.started_at || ''
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).replace('T', ' ').slice(0, 19)
  return date.toLocaleString()
}

function buildRows(featuresPayload, runDetails, evidencePayload, flakyPayload) {
  const latestByCase = new Map()
  const bugsByCase = new Map()

  runDetails.forEach(detail => {
    asArray(detail?.scenarios).forEach(scenario => {
      const caseId = caseIdFromText(scenario.name, scenario.tags)
      if (!caseId) return
      if (!latestByCase.has(caseId)) {
        latestByCase.set(caseId, {
          runId: detail.id,
          status: scenario.status || 'not_run',
          duration: scenario.duration_s,
          error: scenario.error_msg,
          timestamp: latestRunTime(detail),
        })
      }
      const existingBugCount = bugsByCase.get(caseId) || 0
      bugsByCase.set(caseId, existingBugCount + asArray(scenario.bugs).length)
    })
  })

  const flakyByCase = new Map()
  asArray(flakyPayload?.flaky_tests).forEach(item => {
    const caseId = caseIdFromText(item.name, item.feature)
    if (caseId) flakyByCase.set(caseId, item)
  })

  const merged = new Map()

  asArray(featuresPayload?.features).forEach(feature => {
    asArray(feature.scenarios).forEach((scenario, index) => {
      const tags = asArray(scenario.tags).map(normalizeTag)
      const caseId = caseIdFromText(scenario.name, tags) || `UNTRACEABLE-${feature.file}-${index}`
      const latest = latestByCase.get(caseId) || { status: 'not_run' }
      const evidence = evidenceForCase(evidencePayload, caseId)
      const flaky = flakyByCase.get(caseId)
      const bugCount = bugsByCase.get(caseId) || 0
      const layer = layerForTags(tags)
      const area = businessArea(caseId, feature.feature)
      const displayFeature = cleanDisplayTitle(feature.feature)

      const row = {
        key: caseId,
        caseId,
        requirement: requirementKey(caseId),
        area,
        featureFile: feature.file,
        feature: displayFeature,
        rawFeature: feature.feature,
        scenario: scenario.name,
        tags,
        layer,
        automation: 'Automated',
        latestStatus: latest.status || 'not_run',
        latestRunId: latest.runId,
        latestRunAt: latest.timestamp,
        duration: latest.duration,
        evidence,
        evidenceReady: Boolean(evidence?.synced || evidence?.shots > 0),
        bugCount,
        flaky,
        flakinessRate: flaky?.flakiness_rate || 0,
      }

      if (!merged.has(caseId)) {
        merged.set(caseId, row)
        return
      }

      const existing = merged.get(caseId)
      merged.set(caseId, {
        ...existing,
        layer: mergeLayer(existing.layer, row.layer),
        tags: Array.from(new Set([...existing.tags, ...row.tags])),
        bugCount: Math.max(existing.bugCount, row.bugCount),
        evidence: existing.evidence || row.evidence,
        evidenceReady: existing.evidenceReady || row.evidenceReady,
        flakinessRate: Math.max(existing.flakinessRate, row.flakinessRate),
        flaky: existing.flaky || row.flaky,
      })
    })
  })

  return Array.from(merged.values())
}

function buildReleaseGate(rows, runs, apiMonitor) {
  const latestRun = asArray(runs)[0]
  const validRun = asArray(runs).find(run => (run.total || 0) > 0)
  const apiSummary = apiMonitor?.summary || {}
  const failedCases = rows.filter(row => row.latestStatus === 'failed').length
  const erroredCases = rows.filter(row => row.latestStatus === 'error').length
  const notRunCases = rows.filter(row => row.latestStatus === 'not_run').length
  const missingEvidence = rows.filter(row => !row.evidenceReady).length
  const flakyCases = rows.filter(row => row.flakinessRate >= 25).length
  const linkedBugs = rows.reduce((sum, row) => sum + row.bugCount, 0)
  const apiDown = apiSummary.down || 0
  const apiDegraded = apiSummary.degraded || 0

  const blockers = []
  const warnings = []

  if (latestRun?.status === 'error' && (latestRun.total || 0) === 0) {
    blockers.push('Latest test run ended before collecting scenarios')
  }
  if (failedCases > 0 || erroredCases > 0) {
    blockers.push(`${failedCases + erroredCases} case(s) failed or errored in recent execution`)
  }
  if (apiDown > 0) {
    blockers.push(`${apiDown} monitored API endpoint(s) are down`)
  }
  if (linkedBugs > 0) {
    warnings.push(`${linkedBugs} linked defect(s) still require triage`)
  }
  if (apiDegraded > 0) {
    warnings.push(`${apiDegraded} monitored API endpoint(s) are degraded`)
  }
  if (missingEvidence > 0) {
    warnings.push(`${missingEvidence} traceable case(s) have no synced evidence yet`)
  }
  if (notRunCases > 0) {
    warnings.push(`${notRunCases} traceable case(s) have no recent execution result`)
  }
  if (flakyCases > 0) {
    warnings.push(`${flakyCases} case(s) show flaky behavior`)
  }

  let decision = 'ready'
  if (blockers.length > 0) decision = 'blocked'
  else if (warnings.length > 0) decision = 'conditional'

  return {
    decision,
    blockers,
    warnings,
    latestRun,
    validRun,
    failedCases,
    erroredCases,
    notRunCases,
    missingEvidence,
    flakyCases,
    linkedBugs,
    apiDown,
    apiDegraded,
  }
}

function scorePriority(row, gate) {
  let score = 0
  const reasons = []

  if (row.latestStatus === 'failed') {
    score += 40
    reasons.push('latest failure')
  } else if (row.latestStatus === 'error') {
    score += 35
    reasons.push('execution error')
  } else if (row.latestStatus === 'not_run') {
    score += 16
    reasons.push('not recently run')
  } else if (row.latestStatus === 'skipped') {
    score += 12
    reasons.push('skipped')
  }

  if (!row.evidenceReady) {
    score += 14
    reasons.push('evidence gap')
  }
  if (row.bugCount > 0) {
    score += Math.min(30, row.bugCount * 15)
    reasons.push('linked defect')
  }
  if (row.flakinessRate > 0) {
    score += Math.min(30, Math.round(row.flakinessRate))
    reasons.push(`${row.flakinessRate}% flaky`)
  }
  if (row.layer === 'Mixed') {
    score += 10
    reasons.push('cross-layer flow')
  }
  if (row.area === 'Authentication' || row.area === 'Ticketing' || row.area === 'Payment') {
    score += 8
    reasons.push(`${row.area.toLowerCase()} criticality`)
  }
  if ((gate.apiDown > 0 || gate.apiDegraded > 0) && (row.layer === 'API' || row.layer === 'Mixed')) {
    score += 8
    reasons.push('API health signal')
  }

  const priority = score >= 70 ? 'High' : score >= 40 ? 'Medium' : 'Low'
  return { ...row, score, priority, reasons }
}

function percent(part, total) {
  if (!total) return 0
  return Math.round((part / total) * 100)
}

function statusTag(status) {
  const meta = STATUS_META[status] || STATUS_META.not_run
  return <Tag color={meta.color}>{meta.label}</Tag>
}

function priorityTag(priority) {
  const color = priority === 'High' ? 'red' : priority === 'Medium' ? 'gold' : 'green'
  return <Tag color={color}>{priority}</Tag>
}

export default function QADecisionCenterPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const [data, setData] = useState({
    features: null,
    runs: [],
    runDetails: [],
    evidence: null,
    flaky: null,
    apiMonitor: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [features, runs, evidence, flaky, apiMonitor] = await Promise.all([
        listFeatures(projectKey),
        listRuns(projectKey),
        getEvidenceStatus(projectKey),
        fetchFlakyTests(20, projectKey),
        fetchApiMonitorEndpoints(projectKey),
      ])
      const detailTargets = asArray(runs).slice(0, 10)
      const runDetails = await Promise.all(
        detailTargets.map(run => getRunDetail(run.id).catch(() => null)),
      )
      setData({
        features,
        runs: asArray(runs),
        runDetails: runDetails.filter(Boolean),
        evidence,
        flaky,
        apiMonitor,
      })
    } catch (exc) {
      setError(exc?.message || String(exc))
    } finally {
      setLoading(false)
    }
  }, [projectKey])

  useEffect(() => {
    load()
  }, [load])

  const rows = useMemo(
    () => buildRows(data.features, data.runDetails, data.evidence, data.flaky),
    [data.features, data.runDetails, data.evidence, data.flaky],
  )
  const gate = useMemo(
    () => buildReleaseGate(rows, data.runs, data.apiMonitor),
    [rows, data.runs, data.apiMonitor],
  )
  const decisionMeta = DECISION_META[gate.decision]
  const priorityRows = useMemo(
    () => rows.map(row => scorePriority(row, gate)).sort((a, b) => b.score - a.score),
    [rows, gate],
  )

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>
  }

  if (error) {
    return (
      <Alert
        type="error"
        message="QA Decision Center could not load"
        description={error}
        action={<Button icon={<ReloadOutlined />} onClick={load}>Retry</Button>}
      />
    )
  }

  const totalCases = rows.length
  const traceableCases = rows.filter(row => !row.caseId.startsWith('UNTRACEABLE')).length
  const evidenceReady = rows.filter(row => row.evidenceReady).length
  const automatedCases = rows.filter(row => row.automation === 'Automated').length
  const passedCases = rows.filter(row => row.latestStatus === 'passed').length
  const requirements = new Set(rows.map(row => row.requirement)).size
  const apiSummary = data.apiMonitor?.summary || {}

  const rtmColumns = [
    {
      title: 'Requirement',
      dataIndex: 'requirement',
      width: 150,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{row.area}</Text>
        </Space>
      ),
    },
    {
      title: 'Test case',
      dataIndex: 'caseId',
      width: 190,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Text code>{value}</Text>
          <Tooltip title={row.scenario}>
            <Text type="secondary" style={{ fontSize: 12 }}>{row.feature}</Text>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: 'Layer',
      dataIndex: 'layer',
      width: 100,
      filters: [
        { text: 'Mixed', value: 'Mixed' },
        { text: 'API', value: 'API' },
        { text: 'UI', value: 'UI' },
        { text: 'Functional', value: 'Functional' },
      ],
      onFilter: (value, row) => row.layer === value,
      render: value => <Tag color={value === 'Mixed' ? 'purple' : value === 'API' ? 'blue' : 'cyan'}>{value}</Tag>,
    },
    {
      title: 'Automation',
      dataIndex: 'automation',
      width: 115,
      render: value => <Tag color="geekblue">{value}</Tag>,
    },
    {
      title: 'Latest result',
      dataIndex: 'latestStatus',
      width: 135,
      filters: [
        { text: 'Passed', value: 'passed' },
        { text: 'Failed', value: 'failed' },
        { text: 'Errored', value: 'error' },
        { text: 'Not run', value: 'not_run' },
      ],
      onFilter: (value, row) => row.latestStatus === value,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          {statusTag(value)}
          {row.latestRunId && <Text type="secondary" style={{ fontSize: 12 }}>Run #{row.latestRunId}</Text>}
        </Space>
      ),
    },
    {
      title: 'Evidence',
      key: 'evidence',
      width: 130,
      filters: [
        { text: 'Ready', value: 'ready' },
        { text: 'Missing', value: 'missing' },
      ],
      onFilter: (value, row) => value === 'ready' ? row.evidenceReady : !row.evidenceReady,
      render: (_, row) => row.evidenceReady ? (
        <Tooltip title={`${row.evidence?.status || 'Synced'} / ${row.evidence?.shots || 0} screenshot(s)`}>
          <Tag color="green">Evidence ready</Tag>
        </Tooltip>
      ) : <Tag>Missing</Tag>,
    },
    {
      title: 'Defects',
      dataIndex: 'bugCount',
      width: 90,
      sorter: (a, b) => a.bugCount - b.bugCount,
      render: value => value > 0 ? <Tag color="red">{value}</Tag> : <Text type="secondary">0</Text>,
    },
  ]

  const priorityColumns = [
    {
      title: 'Priority',
      dataIndex: 'priority',
      width: 100,
      filters: [
        { text: 'High', value: 'High' },
        { text: 'Medium', value: 'Medium' },
        { text: 'Low', value: 'Low' },
      ],
      onFilter: (value, row) => row.priority === value,
      render: priorityTag,
    },
    {
      title: 'Case',
      dataIndex: 'caseId',
      width: 190,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Text code>{value}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{row.area} / {row.layer}</Text>
        </Space>
      ),
    },
    {
      title: 'Score',
      dataIndex: 'score',
      width: 120,
      sorter: (a, b) => a.score - b.score,
      render: value => <Progress percent={Math.min(100, value)} size="small" status={value >= 70 ? 'exception' : 'normal'} />,
    },
    {
      title: 'Signals',
      dataIndex: 'reasons',
      render: reasons => (
        <Space size={[4, 4]} wrap>
          {reasons.length ? reasons.map(reason => <Tag key={reason}>{reason}</Tag>) : <Text type="secondary">No elevated signal</Text>}
        </Space>
      ),
    },
    {
      title: 'Latest',
      dataIndex: 'latestStatus',
      width: 125,
      render: statusTag,
    },
  ]

  return (
    <div>
      <Space align="start" style={{ width: '100%', justifyContent: 'space-between', marginBottom: 18 }}>
        <div>
          <Title level={2} style={{ marginBottom: 4 }}>QA Decision Center</Title>
          <Paragraph type="secondary" style={{ marginBottom: 0, maxWidth: 820 }}>
            <Tag style={{ marginRight: 6 }}>{projectName}</Tag>
            RTM coverage, release readiness, and risk prioritization built from current run, evidence, flaky, and API monitor data.
          </Paragraph>
        </div>
        <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
      </Space>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 18 }}
        message={`${projectName} release decision context`}
        description="This view consolidates regression coverage, API plus UI execution, synced evidence, ZenTao defects, flaky signals, and monitored endpoint health for the selected project."
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card variant="borderless" style={{ minHeight: 190 }}>
            <Space align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
              <Space direction="vertical" size={2}>
                <Text type="secondary">Release readiness</Text>
                <Space>
                  <span style={{ color: decisionMeta.color, fontSize: 28 }}>{decisionMeta.icon}</span>
                  <Title level={3} style={{ margin: 0 }}>{decisionMeta.title}</Title>
                </Space>
              </Space>
              <Tag color={decisionMeta.tag}>Gate</Tag>
            </Space>
            <Paragraph style={{ marginTop: 14, marginBottom: 10 }}>{decisionMeta.summary}</Paragraph>
            <Space direction="vertical" size={4}>
              {[...gate.blockers, ...gate.warnings].slice(0, 3).map(item => (
                <Text key={item} style={{ fontSize: 12 }}><WarningOutlined style={{ color: '#faad14' }} /> {item}</Text>
              ))}
              {gate.blockers.length + gate.warnings.length === 0 && (
                <Text type="secondary" style={{ fontSize: 12 }}>No open gate findings.</Text>
              )}
            </Space>
          </Card>
        </Col>
        <Col xs={24} md={16}>
          <Row gutter={[16, 16]}>
            <Col xs={12} lg={6}>
              <Card variant="borderless">
                <Statistic title="Traceability" value={percent(traceableCases, totalCases)} suffix="%" prefix={<FileSearchOutlined />} />
                <Progress percent={percent(traceableCases, totalCases)} size="small" />
              </Card>
            </Col>
            <Col xs={12} lg={6}>
              <Card variant="borderless">
                <Statistic title="Evidence Ready" value={percent(evidenceReady, totalCases)} suffix="%" prefix={<AuditOutlined />} />
                <Progress percent={percent(evidenceReady, totalCases)} size="small" strokeColor="#52c41a" />
              </Card>
            </Col>
            <Col xs={12} lg={6}>
              <Card variant="borderless">
                <Statistic title="Automated Cases" value={automatedCases} prefix={<ExperimentOutlined />} />
                <Text type="secondary" style={{ fontSize: 12 }}>{requirements} requirement group(s)</Text>
              </Card>
            </Col>
            <Col xs={12} lg={6}>
              <Card variant="borderless">
                <Statistic title="Recent Passed" value={passedCases} prefix={<CheckCircleOutlined />} />
                <Text type="secondary" style={{ fontSize: 12 }}>{totalCases} traceable case(s)</Text>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={8}>
          <Card
            variant="borderless"
            title={<Space><SafetyCertificateOutlined /> Gate findings</Space>}
            style={{ minHeight: 260 }}
          >
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Badge status={gate.blockers.length ? 'error' : 'success'} text={`${gate.blockers.length} blocker(s)`} />
              <Badge status={gate.warnings.length ? 'warning' : 'success'} text={`${gate.warnings.length} warning(s)`} />
              <Badge status={apiSummary.down ? 'error' : apiSummary.degraded ? 'warning' : 'success'} text={`${apiSummary.down || 0} API down / ${apiSummary.degraded || 0} degraded`} />
              <Badge status={gate.flakyCases ? 'warning' : 'success'} text={`${gate.flakyCases} flaky case(s)`} />
              <Badge status={gate.missingEvidence ? 'warning' : 'success'} text={`${gate.missingEvidence} evidence gap(s)`} />
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            variant="borderless"
            title={<Space><ApiOutlined /> API health input</Space>}
            style={{ minHeight: 260 }}
          >
            <Row gutter={12}>
              <Col span={12}><Statistic title="Up" value={apiSummary.up || 0} valueStyle={{ color: '#52c41a' }} /></Col>
              <Col span={12}><Statistic title="Down" value={apiSummary.down || 0} valueStyle={{ color: '#ff4d4f' }} /></Col>
              <Col span={12}><Statistic title="Degraded" value={apiSummary.degraded || 0} valueStyle={{ color: '#faad14' }} /></Col>
              <Col span={12}><Statistic title="Skipped" value={apiSummary.skipped || 0} /></Col>
            </Row>
            <Text type="secondary" style={{ fontSize: 12 }}>
              API monitor contributes to prioritization for API and Mixed cases.
            </Text>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            variant="borderless"
            title={<Space><ThunderboltOutlined /> {projectName} focus</Space>}
            style={{ minHeight: 260 }}
          >
            <Space direction="vertical" size={8}>
              <Text><CheckCircleOutlined style={{ color: '#52c41a' }} /> Coverage: selected project scenarios, runs, and evidence stay traceable.</Text>
              <Text><CheckCircleOutlined style={{ color: '#52c41a' }} /> Release triage: failures, defects, missing evidence, and skipped cases are ranked with visible reasons.</Text>
              <Text><CheckCircleOutlined style={{ color: '#52c41a' }} /> Integration signals: API health, project defects, and ZenTao state feed the same gate decision.</Text>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card
        variant="borderless"
        title={<Space><AuditOutlined /> RTM Coverage Matrix</Space>}
        extra={<Text type="secondary">{totalCases} case(s)</Text>}
        style={{ marginBottom: 16 }}
      >
        {rows.length ? (
          <Table
            size="small"
            rowKey="key"
            columns={rtmColumns}
            dataSource={rows}
            pagination={{ pageSize: 8, showSizeChanger: true }}
          />
        ) : (
          <Empty description="No feature or scenario data available" />
        )}
      </Card>

      <Card
        variant="borderless"
        title={<Space><BugOutlined /> {projectName} Risk Prioritization</Space>}
        extra={<Text type="secondary">Explainable scoring / QA reviewed</Text>}
      >
        <Table
          size="small"
          rowKey="key"
          columns={priorityColumns}
          dataSource={priorityRows}
          pagination={{ pageSize: 8, showSizeChanger: true }}
        />
      </Card>
    </div>
  )
}
