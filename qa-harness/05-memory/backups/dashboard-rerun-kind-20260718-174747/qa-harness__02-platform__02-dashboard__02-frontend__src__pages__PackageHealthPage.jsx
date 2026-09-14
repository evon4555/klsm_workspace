import { useEffect, useState, useCallback } from 'react'
import {
  Typography, Card, Row, Col, Table, Tag, Button, Space,
  Statistic, Alert, Empty, Tooltip, Descriptions, List, message,
} from 'antd'
import {
  ReloadOutlined, FolderOpenOutlined, CheckCircleFilled,
  MinusCircleOutlined, ExclamationCircleFilled, StopFilled,
  FileWordOutlined, FileTextOutlined, FileExcelOutlined,
  PlayCircleOutlined, FileSyncOutlined, WarningFilled,
} from '@ant-design/icons'
import {
  fetchQualityPackages, fetchQualityPackage,
  openWorkspaceFile, generateReviewDocx, validatePackageXlsx,
  fetchPackageExecutions,
} from '../api'

const { Title, Text, Paragraph } = Typography

// ---------------------------------------------------------------------------
// Per-status visual mapping. Mirrors the scanner's status enum:
//   pass     - all required artifacts present
//   partial  - some present, some missing
//   blocked  - cannot start because an upstream gate (Step 3.5 sign-off) blocks it
//   empty    - nothing in this stage yet
// ---------------------------------------------------------------------------
const STATUS = {
  pass:    { color: '#52c41a', tag: 'green',  icon: <CheckCircleFilled />,       short: 'PASS' },
  partial: { color: '#faad14', tag: 'orange', icon: <ExclamationCircleFilled />, short: 'PART' },
  blocked: { color: '#ff4d4f', tag: 'red',    icon: <StopFilled />,              short: 'GATE' },
  empty:   { color: '#bfbfbf', tag: 'default',icon: <MinusCircleOutlined />,     short: '—'    },
}

const VERDICT = {
  complete:     { color: 'green',  label: 'Complete' },
  'in-progress':{ color: 'gold',   label: 'In progress' },
  'not-started':{ color: 'default',label: 'Not started' },
}

function StageBadge({ stage }) {
  const meta = STATUS[stage.status] || STATUS.empty
  return (
    <Space size={2} align="center">
      <Tooltip title={`${stage.label}: ${stage.summary}`}>
        <Tag color={meta.tag} style={{ minWidth: 56, textAlign: 'center', margin: 0 }}>
          <Space size={4}>
            {meta.icon}
            {meta.short}
          </Space>
        </Tag>
      </Tooltip>
      {stage.gate_note && (
        <Tooltip title={stage.gate_note}>
          <WarningFilled style={{ color: '#fa8c16', fontSize: 13 }} />
        </Tooltip>
      )}
    </Space>
  )
}

// File extension → icon
function fileIcon(name) {
  const n = name.toLowerCase()
  if (n.endsWith('.docx')) return <FileWordOutlined style={{ color: '#1677ff' }} />
  if (n.endsWith('.xlsx')) return <FileExcelOutlined style={{ color: '#52c41a' }} />
  return <FileTextOutlined style={{ color: '#595959' }} />
}

export default function PackageHealthPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [validatorBusy, setValidatorBusy] = useState(false)
  const [validatorResult, setValidatorResult] = useState(null)
  const [docxBusyPath, setDocxBusyPath] = useState(null)
  const [execBusy, setExecBusy] = useState(false)
  const [execResult, setExecResult] = useState(null)

  const loadPackages = useCallback(async (project, selectedId = null) => {
    setLoading(true)
    setError(null)
    try {
      const json = await fetchQualityPackages(project)
      setData(json)
      // re-fetch detail if a row was previously selected
      if (selectedId) {
        const updated = json.packages.find(p => p.id === selectedId)
        if (updated) {
          setDetail(updated)
        }
      }
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  const refresh = useCallback(() => {
    return loadPackages(projectKey, selected)
  }, [loadPackages, projectKey, selected])

  useEffect(() => {
    setSelected(null)
    setDetail(null)
    setValidatorResult(null)
    setExecResult(null)
    loadPackages(projectKey, null)
  }, [loadPackages, projectKey])

  async function pickRow(pkg) {
    setSelected(pkg.id)
    setValidatorResult(null)
    setExecResult(null)
    setDetailLoading(true)
    try {
      const d = await fetchQualityPackage(pkg.id)
      setDetail(d)
    } catch (e) {
      setDetail({ error: e.message || String(e), ...pkg })
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleShowExecutions() {
    if (!selected) return
    setExecBusy(true)
    try {
      const r = await fetchPackageExecutions(selected)
      setExecResult(r)
    } catch (e) {
      message.error(e.message || String(e))
    } finally {
      setExecBusy(false)
    }
  }

  async function handleOpen(relPath) {
    try {
      const r = await openWorkspaceFile(relPath)
      if (r.ok) {
        message.success(`Opened: ${relPath.split('/').pop()}`)
      } else {
        message.error(r.error || 'open failed')
      }
    } catch (e) {
      message.error(e.message || String(e))
    }
  }

  async function handleGenerateDocx(relMdPath) {
    setDocxBusyPath(relMdPath)
    try {
      const r = await generateReviewDocx(relMdPath)
      if (r.ok) {
        message.success(`Generated: ${r.docx_path.split('/').pop()}`)
        // re-fetch detail so the new docx shows up in the file list
        if (selected) {
          const d = await fetchQualityPackage(selected)
          setDetail(d)
        }
      } else {
        message.error(r.error || 'generate failed')
      }
    } catch (e) {
      message.error(e.message || String(e))
    } finally {
      setDocxBusyPath(null)
    }
  }

  async function handleRunValidator() {
    if (!selected) return
    setValidatorBusy(true)
    setValidatorResult(null)
    try {
      const r = await validatePackageXlsx(selected)
      setValidatorResult(r)
      if (r.ok) message.success(r.summary)
    } catch (e) {
      message.error(e.message || String(e))
    } finally {
      setValidatorBusy(false)
    }
  }

  // For a given stage's file list, also include the sibling .docx for any .md
  // that has one. Returns [{path, isDocx, mdSibling}].
  function annotateFiles(files) {
    const set = new Set(files || [])
    return (files || []).map(p => {
      const isDocx = p.toLowerCase().endsWith('.docx')
      const isMd = p.toLowerCase().endsWith('.md')
      const docxSibling = isMd ? p.slice(0, -3) + '.docx' : null
      const hasDocxSibling = docxSibling && set.has(docxSibling)
      return { path: p, isDocx, isMd, docxSibling, hasDocxSibling }
    })
  }

  // -----------------------------------------------------------------------
  // Build table columns from backend stage_defs + verdict + next action.
  // -----------------------------------------------------------------------
  const stageDefs = data?.stage_defs || []
  const columns = [
    {
      title: 'Module / Date',
      dataIndex: 'title',
      fixed: 'left',
      width: 260,
      render: (_, r) => (
        <Space direction="vertical" size={0}>
          <Text strong>{r.module}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {r.date_slug} · {r.subproject}
          </Text>
        </Space>
      ),
    },
    ...stageDefs.map((s, idx) => ({
      title: <Tooltip title={s.id}><Text style={{ fontSize: 12 }}>{idx + 1}. {s.label}</Text></Tooltip>,
      key: s.id,
      width: 110,
      align: 'center',
      render: (_, r) => {
        const stage = (r.stages || []).find(x => x.id === s.id)
        if (!stage) return <Text type="secondary">—</Text>
        return <StageBadge stage={stage} />
      },
    })),
    {
      title: 'Verdict',
      dataIndex: 'verdict',
      width: 120,
      render: (v) => {
        const m = VERDICT[v] || { color: 'default', label: v }
        return <Tag color={m.color}>{m.label}</Tag>
      },
    },
    {
      title: 'Next action',
      dataIndex: 'next_action',
      ellipsis: true,
      render: (v) => v ? <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text> : <Text type="secondary">—</Text>,
    },
  ]

  const packages = data?.packages || []
  const verdictCounts = packages.reduce((acc, p) => {
    acc[p.verdict] = (acc[p.verdict] || 0) + 1
    return acc
  }, {})

  return (
    <div>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space align="center">
            <FolderOpenOutlined style={{ fontSize: 24, color: '#1677ff' }} />
            <Title level={3} style={{ margin: 0 }}>Package Health</Title>
            <Tag color={activeProject?.kind === 'baseline' ? 'blue' : 'green'}>
              {projectName}
            </Tag>
          </Space>
          <Paragraph type="secondary" style={{ margin: '4px 0 0 32px' }}>
            Live scan of every requirement package under{' '}
            <Text code>{projectKey}/01-requirements/</Text>.
            Each row is one date package; each column is one workflow stage.
            The filesystem IS the database — refresh to re-scan.
          </Paragraph>
        </Col>
        <Col>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={refresh}
          >
            Refresh
          </Button>
        </Col>
      </Row>

      {/* Top summary cards */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="Packages" value={packages.length} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Complete"   value={verdictCounts.complete    || 0} valueStyle={{ color: '#52c41a' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="In progress" value={verdictCounts['in-progress'] || 0} valueStyle={{ color: '#faad14' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Not started" value={verdictCounts['not-started'] || 0} valueStyle={{ color: '#bfbfbf' }} /></Card>
        </Col>
      </Row>

      {error && (
        <Alert
          type="error"
          showIcon
          message="Scan failed"
          description={error}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Main grid */}
      <Card
        title={
          <Space>
            <Text strong>Packages × Stages</Text>
            {data?.scanned_at && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                scanned {new Date(data.scanned_at).toLocaleString()}
              </Text>
            )}
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Table
          rowKey="id"
          dataSource={packages}
          columns={columns}
          pagination={false}
          loading={loading}
          size="middle"
          scroll={{ x: 1000 }}
          onRow={(record) => ({
            onClick: () => pickRow(record),
            style: {
              cursor: 'pointer',
              background: selected === record.id ? '#e6f4ff' : undefined,
            },
          })}
          locale={{ emptyText: <Empty description="No packages found" /> }}
        />
      </Card>

      {/* Drill-down */}
      {selected && (
        <Card
          title={
            <Space>
              <Text strong>Drill-down</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>{detail?.id || selected}</Text>
            </Space>
          }
          extra={
            <Space>
              <Button
                size="small"
                icon={<PlayCircleOutlined />}
                loading={validatorBusy}
                onClick={handleRunValidator}
              >
                Run xlsx validator
              </Button>
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={execBusy}
                onClick={handleShowExecutions}
              >
                Show linked runs
              </Button>
            </Space>
          }
          loading={detailLoading}
        >
          {detail?.error && (
            <Alert type="error" showIcon message={detail.error} style={{ marginBottom: 16 }} />
          )}
          {detail && !detail.error && (
            <>
              <Descriptions size="small" column={3} style={{ marginBottom: 16 }}>
                <Descriptions.Item label="Project">{detail.project}</Descriptions.Item>
                <Descriptions.Item label="Subproject">{detail.subproject}</Descriptions.Item>
                <Descriptions.Item label="Module">{detail.module}</Descriptions.Item>
                <Descriptions.Item label="Date">{detail.date_slug}</Descriptions.Item>
                <Descriptions.Item label="Verdict">
                  <Tag color={(VERDICT[detail.verdict] || {}).color}>{(VERDICT[detail.verdict] || {}).label || detail.verdict}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Next">{detail.next_action || '—'}</Descriptions.Item>
              </Descriptions>

              {execResult && (
                <Alert
                  type={execResult.runs && execResult.runs.length > 0 ? 'info' : 'warning'}
                  showIcon
                  message={
                    `Linked runs: ${execResult.runs?.length || 0} run(s) exercised this package's ` +
                    `${execResult.case_count || 0} case ID(s)` +
                    (execResult.note ? ` — ${execResult.note}` : '')
                  }
                  description={
                    (execResult.runs && execResult.runs.length > 0) ? (
                      <Table
                        size="small"
                        rowKey="id"
                        pagination={false}
                        dataSource={execResult.runs}
                        columns={[
                          { title: 'Run', dataIndex: 'id', width: 70, render: v => <Text code>#{v}</Text> },
                          { title: 'Started', dataIndex: 'started_at', render: v => v ? new Date(v).toLocaleString() : '—', width: 170 },
                          { title: 'Env', dataIndex: 'env', width: 60 },
                          {
                            title: 'Run verdict', dataIndex: 'status', width: 110,
                            render: v => <Tag color={v === 'passed' ? 'green' : v === 'failed' ? 'red' : 'default'}>{v}</Tag>,
                          },
                          {
                            title: 'Scope match', key: 'scope', width: 200,
                            render: (_, r) => (
                              <Space size={4}>
                                <Tag color="blue">{r.scope_matched} matched</Tag>
                                {r.scope_passed > 0 && <Tag color="green">{r.scope_passed} P</Tag>}
                                {r.scope_failed > 0 && <Tag color="red">{r.scope_failed} F</Tag>}
                                {r.scope_errored > 0 && <Tag color="volcano">{r.scope_errored} E</Tag>}
                                {r.scope_skipped > 0 && <Tag color="default">{r.scope_skipped} S</Tag>}
                              </Space>
                            ),
                          },
                          { title: 'Run total', dataIndex: 'total_in_run', width: 90 },
                        ]}
                      />
                    ) : null
                  }
                  style={{ marginBottom: 16 }}
                />
              )}

              {validatorResult && (
                <Alert
                  type={validatorResult.ok && (validatorResult.results || []).every(r => r.ok) ? 'success' : 'warning'}
                  showIcon
                  message={`xlsx validator: ${validatorResult.summary}`}
                  description={
                    <List
                      size="small"
                      dataSource={validatorResult.results || []}
                      renderItem={(r) => (
                        <List.Item style={{ padding: '4px 0' }}>
                          <Space direction="vertical" size={2} style={{ width: '100%' }}>
                            <Space>
                              {r.ok
                                ? <Tag color="green">PASS</Tag>
                                : <Tag color="red">FAIL ({r.exit_code})</Tag>}
                              <Text code style={{ fontSize: 12 }}>{r.file.split('/').pop()}</Text>
                            </Space>
                            {!r.ok && r.output && (
                              <pre style={{ fontSize: 11, color: '#999', margin: 0, whiteSpace: 'pre-wrap' }}>
                                {r.output}
                              </pre>
                            )}
                          </Space>
                        </List.Item>
                      )}
                    />
                  }
                  style={{ marginBottom: 16 }}
                />
              )}

              <Row gutter={[16, 16]}>
                {(detail.stages || []).map(stage => {
                  const meta = STATUS[stage.status] || STATUS.empty
                  const annotated = annotateFiles(stage.files)
                  return (
                    <Col key={stage.id} span={8}>
                      <Card
                        size="small"
                        style={{ borderLeft: `4px solid ${meta.color}`, height: '100%' }}
                        title={
                          <Space>
                            <span style={{ color: meta.color }}>{meta.icon}</span>
                            <Text strong>{stage.label}</Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>{stage.id}</Text>
                          </Space>
                        }
                      >
                        <Paragraph style={{ marginBottom: 8, fontSize: 13 }}>
                          {stage.summary}
                        </Paragraph>
                        {stage.gate_note && (
                          <Alert
                            type="warning"
                            showIcon
                            icon={<WarningFilled />}
                            message={stage.gate_note}
                            style={{ marginBottom: 8, padding: '4px 8px', fontSize: 12 }}
                          />
                        )}
                        {annotated.length > 0 && (
                          <List
                            size="small"
                            dataSource={annotated}
                            renderItem={(f) => (
                              <List.Item style={{ padding: '4px 0', fontSize: 12 }}>
                                <Space direction="vertical" size={0} style={{ width: '100%' }}>
                                  <Space size={4}>
                                    {fileIcon(f.path)}
                                    <a
                                      onClick={(e) => { e.preventDefault(); handleOpen(f.path) }}
                                      style={{ fontSize: 12 }}
                                      title={f.path}
                                    >
                                      {f.path.split('/').pop()}
                                    </a>
                                  </Space>
                                  {f.isMd && !f.hasDocxSibling && (
                                    <Button
                                      type="link"
                                      size="small"
                                      icon={<FileSyncOutlined />}
                                      loading={docxBusyPath === f.path}
                                      onClick={() => handleGenerateDocx(f.path)}
                                      style={{ padding: 0, fontSize: 11, height: 'auto' }}
                                    >
                                      Generate review .docx
                                    </Button>
                                  )}
                                </Space>
                              </List.Item>
                            )}
                          />
                        )}
                      </Card>
                    </Col>
                  )
                })}
              </Row>
            </>
          )}
        </Card>
      )}
    </div>
  )
}
