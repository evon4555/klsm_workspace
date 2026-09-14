import { useState } from 'react'
import {
  Table, Tag, Empty, Card, Tooltip, Timeline,
  Button, Modal, Input, Select, message, Space, Spin, Typography,
} from 'antd'
import {
  UnorderedListOutlined, BugOutlined, ExportOutlined, ReloadOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import { openBugForScenario, getCaseHistory } from '../api.js'
import { dashboardTimeValue, formatDashboardTime } from '../utils/time.js'

const { Text } = Typography

const statusColor = {
  passed: 'green',
  failed: 'red',
  // 'error' = scenario crashed before assertion (Playwright timeout,
  // undefined step, fixture exception). Yellow to match the Errored card
  // in KpiCards — semantically "test/infra problem, not product bug".
  error: 'gold',
  skipped: 'default',
  undefined: 'default',
}

// Use the full SIT-TC-... ID as the cross-project key. A trailing numeric key
// is still checked as a legacy fallback for older WestK evidence files.
function caseId(record) {
  if (record?.case_id) return String(record.case_id).toUpperCase()
  const source = `${record?.name || ''} ${record?.tags || ''}`
  const m = source.match(/\b(SIT-TC-[A-Z0-9-]+-\d{3,})\b/i)
  return m ? m[1].toUpperCase() : null
}

function caseEvidenceKeys(record) {
  const full = caseId(record)
  if (!full) return []
  const short = full.match(/-(\d{3,})$/)?.[1]
  return short ? [full, short] : [full]
}

function evidenceRecord(evidenceMap, record) {
  for (const key of caseEvidenceKeys(record)) {
    if (evidenceMap[key]) return evidenceMap[key]
  }
  return null
}

function screenshotCount(rec) {
  if (!rec) return 0
  if (Array.isArray(rec.screenshots)) return rec.screenshots.length
  return Number(rec.screenshot_count ?? rec.shots ?? 0) || 0
}

function screenshotPaths(rec) {
  if (!rec || !Array.isArray(rec.screenshots)) return []
  return rec.screenshots
    .map((shot) => {
      if (!shot) return null
      if (typeof shot === 'string') return shot
      return shot.path || shot.absolute_path || shot.local_path || shot.file || shot.relative_path || shot.url
    })
    .filter(Boolean)
}

function screenshotTooltipTitle(rec, shots, hasScreenshots) {
  if (!hasScreenshots) return 'No screenshot captured for this case'
  const paths = screenshotPaths(rec)
  if (!paths.length) return `${shots} screenshot(s) captured for this case`
  return (
    <div style={{ maxWidth: 620 }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>
        {shots} screenshot(s) captured
      </div>
      {paths.slice(0, 8).map((path, index) => (
        <div key={`${path}-${index}`} style={{ marginTop: index ? 8 : 0 }}>
          <div style={{ color: 'rgba(255,255,255,0.72)', fontSize: 11 }}>
            Screenshot {index + 1}
          </div>
          <code style={{ color: '#fff', whiteSpace: 'normal', wordBreak: 'break-all' }}>
            {path}
          </code>
        </div>
      ))}
      {paths.length > 8 && (
        <div style={{ marginTop: 8, color: 'rgba(255,255,255,0.72)' }}>
          +{paths.length - 8} more screenshot path(s)
        </div>
      )}
    </div>
  )
}

function automationScenario(record) {
  const name = record?.name || ''
  const id = caseId(record)
  if (!id) return name
  return name.replace(new RegExp(`^\\s*${id}\\s*`, 'i'), '').trim() || name
}

function caseDescription(record) {
  return record?.test_case_description || record?.test_case_scenario || automationScenario(record)
}

function testScenarioTooltip(record) {
  return record?.test_case_scenario || 'No test scenario captured'
}

function testCaseDescriptionTooltip(record) {
  return record?.test_case_description || 'No test case description captured'
}

function normalizedTagList(raw) {
  if (Array.isArray(raw)) return raw.map((tag) => String(tag || '').replace(/^@/, '').trim().toLowerCase()).filter(Boolean)
  return String(raw || '')
    .split(',')
    .map((tag) => tag.replace(/^@/, '').trim().toLowerCase())
    .filter(Boolean)
}

function normalizeAutomationType(value) {
  const raw = String(value || '').trim().toLowerCase()
  if (!raw) return null
  if (raw === 'n/a' || raw === 'na' || raw === 'none') return null
  if (raw.includes('mixed') || raw.includes('api + ui') || raw.includes('api/ui')) return 'Mixed'
  if (raw === 'api' || raw.includes(' api') || raw.includes('api ')) return 'API'
  if (raw === 'ui' || raw.includes(' ui') || raw.includes('ui ')) return 'UI'
  if (raw.includes('smoke')) return 'Smoke'
  return value
}

function automationType(record) {
  const fromWorkbook = normalizeAutomationType(record?.automation_type)
  if (fromWorkbook) return fromWorkbook

  const tags = normalizedTagList(record?.tags)
  if (tags.includes('mixed') || tags.includes('api_ui_mixed') || tags.includes('api_first_ui')) return 'Mixed'
  if (tags.includes('api') && tags.includes('ui')) return 'Mixed'
  if (tags.includes('api')) return 'API'
  if (tags.includes('ui')) return 'UI'
  if (tags.includes('smoke')) return 'Smoke'
  return 'N/A'
}

function automationColor(type) {
  if (type === 'API') return 'blue'
  if (type === 'UI') return 'cyan'
  if (type === 'Mixed') return 'purple'
  if (type === 'Smoke') return 'geekblue'
  return 'default'
}

function automationTypeTooltip(record) {
  const loc = record?.automation_location
  const rowStyle = { marginTop: 4, lineHeight: 1.45, fontFamily: 'inherit', color: 'inherit' }
  const labelStyle = { fontWeight: 600 }
  const valueStyle = { overflowWrap: 'anywhere', fontFamily: 'inherit' }
  if (!loc) {
    return (
      <div style={{ maxWidth: 460, fontSize: 12, fontFamily: 'inherit' }}>
        <div style={rowStyle}>
          No automation source location is captured for this scenario.
        </div>
      </div>
    )
  }

  const tags = Array.isArray(loc.tags) ? loc.tags : []
  return (
    <div style={{ maxWidth: 620, fontSize: 12, fontFamily: 'inherit' }}>
      <div style={{ ...rowStyle, marginTop: 6 }}>
        <span style={labelStyle}>Location:</span>{' '}
        <span style={valueStyle}>{loc.absolute_file || loc.file || 'N/A'}</span>
      </div>
      <div style={rowStyle}>
        <span style={labelStyle}>Automation test:</span>{' '}
        <span style={valueStyle}>
          {loc.test_name || loc.scenario || record?.name || 'N/A'}
        </span>
      </div>
      {tags.length > 0 && (
        <div style={rowStyle}>
          <span style={labelStyle}>Tags:</span>{' '}
          <span style={valueStyle}>{tags.join(' ')}</span>
        </div>
      )}
    </div>
  )
}

function automationSuffix(record) {
  const type = automationType(record)
  return type && type !== 'N/A' ? ` / ${type}` : ''
}

const EXECUTION_RESULT_COLOR = { PASS: 'green', FAIL: 'red' }

function executionResult(ev) {
  const explicit = String(ev.execution_result || '').trim().toLowerCase()
  if (explicit === 'pass' || explicit === 'passed') return 'PASS'
  if (explicit === 'fail' || explicit === 'failed') return 'FAIL'

  const status = String(ev.status || '').trim().toLowerCase()
  if (status === 'passed' || status === 'pass') return 'PASS'
  if (['failed', 'fail', 'error', 'errored', 'undefined', 'untested'].includes(status)) return 'FAIL'
  return ''
}

function eventDotColor(ev) {
  if (ev.type === 'behave')   return EXECUTION_RESULT_COLOR[executionResult(ev)] || 'gray'
  return 'gray'
}

function formatTs(iso) {
  return iso ? formatDashboardTime(iso, { withYear: true }) : '(no timestamp)'
}

const RUN_KIND_LABELS = {
  full: 'Full run',
  performance: 'Performance test',
  rerun_single: 'Single rerun',
  rerun_failed: 'Failed-case rerun',
}

function runKindLabel(kind) {
  return RUN_KIND_LABELS[kind] || kind || 'Run'
}

function lastRunSortValue(record) {
  return dashboardTimeValue(record?.last_run_at || record?.run_finished_at || record?.run_started_at)
}

function lastRunTooltip(record) {
  const at = record?.last_run_at || record?.run_finished_at || record?.run_started_at
  return (
    <div style={{ maxWidth: 380, fontSize: 12, fontFamily: 'inherit' }}>
      <div><strong>Latest attempt time</strong></div>
      <div>{formatDashboardTime(at, { withYear: true })}</div>
      <div>Rerun attempts are kept in History.</div>
    </div>
  )
}

function effectiveScenarioStatus(record) {
  const latest = String(record?.last_run_status || '').trim().toLowerCase()
  if (latest && !['skipped', 'undefined', 'untested'].includes(latest)) return latest
  return String(record?.status || '').trim().toLowerCase() || 'unknown'
}

function statusTooltip(record) {
  const selected = String(record?.status || 'unknown').toUpperCase()
  const latest = String(record?.last_run_status || record?.status || 'unknown').toUpperCase()
  const latestRunId = record?.last_run_id || record?.run_id || '?'
  return (
    <div style={{ maxWidth: 360, fontSize: 12, fontFamily: 'inherit' }}>
      <div><strong>Displayed status:</strong> latest executable attempt</div>
      <div>Latest attempt: {latest} in run #{latestRunId}</div>
      <div>Selected full-run status: {selected}</div>
    </div>
  )
}

/**
 * Build the table columns. The "Sync to Excel" column (right after Last Run)
 * joins each scenario to evidenceMap by case ID, showing screenshot
 * availability plus whether the case evidence has been synced into Excel.
 *
 * `openBugFor` is called when the user confirms the "Open Bug" modal for a
 * failed scenario — it pushes the failure into ZenTao via the backend.
 *
 * `rerunOne(scenario)` triggers a single-case rerun attempt and refreshes
 * the selected full run's case-level Last Run metadata.
 */
function buildColumns(evidenceMap, openBugFor, rerunOne, rerunningId,
                      showBugsInBucket, showHistoryFor) {
  return [
    {
      title: 'Case ID',
      key: 'case_id',
      width: 180,
      render: (_, record) => {
        const id = caseId(record)
        return id ? (
          <Tooltip title={testScenarioTooltip(record)}>
            <Text code>{id}</Text>
          </Tooltip>
        ) : (
          <Text type="secondary">N/A</Text>
        )
      },
    },
    {
      title: 'Test Case Description',
      key: 'scenario',
      ellipsis: true,
      render: (_, record) => (
        <Tooltip title={testCaseDescriptionTooltip(record)}>
          <Text>{caseDescription(record)}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Automation Type',
      key: 'automation_type',
      width: 132,
      filters: [
        { text: 'API', value: 'API' },
        { text: 'UI', value: 'UI' },
        { text: 'Mixed', value: 'Mixed' },
      ],
      onFilter: (value, record) => automationType(record) === value,
      render: (_, record) => {
        const type = automationType(record)
        return type === 'N/A' ? (
          <Tooltip title={automationTypeTooltip(record)}>
            <Text type="secondary">N/A</Text>
          </Tooltip>
        ) : (
          <Tooltip title={automationTypeTooltip(record)} placement="left">
            <Tag color={automationColor(type)} style={{ borderRadius: 4, fontWeight: 500, cursor: 'help' }}>
              {type}
            </Tag>
          </Tooltip>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 100,
      filters: [
        { text: 'Passed', value: 'passed' },
        { text: 'Failed', value: 'failed' },
        { text: 'Errored', value: 'error' },
        { text: 'Skipped', value: 'skipped' },
      ],
      onFilter: (value, record) => effectiveScenarioStatus(record) === value,
      render: (_, record) => {
        const s = effectiveScenarioStatus(record)
        return (
          <Tooltip title={statusTooltip(record)}>
            <Tag color={statusColor[s] || 'default'} style={{ borderRadius: 4, fontWeight: 500, cursor: 'help' }}>
              {(s || 'unknown').toUpperCase()}
            </Tag>
          </Tooltip>
        )
      },
    },
    {
      title: 'Last Run',
      key: 'last_run',
      width: 170,
      sorter: (a, b) => lastRunSortValue(a) - lastRunSortValue(b),
      render: (_, record) => {
        const at = record.last_run_at || record.run_finished_at || record.run_started_at
        return (
          <Tooltip title={lastRunTooltip(record)}>
            <Text>{formatDashboardTime(at)}</Text>
          </Tooltip>
        )
      },
    },
    {
      title: 'Sync to Excel',
      key: 'sync',
      width: 134,
      filters: [
        { text: 'Sync Success', value: 'ok' },
        { text: 'Sync Fail', value: 'fail' },
        { text: 'Not synced', value: 'none' },
      ],
      onFilter: (value, record) => {
        const rec = evidenceRecord(evidenceMap, record)
        if (value === 'none') return !rec
        if (value === 'ok') return !!rec && rec.synced
        if (value === 'fail') return !!rec && !rec.synced
        return true
      },
      render: (_, record) => {
        const rec = evidenceRecord(evidenceMap, record)
        const shots = screenshotCount(rec)
        const hasScreenshots = shots > 0
        const screenshotTag = (
          <Tooltip
            styles={{ root: { maxWidth: 660 } }}
            title={screenshotTooltipTitle(rec, shots, hasScreenshots)}
          >
            <Tag
              color={hasScreenshots ? 'green' : 'default'}
              style={{ borderRadius: 4, margin: 0, fontWeight: 500 }}
            >
              {hasScreenshots ? 'Y' : 'N'}
            </Tag>
          </Tooltip>
        )
        if (!rec) {
          return (
            <Space size={4}>
              {screenshotTag}
              <Tooltip title="Not part of any evidence sync yet">
                <Tag style={{ borderRadius: 4, color: '#999', margin: 0 }}>N/A</Tag>
              </Tooltip>
            </Space>
          )
        }
        const when = (rec.synced_at || '').replace('T', ' ')
        return (
          <Space size={4}>
            {screenshotTag}
            <Tooltip
              title={`${rec.status || 'Evidence'} · ${shots} screenshot(s)${when ? ` · ${when}` : ''}`}
            >
              <Tag
                color={rec.synced ? 'green' : 'default'}
                style={{ borderRadius: 4, fontWeight: 500, margin: 0 }}
              >
                {rec.synced ? 'Sync Success' : 'Not synced'}
              </Tag>
            </Tooltip>
          </Space>
        )
        /*
        if (!rec) {
          return (
            <Tooltip title="Not part of any evidence sync yet">
              <Tag style={{ borderRadius: 4, color: '#999' }}>—</Tag>
            </Tooltip>
          )
        }
        const when = (rec.synced_at || '').replace('T', ' ')
        return (
          <Tooltip
            title={`${rec.status} · ${rec.shots} screenshot(s) · ${when}`}
          >
            <Tag
              color={rec.synced ? 'green' : 'default'}
              style={{ borderRadius: 4, fontWeight: 500 }}
            >
              {rec.synced ? 'Sync Success' : 'Sync Fail'}
            </Tag>
          </Tooltip>
        )
        */
      },
    },
    {
      title: 'Rerun',
      key: 'rerun',
      width: 290,
      render: (_, record) => {
        // Three buttons in this column:
        //   - Rerun: always available (passed too — useful for flake checks)
        //   - Open Bug: always available (passed today doesn't mean passed
        //     tomorrow; backend dedupes by exact title within scenario)
        //   - 📜 History: open the execution-result history
        const histBtn = (
          <Tooltip title="Open this case's execution history">
            <Button
              size="small"
              icon={<HistoryOutlined />}
              onClick={() => showHistoryFor(record)}
            />
          </Tooltip>
        )
        const rerunBtn = (
          <Tooltip title="Rerun this case as an audit attempt. The full-run package summary stays selected.">
            <Button
              size="small"
              icon={<ReloadOutlined />}
              loading={rerunningId === record.id}
              onClick={() => rerunOne(record)}
            >
              Rerun
            </Button>
          </Tooltip>
        )
        // Bug button is on EVERY row — passed today doesn't mean passed
        // tomorrow, and the user may want to preemptively track a known
        // flake. Re-clicking with the SAME default title returns the same
        // bug (backend dedup by exact title within the scenario); editing
        // the title creates a new one (multi-bug per scenario).
        const bugCount = (record.bugs || []).length
        const bugBtn = (
          <Tooltip
            title={
              bugCount > 0
                ? `Already has ${bugCount} bug(s); edit title in the modal to file a new one`
                : 'Open a ZenTao bug for this scenario'
            }
          >
            <Button
              size="small"
              type="primary"
              danger
              icon={<BugOutlined />}
              onClick={() => openBugFor(record)}
            >
              Open Bug
            </Button>
          </Tooltip>
        )
        return <Space size={6}>{histBtn}{rerunBtn}{bugBtn}</Space>
      },
    },
    {
      title: 'ZenTao Bug',
      key: 'bug',
      width: 220,
      render: (_, record) => {
        // 2 buckets summed across ALL bugs linked to this scenario.
        //   active   → Open      (still being worked on)
        //   resolved → Completed (dev says fixed)
        //   closed   → Completed (QA confirmed)
        //   unknown  → Open      (conservative fallback)
        let openN = 0, completedN = 0
        for (const b of (record.bugs || [])) {
          const s = b.status || 'active'
          if (s === 'closed' || s === 'resolved') completedN++
          else                                     openN++
        }
        // Click a non-zero tag → popup lists which bug IDs are in that
        // bucket (today: at most 1; tomorrow: N).
        const clickableStyle = { borderRadius: 4, margin: 0, cursor: 'pointer' }
        const staticStyle    = { borderRadius: 4, margin: 0 }
        return (
          <Space size={4}>
            <Tag
              color={openN ? 'red' : 'default'}
              style={openN ? clickableStyle : staticStyle}
              onClick={openN ? () => showBugsInBucket(record, 'open') : undefined}
            >
              {openN} Open
            </Tag>
            <Tag
              color={completedN ? 'green' : 'default'}
              style={completedN ? clickableStyle : staticStyle}
              onClick={completedN ? () => showBugsInBucket(record, 'completed') : undefined}
            >
              {completedN} Completed
            </Tag>
          </Space>
        )
      },
    },
  ]
}

/** Pre-fill the modal with sane defaults derived from the failing scenario.
 * The backend would derive the same defaults if these are omitted; doing it
 * client-side lets the user see + edit them BEFORE the bug is created. */
// Short module-name guesser for the title prefix — mirrors the backend
// _module_from_feature so the modal preview matches what gets submitted.
function moduleFromFeature(feature) {
  if (!feature) return 'Auto Test'
  const head = feature.split('(')[0].trim()
  const low = head.toLowerCase()
  if (low.includes('register') || low.includes('registration')) return '注册'
  if (low.includes('login') || low.includes('auth'))            return '登录'
  if (low.includes('forgot'))                                   return '忘记密码'
  if (low.includes('guest'))                                    return '游客'
  if (low.includes('session'))                                  return '会话'
  return head.slice(0, 30) || 'Auto Test'
}

function shortScenario(name) {
  return caseDescription({ name })
}

// Modal-preview defaults — kept TEXTUAL (not HTML) so the user can edit
// freely; the backend will substitute the rich HTML template if the user
// leaves the field at the default. To force the rich template, just clear
// the steps field and submit.
function bugDefaults(scenario) {
  const module = moduleFromFeature(scenario.feature)
  const short  = shortScenario(scenario.name)
  const titleVerb = scenario.status === 'failed'
    ? '用例未通过 / Failed'
    : `待跟进 / Watch (${scenario.status})`
  const title = `[${module}] ${short} — ${titleVerb}`

  const err = scenario.error_msg ||
    '(no error captured — scenario was not failing in this run)'
  const steps =
    `### 缺陷概述\n` +
    `- 模块: ${module}\n` +
    `- 用例: ${scenario.name}\n` +
    `- 期望: 用例步骤执行后断言通过 (Given/When/Then 全部满足)\n` +
    `- 实际: ${scenario.status === 'failed' ? '用例失败 — 见下错误信息' : `当前 status=${scenario.status}`}\n\n` +
    `### 测试环境\n` +
    `- 环境: SIT\n` +
    `- Feature: ${scenario.feature}\n` +
    `- Automation Type: ${automationType(scenario)}\n` +
    `- Dashboard 引用: run #${scenario.run_id || '?'} / scenario #${scenario.id}\n\n` +
    `### 重现步骤 (Steps to Reproduce)\n` +
    `1. ...（提交时后端会自动从 features/*.feature 提取真实 Given/When/Then 替换此段）\n\n` +
    `### 错误信息\n${err}\n\n` +
    `### 截图\n（后端会优先从 runtime screenshot manifest 按 full case ID 嵌入截图；旧 WestK evidence_*/tcXXX 截图仅作为 fallback）\n\n` +
    `> 提示: 留空 steps 字段或全部清空再提交,后端会生成完整 HTML 模板(含表格/步骤列表/嵌入截图)。`

  return { title, steps, severity: 3, pri: 3, type: 'codeerror' }
}

export default function ResultsTable({
  scenarios: parentScenarios,
  evidenceStatus,
  activeProject,
  onRerunScenario,
}) {
  const zentaoProductId = activeProject?.zentaoProductId || 146
  const projectName = activeProject?.name || activeProject?.key || 'West Kowloon'
  // Overlay: scenarioId -> extra bugs[] added this session. Merged on top
  // of the parent's scenarios.bugs so an open-bug click reflects instantly
  // without forking the source of truth (parent reload still wins).
  const [bugOverlay, setBugOverlay] = useState({})       // {scenarioId: [bug, ...]}
  const scenarios = (parentScenarios || []).map((s) => {
    const extra = bugOverlay[s.id]
    if (!extra) return s
    const seen = new Set((s.bugs || []).map((b) => b.id))
    const merged = [...(s.bugs || []), ...extra.filter((b) => !seen.has(b.id))]
    return { ...s, bugs: merged }
  })

  const [bugModalOpen, setBugModalOpen] = useState(false)
  const [bugTarget, setBugTarget] = useState(null)        // scenario being bugged
  const [bugForm, setBugForm] = useState(null)            // editable defaults
  // Tracks whether the user actually edited title / steps. If they didn't,
  // we send null and let the backend generate its rich HTML template (with
  // env table, Gherkin steps, embedded screenshots, etc).
  const [touched, setTouched] = useState({ title: false, steps: false })
  const [submitting, setSubmitting] = useState(false)
  const [rerunningId, setRerunningId] = useState(null)    // which row is mid-rerun
  // "Bugs in bucket" popup state — opened when the user clicks a count tag.
  // Future: when one scenario can be linked to multiple bugs, `bugs` becomes
  // the multi-element list; today it's at most 1.
  const [bugListModal, setBugListModal] = useState({ open: false, title: '', bugs: [] })
  // Case-history modal (📜 button) — execution-result history for one case.
  // Fetched on click via /api/history/case/{id}.
  const [historyModal, setHistoryModal] = useState({
    open: false, loading: false, caseId: null, data: null,
  })
  const [messageApi, contextHolder] = message.useMessage()

  const openBugFor = (scenario) => {
    setBugTarget(scenario)
    setBugForm(bugDefaults(scenario))
    setTouched({ title: false, steps: false })   // reset per-open
    setBugModalOpen(true)
  }

  const rerunOne = async (scenario) => {
    if (rerunningId) return                                // ignore double-click
    setRerunningId(scenario.id)
    try {
      if (!onRerunScenario) {
        messageApi.error('Rerun handler is not available.')
        return
      }
      const r = await onRerunScenario(scenario)
      if (r.error) {
        messageApi.error(`Rerun failed: ${r.error}`)
      } else {
        messageApi.success({
          content: (
            <>
              Completed rerun <strong>#{r.id}</strong> for{' '}
              <code>{caseId(scenario) || scenario.name}</code>
            </>
          ),
          duration: 6,
        })
      }
    } catch (e) {
      messageApi.error(`Request error: ${e.message || e}`)
    } finally {
      setRerunningId(null)
    }
  }

  const handleConfirm = async () => {
    if (!bugTarget || !bugForm) return
    setSubmitting(true)
    try {
      // Only send fields the user actually edited; null tells the backend
      // to use its own (richer HTML) default for that field.
      const payload = {
        title:    touched.title ? bugForm.title : null,
        steps:    touched.steps ? bugForm.steps : null,
        severity: bugForm.severity,
        pri:      bugForm.pri,
        type:     bugForm.type,
        product_id: zentaoProductId,
      }
      const r = await openBugForScenario(bugTarget.id, payload)
      if (r.error) {
        messageApi.error(`开 bug 失败: ${r.error}`)
      } else {
        messageApi.success({
          content: (
            <>
              {r.already_opened ? '已有 bug ' : '已开 bug '}
              <a href={r.bug_url} target="_blank" rel="noreferrer">
                ZT-{r.bug_id}
              </a>
            </>
          ),
          duration: 6,
        })
        // Append the new bug to this scenario's overlay (idempotent — the
        // merge in `scenarios` filters by id so re-opening the same bug
        // doesn't dup the row visually).
        setBugOverlay((prev) => {
          const existing = prev[bugTarget.id] || []
          const already = existing.some((b) => b.id === r.bug_id)
          const newBug = {
            id: r.bug_id,
            url: r.bug_url,
            title: r.title,
            status: 'active',   // freshly created — refresh after next load
          }
          return {
            ...prev,
            [bugTarget.id]: already ? existing : [...existing, newBug],
          }
        })
        setBugModalOpen(false)
      }
    } catch (e) {
      messageApi.error(`Request error: ${e.message || e}`)
    } finally {
      setSubmitting(false)
    }
  }

  if (!scenarios || scenarios.length === 0) {
    return (
      <Card style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <Empty description="No scenario results to display" style={{ margin: '20px 0' }} />
      </Card>
    )
  }

  const showHistoryFor = async (scenario) => {
    const cid = caseId(scenario)
    if (!cid) {
      messageApi.warning('No test case ID found for this scenario')
      return
    }
    setHistoryModal({ open: true, loading: true, caseId: cid, data: null })
    try {
      const data = await getCaseHistory(cid)
      if (data?.error) {
        messageApi.error(data.error)
        setHistoryModal({ open: false, loading: false, caseId: null, data: null })
        return
      }
      setHistoryModal({ open: true, loading: false, caseId: cid, data })
    } catch (e) {
      messageApi.error(`Failed to load history: ${e.message || e}`)
      setHistoryModal({ open: false, loading: false, caseId: null, data: null })
    }
  }

  const showBugsInBucket = (scenario, bucket /* 'open' | 'completed' */) => {
    const all = scenario.bugs || []
    const matchBucket = (b) => {
      const s = b.status || 'active'
      const completed = (s === 'closed' || s === 'resolved')
      return bucket === 'completed' ? completed : !completed
    }
    const filtered = all.filter(matchBucket)
    if (filtered.length === 0) return                     // tag was 0; ignore click
    setBugListModal({
      open: true,
      title: `${bucket === 'open' ? 'Open' : 'Completed'} bugs for ${scenario.name}`,
      bugs: filtered,
    })
  }

  const evidenceMap = evidenceStatus?.cases || {}
  const columns = buildColumns(evidenceMap, openBugFor, rerunOne, rerunningId,
                                showBugsInBucket, showHistoryFor)
  const executed = scenarios.filter((s) => !['skipped', 'undefined', 'untested'].includes(s.status)).length
  const skipped = scenarios.filter((s) => s.status === 'skipped').length

  return (
    <>
      {contextHolder}
      <Card
        title={
          <>
            <UnorderedListOutlined /> Scenario Results: {executed} executed / {scenarios.length} collected
            <span style={{ marginLeft: 8, color: '#8c8c8c', fontSize: 12, fontWeight: 400 }}>
              ({skipped} skipped)
            </span>
          </>
        }
        style={{
          borderRadius: 12,
          border: 'none',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
        styles={{ body: { padding: 0 } }}
      >
        <Table
          dataSource={scenarios}
          columns={columns}
          rowKey="id"
          size="small"
          pagination={scenarios.length > 20 ? { pageSize: 20, showSizeChanger: true } : false}
          expandable={{
            expandedRowRender: (record) =>
              record.error_msg ? (
                <pre
                  style={{
                    color: '#ff4d4f',
                    background: '#fff2f0',
                    padding: 12,
                    borderRadius: 6,
                    fontSize: 12,
                    whiteSpace: 'pre-wrap',
                    maxHeight: 300,
                    overflow: 'auto',
                    border: '1px solid #ffccc7',
                  }}
                >
                  {record.error_msg}
                </pre>
              ) : null,
            rowExpandable: (record) => !!record.error_msg,
          }}
        />
      </Card>

      <Modal
        title={
          <Space>
            <HistoryOutlined />
            <span>Execution history - <code>{historyModal.caseId || ''}</code></span>
            {historyModal.data?.counts && (
              <span style={{ fontSize: 12, color: '#888' }}>
                ({historyModal.data.counts.execution_results ?? historyModal.data.counts.behave_runs} execution results / {historyModal.data.counts.attempts ?? '-'} attempts
                {historyModal.data.counts.reruns ? ` / ${historyModal.data.counts.reruns} rerun(s)` : ''})
              </span>
            )}
          </Space>
        }
        open={historyModal.open}
        onCancel={() => setHistoryModal({ ...historyModal, open: false })}
        footer={null}
        width={760}
        destroyOnHidden
      >
        {historyModal.loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin tip="Loading history...">
              <div style={{ minHeight: 48 }} />
            </Spin>
          </div>
        ) : historyModal.data ? (
          <>
            {historyModal.data.events?.length ? (
              <Timeline
                mode="left"
                items={historyModal.data.events.map((ev, idx) => ({
                  key: idx,
                  color: eventDotColor(ev),
                  label: <span style={{ fontSize: 11, color: '#888' }}>
                           {formatTs(ev.timestamp)}
                         </span>,
                  children: (
                    <div>
                      {ev.type === 'behave' && (
                        <>
                          <Tag color={EXECUTION_RESULT_COLOR[executionResult(ev)] || 'default'}>
                            EXECUTION / {executionResult(ev) || 'UNKNOWN'}
                          </Tag>
                          <span style={{ marginLeft: 6, fontWeight: 500 }}>
                            run #{ev.run_id}
                          </span>
                          <Tag style={{ marginLeft: 8 }}>
                            {runKindLabel(ev.run_kind || 'full')}
                          </Tag>
                          <span style={{ color: '#888', fontSize: 11, marginLeft: 8 }}>
                            {ev.env} / {(ev.duration_s || 0).toFixed(2)}s
                            {automationSuffix(ev)}
                          </span>
                          {ev.error_msg && (
                            <pre style={{
                              background: '#fff2f0', color: '#a8071a',
                              padding: 6, borderRadius: 4, fontSize: 11,
                              marginTop: 4, maxHeight: 100, overflow: 'auto',
                              whiteSpace: 'pre-wrap',
                            }}>{ev.error_msg}</pre>
                          )}
                        </>
                      )}
                    </div>
                  ),
                }))}
              />
            ) : (
              <Empty description="No history events yet for this case" />
            )}
          </>
        ) : (
          <Empty description="No data" />
        )}
      </Modal>

      <Modal
        title={<><ExportOutlined /> {bugListModal.title}</>}
        open={bugListModal.open}
        onCancel={() => setBugListModal({ ...bugListModal, open: false })}
        footer={null}
        width={460}
      >
        {bugListModal.bugs.length === 0 ? (
          <Empty description="No bugs in this bucket" />
        ) : (
          <Space direction="vertical" size={6} style={{ width: '100%' }}>
            {bugListModal.bugs.map((b) => (
              <div key={b.id} style={{
                padding: '8px 12px',
                borderRadius: 6,
                background: '#fafafa',
                border: '1px solid #f0f0f0',
              }}>
                <a href={b.url} target="_blank" rel="noreferrer" style={{ fontWeight: 500 }}>
                  ZT-{b.id} <ExportOutlined />
                </a>
                <span style={{ marginLeft: 12, color: '#888', fontSize: 12 }}>
                  ZenTao status: <code>{b.status}</code>
                </span>
              </div>
            ))}
          </Space>
        )}
      </Modal>

      <Modal
        title={<><BugOutlined /> Open ZenTao bug - {projectName} (product {zentaoProductId})</>}
        open={bugModalOpen}
        onCancel={() => !submitting && setBugModalOpen(false)}
        onOk={handleConfirm}
        okText={submitting ? '提交中…' : '确认提交'}
        cancelText="取消"
        confirmLoading={submitting}
        width={640}
        destroyOnHidden
      >
        {bugForm && (
          <Space direction="vertical" style={{ width: '100%' }} size={12}>
            <div>
              <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>
                标题{touched.title ? '（已修改 - 将按此提交）' : '（默认 - 留空使用模块名 + 简要场景）'}
              </div>
              <Input
                value={bugForm.title}
                onChange={(e) => {
                  setBugForm({ ...bugForm, title: e.target.value })
                  setTouched({ ...touched, title: true })
                }}
                maxLength={200}
              />
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>
                {touched.steps
                  ? '描述（已修改 - 提交时按此原文）'
                  : '描述预览（默认 - 提交时后端会生成完整 HTML 模板:环境表 / Gherkin 步骤 / 错误信息 / 内嵌截图）'}
              </div>
              <Input.TextArea
                value={bugForm.steps}
                onChange={(e) => {
                  setBugForm({ ...bugForm, steps: e.target.value })
                  setTouched({ ...touched, steps: true })
                }}
                autoSize={{ minRows: 10, maxRows: 22 }}
                style={touched.steps ? {} : { color: '#888', fontStyle: 'italic' }}
              />
            </div>
            <Space size={16}>
              <div>
                <div style={{ fontSize: 12, color: '#888' }}>严重程度</div>
                <Select
                  value={bugForm.severity}
                  onChange={(v) => setBugForm({ ...bugForm, severity: v })}
                  style={{ width: 120 }}
                  options={[
                    { value: 1, label: '1 (最严重)' },
                    { value: 2, label: '2 (严重)' },
                    { value: 3, label: '3 (一般)' },
                    { value: 4, label: '4 (轻微)' },
                  ]}
                />
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#888' }}>优先级</div>
                <Select
                  value={bugForm.pri}
                  onChange={(v) => setBugForm({ ...bugForm, pri: v })}
                  style={{ width: 120 }}
                  options={[
                    { value: 1, label: '1 (最高)' },
                    { value: 2, label: '2 (高)' },
                    { value: 3, label: '3 (中)' },
                    { value: 4, label: '4 (低)' },
                  ]}
                />
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#888' }}>类型</div>
                <Select
                  value={bugForm.type}
                  onChange={(v) => setBugForm({ ...bugForm, type: v })}
                  style={{ width: 160 }}
                  options={[
                    { value: 'codeerror', label: '代码错误' },
                    { value: 'config', label: '配置相关' },
                    { value: 'security', label: '安全相关' },
                    { value: 'performance', label: '性能问题' },
                    { value: 'designdefect', label: '设计缺陷' },
                    { value: 'others', label: '其他' },
                  ]}
                />
              </div>
            </Space>
            <div style={{ fontSize: 12, color: '#888' }}>
              来源场景: <code>#{bugTarget?.id}</code>{' '}
              · run <code>#{bugTarget?.run_id}</code>{' '}
              · {bugTarget?.feature}
            </div>
          </Space>
        )}
      </Modal>
    </>
  )
}
