import { useMemo, useState, useEffect, useCallback, useRef } from 'react'
import {
  Typography, Card, Row, Col, Tag, Progress, Table, Space, Statistic,
  Avatar, Tooltip, Alert, Spin, Button, Empty, Select, Modal,
} from 'antd'
import {
  DashboardOutlined, ProjectOutlined, BugOutlined, TeamOutlined,
  ExperimentOutlined, RobotOutlined, PieChartOutlined,
  RiseOutlined, UserOutlined, ApartmentOutlined,
  ThunderboltOutlined, FireOutlined, LineChartOutlined,
  ReloadOutlined, ClockCircleOutlined, ExportOutlined,
  FileExcelOutlined,
} from '@ant-design/icons'
import { requestJson } from '../apiClient'

const { Title, Text } = Typography

// ---------------------------------------------------------------------------
// Static labels — everything else comes from /api/zentao/dashboard.
// ---------------------------------------------------------------------------

const BUG_HEATMAP_LABELS = {
  cols: ['开', '验证', '关闭'],
  rows: ['S1 致命', 'S2 严重', 'S3 一般', 'S4 轻微'],
}

const EMPTY_DATA = {
  iterations: [],
  requirementsByIter: {},
  modules: [],
  qaThroughput: [],
  autoTrend: [],
  meta: { fetchedAt: null, cached: false },
}

const EMPTY_QA_TASK_MATRIX = {
  scope: 'all-executions',
  peopleType: 'qa',
  statusColumns: [],
  ownerRows: [],
  matrix: [],
  matrixTasks: [],
  summary: { total: 0, people: 0, qaWithTasks: 0, byStatus: {}, fetchedExecutions: 0 },
  fetchedAt: null,
  cached: false,
}

// ---------------------------------------------------------------------------
// Derived aggregates
// ---------------------------------------------------------------------------

function totals(iterations) {
  let stories = 0, cases = 0, auto = 0, active = 0, bugA = 0, bugC = 0, bugP1 = 0, bugP0 = 0
  iterations.forEach(it => {
    if (it.status === 'active' || it.status === 'closing') active++
    // Defensive `?? 0` — partial / lazy-loaded iters may not have every field.
    stories += it.storyTotal ?? 0
    cases   += it.testCases ?? 0
    auto    += it.autoTestCases ?? 0
    bugA    += it.bugActive ?? 0
    bugC    += it.bugClosed ?? 0
    bugP0   += it.bugP0 ?? 0
    bugP1   += it.bugP1 ?? 0
  })
  return {
    active, stories, cases, auto, bugA, bugC, bugP0, bugP1,
    autoPct: cases ? Math.round(auto / cases * 100) : 0,
  }
}

const STORY_STATUS_COLOR = {
  '待评审': '#bfbfbf', '已评审': '#1677ff', '进行中': '#faad14',
  '已完成': '#52c41a', '已发布': '#722ed1',
}
const ITER_STATUS_COLOR = {
  active:   { tag: 'processing', text: '进行中' },
  planning: { tag: 'default',    text: '规划中' },
  closing:  { tag: 'warning',    text: '收尾中' },
  done:     { tag: 'success',    text: '已结项' },
}

// ---------------------------------------------------------------------------
// Section header — the visual delimiter between zones
// ---------------------------------------------------------------------------

function SectionHeader({ accent, icon, title, subtitle, extra }) {
  return (
    <div style={{
      marginTop: 28,
      marginBottom: 16,
      display: 'flex', alignItems: 'center', gap: 12,
      paddingBottom: 10,
      borderBottom: `2px solid ${accent}33`,
    }}>
      <div style={{
        width: 5, height: 28, background: accent, borderRadius: 3,
      }} />
      <div style={{
        width: 38, height: 38, borderRadius: 8,
        background: `${accent}1a`, color: accent,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 18,
      }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <Text strong style={{ fontSize: 16, color: '#262626' }}>{title}</Text>
        {subtitle && (
          <div><Text type="secondary" style={{ fontSize: 12 }}>{subtitle}</Text></div>
        )}
      </div>
      {extra}
    </div>
  )
}

// ---------------------------------------------------------------------------
// SVG visualisations
// ---------------------------------------------------------------------------

function DonutChart({ data, size = 160, valueKey = 'cases', labelKey = 'name', colors, onItemClick }) {
  const total = data.reduce((s, d) => s + d[valueKey], 0)
  const hasData = total > 0
  const cx = size / 2, cy = size / 2
  const r = size / 2 - 12
  const inner = r * 0.62
  const palette = colors || [
    '#1677ff', '#52c41a', '#722ed1', '#fa8c16', '#13c2c2', '#eb2f96', '#faad14', '#f5222d',
  ]

  let startAngle = -Math.PI / 2
  const slices = hasData ? data.map((d, i) => {
    const angle = (d[valueKey] / total) * 2 * Math.PI
    const endAngle = startAngle + angle
    const largeArc = angle > Math.PI ? 1 : 0
    const x1 = cx + r * Math.cos(startAngle), y1 = cy + r * Math.sin(startAngle)
    const x2 = cx + r * Math.cos(endAngle),   y2 = cy + r * Math.sin(endAngle)
    const ix1 = cx + inner * Math.cos(endAngle),  iy1 = cy + inner * Math.sin(endAngle)
    const ix2 = cx + inner * Math.cos(startAngle), iy2 = cy + inner * Math.sin(startAngle)
    const path = [
      `M ${x1} ${y1}`,
      `A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${ix1} ${iy1}`,
      `A ${inner} ${inner} 0 ${largeArc} 0 ${ix2} ${iy2}`,
      'Z',
    ].join(' ')
    startAngle = endAngle
    return { d: path, fill: palette[i % palette.length], label: d[labelKey], value: d[valueKey] }
  }) : []
  const legendRows = hasData
    ? slices
    : data.map((d, i) => ({
      fill: palette[i % palette.length],
      label: d[labelKey],
      value: d[valueKey],
    }))

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 14,
      // Center the donut+legend group horizontally within whatever
      // container we're rendered into.
      justifyContent: 'center',
      width: '100%',
    }}>
      <svg width={size} height={size}>
        {!hasData && (
          <circle
            cx={cx}
            cy={cy}
            r={(r + inner) / 2}
            fill="none"
            stroke="#f0f0f0"
            strokeWidth={r - inner}
          />
        )}
        {slices.map((s, i) => (
          <path key={i} d={s.d} fill={s.fill} opacity={0.9}>
            <title>{s.label}: {s.value} ({Math.round(s.value / total * 100)}%)</title>
          </path>
        ))}
        <text x={cx} y={cy - 4} textAnchor="middle" fontSize={20} fontWeight={700} fill="#262626">
          {total}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fontSize={10} fill="#8c8c8c">总计</text>
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12 }}>
        {legendRows.map((s, i) => {
          const clickable = onItemClick && s.value > 0
          return (
            <div
              key={i}
              data-testid="donut-legend-row"
              data-label={s.label}
              data-value={s.value}
              onClick={clickable ? () => onItemClick(s.label, s.value) : undefined}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                cursor: clickable ? 'pointer' : 'default',
                padding: '1px 4px', borderRadius: 4,
                transition: 'background 0.1s',
              }}
              onMouseEnter={(e) => { if (clickable) e.currentTarget.style.background = '#f5f5f5' }}
              onMouseLeave={(e) => { if (clickable) e.currentTarget.style.background = 'transparent' }}
            >
              <span style={{ width: 10, height: 10, background: s.fill, borderRadius: 2 }} />
              <Text style={{ fontSize: 12 }}>{s.label}</Text>
              <Text style={{
                fontSize: 12, fontWeight: 600,
                color: clickable ? s.fill : '#8c8c8c',
              }}>{s.value}</Text>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function StackedBarChart({ series, width = 520, height = 200 }) {
  if (!series || series.length === 0) return null
  const iters = series[0].data.map(d => d.iter)
  const palette = ['#1677ff', '#13c2c2', '#722ed1', '#fa8c16', '#eb2f96']
  const totals = iters.map((_, i) =>
    series.reduce((s, q) => s + q.data[i].cases, 0))
  const maxTotal = Math.max(...totals)
  const barW = (width - 50) / iters.length - 8
  const baseY = height - 26

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      width="100%"
      style={{ display: 'block', maxHeight: height }}
    >
      {iters.map((iter, i) => {
        const x = 30 + i * (barW + 8)
        let y = baseY
        return (
          <g key={i}>
            {series.map((q, si) => {
              const v = q.data[i].cases
              const h = (v / maxTotal) * (height - 50)
              y -= h
              return (
                <rect key={si} x={x} y={y} width={barW} height={h}
                      fill={palette[si % palette.length]} opacity={0.9}>
                  <title>{q.qa} · {iter}月: {v}</title>
                </rect>
              )
            })}
            <text x={x + barW / 2} y={baseY + 14}
                  textAnchor="middle" fontSize={10} fill="#8c8c8c">{iter}月</text>
            <text x={x + barW / 2} y={baseY - totals[i] / maxTotal * (height - 50) - 4}
                  textAnchor="middle" fontSize={10} fill="#262626" fontWeight={600}>
              {totals[i]}
            </text>
          </g>
        )
      })}
      <g transform={`translate(${width - 90}, 8)`}>
        {series.map((q, i) => (
          <g key={i} transform={`translate(0, ${i * 14})`}>
            <rect width={10} height={10} fill={palette[i % palette.length]} />
            <text x={14} y={9} fontSize={10} fill="#595959">{q.qa}</text>
          </g>
        ))}
      </g>
    </svg>
  )
}

function AutoTrendChart({ data, width = 560, height = 200 }) {
  if (!data || data.length < 2) return null
  const max = 100  // percentage scale
  const min = 0
  const range = max - min
  const padding = 30
  const stepX = (width - padding * 2) / (data.length - 1)
  const points = data.map((d, i) => ({
    x: padding + i * stepX,
    y: height - padding - ((d.pct - min) / range) * (height - padding * 2),
    label: d.month, value: d.pct,
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - padding} L ${padding} ${height - padding} Z`

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      width="100%"
      style={{ display: 'block', maxHeight: height }}
    >
      {[0, 25, 50, 75, 100].map((v, i) => {
        const y = height - padding - (v / 100) * (height - padding * 2)
        return (
          <g key={i}>
            <line x1={padding} y1={y} x2={width - padding} y2={y} stroke="#f0f0f0" />
            <text x={padding - 6} y={y + 3} textAnchor="end" fontSize={10} fill="#8c8c8c">{v}%</text>
          </g>
        )
      })}
      <path d={areaPath} fill="rgba(82,196,26,0.12)" />
      <path d={linePath} fill="none" stroke="#52c41a" strokeWidth={2.5} />
      {points.map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r={4} fill="#52c41a">
            <title>{p.label}月: {p.value}%</title>
          </circle>
          <text x={p.x} y={p.y - 10} textAnchor="middle" fontSize={11}
                fill="#52c41a" fontWeight={600}>{p.value}%</text>
          <text x={p.x} y={height - padding + 16} textAnchor="middle"
                fontSize={11} fill="#595959">{p.label}月</text>
        </g>
      ))}
    </svg>
  )
}

// Per-column number colors — open=red, verify=orange, closed=green.
// Reflects bug status at a glance without painting cell backgrounds.
const BUG_COL_FG = ['#ff4d4f', '#fa8c16', '#52c41a']
const BUG_COL_FG_ZERO = '#d9d9d9'                    // dim zeros so they don't shout
const BUG_TOTAL_FG = '#595959'                       // row totals (no status meaning)
const BUG_GRAND_FG = '#1677ff'

// S × Status matrix with row totals (col 5) + col totals (row 5).
// Numbers carry the color signal; backgrounds stay neutral.
function BugMatrix({ matrix, onCellClick, onRowClick, onColClick, onAllClick }) {
  const grid = matrix || [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
  const rowTotals = grid.map(row => row.reduce((a, b) => a + b, 0))
  const colTotals = [0, 1, 2].map(c => grid.reduce((sum, row) => sum + row[c], 0))
  const grandTotal = rowTotals.reduce((a, b) => a + b, 0)

  const dataCellStyle = (v, ci, clickable) => ({
    background: '#fff',
    color: v === 0 ? BUG_COL_FG_ZERO : BUG_COL_FG[ci],
    textAlign: 'center',
    padding: 10,
    border: '1px solid #f0f0f0',
    fontWeight: v === 0 ? 500 : 700,
    fontSize: 14,
    cursor: clickable ? 'pointer' : 'default',
    transition: 'background 0.1s',
  })

  const totalCellStyle = (v, color, clickable) => ({
    background: '#fafafa',
    color: v === 0 ? BUG_COL_FG_ZERO : color,
    textAlign: 'center',
    padding: 10,
    border: '1px solid #f0f0f0',
    fontWeight: 900,
    fontSize: 15,
    cursor: clickable ? 'pointer' : 'default',
    transition: 'background 0.1s',
  })

  const hoverIn = (clickable) => (e) => {
    if (clickable) e.currentTarget.style.background = '#f5f5f5'
  }
  const hoverOut = (isTotal) => (e) => {
    e.currentTarget.style.background = isTotal ? '#fafafa' : '#fff'
  }

  return (
    <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
      <thead>
        <tr>
          <th style={{ width: 80, padding: 6 }}></th>
          {BUG_HEATMAP_LABELS.cols.map((c, ci) => (
            <th key={c} style={{
              padding: 6, fontSize: 11, color: BUG_COL_FG[ci],
              textAlign: 'center', fontWeight: 700,
            }}>{c}</th>
          ))}
          <th style={{ padding: 6, fontSize: 11, color: '#262626',
                       textAlign: 'center', fontWeight: 900 }}>总</th>
        </tr>
      </thead>
      <tbody>
        {BUG_HEATMAP_LABELS.rows.map((r, ri) => (
          <tr key={r}>
            <th style={{ padding: 6, fontSize: 11, color: '#595959',
                         textAlign: 'left', fontWeight: 600 }}>{r}</th>
            {grid[ri].map((v, ci) => {
              const clickable = v > 0 && !!onCellClick
              return (
                <td
                  key={ci}
                  data-testid="heatmap-cell"
                  data-sev={ri + 1}
                  data-status={ci + 1}
                  data-count={v}
                  onClick={clickable ? () => onCellClick(ri + 1, ci + 1) : undefined}
                  style={dataCellStyle(v, ci, clickable)}
                  onMouseEnter={hoverIn(clickable)}
                  onMouseLeave={hoverOut(false)}
                >{v}</td>
              )
            })}
            {/* Row total — neutral grey number */}
            {(() => {
              const v = rowTotals[ri]
              const clickable = v > 0 && !!onRowClick
              return (
                <td
                  data-testid="row-total"
                  data-sev={ri + 1}
                  data-count={v}
                  onClick={clickable ? () => onRowClick(ri + 1) : undefined}
                  style={totalCellStyle(v, BUG_TOTAL_FG, clickable)}
                  onMouseEnter={hoverIn(clickable)}
                  onMouseLeave={hoverOut(true)}
                >{v}</td>
              )
            })()}
          </tr>
        ))}
        {/* Column totals row — per-column color so 开/验证/关闭 still readable */}
        <tr>
          <th style={{ padding: 6, fontSize: 11, color: '#262626',
                       textAlign: 'left', fontWeight: 900 }}>总</th>
          {colTotals.map((v, ci) => {
            const clickable = v > 0 && !!onColClick
            return (
              <td
                key={ci}
                data-testid="col-total"
                data-status={ci + 1}
                data-count={v}
                onClick={clickable ? () => onColClick(ci + 1) : undefined}
                style={totalCellStyle(v, BUG_COL_FG[ci], clickable)}
                onMouseEnter={hoverIn(clickable)}
                onMouseLeave={hoverOut(true)}
              >{v}</td>
            )
          })}
          {/* Grand total — blue accent */}
          {(() => {
            const clickable = grandTotal > 0 && !!onAllClick
            return (
              <td
                data-testid="grand-total"
                data-count={grandTotal}
                onClick={clickable ? () => onAllClick() : undefined}
                style={totalCellStyle(grandTotal, BUG_GRAND_FG, clickable)}
                onMouseEnter={hoverIn(clickable)}
                onMouseLeave={hoverOut(true)}
              >{grandTotal}</td>
            )
          })()}
        </tr>
      </tbody>
    </table>
  )
}

function TaskOwnerStatusMatrix({ rows, columns, matrix, onCellClick, onRowClick, onColClick, onAllClick }) {
  const safeRows = rows || []
  const safeCols = columns || []
  const safeMatrix = matrix || []
  const rowTotals = safeRows.map((_, ri) => (safeMatrix[ri] || []).reduce((a, b) => a + b, 0))
  const colTotals = safeCols.map((_, ci) => safeRows.reduce((sum, __, ri) => sum + ((safeMatrix[ri] || [])[ci] || 0), 0))
  const grandTotal = rowTotals.reduce((a, b) => a + b, 0)

  const cellStyle = (v, color, isTotal, clickable) => ({
    background: isTotal ? '#f5f7ff' : '#fff',
    color: v === 0 ? '#d9d9d9' : color,
    textAlign: 'center',
    padding: 10,
    border: '1px solid #f0f0f0',
    fontWeight: isTotal ? 900 : (v === 0 ? 500 : 700),
    fontSize: isTotal ? 15 : 14,
    cursor: clickable ? 'pointer' : 'default',
    transition: 'background 0.1s',
    minWidth: 72,
  })

  const hoverIn = (clickable) => (e) => {
    if (clickable) e.currentTarget.style.background = '#f5f5f5'
  }
  const hoverOut = (isTotal) => (e) => {
    e.currentTarget.style.background = isTotal ? '#fafafa' : '#fff'
  }

  if (safeRows.length === 0 || safeCols.length === 0) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无任务数据" />
  }

  return (
    <div style={{ width: '100%', overflow: 'auto', maxHeight: 300 }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: Math.max(640, 150 + safeCols.length * 82), fontSize: 12 }}>
        <thead>
          <tr>
            <th style={{ width: 150, padding: 6, textAlign: 'left', color: '#595959' }}>负责人</th>
            {safeCols.map(col => (
              <th key={col.key} style={{
                padding: 6, fontSize: 11, color: col.color || '#595959',
                textAlign: 'center', fontWeight: 700,
              }}>{col.label}</th>
            ))}
            <th style={{ padding: 6, fontSize: 11, color: '#262626',
                         textAlign: 'center', fontWeight: 900 }}>总</th>
          </tr>
        </thead>
        <tbody>
          {safeRows.map((owner, ri) => (
            <tr key={owner}>
              <th style={{
                padding: 6, fontSize: 12, color: owner === 'Unassigned' ? '#8c8c8c' : '#262626',
                textAlign: 'left', fontWeight: 600, whiteSpace: 'nowrap',
              }}>
                {owner === 'Unassigned' ? '未指派' : owner}
              </th>
              {safeCols.map((col, ci) => {
                const v = (safeMatrix[ri] || [])[ci] || 0
                const clickable = v > 0 && !!onCellClick
                return (
                  <td
                    key={col.key}
                    data-testid="task-matrix-cell"
                    data-owner={owner}
                    data-status={col.key}
                    data-count={v}
                    onClick={clickable ? () => onCellClick(ri, ci) : undefined}
                    style={cellStyle(v, col.color || '#595959', false, clickable)}
                    onMouseEnter={hoverIn(clickable)}
                    onMouseLeave={hoverOut(false)}
                  >{v}</td>
                )
              })}
              {(() => {
                const v = rowTotals[ri]
                const clickable = v > 0 && !!onRowClick
                return (
                  <td
                    data-testid="task-row-total"
                    data-owner={owner}
                    data-count={v}
                    onClick={clickable ? () => onRowClick(ri) : undefined}
                    style={cellStyle(v, '#595959', true, clickable)}
                    onMouseEnter={hoverIn(clickable)}
                    onMouseLeave={hoverOut(true)}
                  >{v}</td>
                )
              })()}
            </tr>
          ))}
          <tr>
            <th style={{ padding: 6, fontSize: 12, color: '#262626',
                         textAlign: 'left', fontWeight: 900 }}>总</th>
            {safeCols.map((col, ci) => {
              const v = colTotals[ci]
              const clickable = v > 0 && !!onColClick
              return (
                <td
                  key={col.key}
                  data-testid="task-col-total"
                  data-status={col.key}
                  data-count={v}
                  onClick={clickable ? () => onColClick(ci) : undefined}
                  style={cellStyle(v, col.color || '#595959', true, clickable)}
                  onMouseEnter={hoverIn(clickable)}
                  onMouseLeave={hoverOut(true)}
                >{v}</td>
              )
            })}
            {(() => {
              const clickable = grandTotal > 0 && !!onAllClick
              return (
                <td
                  data-testid="task-grand-total"
                  data-count={grandTotal}
                  onClick={clickable ? () => onAllClick() : undefined}
                  style={cellStyle(grandTotal, '#1677ff', true, clickable)}
                  onMouseEnter={hoverIn(clickable)}
                  onMouseLeave={hoverOut(true)}
                >{grandTotal}</td>
              )
            })()}
          </tr>
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Iteration card
// ---------------------------------------------------------------------------

function IterationCard({ iter, isSelected, onSelect }) {
  const c = ITER_STATUS_COLOR[iter.status] || ITER_STATUS_COLOR.active
  const autoPct = iter.testCases ? Math.round(iter.autoTestCases / iter.testCases * 100) : 0

  return (
    <Card
      size="small"
      hoverable
      onClick={() => onSelect(iter.id)}
      style={{
        borderRadius: 10,
        border: isSelected ? '2px solid #1677ff' : '1px solid #f0f0f0',
        boxShadow: isSelected ? '0 0 0 3px rgba(22,119,255,0.10)' : 'none',
        cursor: 'pointer',
        transition: 'border-color 0.15s, box-shadow 0.15s',
        background: '#fff',
        // Fixed body height + flex column makes cards 4-up align row-to-row
        // regardless of iter-name length / optional P0 tag / variable QA count.
        height: '100%',
      }}
      styles={{ body: { display: 'flex', flexDirection: 'column', minHeight: 200 } }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <Tooltip title={iter.name}>
            <Text strong style={{
              fontSize: 14,
              display: 'block',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>{iter.name}</Text>
          </Tooltip>
          <Text type="secondary" style={{ fontSize: 11 }}>{iter.code}</Text>
        </div>
        <Tag color={c.tag} style={{ marginRight: 0, flexShrink: 0 }}>{c.text}</Tag>
      </div>

      <div style={{ marginTop: 4, fontSize: 11, color: '#8c8c8c' }}>
        {iter.startDate} → {iter.endDate}
        {iter.daysLeft > 0 && (
          <span style={{ marginLeft: 8, color: iter.daysLeft <= 3 ? '#ff4d4f' : '#8c8c8c' }}>
            剩 {iter.daysLeft} 天
          </span>
        )}
      </div>

      <Progress
        percent={iter.progressPct}
        size="small"
        strokeColor={iter.progressPct >= 80 ? '#52c41a' : iter.progressPct >= 40 ? '#1677ff' : '#faad14'}
        style={{ marginTop: 6, marginBottom: 8 }}
      />

      <Row gutter={6}>
        <Col span={8}>
          <Text type="secondary" style={{ fontSize: 11 }}>需求</Text>
          <div style={{ fontSize: 14, fontWeight: 600 }}>
            {(iter.storyByStatus?.['已完成'] ?? 0) + (iter.storyByStatus?.['已发布'] ?? 0)} <Text type="secondary" style={{ fontSize: 11 }}>/ {iter.storyTotal}</Text>
          </div>
        </Col>
        <Col span={8}>
          <Text type="secondary" style={{ fontSize: 11 }}>用例 / 自动</Text>
          <div style={{ fontSize: 14, fontWeight: 600 }}>
            {iter.testCases} <Text style={{ fontSize: 11, color: autoPct >= 50 ? '#52c41a' : '#fa8c16' }}>· {autoPct}%</Text>
          </div>
        </Col>
        <Col span={8}>
          <Text type="secondary" style={{ fontSize: 11 }}>缺陷</Text>
          <div style={{ fontSize: 14, fontWeight: 600 }}>
            <span style={{ color: iter.bugActive ? '#ff4d4f' : '#52c41a' }}>{iter.bugActive}</span>
            <Text type="secondary" style={{ fontSize: 11 }}> · 已关 {iter.bugClosed}</Text>
            {iter.bugP0 > 0 && <Tag color="error" style={{ marginLeft: 4, fontSize: 10 }}>P0 {iter.bugP0}</Tag>}
          </div>
        </Col>
      </Row>

      <div style={{
        marginTop: 'auto', paddingTop: 8,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        {(() => {
          const team = iter.qaTeam || []   // defensive: lazy-loaded iters may not yet have qaTeam
          if (team.length === 0) return <Text type="secondary" style={{ fontSize: 11 }}>无指派</Text>
          return (
            <Avatar.Group size="small" maxCount={4}>
              {team.map(q => (
                <Tooltip key={q.name} title={`${q.name} · ${q.cases} 用例 · 自动 ${q.auto}`}>
                  <Avatar style={{ background: '#1677ff', fontSize: 11 }}>{q.name.slice(-2)}</Avatar>
                </Tooltip>
              ))}
            </Avatar.Group>
          )
        })()}
        <Text type="secondary" style={{ fontSize: 11 }}>{(iter.qaTeam || []).length} 位 QA</Text>
      </div>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Card wrapper used inside sections — flatter look (no shadow, light border)
// ---------------------------------------------------------------------------

function SubCard({ title, extra, children, height, bodyHeight, centered }) {
  const bodyStyle = { padding: 14 }
  if (bodyHeight) {
    bodyStyle.height = bodyHeight
    bodyStyle.overflow = 'hidden'
    if (centered) {
      bodyStyle.display = 'flex'
      bodyStyle.alignItems = 'center'
      bodyStyle.justifyContent = 'center'
    }
  }
  return (
    <Card
      size="small"
      title={<Text strong style={{ fontSize: 13 }}>{title}</Text>}
      extra={extra}
      style={{
        borderRadius: 10,
        border: '1px solid #f0f0f0',
        boxShadow: 'none',
        background: '#fff',
        height: height || '100%',
      }}
      styles={{
        header: { minHeight: 38, borderBottom: '1px solid #f5f5f5' },
        body: bodyStyle,
      }}
    >
      {children}
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

const VISIBLE_ITERS = 4   // first N iteration cards shown; rest go in dropdown
const MAX_FETCH = 6       // pull this many from backend; user can rotate through the rest
const LS_ORDER  = 'zentao.displayOrder'
const LS_PINNED = 'zentao.pinnedIds'

function readLS(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    const parsed = JSON.parse(raw)
    // Both displayOrder + pinnedIds are arrays — defend against corrupt LS.
    return Array.isArray(parsed) ? parsed : fallback
  } catch { return fallback }
}
function writeLS(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* quota / disabled */ }
}

function normalizeSearchText(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[\s._\-—–()（）/\\:：[\]【】]+/g, '')
}

function executionSearchAliases(name) {
  const raw = String(name || '')
  return `${raw} ${raw.replace(/[vV](?=\d)/g, '')}`
}

function filterExecutionOption(input, option) {
  const needle = normalizeSearchText(input)
  if (!needle) return true
  return normalizeSearchText(option?.searchText || option?.label).includes(needle)
}

function qaSourceLabel(source) {
  if (source === 'current_test_task') return '当前测试任务'
  if (source === 'other_current_test_task') return '其它当前测试任务'
  if (source === 'unassigned_current_test_task') return '未指派当前测试任务'
  if (source === 'historical_test_task') return '历史测试任务'
  if (source === 'evidence_only') return '仅历史证据'
  return '无证据'
}

function qaEvidenceTooltip(record) {
  const evidence = record?.qaEvidence || []
  if (evidence.length === 0) {
    return '没有找到当前未关闭的测试任务、历史测试任务或用例证据。'
  }
  return (
    <Space direction="vertical" size={2}>
      <Text style={{ color: '#fff', fontSize: 12 }}>
        负责人来源：{qaSourceLabel(record.qaSource)}
      </Text>
      {evidence.slice(0, 5).map((item, idx) => {
        if (item.source === 'test_case_author') {
          return (
            <Text key={idx} style={{ color: '#fff', fontSize: 12 }}>
              用例创建人：{item.owner}（{item.count} 条）
            </Text>
          )
        }
        return (
          <Text key={idx} style={{ color: '#fff', fontSize: 12 }}>
            {qaSourceLabel(item.source)}：{item.owner || '未指派'} · {item.name || `#${item.id}`} · {item.status || 'unknown'}
          </Text>
        )
      })}
    </Space>
  )
}

function isFallbackIteration(iter) {
  return String(iter?.name || '').includes('local story generation fallback')
}

export default function ZenTaoDashboardPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const projectDefaultProductId = activeProject
    ? (activeProject.zentaoProductId != null ? Number(activeProject.zentaoProductId) : 0)
    : 146
  // Data + fetch state
  const [data, setData] = useState(EMPTY_DATA)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [products, setProducts] = useState([])
  const [productsError, setProductsError] = useState(null)
  const [productId, setProductId] = useState(projectDefaultProductId || 0)
  const projectProductLabel = useMemo(() => {
    if (!projectDefaultProductId) return `${projectName} - ZenTao product not mapped`
    const matched = products.find((p) => Number(p.id) === Number(projectDefaultProductId))
    const name = matched?.name || projectName
    const status = matched?.status && !['normal', 'unknown'].includes(matched.status)
      ? ` - ${matched.status}`
      : ''
    return `${name} (${projectDefaultProductId})${status}`
  }, [products, projectDefaultProductId, projectName])
  const [qaTaskMatrix, setQaTaskMatrix] = useState(EMPTY_QA_TASK_MATRIX)
  const [qaTaskLoading, setQaTaskLoading] = useState(true)
  const [qaTaskError, setQaTaskError] = useState(null)
  // displayOrder = list of iteration IDs in user-preferred order. Position 0
  // is the currently selected iteration (drives Section 2). When user picks
  // an iter from the dropdown OR clicks any visible card, it moves to pos 0.
  // Hydrated from localStorage so "pinned" execs survive page reload.
  const [displayOrder, setDisplayOrder] = useState(() => readLS(LS_ORDER, []))
  // pinnedIds = execs the user has manually loaded via the dropdown. On data
  // refresh we make sure they are kept in `iterations` even if they fell
  // out of the backend's top-N sort.
  const [pinnedIds, setPinnedIds] = useState(() => readLS(LS_PINNED, []))

  // Snapshot pinnedIds in a ref so fetchData stays referentially stable across
  // re-renders (pinnedIds changes whenever the user opens a dropdown exec).
  const pinnedIdsRef = useRef(pinnedIds)
  useEffect(() => { pinnedIdsRef.current = pinnedIds }, [pinnedIds])
  const projectKeyRef = useRef(projectKey)

  useEffect(() => {
    if (projectKeyRef.current === projectKey) return
    projectKeyRef.current = projectKey
    setProductId(projectDefaultProductId || 0)
    setDisplayOrder([])
    setPinnedIds([])
    setData(EMPTY_DATA)
  }, [projectKey, projectDefaultProductId])

  // Likewise for the lazy-load fn (it depends on data.iterations which churns).
  const lazyLoadRef = useRef(null)

  const fetchData = useCallback(async (refresh = false) => {
    setLoading(true)
    setError(null)
    try {
      const url = `/api/zentao/dashboard?product_id=${productId}&max_iterations=${MAX_FETCH}&project=${encodeURIComponent(projectKey)}${refresh ? '&refresh=true' : ''}`
      const json = await requestJson(url)
      setData(json)
      // Refresh button only invalidates the dashboard endpoint's cache.
      // Pinned execs that came in via the dropdown have their own per-exec
      // cache (`/api/zentao/execution/{id}/detail`) which the dashboard
      // refetch does NOT touch. Fire-and-forget per-pinned refreshes so
      // the user sees fresh data everywhere on `刷新`.
      if (refresh && lazyLoadRef.current) {
        const topIds = new Set((json.iterations || []).map(i => i.id))
        const moreIds = new Set((json.moreExecutions || []).map(e => e.id))
        for (const pid of pinnedIdsRef.current) {
          if (!topIds.has(pid) && moreIds.has(pid)) {
            // silent: true → no spinner change; refresh: true → bypass cache.
            lazyLoadRef.current(pid, { silent: true, refresh: true })
          }
        }
      }
    } catch (e) {
      setError(e.message || 'fetch failed')
    } finally {
      setLoading(false)
    }
  }, [productId, projectKey])

  useEffect(() => { fetchData(false) }, [productId])  // eslint-disable-line react-hooks/exhaustive-deps

  const fetchQaTaskMatrix = useCallback(async (refresh = false) => {
    setQaTaskLoading(true)
    setQaTaskError(null)
    try {
      const qs = new URLSearchParams({
        project: projectKey,
        execution_id: String(
          Number(String(displayOrder[0] || '').replace(/^iter-/, ''))
          || activeProject?.zentaoExecutionId
          || 0
        ),
      })
      if (refresh) qs.set('refresh', 'true')
      const json = await requestJson(`/api/zentao/qa-task-matrix?${qs.toString()}`)
      if (json.error) throw new Error(json.error)
      setQaTaskMatrix(json)
    } catch (e) {
      setQaTaskError(e.message || 'fetch QA task matrix failed')
      setQaTaskMatrix(EMPTY_QA_TASK_MATRIX)
    } finally {
      setQaTaskLoading(false)
    }
  }, [projectKey, activeProject?.zentaoExecutionId, displayOrder])

  useEffect(() => { fetchQaTaskMatrix(false) }, [fetchQaTaskMatrix])

  const refreshAll = useCallback(() => {
    fetchData(true)
    fetchQaTaskMatrix(true)
  }, [fetchData, fetchQaTaskMatrix])

  const fetchProducts = useCallback(async () => {
    try {
      const json = await requestJson('/api/zentao/products')
      setProducts(json.products || [])
      setProductsError(json.error || null)
    } catch (e) {
      setProductsError(e.message || 'fetch products failed')
    }
  }, [])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  // Persist displayOrder + pinnedIds to localStorage on every change.
  useEffect(() => { writeLS(LS_ORDER, displayOrder) }, [displayOrder])
  useEffect(() => { writeLS(LS_PINNED, pinnedIds) }, [pinnedIds])

  // Sync displayOrder when iterations / moreExecutions change. Treat IDs
  // from BOTH lists as valid so pinned execs not yet lazy-loaded stay in
  // their display position. Do NOT clear when both lists are empty —
  // that's just the initial pre-fetch state, and clearing would wipe the
  // localStorage-restored order.
  useEffect(() => {
    const iterIds = data.iterations.map(i => i.id)
    const moreIds = (data.moreExecutions || []).map(e => e.id)
    const validIds = new Set([...iterIds, ...moreIds])
    if (validIds.size === 0) return        // initial mount, nothing to sync
    const kept = displayOrder.filter(id => validIds.has(id))
    const newOnes = iterIds.filter(id => !kept.includes(id))
    const next = [...kept, ...newOnes]
    if (next.length !== displayOrder.length || next.some((id, i) => id !== displayOrder[i])) {
      setDisplayOrder(next)
    }
  }, [data.iterations, data.moreExecutions, displayOrder])

  // Track which executions have had their detail loaded (lazy-load).
  const [lazyLoading, setLazyLoading] = useState(false)
  // Modal for clicking a bug count → list of bugs with links
  const [bugModal, setBugModal] = useState({ open: false, story: null, bugs: [] })
  // Modal for clicking a test-case count / chip → list of cases for a story.
  // bucket = null → show all; else 'pass'|'fail'|'inProgress'|'unexecuted'
  const [caseModal, setCaseModal] = useState({ open: false, story: null, bucket: null })
  // Modal for clicking a Donut slice → stories in that status
  const [storyStatusModal, setStoryStatusModal] = useState({ open: false, status: null })
  // Modal for clicking any cell of the bug-overview matrix
  // (severity row × status column, row totals, col totals, or grand total).
  // `label` is the rendered title chip (e.g. "S2 · 验证" / "S2 · 全部" / "全部 · 开" / "全部").
  const [heatmapModal, setHeatmapModal] = useState({ open: false, label: '', bugs: [] })
  // Modal for clicking a person × task-status matrix cell.
  const [taskModal, setTaskModal] = useState({ open: false, label: '', tasks: [] })
  // Modal for clicking a QA name in the QA-workload card → reqs assigned to them
  const [qaModal, setQaModal] = useState({ open: false, qa: null, reqs: [] })
  const [generatingStoryId, setGeneratingStoryId] = useState(null)

  // Promote = move iter to position 0 (= "select" it).
  const promoteIter = useCallback((id) => {
    setDisplayOrder(prev => [id, ...prev.filter(x => x !== id)])
  }, [])

  // Lazy-load: fetch detail for a moreExecutions entry, merge into iterations,
  // promote to front. Called when user picks an unloaded execution from
  // dropdown, AND on refresh for any previously-pinned exec that fell out of
  // the backend's top-N. `silent`=true skips selection promotion.
  // Tracks lazy-load fetches that haven't completed yet. Prevents the silent
  // rehydrate effect from firing duplicate requests while a fetch is in flight
  // (the effect's deps update on every state change but the in-flight set
  // doesn't, so we get correct dedup).
  const inflightLazy = useRef(new Set())

  const lazyLoadAndPromote = useCallback(async (iterId, { silent = false, refresh = false } = {}) => {
    // Pin EVERY manual pick — even if the exec is already loaded — so that
    // it survives subsequent refreshes / re-sorts.
    if (!silent) {
      setPinnedIds(prev => prev.includes(iterId) ? prev : [...prev, iterId])
    }
    const already = data.iterations.find(i => i.id === iterId)
    // Already loaded AND not asking for fresh data? Just promote, no refetch.
    if (already && !refresh && !isFallbackIteration(already)) {
      if (!silent) promoteIter(iterId)
      return
    }
    if (inflightLazy.current.has(iterId)) return    // dedup duplicate fires
    inflightLazy.current.add(iterId)
    if (!silent) setLazyLoading(true)
    try {
      const execId = iterId.replace(/^iter-/, '')
      const url = `/api/zentao/execution/${execId}/detail${refresh ? '?refresh=true' : ''}`
      const json = await requestJson(url)
      if (json.error) throw new Error(json.error)
      setData(prev => ({
        ...prev,
        // Replace if exec was already in the list (refresh path), else append.
        iterations: prev.iterations.find(i => i.id === iterId)
          ? prev.iterations.map(i => i.id === iterId ? json.summary : i)
          : [...prev.iterations, json.summary],
        requirementsByIter: { ...prev.requirementsByIter, [json.summary.id]: json.requirements },
        moreExecutions: prev.moreExecutions.filter(e => e.id !== iterId),
      }))
      if (!silent) promoteIter(iterId)
    } catch (e) {
      if (!silent) setError(`加载执行详情失败: ${e.message}`)
    } finally {
      inflightLazy.current.delete(iterId)
      if (!silent) setLazyLoading(false)
    }
  }, [data.iterations, promoteIter])

  // Keep the ref in sync so fetchData can invoke it without a circular dep.
  useEffect(() => { lazyLoadRef.current = lazyLoadAndPromote }, [lazyLoadAndPromote])

  // Auto-rehydrate pinned execs after data load. If a pinned exec is NOT in
  // the current iterations list (because backend's sort pushed it out of the
  // top-N), fetch its detail silently and merge it in. Runs once per data load.
  useEffect(() => {
    if (loading) return
    if (data.iterations.length === 0) return
    const haveIds = new Set(data.iterations.map(i => i.id))
    const moreIds = new Set((data.moreExecutions || []).map(e => e.id))
    for (const iter of data.iterations) {
      if (isFallbackIteration(iter) && moreIds.has(iter.id)) {
        lazyLoadAndPromote(iter.id, { silent: true, refresh: true })
      }
    }
    for (const pid of pinnedIds) {
      if (!haveIds.has(pid) && moreIds.has(pid)) {
        lazyLoadAndPromote(pid, { silent: true })
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, data.iterations.length, data.moreExecutions?.length])

  // Ordered iterations (full list in user-preferred order) — only loaded ones.
  const orderedIters = useMemo(() => {
    const byId = Object.fromEntries(data.iterations.map(i => [i.id, i]))
    return displayOrder.map(id => byId[id]).filter(Boolean)
  }, [data.iterations, displayOrder])

  const visibleIters = orderedIters.slice(0, VISIBLE_ITERS)
  const hiddenLoaded = orderedIters.slice(VISIBLE_ITERS)
  const selectedIter = orderedIters[0] || null

  const executionOptions = useMemo(() => {
    const loadedIds = new Set(data.iterations.map(i => i.id))
    const seen = new Set()
    return [...(data.moreExecutions || []), ...orderedIters, ...data.iterations]
      .filter((i) => {
        if (!i?.id || seen.has(i.id)) return false
        seen.add(i.id)
        return true
      })
      .map((i) => {
        const code = i.code || i.id.replace(/^iter-/, 'EXEC-')
        const dates = i.startDate || i.endDate ? ` · ${i.startDate || '?'} → ${i.endDate || '?'}` : ''
        const label = `${i.name} (${code})${dates}`
        return {
          label,
          value: i.id,
          loaded: loadedIds.has(i.id),
          searchText: `${label} ${executionSearchAliases(i.name)} ${i.project || ''}`,
        }
      })
  }, [orderedIters, data.iterations, data.moreExecutions])

  // Secondary dropdown choices = loaded-but-hidden + not-yet-loaded.
  const dropdownOptions = useMemo(() => {
    const visibleIds = new Set(visibleIters.map(i => i.id))
    return executionOptions.filter(o => !visibleIds.has(o.value))
  }, [executionOptions, visibleIters])

  const t = useMemo(() => totals(data.iterations), [data.iterations])
  const reqs = (selectedIter && data.requirementsByIter[selectedIter.id]) || []

  const generateStoryTestcases = useCallback(async (story) => {
    const storyId = story?.storyId
    if (!storyId) return
    const execId = Number(String(selectedIter?.id || '').replace(/^iter-/, '')) || 614
    setGeneratingStoryId(storyId)
    try {
      const json = await requestJson(`/api/zentao/story/${storyId}/testcases/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ execution_id: execId }),
      })
      if (json.error) throw new Error(json.error)

      if (json.downloadUrl) {
        const a = document.createElement('a')
        a.href = json.downloadUrl
        a.download = json.filename || ''
        document.body.appendChild(a)
        a.click()
        a.remove()
      }

      Modal.success({
        title: '测试用例已生成',
        content: (
          <Space direction="vertical" size={4}>
            <Text>{json.title || story.title}</Text>
            <Text type="secondary">{json.cases} 条用例 · 已复制 {json.images} 张截图</Text>
            {(json.missingSourceCaseIds || []).length > 0 && (
              <Text type="warning">
                源 workbook 未找到：{json.missingSourceCaseIds.join(', ')}
              </Text>
            )}
            <a href={json.downloadUrl} target="_blank" rel="noreferrer">
              {json.filename}
            </a>
            <Text code style={{ whiteSpace: 'normal' }}>{json.path}</Text>
          </Space>
        ),
      })
    } catch (e) {
      Modal.error({
        title: '生成测试用例失败',
        content: e.message || String(e),
      })
    } finally {
      setGeneratingStoryId(null)
    }
  }, [selectedIter])

  const storyData = useMemo(() => {
    if (!selectedIter) return []
    return Object.entries(selectedIter.storyByStatus || {}).map(([name, value]) => ({ name, value }))
  }, [selectedIter])
  const moduleData = (data.modules || []).map(m => ({ name: m.name, cases: m.cases }))

  // Current test owner → requirement count for the selected execution only.
  // Backend only assigns an owner from current, not-closed test tasks;
  // historical task/case evidence is shown but not counted as owner.
  const qaWorkload = useMemo(() => {
    const map = {}
    for (const r of reqs) {
      const qa = r.qa || 'Unassigned'
      if (!map[qa]) map[qa] = { qa, count: 0, reqs: [] }
      map[qa].count += 1
      map[qa].reqs.push({ ...r, _iterName: selectedIter?.name })
    }
    return Object.values(map).sort((a, b) => b.count - a.count)
  }, [reqs, selectedIter?.name])

  const reqColumns = [
    { title: 'ID', dataIndex: 'id', width: 110,
      render: (v, r) => (
        <a href={r.storyUrl} target="_blank" rel="noreferrer"
           style={{ fontFamily: 'monospace', fontSize: 11 }}
           onClick={(e) => e.stopPropagation()}>
          {v} <ExportOutlined style={{ fontSize: 10 }} />
        </a>
      ),
    },
    { title: '需求', dataIndex: 'title',
      render: (v) => <Text strong style={{ fontSize: 13 }}>{v}</Text> },
    { title: '状态', dataIndex: 'status', width: 80,
      render: (v) => (
        <Tag color={
          v === '已完成' ? 'success' :
          v === '已发布' ? 'purple' :
          v === '进行中' ? 'warning' :
          v === '已评审' ? 'processing' : 'default'
        }>{v}</Tag>
      ),
      filters: ['待评审', '已评审', '进行中', '已完成', '已发布'].map(s => ({ text: s, value: s })),
      onFilter: (val, r) => r.status === val,
    },
    { title: '测试负责人', dataIndex: 'qa', width: 140,
      render: (v, r) => {
        const isUnassigned = !v || v === 'Unassigned' || v === '—'
        const color = isUnassigned
          ? (r.qaSource === 'evidence_only' ? 'gold' : 'default')
          : 'blue'
        return (
          <Tooltip title={qaEvidenceTooltip(r)}>
            <Space direction="vertical" size={2}>
              <Tag icon={<UserOutlined />} color={color} style={{ margin: 0 }}>
                {isUnassigned ? '未指派' : v}
              </Tag>
              <Text type="secondary" style={{ fontSize: 10 }}>
                {qaSourceLabel(r.qaSource)}
              </Text>
            </Space>
          </Tooltip>
        )
      },
    },
    { title: '测试用例', dataIndex: 'cases', width: 90,
      sorter: (a, b) => a.cases - b.cases,
      render: (v, r) => v > 0
        ? (
          <Space size={4}>
            <Tag
              color="cyan"
              style={{ cursor: 'pointer', fontWeight: 600, fontSize: 12, margin: 0, padding: '1px 8px' }}
              onClick={(e) => {
                e.stopPropagation()
                setCaseModal({ open: true, story: r, bucket: null })
              }}
            >
              {v} <ExportOutlined style={{ fontSize: 10 }} />
            </Tag>
            {r.isDemo && <Tag style={{ fontSize: 9, margin: 0 }}>DEMO</Tag>}
          </Space>
        )
        : <Text type="secondary" style={{ fontSize: 12 }}>—</Text> },
    { title: '生成用例', dataIndex: 'generate', width: 112,
      render: (_, r) => (
        <Tooltip title={`按当前 Story 生成 ${projectName} 标准 xlsx 测试用例`}>
          <Button
            size="small"
            icon={<FileExcelOutlined />}
            loading={generatingStoryId === r.storyId}
            onClick={(e) => {
              e.stopPropagation()
              generateStoryTestcases(r)
            }}
          >
            生成
          </Button>
        </Tooltip>
      ),
    },
    { title: '测试执行', dataIndex: 'execRatePct', width: 280,
      sorter: (a, b) => (a.execRatePct ?? -1) - (b.execRatePct ?? -1),
      render: (pct, r) => {
        const bd = r.caseBreakdown
        if (!bd || bd.total === 0 || pct == null) {
          return <Text type="secondary" style={{ fontSize: 12 }}>—</Text>
        }
        const color = pct >= 80 ? '#52c41a' : pct >= 40 ? '#faad14' : '#ff4d4f'
        const chips = [
          { key: 'pass',        label: 'Pass',        color: '#52c41a', count: bd.pass ?? 0 },
          { key: 'fail',        label: 'Fail',        color: '#ff4d4f', count: bd.fail ?? 0 },
          { key: 'inProgress',  label: 'InProg',      color: '#faad14', count: bd.inProgress ?? 0 },
          { key: 'unexecuted',  label: 'Unexec',      color: '#8c8c8c', count: bd.unexecuted ?? 0 },
        ]
        return (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <Text style={{ fontSize: 12, color, fontWeight: 700 }}>{pct}%</Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                ({r.executedCases}/{bd.total})
              </Text>
            </div>
            <Space size={2} wrap>
              {chips.map(c => (
                <Tag
                  key={c.key}
                  style={{
                    cursor: c.count > 0 ? 'pointer' : 'default',
                    fontSize: 11, padding: '0 6px', margin: 0,
                    background: c.count > 0 ? c.color : '#fafafa',
                    color: c.count > 0 ? '#fff' : '#bfbfbf',
                    border: c.count > 0 ? 'none' : '1px solid #f0f0f0',
                    fontWeight: 600,
                  }}
                  onClick={c.count > 0 ? (e) => {
                    e.stopPropagation()
                    setCaseModal({ open: true, story: r, bucket: c.key })
                  } : undefined}
                >
                  {c.label}({c.count})
                </Tag>
              ))}
            </Space>
          </div>
        )
      },
    },
    { title: '缺陷', dataIndex: 'bugs', width: 110,
      sorter: (a, b) => a.bugs - b.bugs,
      render: (v, r) => v === 0
        ? <Text type="secondary" style={{ fontSize: 12 }}>—</Text>
        : (
          <Space size={4}>
            <Tag
              color="error"
              style={{ cursor: 'pointer', fontWeight: 600, fontSize: 13, padding: '2px 10px', margin: 0 }}
              onClick={(e) => {
                e.stopPropagation()
                setBugModal({ open: true, story: r, bugs: r.bugList || [] })
              }}
            >
              {v} <BugOutlined />
            </Tag>
            {r.severity && r.severity !== '—' && (
              <Tag color={r.severity === 'P1' ? 'volcano' : r.severity === 'P2' ? 'orange' : 'default'}
                   style={{ fontSize: 10, margin: 0 }}>
                {r.severity}
              </Tag>
            )}
          </Space>
        ),
    },
  ]

  const fetchedAt = data.meta?.fetchedAt ? new Date(data.meta.fetchedAt) : null
  const isEmpty = !loading && !error && data.iterations.length === 0
  const isUnmappedProject = data.meta?.scope === 'unmapped-project'

  // Data-sparsity flags — used to show hints and hide empty sub-cards
  const noModules = data.modules.length === 0
  const noQaThroughput = data.qaThroughput.length === 0
  const noAutoTrend = data.autoTrend.every(p => p.pct === 0)
  const allBugsZero = !selectedIter?.bugKpi?.total
  const noTaskMatrix = !qaTaskMatrix?.summary?.total
  const sparseData = productId === 0 && (noModules || noQaThroughput)

  return (
    <div style={{ maxWidth: 1400 }}>
      {/* Page header */}
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
            <DashboardOutlined style={{ color: '#1677ff', marginRight: 8 }} />
            ZenTao Integration
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            数据源：lengliwh.chandao.net
            {' | '}
            Project: {projectName}
            {' | '}
            Default product: {projectDefaultProductId || 'all'}
            {fetchedAt && (
              <>
                {' · '}<ClockCircleOutlined style={{ fontSize: 11 }} />{' '}
                {fetchedAt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                {data.meta?.cached && <Tag style={{ marginLeft: 6, fontSize: 10 }}>cached</Tag>}
              </>
            )}
          </Text>
        </div>
        <Space wrap align="start" size={8} style={{ justifyContent: 'flex-end' }}>
          <Space direction="vertical" size={2}>
            <Text type="secondary" style={{ fontSize: 12 }}>项目 / 执行</Text>
            <Select
              size="small"
              showSearch
              value={selectedIter?.id}
              placeholder="搜索执行，例如 国际版官网1.0"
              optionFilterProp="label"
              filterOption={filterExecutionOption}
              onChange={(id) => { if (id) lazyLoadAndPromote(id) }}
              options={executionOptions.map(o => ({
                ...o,
                label: o.label + (o.loaded ? '' : '  [未加载 · 点击加载]'),
              }))}
              loading={loading || lazyLoading}
              disabled={(loading && executionOptions.length === 0) || lazyLoading}
              style={{ width: 360 }}
              notFoundContent="没有匹配的执行（试试 国际版官网1.0 / 国际版 / 官网）"
            />
          </Space>
          <Space direction="vertical" size={2}>
            <Tooltip title="产品范围用于产品级模块、趋势等统计；当前明细由左侧项目 / 执行决定。">
              <Text type="secondary" style={{ fontSize: 12 }}>产品范围</Text>
            </Tooltip>
            <Select
              size="small"
              value={productId}
              disabled
              style={{ width: 260 }}
              options={[{ value: projectDefaultProductId || 0, label: projectProductLabel }]}
            />
          </Space>
          <Button
            size="small"
            icon={<ReloadOutlined spin={loading || qaTaskLoading} />}
            onClick={refreshAll}
            disabled={loading || qaTaskLoading}
            style={{ marginTop: 22 }}
          >
            刷新
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          type="error"
          showIcon
          closable
          message={`加载失败: ${error}`}
          style={{ marginBottom: 16 }}
          action={<Button size="small" onClick={refreshAll}>重试</Button>}
        />
      )}
      {data.meta?.error && !error && (
        <Alert
          type="warning"
          showIcon
          closable
          message={`后端提示: ${data.meta.error}`}
          style={{ marginBottom: 16, fontSize: 12 }}
        />
      )}

      {loading && data.iterations.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text strong style={{ fontSize: 14 }}>正在从禅道拉取数据…</Text>
          </div>
          <div style={{ marginTop: 4 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              首次冷启动 5–10 秒（禅道 SaaS 慢 + 多执行并发） · 之后 5 分钟内走缓存
            </Text>
          </div>
        </div>
      )}

      {isEmpty && (
        <Empty
          description={
            <Space direction="vertical">
              <Text type="secondary">
                {isUnmappedProject
                  ? `${projectName} has no mapped ZenTao product or execution yet`
                  : productId > 0
                  ? `产品 ${productId} 下没有活跃执行`
                  : '禅道里没有处于 doing 状态的执行'}
              </Text>
              <Button size="small" onClick={refreshAll} icon={<ReloadOutlined />}>
                重新拉取
              </Button>
            </Space>
          }
          style={{ marginTop: 40 }}
        />
      )}

      {sparseData && !loading && !isEmpty && (
        <Alert
          type="info"
          showIcon
          closable
          message={
            <Text style={{ fontSize: 12 }}>
              当前未指定产品 ID（=0），第三区的模块 / QA 吞吐 / 自动化趋势依赖产品级数据，
              输入特定产品 ID（如 146）后会自动加载。
            </Text>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {!loading && !isEmpty && selectedIter && (<>


      {/* ───────────────────────────────────────────────────────────────────
          SECTION 1：总览
          ─────────────────────────────────────────────────────────────────── */}
      <SectionHeader
        accent="#1677ff"
        icon={<DashboardOutlined />}
        title="总览"
        subtitle="核心数字 + 所有执行状态 — 点击执行卡片切换下方详情"
      />

      <Row gutter={10} style={{ marginBottom: 14 }}>
        <Col xs={12} sm={8} md={5}>
          <Card size="small" style={{ borderRadius: 10, border: '1px solid #f0f0f0', boxShadow: 'none' }}>
            <Statistic
              title="进行中执行"
              value={t.active}
              prefix={<ProjectOutlined style={{ color: '#1677ff' }} />}
              valueStyle={{ fontSize: 22 }}
            />
            <Text type="secondary" style={{ fontSize: 11 }}>共 {data.iterations.length} 个</Text>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={5}>
          <Card size="small" style={{ borderRadius: 10, border: '1px solid #f0f0f0', boxShadow: 'none' }}>
            <Statistic
              title="本月需求"
              value={selectedIter.storyTotal}
              prefix={<ApartmentOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ fontSize: 22 }}
            />
            <Text type="secondary" style={{ fontSize: 11 }}>
              完 {(selectedIter.storyByStatus?.['已完成'] ?? 0) + (selectedIter.storyByStatus?.['已发布'] ?? 0)} · 进 {selectedIter.storyByStatus?.['进行中'] ?? 0}
            </Text>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={5}>
          <Card size="small" style={{ borderRadius: 10, border: '1px solid #f0f0f0', boxShadow: 'none' }}>
            <Statistic
              title="测试用例总数"
              value={t.cases}
              prefix={<ExperimentOutlined style={{ color: '#13c2c2' }} />}
              valueStyle={{ fontSize: 22 }}
            />
            <Text type="secondary" style={{ fontSize: 11 }}>{projectName}</Text>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={5}>
          <Card size="small" style={{ borderRadius: 10, border: '1px solid #f0f0f0', boxShadow: 'none' }}>
            <Statistic
              title="自动化覆盖率"
              value={t.autoPct}
              suffix="%"
              prefix={<RobotOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ fontSize: 22, color: t.autoPct >= 50 ? '#52c41a' : '#faad14' }}
            />
            <Space size={4}>
              <RiseOutlined style={{ color: '#52c41a', fontSize: 11 }} />
              <Text style={{ fontSize: 11, color: '#52c41a' }}>+4% vs 上月</Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={8} md={4}>
          <Card size="small" style={{
            borderRadius: 10,
            border: t.bugP0 > 0 ? '1px solid #ffccc7' : '1px solid #f0f0f0',
            background: t.bugP0 > 0 ? '#fff2f0' : '#fff',
            boxShadow: 'none',
          }}>
            <Statistic
              title="激活缺陷"
              value={t.bugA}
              prefix={<BugOutlined style={{ color: t.bugP0 > 0 ? '#ff4d4f' : '#fa541c' }} />}
              valueStyle={{ fontSize: 22, color: t.bugP0 > 0 ? '#ff4d4f' : '#262626' }}
            />
            <Text type="secondary" style={{ fontSize: 11 }}>
              P0 {t.bugP0} · P1 {t.bugP1} · 已关 {t.bugC}
            </Text>
          </Card>
        </Col>
      </Row>

      <div style={{
        marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
      }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          当前查看：<Text strong style={{ color: '#1677ff' }}>{selectedIter.name}</Text>
          <Text type="secondary" style={{ fontSize: 11, marginLeft: 6 }}>
            （点击执行卡片切换 →）
          </Text>
        </Text>
        {dropdownOptions.length > 0 && (
          <Select
            size="small"
            placeholder={`其他 ${dropdownOptions.length} 个执行（可搜索: 输入名字 / EXEC-ID） ⌄`}
            value={null}
            allowClear={false}
            showSearch
            optionFilterProp="label"
            filterOption={filterExecutionOption}
            style={{ minWidth: 360, marginLeft: 'auto' }}
            onChange={(id) => { if (id) lazyLoadAndPromote(id) }}
            options={dropdownOptions.map(o => ({
              ...o,
              label: o.label + (o.loaded ? '' : '  [未加载 · 点击加载]'),
            }))}
            loading={lazyLoading}
            disabled={lazyLoading}
            notFoundContent="没有匹配的执行（试试 国际版 / 官网 等关键字）"
          />
        )}
      </div>
      <Row gutter={[10, 10]}>
        {visibleIters.map(it => (
          <Col xs={24} sm={12} md={6} key={it.id}>
            <IterationCard
              iter={it}
              isSelected={it.id === selectedIter?.id}
              onSelect={promoteIter}
            />
          </Col>
        ))}
      </Row>

      {/* ───────────────────────────────────────────────────────────────────
          SECTION 2：需求 & 功能测试
          ─────────────────────────────────────────────────────────────────── */}
      <SectionHeader
        accent="#722ed1"
        icon={<ApartmentOutlined />}
        title="需求 & 功能测试"
        subtitle={`${selectedIter.name} 的需求 / QA 指派 / 用例覆盖 / 功能缺陷`}
      />

      <Row gutter={[10, 10]}>
        <Col xs={24}>
          <SubCard
            title={<><ThunderboltOutlined style={{ color: '#722ed1' }} /> 需求明细（{reqs.length} 条）</>}
          >
            {(() => {
              // Keep the expanded requirement table readable while preserving
              // the section's rhythm with a bounded vertical scroll.
              const N = reqs.length
              const tableScrollY = N > 6
                ? Math.min(560, 96 + N * 40)
                : undefined
              return (
                <Table
                  dataSource={reqs}
                  columns={reqColumns}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  scroll={{ x: 1220, ...(tableScrollY ? { y: tableScrollY } : {}) }}
                  locale={{ emptyText: '本执行无需求' }}
                />
              )
            })()}
          </SubCard>
        </Col>
      </Row>

      <Row gutter={[10, 10]} style={{ marginTop: 10 }}>
        <Col xs={24} md={8} lg={7}>
          <SubCard
            title={<><PieChartOutlined style={{ color: '#722ed1' }} /> 需求状态分布</>}
            bodyHeight={232}
            centered
          >
            <DonutChart
              data={storyData}
              size={128}
              valueKey="value"
              labelKey="name"
              colors={Object.values(STORY_STATUS_COLOR)}
              onItemClick={(label) => setStoryStatusModal({ open: true, status: label })}
            />
          </SubCard>
        </Col>
        <Col xs={24} md={8} lg={9}>
          <SubCard
            title={<><FireOutlined style={{ color: '#ff4d4f' }} /> 缺陷概览 · Severity × 状态</>}
            extra={<Text type="secondary" style={{ fontSize: 11 }}>{selectedIter?.name || ''}</Text>}
            bodyHeight={232}
            centered
          >
            {(() => {
              const matrix = selectedIter?.bugMatrix || [[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
              const matrixBugs = selectedIter?.bugMatrixBugs || [[[],[],[]],[[],[],[]],[[],[],[]],[[],[],[]]]
              const rowLabels = ['S1', 'S2', 'S3', 'S4']
              return (
                <BugMatrix
                  matrix={matrix}
                  onCellClick={(sev, statusCol) => {
                    const bugs = matrixBugs[sev - 1][statusCol - 1] || []
                    const label = `${rowLabels[sev - 1]} · ${BUG_HEATMAP_LABELS.cols[statusCol - 1]}`
                    setHeatmapModal({ open: true, label, bugs })
                  }}
                  onRowClick={(sev) => {
                    const bugs = matrixBugs[sev - 1].flat()
                    setHeatmapModal({ open: true, label: `${rowLabels[sev - 1]} · 全部`, bugs })
                  }}
                  onColClick={(statusCol) => {
                    const bugs = [0,1,2,3].flatMap(r => matrixBugs[r][statusCol - 1])
                    setHeatmapModal({ open: true, label: `全部 · ${BUG_HEATMAP_LABELS.cols[statusCol - 1]}`, bugs })
                  }}
                  onAllClick={() => {
                    const bugs = matrixBugs.flat().flat()
                    setHeatmapModal({ open: true, label: '全部缺陷', bugs })
                  }}
                />
              )
            })()}
          </SubCard>
        </Col>
        <Col xs={24} md={8} lg={8}>
          <SubCard
            title={<><TeamOutlined style={{ color: '#fa8c16' }} /> 当前测试负责人 · 需求负载</>}
            extra={
              <Space size={6}>
                <Text type="secondary" style={{ fontSize: 11 }}>{selectedIter?.name || ''}</Text>
                <Tag color="orange" style={{ margin: 0, fontSize: 11 }}>{qaWorkload.length} 类</Tag>
              </Space>
            }
            bodyHeight={232}
            centered={qaWorkload.length === 0}
          >
            {qaWorkload.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无 QA 负载数据" />
            ) : (
              (() => {
                const max = Math.max(...qaWorkload.map(q => q.count))
                return (
                  <div style={{ maxHeight: 204, overflowY: 'auto', paddingRight: 4 }}>
                    {qaWorkload.map(q => {
                      const pct = max ? Math.round(q.count / max * 100) : 0
                      const isUnassigned = q.qa === 'Unassigned'
                      const color = isUnassigned ? '#bfbfbf'
                        : q.count >= 10 ? '#ff4d4f'
                        : q.count >= 5 ? '#faad14' : '#52c41a'
                      return (
                        <div
                          key={q.qa}
                          data-testid="qa-workload-row"
                          data-qa={q.qa}
                          onClick={() => setQaModal({ open: true, qa: q.qa, reqs: q.reqs })}
                          style={{
                            padding: '6px 4px', cursor: 'pointer', borderRadius: 4,
                            transition: 'background 0.1s',
                          }}
                          onMouseEnter={(e) => { e.currentTarget.style.background = '#f5f5f5' }}
                          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                            <Space size={4}>
                              <UserOutlined style={{ color, fontSize: 11 }} />
                              <Text strong style={{ fontSize: 12, color: isUnassigned ? '#8c8c8c' : '#262626' }}>
                                {q.qa}
                              </Text>
                            </Space>
                            <Text style={{ color, fontSize: 12, fontWeight: 700 }}>
                              {q.count} <Text type="secondary" style={{ fontSize: 11 }}>条</Text>
                            </Text>
                          </div>
                          <Progress percent={pct} size="small" showInfo={false} strokeColor={color} />
                        </div>
                      )
                    })}
                  </div>
                )
              })()
            )}
          </SubCard>
        </Col>
      </Row>

      {/* ───────────────────────────────────────────────────────────────────
          SECTION 3：全量自动化（回归）· 不随执行切换
          ─────────────────────────────────────────────────────────────────── */}
      <SectionHeader
        accent="#52c41a"
        icon={<RobotOutlined />}
        title="全量自动化（回归）"
        subtitle={`${projectName} 回归进度 · 不随上方执行切换 · 反映当前项目整体水平`}
        extra={<Tag color="default" style={{ marginRight: 0, fontSize: 11 }}>全量 · 跨执行</Tag>}
      />

      {/* All 4 cards in Section 3 use the same column split (12/12) and the
          same body height so the 2×2 grid is visually aligned regardless of
          the chart's natural aspect ratio. SVGs use viewBox to scale to the
          card width while preserving aspect ratio. */}
      <Row gutter={[10, 10]}>
        <Col xs={24} lg={12}>
          <SubCard
            title={<><LineChartOutlined style={{ color: '#52c41a' }} /> 自动化覆盖率 · 6 个月趋势</>}
            extra={
              noAutoTrend
                ? <Text type="secondary" style={{ fontSize: 11 }}>暂无自动化数据</Text>
                : <Text style={{ fontSize: 11, color: '#52c41a', fontWeight: 600 }}>
                    {data.autoTrend[0]?.pct ?? 0}% → {data.autoTrend.at(-1)?.pct ?? 0}%
                  </Text>
            }
            bodyHeight={260}
            centered
          >
            {data.autoTrend.length === 0
              ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无趋势数据" />
              : <AutoTrendChart data={data.autoTrend} width={560} height={220} />}
          </SubCard>
        </Col>
        <Col xs={24} lg={12}>
          <SubCard
            title={<><TeamOutlined style={{ color: '#fa8c16' }} /> QA 写用例数 · 按月份</>}
            extra={<Text type="secondary" style={{ fontSize: 11 }}>近 {data.qaThroughput[0]?.data.length ?? 0} 个月</Text>}
            bodyHeight={260}
            centered
          >
            {data.qaThroughput.length === 0
              ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无 QA 吞吐数据" />
              : <StackedBarChart series={data.qaThroughput} width={520} height={220} />}
          </SubCard>
        </Col>
        <Col xs={24} lg={12}>
          <SubCard
            title={<><PieChartOutlined style={{ color: '#13c2c2' }} /> 全量测试用例 · 按模块分布</>}
            extra={<Text type="secondary" style={{ fontSize: 11 }}>{data.modules.reduce((s, m) => s + m.cases, 0)} 条 · {data.modules.length} 模块</Text>}
            bodyHeight={260}
            centered
          >
            {noModules
              ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无模块数据" />
              : <DonutChart data={moduleData} size={180} valueKey="cases" labelKey="name" />}
          </SubCard>
        </Col>
        <Col xs={24} lg={12}>
          <SubCard
            title={<><ApartmentOutlined style={{ color: '#722ed1' }} /> 模块自动化覆盖排名</>}
            extra={<Text type="secondary" style={{ fontSize: 11 }}>{data.modules.length} 个模块</Text>}
            bodyHeight={260}
            centered={noModules}
          >
            {noModules ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无模块数据" />
            ) : (
            <div style={{ height: '100%', overflowY: 'auto', paddingRight: 4 }}>
              {[...data.modules]
                .map(m => ({ ...m, pct: m.cases ? Math.round(m.auto / m.cases * 100) : 0 }))
                .sort((a, b) => b.pct - a.pct)
                .map(m => {
                  const color = m.pct >= 60 ? '#52c41a' : m.pct >= 30 ? '#faad14' : '#ff4d4f'
                  return (
                    <div key={m.name} style={{ padding: '4px 0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                        <Text strong style={{ fontSize: 12 }}>{m.name}</Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          <Text style={{ color, fontWeight: 600 }}>{m.pct}%</Text>
                          <Text type="secondary"> · {m.auto}/{m.cases}</Text>
                        </Text>
                      </div>
                      <Progress percent={m.pct} size="small" showInfo={false} strokeColor={color} />
                    </div>
                  )
                })}
            </div>
            )}
          </SubCard>
        </Col>
      </Row>

      <SectionHeader
        accent="#1677ff"
        icon={<ClockCircleOutlined />}
        title="任务数量分布"
        subtitle={`${projectName} · 仅测试类任务（type=test 或名称含【测试】）· 当前项目绑定执行`}
        extra={<Tag color="blue" style={{ marginRight: 0, fontSize: 11 }}>{qaTaskMatrix?.scope || projectName}</Tag>}
      />

      <Row gutter={[10, 10]}>
        <Col span={24}>
          <SubCard
            title={<><TeamOutlined style={{ color: '#1677ff' }} /> QA 任务数量 · 人员 × 状态</>}
            extra={
              <Space size={6}>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {qaTaskMatrix?.summary?.fetchedExecutions || 0} 个执行
                </Text>
                <Text type="secondary" style={{ fontSize: 11 }}>{qaTaskMatrix?.summary?.people || 0} 位 QA</Text>
                <Tag color="blue" style={{ margin: 0, fontSize: 11 }}>{qaTaskMatrix?.summary?.total || 0} 个任务</Tag>
              </Space>
            }
            bodyHeight={360}
            centered={qaTaskLoading || qaTaskError || noTaskMatrix}
          >
            {qaTaskLoading ? (
              <Spin tip="加载 QA 任务矩阵...">
                <div style={{ minHeight: 80 }} />
              </Spin>
            ) : qaTaskError ? (
              <Alert
                type="error"
                showIcon
                message="QA 任务矩阵加载失败"
                description={qaTaskError}
                action={<Button size="small" onClick={() => fetchQaTaskMatrix(true)}>重试</Button>}
              />
            ) : noTaskMatrix ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无任务数据" />
            ) : (
              (() => {
                const taskRows = qaTaskMatrix?.ownerRows || []
                const taskCols = qaTaskMatrix?.statusColumns || []
                const taskMatrix = qaTaskMatrix?.matrix || []
                const taskMatrixTasks = qaTaskMatrix?.matrixTasks || []
                const ownerLabel = (owner) => owner || '未命名 QA'
                return (
                  <TaskOwnerStatusMatrix
                    rows={taskRows}
                    columns={taskCols}
                    matrix={taskMatrix}
                    onCellClick={(ri, ci) => {
                      const owner = taskRows[ri]
                      const col = taskCols[ci]
                      const tasks = taskMatrixTasks?.[ri]?.[ci] || []
                      setTaskModal({ open: true, label: `${ownerLabel(owner)} · ${col?.label || '未知状态'}`, tasks })
                    }}
                    onRowClick={(ri) => {
                      const owner = taskRows[ri]
                      const tasks = (taskMatrixTasks?.[ri] || []).flat()
                      setTaskModal({ open: true, label: `${ownerLabel(owner)} · 全部任务`, tasks })
                    }}
                    onColClick={(ci) => {
                      const col = taskCols[ci]
                      const tasks = taskMatrixTasks.flatMap(row => row?.[ci] || [])
                      setTaskModal({ open: true, label: `全部 QA · ${col?.label || '未知状态'}`, tasks })
                    }}
                    onAllClick={() => {
                      const tasks = taskMatrixTasks.flat().flat()
                      setTaskModal({ open: true, label: '全部 QA · 全部任务', tasks })
                    }}
                  />
                )
              })()
            )}
          </SubCard>
        </Col>
      </Row>
      </>)}

      {/* Bug list modal — opens when user clicks a non-zero "缺陷" count
          in the requirements table. Lists ZenTao bugs that link to the
          clicked story, each with a direct link to bug-view-{id}.html. */}
      <Modal
        title={
          <Space>
            <BugOutlined style={{ color: '#ff4d4f' }} />
            <Text strong>
              {bugModal.story ? `${bugModal.story.id} · ${bugModal.story.title} 的缺陷` : '缺陷列表'}
            </Text>
            <Tag color="error">{bugModal.bugs.length}</Tag>
          </Space>
        }
        open={bugModal.open}
        onCancel={() => setBugModal({ open: false, story: null, bugs: [] })}
        footer={null}
        width={680}
      >
        {bugModal.bugs.length === 0 ? (
          <Empty description="无缺陷" />
        ) : (
          <Space direction="vertical" size={6} style={{ width: '100%', maxHeight: 500, overflow: 'auto' }}>
            {bugModal.bugs.map(b => {
              const sevColor = b.severity === 1 ? '#ff4d4f' : b.severity === 2 ? '#fa8c16' : '#bfbfbf'
              const stColor = b.status === 'active' ? 'error' : b.status === 'resolved' ? 'warning' : 'success'
              return (
                <div key={b.id} style={{
                  padding: '10px 12px', borderRadius: 6,
                  background: '#fafafa', border: '1px solid #f0f0f0',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <a href={b.url} target="_blank" rel="noreferrer"
                       style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                      ZT-{b.id} <ExportOutlined style={{ fontSize: 11 }} />
                    </a>
                    <Tag color={stColor}>{b.status}</Tag>
                    {b.severity && (
                      <Tag style={{ background: sevColor, color: '#fff', border: 'none', fontSize: 11 }}>
                        S{b.severity}
                      </Tag>
                    )}
                    {b.pri && <Tag>P{b.pri}</Tag>}
                  </div>
                  <Text style={{ fontSize: 12 }}>{b.title}</Text>
                  {b.assignedTo && (
                    <div style={{ marginTop: 2 }}>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        指派给: {b.assignedTo}
                      </Text>
                    </div>
                  )}
                </div>
              )
            })}
          </Space>
        )}
      </Modal>

      {/* Story-status list modal — opens when user clicks a row in the
          需求状态分布 donut legend. Shows stories in that status with
          links to ZenTao. */}
      {(() => {
        const status = storyStatusModal.status
        const filtered = reqs.filter(r => r.status === status)
        return (
          <Modal
            title={
              <Space>
                <PieChartOutlined style={{ color: '#722ed1' }} />
                <Text strong>{selectedIter?.name} · 需求状态: {status}</Text>
                <Tag color="purple">{filtered.length}</Tag>
              </Space>
            }
            open={storyStatusModal.open}
            onCancel={() => setStoryStatusModal({ open: false, status: null })}
            footer={null}
            width={680}
          >
            {filtered.length === 0 ? (
              <Empty description={`无 ${status} 状态需求`} />
            ) : (
              <Space direction="vertical" size={6} style={{ width: '100%', maxHeight: 500, overflow: 'auto' }}>
                {filtered.map(r => (
                  <div key={r.id} style={{
                    padding: '8px 12px', borderRadius: 6,
                    background: '#fafafa', border: '1px solid #f0f0f0',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <a href={r.storyUrl} target="_blank" rel="noreferrer"
                         style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>
                        {r.id} <ExportOutlined style={{ fontSize: 11 }} />
                      </a>
                      <Tag color="processing" style={{ fontSize: 10 }}>{r.status}</Tag>
                      <Tag icon={<UserOutlined />} color={r.qa === 'Unassigned' ? 'default' : 'blue'}
                           style={{ fontSize: 10 }}>{r.qa}</Tag>
                    </div>
                    <div style={{ marginTop: 3 }}>
                      <Text style={{ fontSize: 12 }}>{r.title}</Text>
                    </div>
                  </div>
                ))}
              </Space>
            )}
          </Modal>
        )
      })()}

      {/* Bug-matrix modal — opens when user clicks any cell of the
          Severity × 状态 grid (or a row/col total / KPI). Lists the bugs
          in the selected slice with links to ZenTao. */}
      <Modal
        title={
          <Space>
            <FireOutlined style={{ color: '#ff4d4f' }} />
            <Text strong>{heatmapModal.label}</Text>
            <Tag color="error">{heatmapModal.bugs.length}</Tag>
          </Space>
        }
        open={heatmapModal.open}
        onCancel={() => setHeatmapModal({ open: false, label: '', bugs: [] })}
        footer={null}
        width={680}
      >
        {heatmapModal.bugs.length === 0 ? (
          <Empty description="无缺陷" />
        ) : (
          <Space direction="vertical" size={6} style={{ width: '100%', maxHeight: 500, overflow: 'auto' }}>
            {heatmapModal.bugs.map(b => {
              const sevColor = b.severity === 1 ? '#ff4d4f' : b.severity === 2 ? '#fa8c16' : '#bfbfbf'
              const stColor = b.status === 'active' ? 'error' : b.status === 'resolved' ? 'warning' : 'success'
              return (
                <div key={b.id} style={{
                  padding: '10px 12px', borderRadius: 6,
                  background: '#fafafa', border: '1px solid #f0f0f0',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <a href={b.url} target="_blank" rel="noreferrer"
                       style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                      ZT-{b.id} <ExportOutlined style={{ fontSize: 11 }} />
                    </a>
                    <Tag color={stColor}>{b.status}</Tag>
                    {b.severity && (
                      <Tag style={{ background: sevColor, color: '#fff', border: 'none', fontSize: 11 }}>
                        S{b.severity}
                      </Tag>
                    )}
                    {b.pri && <Tag>P{b.pri}</Tag>}
                  </div>
                  <Text style={{ fontSize: 12 }}>{b.title}</Text>
                  {b.assignedTo && (
                    <div style={{ marginTop: 2 }}>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        指派给: {b.assignedTo}
                      </Text>
                    </div>
                  )}
                </div>
              )
            })}
          </Space>
        )}
      </Modal>

      {/* Task matrix modal — opens when user clicks any person × status cell
          in the bottom task-count matrix. */}
      <Modal
        title={
          <Space>
            <ClockCircleOutlined style={{ color: '#1677ff' }} />
            <Text strong>{taskModal.label}</Text>
            <Tag color="blue">{taskModal.tasks.length}</Tag>
          </Space>
        }
        open={taskModal.open}
        onCancel={() => setTaskModal({ open: false, label: '', tasks: [] })}
        footer={null}
        width={720}
      >
        {taskModal.tasks.length === 0 ? (
          <Empty description="无任务" />
        ) : (
          <Space direction="vertical" size={6} style={{ width: '100%', maxHeight: 520, overflow: 'auto' }}>
            {taskModal.tasks.map(t => (
              <div key={t.id || `${t.owner}-${t.name}`} style={{
                padding: '8px 12px', borderRadius: 6,
                background: '#fafafa', border: '1px solid #f0f0f0',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  {t.url ? (
                    <a href={t.url} target="_blank" rel="noreferrer"
                       style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>
                      TASK-{t.id} <ExportOutlined style={{ fontSize: 11 }} />
                    </a>
                  ) : (
                    <Text code style={{ fontSize: 12 }}>TASK-{t.id || '—'}</Text>
                  )}
                  <Tag color={t.status === 'doing' ? 'warning' : t.status === 'done' || t.status === 'closed' ? 'success' : 'default'}
                       style={{ fontSize: 10 }}>
                    {t.statusLabel || t.status || 'unknown'}
                  </Tag>
                  <Tag icon={<UserOutlined />} color={t.owner === 'Unassigned' ? 'default' : 'blue'}
                       style={{ fontSize: 10 }}>
                    {t.owner === 'Unassigned' ? '未指派' : t.owner}
                  </Tag>
                  {t.executionId && <Tag style={{ fontSize: 10 }}>EXEC-{t.executionId}</Tag>}
                  {t.storyId && <Tag style={{ fontSize: 10 }}>STORY-{t.storyId}</Tag>}
                  {t.date && <Text type="secondary" style={{ fontSize: 11 }}>{t.date.slice(0, 10)}</Text>}
                </div>
                <div style={{ marginTop: 3 }}>
                  <Text style={{ fontSize: 12 }}>{t.name || '未命名任务'}</Text>
                </div>
              </div>
            ))}
          </Space>
        )}
      </Modal>

      {/* Test-owner workload modal — opens when user clicks a row in the
          current test owner card. Lists every requirement assigned to that
          owner by current test task, with evidence shown per row. */}
      <Modal
        title={
          <Space>
            <TeamOutlined style={{ color: '#fa8c16' }} />
            <Text strong>{qaModal.qa === 'Unassigned' ? '未指派' : qaModal.qa} · 当前测试任务归属</Text>
            <Tag color="orange">{qaModal.reqs.length}</Tag>
          </Space>
        }
        open={qaModal.open}
        onCancel={() => setQaModal({ open: false, qa: null, reqs: [] })}
        footer={null}
        width={720}
      >
        {qaModal.reqs.length === 0 ? (
          <Empty description="无当前测试任务归属" />
        ) : (
          <Space direction="vertical" size={6} style={{ width: '100%', maxHeight: 520, overflow: 'auto' }}>
            {qaModal.reqs.map(r => (
              <div key={`${r._iterName}-${r.id}`} style={{
                padding: '8px 12px', borderRadius: 6,
                background: '#fafafa', border: '1px solid #f0f0f0',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <a href={r.storyUrl} target="_blank" rel="noreferrer"
                     style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>
                    {r.id} <ExportOutlined style={{ fontSize: 11 }} />
                  </a>
                  <Tag color="processing" style={{ fontSize: 10 }}>{r.status}</Tag>
                  <Tag style={{ fontSize: 10 }}>{r._iterName}</Tag>
                  <Tooltip title={qaEvidenceTooltip(r)}>
                    <Tag color={r.qaSource === 'current_test_task' ? 'blue' : 'gold'} style={{ fontSize: 10 }}>
                      {qaSourceLabel(r.qaSource)}
                    </Tag>
                  </Tooltip>
                  {r.bugs > 0 && (
                    <Tag color="error" style={{ fontSize: 10 }}>
                      <BugOutlined /> {r.bugs}
                    </Tag>
                  )}
                </div>
                <div style={{ marginTop: 3 }}>
                  <Text style={{ fontSize: 12 }}>{r.title}</Text>
                </div>
              </div>
            ))}
          </Space>
        )}
      </Modal>

      {/* Test-case list modal — opens from 测试用例 count OR a 测试执行 chip.
          When `bucket` is set, only cases in that bucket are listed. */}
      {(() => {
        const story = caseModal.story
        const bucket = caseModal.bucket
        const allCases = story?.caseList || []
        const filtered = bucket ? allCases.filter(c => c.bucket === bucket) : allCases
        const BUCKET_LABEL = {
          pass: 'Pass · 通过', fail: 'Fail · 失败',
          inProgress: 'In Progress · 进行中', unexecuted: 'Unexecuted · 未执行',
        }
        const BUCKET_COLOR = {
          pass: 'success', fail: 'error', inProgress: 'warning', unexecuted: 'default',
        }
        return (
          <Modal
            title={
              <Space>
                <ExperimentOutlined style={{ color: '#13c2c2' }} />
                <Text strong>
                  {story?.id} · 测试用例 {bucket ? `· ${BUCKET_LABEL[bucket]}` : '(全部)'}
                </Text>
                <Tag color={bucket ? BUCKET_COLOR[bucket] : 'cyan'}>{filtered.length}</Tag>
                {story?.isDemo && <Tag color="orange">DEMO DATA</Tag>}
              </Space>
            }
            open={caseModal.open}
            onCancel={() => setCaseModal({ open: false, story: null, bucket: null })}
            footer={null}
            width={720}
          >
            {filtered.length === 0 ? (
              <Empty description={bucket ? `${BUCKET_LABEL[bucket]} 无用例` : '无测试用例'} />
            ) : (
              <Space direction="vertical" size={4} style={{ width: '100%', maxHeight: 500, overflow: 'auto' }}>
                {filtered.map(c => (
                  <div key={c.id} style={{
                    padding: '8px 12px', borderRadius: 6,
                    background: '#fafafa', border: '1px solid #f0f0f0',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      {c.demo ? (
                        <Text code style={{ fontSize: 11, fontWeight: 600 }}>{c.id}</Text>
                      ) : (
                        <a href={c.url} target="_blank" rel="noreferrer"
                           style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>
                          {c.id} <ExportOutlined style={{ fontSize: 11 }} />
                        </a>
                      )}
                      <Tag color={BUCKET_COLOR[c.bucket]} style={{ fontSize: 10, margin: 0 }}>
                        {c.bucket}
                      </Tag>
                      {c.lastRunResult && (
                        <Tag style={{ fontSize: 10, margin: 0 }}>
                          last: {c.lastRunResult}
                        </Tag>
                      )}
                      {c.lastRunner && (
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          执行人: {c.lastRunner}
                        </Text>
                      )}
                    </div>
                    <div style={{ marginTop: 3 }}>
                      <Text style={{ fontSize: 12 }}>{c.title}</Text>
                    </div>
                  </div>
                ))}
              </Space>
            )}
          </Modal>
        )
      })()}
    </div>
  )
}
