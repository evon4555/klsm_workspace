import { useEffect, useMemo, useState } from 'react'
import {
  Typography, Card, Row, Col, Tag, Progress, Checkbox, Table,
  InputNumber, Tooltip, Space,
} from 'antd'
import {
  SafetyCertificateOutlined, AimOutlined, FileDoneOutlined, BugOutlined,
  ApartmentOutlined, ImportOutlined, ExportOutlined, LinkOutlined,
  CrownOutlined, HighlightOutlined, CodeOutlined, ExperimentOutlined,
  CloudServerOutlined, RightOutlined, BookOutlined, WarningFilled,
  ThunderboltOutlined, ReadOutlined, LineChartOutlined,
} from '@ant-design/icons'
import { requestJson } from '../apiClient'

const { Title, Text, Paragraph } = Typography

// ---------------------------------------------------------------------------
// Roles (used on the SDLC standards section, Phase 3 of the build flow)
// ---------------------------------------------------------------------------

const ROLES = {
  PM:       { key: 'PM',       name: '产品经理',     short: 'PM',   color: '#1677ff', icon: <CrownOutlined /> },
  Designer: { key: 'Designer', name: 'UI/UX 设计',  short: 'UI',   color: '#eb2f96', icon: <HighlightOutlined /> },
  Dev:      { key: 'Dev',      name: '开发工程师',   short: 'DEV',  color: '#52c41a', icon: <CodeOutlined /> },
  QA:       { key: 'QA',       name: '测试 (QA)',   short: 'QA',   color: '#fa8c16', icon: <ExperimentOutlined /> },
  DevOps:   { key: 'DevOps',   name: 'DevOps / SRE', short: 'OPS', color: '#722ed1', icon: <CloudServerOutlined /> },
}
const ROLE_ORDER = ['PM', 'Designer', 'Dev', 'QA', 'DevOps']

// ---------------------------------------------------------------------------
// Build phases — the top "Quality System Build Flow" strip
//
// Each phase has a `content` discriminator that decides what panel renders
// below when the phase is selected:
//   - 'sdlc'        → SDLC standards (stage strip + role swim-lanes)
//   - 'review'      → qa-harness gap review
//   - 'deliverables' (default) → generic checkbox list
// ---------------------------------------------------------------------------

const PHASES = [
  // Original Phase 1 (现状诊断) intentionally omitted per product call.
  // `id` stays at the original number to keep localStorage keys stable
  // (deliverable ids `p2-d1`, selectedPhaseId persisted, etc.).
  // `displayId` is the renumbered 1..N shown in the UI.
  {
    id: 2, displayId: 1, name: '质量目标与指标', goal: '与业务对齐质量目标', content: 'deliverables',
    input: '公司业务目标、发布节奏、风险类型',
    output: '质量目标、核心指标',
    actions: '定 5-8 个指标：逃逸缺陷率、证据完整率、自动化覆盖率、发布通过率等',
    deliverables: [
      { id: 'p2-d1', name: '质量目标（年度/项目级）' },
      { id: 'p2-d2', name: '核心质量指标定义' },
      { id: 'p2-d3', name: '指标采集渠道明确' },
    ],
  },
  {
    id: 3, displayId: 2, name: '流程标准与角色', goal: '统一 SDLC 流程 + 各角色职责', content: 'sdlc',
    input: 'SDLC 流程、团队角色、合规要求',
    output: '流程图、各阶段角色职责、质量门禁',
    actions: '为 8 个 SDLC 阶段定义角色 × 输入 × 产出 × 门禁',
  },
  {
    id: 4, displayId: 3, name: '交付物与模板', goal: '统一测试资产格式', content: 'deliverables',
    input: '历史文档、最佳实践、项目案例',
    output: '测试策略、用例、需求评审、报告、复盘模板',
    actions: '统一格式和必填项',
    deliverables: [
      { id: 'p4-d1', name: '测试策略模板' },
      { id: 'p4-d2', name: '测试用例模板' },
      { id: 'p4-d3', name: '需求评审 checklist' },
      { id: 'p4-d4', name: '测试报告模板' },
      { id: 'p4-d5', name: '复盘模板' },
    ],
  },
  {
    id: 5, displayId: 4, name: '执行与证据机制', goal: '定义什么叫"测过"', content: 'deliverables',
    input: '测试用例、环境、数据、版本',
    output: '执行记录、截图、日志、缺陷单',
    actions: '规定结果 + 证据 + 缺陷记录三件套',
    deliverables: [
      { id: 'p5-d1', name: '执行结果回填规范' },
      { id: 'p5-d2', name: '证据上传规范（截图/日志）' },
      { id: 'p5-d3', name: '缺陷登记规范' },
      { id: 'p5-d4', name: 'evidence 目录约定' },
    ],
  },
  {
    id: 6, displayId: 5, name: '自动化与平台', goal: '覆盖核心执行链路', content: 'deliverables',
    input: '核心业务流、回归场景',
    output: '自动化框架、回归集、Dashboard、报告',
    actions: '先覆盖核心链路，不追求全量自动化',
    deliverables: [
      { id: 'p6-d1', name: 'Behave + Playwright 框架' },
      { id: 'p6-d2', name: '核心回归用例集' },
      { id: 'p6-d3', name: 'Dashboard 展示自动化结果' },
      { id: 'p6-d4', name: '证据自动入库（dashboard.db）' },
    ],
  },
  {
    id: 7, displayId: 6, name: '质量门禁与发布准入', goal: '不达标不能发布', content: 'deliverables',
    input: '用例、自动化、报告、缺陷状态',
    output: 'Gate 检查、CI 门禁、发布准入',
    actions: 'gate.py 接入 CI 和发布流程',
    deliverables: [
      { id: 'p7-d1', name: 'gate.py 全绿' },
      { id: 'p7-d2', name: 'CI 门禁接入' },
      { id: 'p7-d3', name: '发布准入 checklist' },
      { id: 'p7-d4', name: 'Go/No-Go 决策机制' },
    ],
  },
  {
    id: 8, displayId: 7, name: '度量与持续改进', goal: '形成质量治理闭环', content: 'review',
    input: '缺陷、执行结果、线上问题、复盘',
    output: '质量看板、复盘记录、改进项、qa-harness 现状评审',
    actions: '复盘机制、问题反向更新模板、技能、自动化',
    deliverables: [
      { id: 'p8-d1', name: '质量看板（指标可视化）已上线' },
      { id: 'p8-d2', name: '复盘机制（按版本 / 季度）已运行' },
      { id: 'p8-d3', name: '改进项有 Owner / Due / 状态跟踪' },
      { id: 'p8-d4', name: '改进反向更新模板 / Gate / 自动化' },
      { id: 'p8-d5', name: 'qa-harness 现状评审项全部绿' },
    ],
  },
]

// ---------------------------------------------------------------------------
// SDLC stages — used when Phase 3 is selected.
//
// Per stage we list each role's inputs + outputs.
// Inputs are checkboxes (received / confirmed).
// Outputs are either:
//   - kind:'doc'   → checkbox
//   - kind:'count' → numeric pair (current / target). Auto-checked when
//                    current >= target. `linkedTo` makes target track another
//                    item's `current` value (cross-stage data binding).
//
// TODO: replace local current/target with live counts pulled from
//   - ZenTao /api.php/v1 (test case count, bug count)
//   - dashboard.db (executed scenarios)
//   - Behave junit reports (script count)
// ---------------------------------------------------------------------------

const SDLC_STAGES = [
  {
    id: 'sdlc-req', name: '需求阶段',
    purpose: '理解业务诉求 → 明确范围 → 测试点对齐',
    gate: 'PRD 评审通过 + 测试点已记录 + 用例已评审',
    roles: {
      PM: {
        inputs: [
          { id: 'req-pm-i1', name: '业务目标', from: '运营' },
          { id: 'req-pm-i2', name: '客户访谈结论', from: '运营' },
          { id: 'req-pm-i3', name: '历史相关数据', from: 'BI' },
        ],
        outputs: [
          { id: 'req-pm-o1', name: 'PRD', kind: 'doc' },
          { id: 'req-pm-o2', name: '低保真原型 / 流程图', kind: 'doc',
            note: '高保真 Figma 由 Designer 输出' },
          { id: 'req-pm-o3', name: '验收标准', kind: 'doc' },
          { id: 'req-pm-o4', name: '需求评审会议纪要', kind: 'doc' },
        ],
      },
      Designer: {
        inputs: [
          { id: 'req-ui-i1', name: 'PRD', from: 'PM' },
          { id: 'req-ui-i2', name: '用户画像', from: 'PM/运营' },
        ],
        outputs: [
          { id: 'req-ui-o1', name: '用户旅程 / 信息架构', kind: 'doc' },
          { id: 'req-ui-o2', name: 'Figma 设计稿（高保真）', kind: 'doc',
            note: 'QA 需在本阶段拿到，用于写用例' },
        ],
      },
      Dev: {
        inputs: [
          { id: 'req-dev-i1', name: 'PRD', from: 'PM' },
        ],
        outputs: [
          { id: 'req-dev-o1', name: '技术可行性评估', kind: 'doc' },
          { id: 'req-dev-o2', name: '工时评估', kind: 'doc' },
        ],
      },
      QA: {
        inputs: [
          { id: 'req-qa-i1', name: '脑图', from: 'PM' },
          { id: 'req-qa-i2', name: 'PRD', from: 'PM' },
          { id: 'req-qa-i3', name: 'Figma 设计稿', from: 'Designer' },
          { id: 'req-qa-i4', name: '历史相关缺陷', from: 'QA / 客户' },
        ],
        outputs: [
          { id: 'req-qa-o1', name: '测试用例', kind: 'count', defaultTarget: 0, note: '基于需求颗粒度估算（目标可被禅道 API 覆盖）' },
          { id: 'req-qa-o2', name: '测试用例同行评审记录', kind: 'doc', note: '至少 1 QA + 1 开发参与' },
          { id: 'req-qa-o3', name: '测试点 / 风险记录', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-design', name: '设计阶段',
    purpose: '把架构 / 接口 / 数据流转成测试策略',
    gate: '测试策略评审通过 + 关键场景策略明确',
    roles: {
      PM: {
        inputs: [{ id: 'des-pm-i1', name: 'PRD 已锁版', from: 'PM' }],
        outputs: [{ id: 'des-pm-o1', name: '设计走查 + PRD 一致性确认', kind: 'doc' }],
      },
      Designer: {
        inputs: [{ id: 'des-ui-i1', name: 'PRD', from: 'PM' }],
        outputs: [
          { id: 'des-ui-o1', name: '交互细节 / 边界态设计', kind: 'doc' },
          { id: 'des-ui-o2', name: '设计规范 / 设计 Token', kind: 'doc' },
        ],
      },
      Dev: {
        inputs: [
          { id: 'des-dev-i1', name: 'PRD', from: 'PM' },
          { id: 'des-dev-i2', name: '设计稿', from: 'Designer' },
        ],
        outputs: [
          { id: 'des-dev-o1', name: '系统架构图', kind: 'doc' },
          { id: 'des-dev-o2', name: 'API 接口文档 (Swagger)', kind: 'doc' },
          { id: 'des-dev-o3', name: '数据模型 / 表结构', kind: 'doc' },
          { id: 'des-dev-o4', name: '数据流图 / 状态机', kind: 'doc' },
        ],
      },
      QA: {
        inputs: [
          { id: 'des-qa-i1', name: '系统架构图', from: 'Dev' },
          { id: 'des-qa-i2', name: 'API 文档', from: 'Dev' },
          { id: 'des-qa-i3', name: '数据流图 / 状态机', from: 'Dev' },
          { id: 'des-qa-i4', name: '权限 / 角色定义', from: 'PM' },
        ],
        outputs: [
          { id: 'des-qa-o1', name: '测试策略', kind: 'doc' },
          { id: 'des-qa-o2', name: '接口测试方案', kind: 'doc' },
          { id: 'des-qa-o3', name: '非功能测试方案 (性能 / 安全)', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [{ id: 'des-ops-i1', name: '架构图', from: 'Dev' }],
        outputs: [{ id: 'des-ops-o1', name: '环境部署方案', kind: 'doc' }],
      },
    },
  },
  {
    id: 'sdlc-dev', name: '开发阶段',
    purpose: 'QA 同步开发产物 → 准备自动化与冒烟',
    gate: '开发自测通过 + 冒烟脚本就位 + 关键接口可调',
    roles: {
      PM: {
        inputs: [],
        outputs: [{ id: 'dev-pm-o1', name: '需求澄清答疑', kind: 'doc' }],
      },
      Designer: {
        inputs: [],
        outputs: [{ id: 'dev-ui-o1', name: '设计走查 (实现 vs 设计)', kind: 'doc' }],
      },
      Dev: {
        inputs: [
          { id: 'dev-dev-i1', name: '冻结后的需求 + 设计', from: 'PM / Designer' },
        ],
        outputs: [
          { id: 'dev-dev-o1', name: '编码完成', kind: 'doc' },
          { id: 'dev-dev-o2', name: '单元测试覆盖率', kind: 'count', defaultTarget: 60, unit: '%', note: '行覆盖率 ≥ 60%' },
          { id: 'dev-dev-o3', name: '代码评审通过', kind: 'doc' },
          { id: 'dev-dev-o4', name: 'CI 构建绿', kind: 'doc' },
        ],
      },
      QA: {
        inputs: [
          { id: 'dev-qa-i1', name: 'API 文档 (最新版)', from: 'Dev' },
          { id: 'dev-qa-i2', name: '系统架构图 (最新版)', from: 'Dev' },
          { id: 'dev-qa-i3', name: '数据库 Schema / 测试数据', from: 'Dev' },
          { id: 'dev-qa-i4', name: '开发自测 / 冒烟报告', from: 'Dev' },
        ],
        outputs: [
          { id: 'dev-qa-o1', name: '测试脚本 (自动化)', kind: 'count', defaultTarget: 0,
            linkedTo: 'req-qa-o1', note: '与测试用例 1:1，目标 = 测试用例数（自动同步）' },
          { id: 'dev-qa-o2', name: '接口冒烟脚本', kind: 'count', defaultTarget: 0 },
          { id: 'dev-qa-o3', name: '测试数据脚本', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [
          { id: 'dev-ops-o1', name: 'CI 流水线配置', kind: 'doc' },
          { id: 'dev-ops-o2', name: '测试环境可用 (SIT)', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-testdesign', name: '测试设计',
    purpose: '细化用例 + 准备数据，让需求阶段写的用例可执行',
    gate: '边界 / 异常 / 权限场景已纳入 + 测试数据已准备 + 用例最终冻结',
    roles: {
      PM: {
        inputs: [],
        outputs: [{ id: 'td-pm-o1', name: '用例评审参与', kind: 'doc' }],
      },
      Dev: {
        inputs: [],
        outputs: [{ id: 'td-dev-o1', name: '技术细节澄清', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'td-qa-i1', name: '需求 + 风险清单', from: 'PM / QA' },
          { id: 'td-qa-i2', name: '历史缺陷库 (禅道)', from: 'QA' },
          { id: 'td-qa-i3', name: '需求阶段已写的测试用例', from: 'QA' },
        ],
        outputs: [
          // No new count here — 测试用例 lives in 需求阶段 to avoid double-counting.
          // 测试设计 is refinement work on top of it.
          { id: 'td-qa-o1', name: '用例细化（边界 / 异常 / 权限）', kind: 'doc' },
          { id: 'td-qa-o2', name: '测试数据集设计', kind: 'doc' },
          { id: 'td-qa-o3', name: '用例最终冻结 / 版本号确定', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-execute', name: '测试执行',
    purpose: '按用例执行 + 证据 + 缺陷登记',
    gate: '执行率 100% + 缺陷有归属 + 证据完整',
    roles: {
      PM: {
        inputs: [],
        outputs: [
          { id: 'ex-pm-o1', name: '缺陷优先级裁定', kind: 'doc' },
          { id: 'ex-pm-o2', name: 'UAT 验收', kind: 'doc' },
        ],
      },
      Dev: {
        inputs: [{ id: 'ex-dev-i1', name: '缺陷单 (禅道)', from: 'QA' }],
        outputs: [{ id: 'ex-dev-o1', name: '缺陷修复 + 提测', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'ex-qa-i1', name: '测试环境 (SIT/UAT) 可用', from: 'DevOps' },
          { id: 'ex-qa-i2', name: '可测版本 (Build)', from: 'Dev' },
          { id: 'ex-qa-i3', name: '测试数据已准备', from: 'QA' },
        ],
        outputs: [
          { id: 'ex-qa-o1', name: '执行记录 (Pass / Fail)', kind: 'count', defaultTarget: 0,
            linkedTo: 'req-qa-o1', note: '目标 = 测试用例数（自动同步）' },
          { id: 'ex-qa-o2', name: '缺陷单 (禅道)', kind: 'count', defaultTarget: 0, note: '禅道 API 可自动拉取' },
          { id: 'ex-qa-o3', name: '截图 / 日志证据', kind: 'doc' },
          { id: 'ex-qa-o4', name: '日报 / 进度同步', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [{ id: 'ex-ops-o1', name: '测试环境稳定运行', kind: 'doc' }],
      },
    },
  },
  {
    id: 'sdlc-regress', name: '回归阶段',
    purpose: '保证修复不引入新问题',
    gate: '高风险路径回归全绿',
    roles: {
      Dev: {
        inputs: [],
        outputs: [{ id: 'rg-dev-o1', name: '修复缺陷自验证', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'rg-qa-i1', name: '修复缺陷列表 (禅道)', from: 'QA' },
          { id: 'rg-qa-i2', name: '影响范围说明', from: 'Dev' },
        ],
        outputs: [
          { id: 'rg-qa-o1', name: '回归计划', kind: 'doc' },
          { id: 'rg-qa-o2', name: '自动化回归运行', kind: 'count', defaultTarget: 0 },
          { id: 'rg-qa-o3', name: '回归报告', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-release', name: '执行评审阶段',
    purpose: '给出 QA readiness 结论，不替代业务发布决策',
    gate: '执行结果明确 + 风险 Owner 签字',
    roles: {
      PM: {
        inputs: [],
        outputs: [
          { id: 'rl-pm-o1', name: 'Go / No-Go 决策', kind: 'doc' },
          { id: 'rl-pm-o2', name: '发布通告 / 用户告知', kind: 'doc' },
        ],
      },
      Dev: {
        inputs: [],
        outputs: [{ id: 'rl-dev-o1', name: '发布包 / 部署脚本', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'rl-qa-i1', name: '所有用例执行完毕', from: 'QA' },
          { id: 'rl-qa-i2', name: '遗留缺陷状态确认', from: 'QA + PM' },
        ],
        outputs: [
          { id: 'rl-qa-o1', name: 'QA Readiness Report', kind: 'doc' },
          { id: 'rl-qa-o2', name: '执行风险接受记录', kind: 'doc' },
          { id: 'rl-qa-o3', name: '执行评审 checklist 已过', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [
          { id: 'rl-ops-o1', name: '生产部署', kind: 'doc' },
          { id: 'rl-ops-o2', name: '监控告警就位', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-postrelease', name: '上线反馈阶段',
    purpose: '监控 + 复盘 + 反向改进',
    gate: '问题闭环 + 改进闭环',
    roles: {
      PM: {
        inputs: [{ id: 'po-pm-i1', name: '上线数据 / 用户反馈', from: 'Ops / SRE' }],
        outputs: [{ id: 'po-pm-o1', name: '数据复盘 + 改进项跟踪', kind: 'doc' }],
      },
      Dev: {
        inputs: [],
        outputs: [{ id: 'po-dev-o1', name: '线上 bug 修复', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'po-qa-i1', name: '上线监控数据', from: 'DevOps / SRE' },
          { id: 'po-qa-i2', name: '用户 / 客服反馈', from: '运营' },
        ],
        outputs: [
          { id: 'po-qa-o1', name: '上线问题复盘', kind: 'doc' },
          { id: 'po-qa-o2', name: '上线缺陷分析', kind: 'doc' },
          { id: 'po-qa-o3', name: '改进项 (有 Owner / Due)', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [
          { id: 'po-ops-o1', name: '监控告警闭环', kind: 'doc' },
          { id: 'po-ops-o2', name: 'SLA 报告', kind: 'doc' },
        ],
      },
    },
  },
]

const HARNESS_REVIEW = [
  { module: '流程标准', status: 'partial', gap: '需要在真实项目中持续强制执行', action: '在门禁中真项目落地' },
  { module: '模板体系', status: 'partial', gap: 'QA Readiness Report 需要与 06-execution-review 串联', action: '生成执行评审报告和风险接受记录' },
  { module: '自动化平台', status: '已有基础', gap: '项目首页/SKU 详情未自动化', action: '补齐核心链路覆盖' },
  { module: '证据机制', status: '已有但拒收', gap: 'gate 显示 comments/截图/状态等问题', action: '先把 gate.py 跑绿' },
  { module: '质量门禁', status: '已有工具', gap: '当前 OVERALL FAIL，未接入 CI', action: '修复失败项接入 CI' },
  { module: '度量看板', status: '雏形中', gap: '指标定义未完全自动化', action: '自动汇总各阶段指标' },
  { module: '复盘闭环', status: '偏弱', gap: '缺执行评审、上线反馈、签字流', action: '用 execution review 模板实例化' },
  { module: '持续运营机制', status: '偏弱', gap: '不是 Git 仓库，无 .gitignore', action: '建立版本与可审计性' },
]

// ---------------------------------------------------------------------------
// PHASE_RICH — depth content per phase, sourced from industry frameworks:
//
//   • DORA Four Keys (https://dora.dev/guides/dora-metrics-four-keys/)
//   • ISO/IEC 25010:2023 — Software product quality model
//   • IEEE 829-2008 — Test documentation standards
//   • ISTQB Foundation — Defect lifecycle, test process
//   • Mike Cohn / Martin Fowler — Test Pyramid
//   • Scrum Guide — Definition of Done / Ready
//
// keyed by phase.id (NOT displayId — id is stable across renumbering)
// ---------------------------------------------------------------------------

const PHASE_RICH = {
  // ---- Phase 2 / id=3  流程标准与角色（SDLC） -------------------------------
  3: {
    brief: '每个 SDLC 阶段定义清楚：谁做什么、输入什么、产出什么、Gate 在哪。RACI 是行业语言。',
    frameworks: [
      { name: 'RACI Matrix', url: 'https://www.pmi.org/learning/library/raci-matrix-creating-clarity-9534',
        summary: 'PMI 标准的角色责任矩阵：Responsible / Accountable / Consulted / Informed' },
      { name: 'ISTQB Foundation', url: 'https://www.istqb.org/',
        summary: '测试过程 7 活动 + 各角色分工的国际基准（CTFL 大纲）' },
      { name: 'SAFe Agile Roles', url: 'https://scaledagileframework.com/',
        summary: '大规模 Agile 框架的角色定义（PO / SM / Dev / QA / RTE…）' },
    ],
    sections: [],
    antiPatterns: [
      '所有人都对，所有人都不对 — RACI 里 Accountable 必须唯一',
      '角色清单写了但不在 PR / 评审里被引用 — 流于形式',
      '只有 QA 角色被细化，其他角色一句话带过 — 跨职能协作没基础',
    ],
  },

  // ---- Phase 1 / id=2  质量目标与指标 ----------------------------------------
  2: {
    brief: '把"质量好不好"变成"质量数字"。北极星指标驱动整个体系的优先级。',
    frameworks: [
      { name: 'DORA Four Keys', url: 'https://dora.dev/guides/dora-metrics-four-keys/',
        summary: 'Google DORA 团队定义的 4 项交付绩效指标，行业基准（精英团队按需部署 + 1 小时内恢复 + CFR 0-15%）' },
      { name: 'ISO/IEC 25010:2023', url: 'https://www.iso.org/standard/35733.html',
        summary: '8 大质量属性 × 31 子属性，软件质量评估的世界基准' },
      { name: 'ISTQB Defect Metrics', url: 'https://www.istqb.org/',
        summary: '逃逸缺陷率 (DER)、缺陷去除率 (DRE)、缺陷密度等经典 QA 指标' },
    ],
    sections: [
      {
        kind: 'kpiCatalog', title: 'KPI 目录（你的"北极星"）',
        columns: ['指标', '公式', '团队目标', '精英标杆', '采集来源', '类别'],
        rows: [
          ['部署频率 (DF)', '生产部署次数 / 周',           '每日 ≥ 1', '按需',           'CI/CD',       'DORA'],
          ['变更前置时间 (LT)', 'commit → 生产用时',       '< 1 天',   '< 1 小时',       'CI/CD',       'DORA'],
          ['变更失败率 (CFR)', '失败部署 / 总部署',         '< 15%',    '0-15%',          'CI/CD+监控',  'DORA'],
          ['恢复时间 (MTTR)', '故障开始 → 恢复用时',       '< 1 天',   '< 1 小时',       '监控告警',    'DORA'],
          ['逃逸缺陷率 (DER)', '上线后缺陷 / 总缺陷',       '< 5%',     '< 1%',           '禅道',        'QA'],
          ['缺陷去除率 (DRE)', '上线前发现缺陷 / 总缺陷',   '≥ 95%',    '≥ 99%',          '禅道',        'QA'],
          ['自动化覆盖率', '自动化用例 / 总用例',           '≥ 50%',    '≥ 80%',          'dashboard.db','QA'],
          ['证据完整率', '完整证据用例 / 执行用例',         '100%',     '100%',           'gate.py',     'QA'],
        ],
      },
      {
        kind: 'iso25010', title: 'ISO 25010 八大质量属性 — 测试目标拆分',
        items: [
          { name: '功能性', sub: '完整性 / 正确性 / 适合性' },
          { name: '性能效率', sub: '时间特性 / 资源利用 / 容量' },
          { name: '兼容性', sub: '共存性 / 互操作性' },
          { name: '可用性', sub: '易学 / 易操作 / 用户错误防护 / 美学 / 可访问性' },
          { name: '可靠性', sub: '成熟性 / 可用性 / 容错性 / 可恢复性' },
          { name: '安全性', sub: '机密性 / 完整性 / 不可否认性 / 可问责性 / 真实性' },
          { name: '可维护性', sub: '模块化 / 可重用性 / 可分析性 / 可修改性 / 可测试性' },
          { name: '可移植性', sub: '适应性 / 可安装性 / 可替换性' },
        ],
      },
    ],
    antiPatterns: [
      '指标只展示不行动 — dashboard 不连改进项 = 装饰',
      '只看测试用例数不看覆盖率与逃逸率 — case 多 ≠ 测得好',
      '指标依赖人肉采集 — 不自动化就会断',
      '所有指标都重要 = 没有北极星 — 选 3-5 个就够',
    ],
  },

  // ---- Phase 3 / id=4  交付物与模板 ------------------------------------------
  4: {
    brief: '模板降低团队上手门槛 + 保证产出一致。IEEE 829 + ISTQB 是行业基准。',
    frameworks: [
      { name: 'IEEE 829-2008', url: 'https://standards.ieee.org/ieee/829/4453/',
        summary: '8 大测试文档标准：Master Plan / Level Plan / Design Spec / Case Spec / Procedure Spec / Item Transmittal Report / Log / Incident Report / Summary Report' },
      { name: 'ISTQB Foundation Test Process', url: 'https://www.istqb.org/',
        summary: '测试过程 7 活动：planning / monitoring / analysis / design / implementation / execution / completion' },
    ],
    sections: [
      {
        kind: 'templateCatalog', title: '模板目录（对应 IEEE 829）',
        columns: ['模板', 'IEEE 829 对应', '关键章节', 'Owner'],
        rows: [
          ['测试策略',          'Master Test Plan',          'Scope / Approach / Risks / Schedule / Resources', 'Test Manager'],
          ['测试用例',          'Test Case Specification',   '前置 / 步骤 / 期望 / 实际 / Pass/Fail',         'QA'],
          ['需求评审 Checklist', '—',                         '可测性 / 完整性 / 边界 / 权限 / 数据干扰',      'QA Lead'],
          ['测试报告',          'Test Summary Report',       '执行统计 / 缺陷分布 / 风险 / Go/No-Go 建议',    'Test Manager'],
          ['复盘报告',          '—',                         'Went well / Didn\'t / Improve / Owners',        'Team'],
          ['缺陷报告',          'Test Incident Report',      '标题 / 步骤 / 期望 / 实际 / 严重 / 优先 / 环境 / 截图', 'QA'],
        ],
      },
    ],
    antiPatterns: [
      '模板太厚 → 填表疲劳 → 团队跳过',
      '模板放 Wiki 没人维护 → 版本过时 → 团队自己 fork',
      '没有 Owner → 没人为模板质量负责',
    ],
  },

  // ---- Phase 4 / id=5  执行与证据机制 ----------------------------------------
  5: {
    brief: '"测过"不是"跑过"。结果 + 证据 + 缺陷三件套缺一不可，audit trail 是基础。',
    frameworks: [
      { name: 'ISTQB Defect Lifecycle', url: 'https://www.istqb.org/',
        summary: '标准缺陷状态机：New → Assigned → Open → Fixed → Retest → Verified → Closed' },
      { name: 'Severity × Priority Matrix', url: 'https://www.istqb.org/',
        summary: 'Severity = 技术严重程度，Priority = 业务紧急度；两者独立，二维矩阵决定处理顺序' },
    ],
    sections: [
      {
        kind: 'defectLifecycle', title: '缺陷状态机（ISTQB 标准）',
        states: [
          { name: 'New', color: '#1677ff', desc: '刚发现，未分配' },
          { name: 'Assigned', color: '#13c2c2', desc: '已派给开发' },
          { name: 'Open', color: '#fa8c16', desc: '开发确认，待修' },
          { name: 'Fixed', color: '#722ed1', desc: '开发修复，待 QA 验证' },
          { name: 'Verified', color: '#52c41a', desc: 'QA 验证通过' },
          { name: 'Closed', color: '#389e0d', desc: '关闭归档' },
        ],
        sideStates: ['Reopened', 'Rejected', 'Deferred', 'Duplicate'],
      },
      {
        kind: 'severityMatrix', title: 'Severity × Priority 处理矩阵',
        cols: ['P1 立即', 'P2 本版', 'P3 下版'],
        rows: ['S1 致命', 'S2 严重', 'S3 一般', 'S4 轻微'],
        cells: [
          [{ text: '立即修', color: '#ff4d4f' }, { text: '本版必修', color: '#ff7a45' }, { text: '下版必修', color: '#fa8c16' }],
          [{ text: '立即修', color: '#ff4d4f' }, { text: '本版必修', color: '#ff7a45' }, { text: '排期', color: '#faad14' }],
          [{ text: '本版必修', color: '#ff7a45' }, { text: '排期', color: '#faad14' }, { text: '排期或拒绝', color: '#d9d9d9' }],
          [{ text: '排期', color: '#faad14' }, { text: '排期或拒绝', color: '#d9d9d9' }, { text: '可拒绝', color: '#bfbfbf' }],
        ],
      },
      {
        kind: 'evidenceRules', title: '证据规范（按测试类型）',
        columns: ['测试类型', '必需证据', '可选证据'],
        rows: [
          ['功能测试', '步骤截图 + 结果截图', '操作录屏'],
          ['接口测试', 'Request + Response + Status Code', '抓包日志'],
          ['性能测试', 'Locust 汇总 + Grafana 截图', 'Prometheus 原始查询'],
          ['兼容性', '设备截图（含 UA）', 'BrowserStack 链接'],
          ['安全测试', '工具报告 + 复现步骤', 'CVE 引用'],
        ],
      },
    ],
    antiPatterns: [
      'Pass / Fail 不写原因 → 复盘无证据',
      '缺陷无 Owner / 无 Due → 烂在系统里',
      '证据是个 zip 包没人看 → 等于没有',
      '"重新跑一遍就过了" → 没记 flaky 标记 → 下次还是这样',
    ],
  },

  // ---- Phase 5 / id=6  自动化与平台 ------------------------------------------
  6: {
    brief: '测试金字塔不是规则是经济学：底层多 + 顶层少 = 反馈快 + 成本低。',
    frameworks: [
      { name: 'Mike Cohn Test Pyramid', url: 'https://martinfowler.com/bliki/TestPyramid.html',
        summary: 'Cohn《Succeeding with Agile》(2009) 首提；底宽顶窄；70/20/10 的经验比例' },
      { name: 'Practical Test Pyramid (Fowler)', url: 'https://martinfowler.com/articles/practical-test-pyramid.html',
        summary: 'Fowler 强调 E2E 是"二线防御"；E2E 失败 = 一个 bug + 一个单元测试缺口' },
      { name: 'Testing Honeycomb (微服务)', url: 'https://engineering.atspotify.com/2018/01/testing-of-microservices/',
        summary: '微服务架构下，integration 层增厚成"蜂巢"形' },
    ],
    sections: [
      {
        kind: 'testPyramid', title: '测试金字塔 — 理想比例',
        layers: [
          { layer: 'E2E / UI',           pct: 10, speed: '慢 (分钟)', flaky: '高', maintain: '高', stack: 'Behave + Playwright' },
          { layer: 'Integration / API',  pct: 20, speed: '中 (秒)',   flaky: '中', maintain: '中', stack: 'requests + pytest' },
          { layer: 'Unit',               pct: 70, speed: '快 (毫秒)', flaky: '低', maintain: '低', stack: 'pytest / Vitest' },
        ],
      },
      {
        kind: 'toolStack', title: '当前工具栈',
        columns: ['层', '工具', '当前状态'],
        rows: [
          ['E2E', 'Behave + Playwright', '已落地'],
          ['API', 'requests + pytest', '部分'],
          ['Unit', 'pytest / Vitest', '由开发负责'],
          ['性能', 'Locust + Prometheus + Grafana', '已落地'],
          ['日志', 'Loki', '已落地'],
          ['看板', 'FastAPI + Vite + Ant Design', '已落地'],
        ],
      },
    ],
    antiPatterns: [
      'Ice Cream Cone (反金字塔) — E2E 多 + 单元少 → 慢 + flaky',
      'Selenium / Playwright 测后端逻辑 → 应该用单元测试',
      'CSS 选择器写死 → 一改 UI 全挂；用 data-testid',
      'sleep() 代替显式等待 → 慢 + flaky',
    ],
  },

  // ---- Phase 6 / id=7  质量门禁与发布准入 ------------------------------------
  7: {
    brief: 'Gate 不是阻挠是保险。DoR / DoD 让团队对"准备好了"有共同语言。',
    frameworks: [
      { name: 'Scrum Guide — DoD', url: 'https://scrumguides.org/scrum-guide.html#done',
        summary: 'Scrum Guide 强制要求 DoD 是"做完了"的统一标准；Sutherland《Be Ready to be Done》延伸到 DoR' },
      { name: 'Definition of Ready (DoR)', url: 'https://www.scrum.org/resources/blog/walking-through-definition-ready',
        summary: '进入 Sprint 的准入条件，确保需求"可做"；DoR 是 optional 但强烈推荐' },
      { name: 'ISTQB Risk-Based Testing', url: 'https://www.istqb.org/',
        summary: '风险驱动测试 + Go/No-Go 决策矩阵' },
    ],
    sections: [
      {
        kind: 'twoListChecklist', title: 'DoR vs DoD',
        left: {
          title: 'Definition of Ready (DoR) — 需求可做',
          items: [
            'PRD 已评审通过',
            '验收标准明确',
            '技术方案已澄清',
            '测试点已识别',
            '依赖已就绪（API / 数据 / 环境）',
            '故事可在一个 Sprint 内交付',
          ],
        },
        right: {
          title: 'Definition of Done (DoD) — 需求做完',
          items: [
            '代码已合并到主干',
            '单元测试覆盖率 ≥ 60%',
            '所有 P0 / P1 缺陷关闭',
            '所有测试用例已执行',
            'QA Readiness Report 已生成并签字',
            'gate.py OVERALL PASS',
            '上线风险已记录',
          ],
        },
      },
      {
        kind: 'releaseGate', title: '执行评审 Gate（数字门槛 + 数据源）',
        columns: ['指标', '门槛', '当前', '数据源'],
        rows: [
          ['执行率', '100%', '—', 'dashboard.db'],
          ['P0 缺陷未关闭', '0', '—', '禅道'],
          ['P1 缺陷未关闭', '0', '—', '禅道'],
          ['回归 Pass Rate', '≥ 95%', '—', 'dashboard.db'],
          ['gate.py 状态', 'OVERALL PASS', 'FAIL', 'gate.py'],
          ['执行评审签字', 'Owner 已签字', '—', 'QA Readiness Report'],
        ],
      },
    ],
    antiPatterns: [
      'Gate 太松 = 没有 Gate',
      'DoD 写在 Wiki 但 PR 不卡 → 等于装饰',
      '无视风险硬上 Go → 一次事故抵 10 次 Gate',
      'Gate 只看测试不看缺陷状态 → 漏 P0',
    ],
  },

  // ---- Phase 7 / id=8  度量与持续改进 ----------------------------------------
  8: {
    brief: '没有改进的度量是数据噪音。复盘 → 行动 → 反向更新模板 / Gate / 自动化 = 闭环。',
    frameworks: [
      { name: 'Toyota / Lean — PDCA', url: 'https://en.wikipedia.org/wiki/PDCA',
        summary: 'Plan → Do → Check → Act 戴明环；改进的根本框架' },
      { name: 'Google SRE — Blameless Postmortem', url: 'https://sre.google/sre-book/postmortem-culture/',
        summary: '无指责复盘文化；focus on systems not people' },
      { name: 'DORA — Generative Culture', url: 'https://dora.dev/research/2022/',
        summary: 'Westrum 文化模型；信息流 / 责任分担 / 系统性思考 → 高绩效' },
    ],
    sections: [],
    antiPatterns: [
      '复盘只写"以后注意" — 没有具体改进项 + Owner + Due',
      '改进项写完就忘 — 没纳入 Sprint / OKR / Gate',
      '看板做完不更新 — 数据陈旧 → 没人看 → 死循环',
    ],
  },
}

// ---------------------------------------------------------------------------
// localStorage helpers
// ---------------------------------------------------------------------------

const LS_KEY_DONE = 'qa-system.deliverables.done.v1'
const LS_KEY_SDLC = 'qa-system.sdlc.role.state.v2'
const LS_KEY_SELECTED_PHASE = 'qa-system.selectedPhaseId.v1'
const LS_KEY_SELECTED_STAGE = 'qa-system.selectedStageId.v1'

function useLocalStorage(key, initial) {
  const [val, setVal] = useState(() => {
    try {
      const raw = localStorage.getItem(key)
      return raw !== null ? JSON.parse(raw) : initial
    } catch { return initial }
  })
  useEffect(() => {
    try { localStorage.setItem(key, JSON.stringify(val)) } catch {}
  }, [key, val])
  return [val, setVal]
}

// ---------------------------------------------------------------------------
// Status / progress helpers
// ---------------------------------------------------------------------------

const STATUS_COLORS = {
  green:  { tag: 'success', dot: '#52c41a', bg: 'rgba(82,196,26,0.12)',  border: '#52c41a', text: '完成' },
  yellow: { tag: 'warning', dot: '#faad14', bg: 'rgba(250,173,20,0.12)', border: '#faad14', text: '进行中' },
  gray:   { tag: 'default', dot: '#bfbfbf', bg: 'rgba(0,0,0,0.04)',      border: '#d9d9d9', text: '未开始' },
}

const EMPTY_QUALITY_EVIDENCE = {
  summary: {
    packageCount: 0,
    trustedPackageCount: 0,
    deliverableCount: 0,
    trustedDeliverableCount: 0,
  },
  gate: { status: 'UNKNOWN', trusted: false, blockingIssues: [], checkedAt: null },
  deliverables: {},
  packages: [],
  errors: [],
  requiredDeliverables: [],
}

function deliverableEvidence(qualityEvidence, deliverableId) {
  return qualityEvidence?.deliverables?.[deliverableId] || {
    packageCount: 0,
    trustedCount: 0,
    latestPackage: null,
    blockingIssues: [],
  }
}

function isEvidenceBacked(qualityEvidence, deliverableId) {
  return deliverableEvidence(qualityEvidence, deliverableId).trustedCount > 0
}

function isDeliverableComplete(deliverable, done, qualityEvidence) {
  return !!done[deliverable.id] || isEvidenceBacked(qualityEvidence, deliverable.id)
}

function phaseProgress(phase, done, qualityEvidence = EMPTY_QUALITY_EVIDENCE) {
  if (!phase.deliverables) return { completed: 0, total: 0, pct: 0 }
  const total = phase.deliverables.length
  const completed = phase.deliverables.filter(d => isDeliverableComplete(d, done, qualityEvidence)).length
  return { completed, total, pct: total ? Math.round(completed / total * 100) : 0 }
}

// Map qualitative harness review status to a rough 0-100 score so the chip
// can show a real number instead of being hardcoded yellow.
const HARNESS_STATUS_SCORE = {
  '完成': 100,
  '已有基础': 70, '已有工具': 70,
  'partial': 50, '部分': 50, '雏形中': 50,
  '已有但拒收': 30,
  '偏弱': 10,
}

function harnessReviewPct() {
  if (HARNESS_REVIEW.length === 0) return 0
  const total = HARNESS_REVIEW.reduce((s, r) => s + (HARNESS_STATUS_SCORE[r.status] ?? 0), 0)
  return Math.round(total / HARNESS_REVIEW.length)
}

function buildPhaseStatus(phase, done, sdlcState, qualityEvidence = EMPTY_QUALITY_EVIDENCE) {
  if (phase.content === 'sdlc') {
    const allStages = SDLC_STAGES.map(s => sdlcStageReadiness(s, sdlcState))
    const sum = allStages.reduce((a, r) => ({ done: a.done + r.allDone, total: a.total + r.allTotal }), { done: 0, total: 0 })
    if (sum.total === 0) return { status: 'gray', pct: 0 }
    const pct = Math.round(sum.done / sum.total * 100)
    return { status: pct === 100 ? 'green' : pct > 0 ? 'yellow' : 'gray', pct }
  }
  if (phase.content === 'review') {
    // Average of (qa-harness module health) and (improvement-action checklist).
    const reviewPct = harnessReviewPct()
    const delivPct = phase.deliverables ? phaseProgress(phase, done, qualityEvidence).pct : reviewPct
    const pct = Math.round((reviewPct + delivPct) / 2)
    return { status: pct === 100 ? 'green' : pct > 0 ? 'yellow' : 'gray', pct }
  }
  const { pct } = phaseProgress(phase, done, qualityEvidence)
  return { status: pct === 100 ? 'green' : pct > 0 ? 'yellow' : 'gray', pct }
}

// SDLC helpers ---------------------------------------------------------------

function setItem(state, setState, stageId, roleKey, itemId, patch) {
  setState({
    ...state,
    [stageId]: {
      ...(state[stageId] || {}),
      [roleKey]: {
        ...((state[stageId] || {})[roleKey] || {}),
        [itemId]: { ...(((state[stageId] || {})[roleKey] || {})[itemId] || {}), ...patch },
      },
    },
  })
}

// Find a referenced output's current value across all stages/roles
function resolveLinkedTarget(linkId, sdlcState) {
  for (const st of SDLC_STAGES) {
    for (const roleKey of Object.keys(st.roles || {})) {
      const found = st.roles[roleKey].outputs?.find(o => o.id === linkId)
      if (found) {
        const cur = sdlcState?.[st.id]?.[roleKey]?.[found.id]?.current ?? 0
        return { stage: st, role: roleKey, current: cur }
      }
    }
  }
  return null
}

function targetForOutput(output, sdlcState, stageId, roleKey) {
  if (output.linkedTo) {
    const link = resolveLinkedTarget(output.linkedTo, sdlcState)
    return link ? (link.current || output.defaultTarget || 0) : (output.defaultTarget || 0)
  }
  const stored = sdlcState?.[stageId]?.[roleKey]?.[output.id]?.target
  return stored != null ? stored : (output.defaultTarget || 0)
}

function isDocChecked(state, stageId, roleKey, itemId) {
  return !!state?.[stageId]?.[roleKey]?.[itemId]?.checked
}
function isCountDone(output, state, stageId, roleKey) {
  const cur = state?.[stageId]?.[roleKey]?.[output.id]?.current ?? 0
  const tgt = targetForOutput(output, state, stageId, roleKey)
  return tgt > 0 && cur >= tgt
}

function sdlcStageReadiness(stage, sdlcState) {
  let inDone = 0, inTotal = 0, outDone = 0, outTotal = 0
  for (const roleKey of Object.keys(stage.roles || {})) {
    const r = stage.roles[roleKey]
    for (const inp of r.inputs || []) {
      inTotal++
      if (isDocChecked(sdlcState, stage.id, roleKey, inp.id)) inDone++
    }
    for (const out of r.outputs || []) {
      outTotal++
      if (out.kind === 'doc'
        ? isDocChecked(sdlcState, stage.id, roleKey, out.id)
        : isCountDone(out, sdlcState, stage.id, roleKey)) outDone++
    }
  }
  const allTotal = inTotal + outTotal
  const allDone = inDone + outDone
  const pct = allTotal ? Math.round(allDone / allTotal * 100) : 0
  return {
    inDone, inTotal, outDone, outTotal, allDone, allTotal, pct,
    status: pct === 100 ? 'green' : pct > 0 ? 'yellow' : 'gray',
  }
}

function QualityGateSummary({ qualityEvidence, loading }) {
  const q = qualityEvidence || EMPTY_QUALITY_EVIDENCE
  const gate = q.gate || {}
  const summary = q.summary || EMPTY_QUALITY_EVIDENCE.summary
  const trusted = !!gate.trusted
  const color = trusted ? '#52c41a' : '#ff4d4f'
  const bg = trusted ? 'rgba(82,196,26,0.08)' : 'rgba(255,77,79,0.08)'
  const blocking = gate.blockingIssues || []

  return (
    <Card
      size="small"
      title={<><SafetyCertificateOutlined style={{ color }} /> Evidence-backed Quality Gate</>}
      extra={
        <Space size={8}>
          <Tag color={trusted ? 'success' : 'error'}>{loading ? 'loading' : gate.status || 'UNKNOWN'}</Tag>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {summary.trustedPackageCount}/{summary.packageCount} trusted packages
          </Text>
        </Space>
      }
      style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
    >
      <Row gutter={[12, 12]} align="middle">
        <Col xs={24} md={8}>
          <div style={{ padding: '10px 12px', border: `1px solid ${color}33`, background: bg, borderRadius: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>Gate conclusion</Text>
            <div style={{ color, fontWeight: 700, fontSize: 18, marginTop: 2 }}>
              {trusted ? '可信' : '阻塞'}
            </div>
          </div>
        </Col>
        <Col xs={24} md={8}>
          <div style={{ padding: '10px 12px', background: '#fafafa', border: '1px solid #f0f0f0', borderRadius: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>Evidence coverage</Text>
            <div style={{ fontWeight: 700, fontSize: 18, marginTop: 2 }}>
              {summary.trustedDeliverableCount}/{summary.deliverableCount}
            </div>
          </div>
        </Col>
        <Col xs={24} md={8}>
          <div style={{ padding: '10px 12px', background: '#fafafa', border: '1px solid #f0f0f0', borderRadius: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>Latest check</Text>
            <div style={{ fontWeight: 600, fontSize: 12, marginTop: 6 }}>
              {gate.checkedAt ? new Date(gate.checkedAt).toLocaleString() : '—'}
            </div>
          </div>
        </Col>
      </Row>
      {blocking.length > 0 && (
        <div style={{ marginTop: 10, padding: '8px 10px', background: '#fff2f0', border: '1px solid #ffccc7', borderRadius: 8 }}>
          <Text strong style={{ fontSize: 12, color: '#cf1322' }}>Blocking issues</Text>
          <Space direction="vertical" size={2} style={{ display: 'flex', marginTop: 4 }}>
            {blocking.slice(0, 4).map((issue, idx) => (
              <Text key={idx} style={{ fontSize: 12, color: '#8c1d18' }}>{issue}</Text>
            ))}
          </Space>
        </div>
      )}
    </Card>
  )
}

function DeliverableRow({ deliverable, done, setDone, qualityEvidence }) {
  const ev = deliverableEvidence(qualityEvidence, deliverable.id)
  const backed = ev.trustedCount > 0
  const hasPackage = ev.packageCount > 0
  const checked = !!done[deliverable.id]
  const complete = checked || backed
  const pkg = ev.latestPackage
  const tag = backed
    ? <Tag color="success" style={{ margin: 0, fontSize: 11 }}>证据支撑</Tag>
    : hasPackage
      ? <Tag color="error" style={{ margin: 0, fontSize: 11 }}>证据阻塞</Tag>
      : checked
        ? <Tag color="warning" style={{ margin: 0, fontSize: 11 }}>人工</Tag>
        : <Tag style={{ margin: 0, fontSize: 11 }}>无证据</Tag>
  const tooltip = backed
    ? `${ev.trustedCount} trusted package(s); latest ${pkg?.packageId || ''}`
    : hasPackage
      ? (ev.blockingIssues || []).join('; ') || 'package exists but is not trusted'
      : 'No promoted evidence manifest found for this deliverable'

  return (
    <div
      style={{
        padding: '7px 0',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        borderBottom: '1px solid #f5f5f5',
      }}
    >
      <Checkbox
        checked={checked}
        onChange={(e) => setDone({ ...done, [deliverable.id]: e.target.checked })}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text delete={complete} style={{ color: complete ? '#8c8c8c' : '#262626', fontSize: 13 }}>
          {deliverable.name}
        </Text>
        {pkg && (
          <div style={{ marginTop: 1 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {pkg.packageId} · run #{pkg.runId || '—'} · {pkg.environment || 'env?'} · {pkg.build || 'build?'}
            </Text>
          </div>
        )}
      </div>
      <Tooltip title={tooltip}>
        {tag}
      </Tooltip>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Reusable chip strip
// ---------------------------------------------------------------------------

function ChipStrip({ items, selectedId, onSelect, getStatus, getPct, getLabel, getSubtitle }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'stretch', gap: 0, overflowX: 'auto',
      padding: '8px 4px', background: '#fafafa', borderRadius: 8,
    }}>
      {items.map((it, idx) => {
        const status = getStatus(it)
        const pct = getPct(it)
        const isSel = it.id === selectedId
        const c = STATUS_COLORS[status]
        return (
          <div key={it.id} style={{ display: 'flex', alignItems: 'center', flex: '0 0 auto' }}>
            <div
              onClick={() => onSelect(it.id)}
              style={{
                padding: '10px 12px',
                minWidth: 150,
                background: isSel ? '#fff' : c.bg,
                // Constant 2px border — only the COLOR changes on selection,
                // so chip dimensions stay fixed and the strip doesn't shift.
                border: `2px solid ${isSel ? '#1677ff' : c.border}`,
                borderRadius: 8,
                boxShadow: isSel ? '0 0 0 3px rgba(22,119,255,0.15)' : 'none',
                cursor: 'pointer',
                transition: 'background 0.15s, border-color 0.15s, box-shadow 0.15s',
                position: 'relative',
              }}
            >
              <div style={{ fontSize: 11, color: isSel ? '#1677ff' : '#8c8c8c', fontWeight: isSel ? 600 : 400 }}>
                {getLabel ? getLabel(it) : ''}
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#262626', marginTop: 2 }}>
                {it.name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
                <span style={{
                  display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
                  background: c.dot,
                }} />
                {pct != null && (
                  <Text style={{ fontSize: 11, color: c.dot, fontWeight: 600 }}>{pct}%</Text>
                )}
                {getSubtitle && (
                  <Text type="secondary" style={{ fontSize: 11 }}>{getSubtitle(it)}</Text>
                )}
              </div>
            </div>
            {idx < items.length - 1 && (
              <div style={{ color: '#bfbfbf', fontSize: 16, padding: '0 4px' }}>→</div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// SDLC: Input / Output rows
// ---------------------------------------------------------------------------

function InputRow({ stageId, roleKey, input, sdlcState, setSdlcState }) {
  const checked = !!sdlcState?.[stageId]?.[roleKey]?.[input.id]?.checked
  return (
    <div style={{ padding: '4px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
      <Checkbox
        checked={checked}
        onChange={(e) => setItem(sdlcState, setSdlcState, stageId, roleKey, input.id, { checked: e.target.checked })}
      >
        <Text delete={checked} style={{ color: checked ? '#8c8c8c' : '#262626', fontSize: 13 }}>
          {input.name}
        </Text>
      </Checkbox>
      {input.from && (
        <Tag color="blue" style={{ marginInlineEnd: 0, fontSize: 10 }}>from {input.from}</Tag>
      )}
    </div>
  )
}

function OutputRow({ stageId, roleKey, output, sdlcState, setSdlcState }) {
  if (output.kind === 'count') {
    const cur = sdlcState?.[stageId]?.[roleKey]?.[output.id]?.current ?? 0
    const tgt = targetForOutput(output, sdlcState, stageId, roleKey)
    const done = tgt > 0 && cur >= tgt
    return (
      <div style={{ padding: '4px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{
            width: 16, height: 16, display: 'inline-flex',
            alignItems: 'center', justifyContent: 'center',
            background: done ? '#52c41a' : '#fff',
            border: `1.5px solid ${done ? '#52c41a' : '#d9d9d9'}`,
            borderRadius: 3, color: '#fff', fontSize: 11,
          }}>{done ? '✓' : ''}</span>
          <Text style={{ fontSize: 13, color: done ? '#8c8c8c' : '#262626' }} delete={done}>
            {output.name}
          </Text>
          <InputNumber
            size="small"
            min={0}
            value={cur}
            onChange={(v) => setItem(sdlcState, setSdlcState, stageId, roleKey, output.id, { current: v ?? 0 })}
            style={{ width: 64 }}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>/</Text>
          {output.linkedTo ? (
            <Tooltip title={`目标自动同步自 ${output.linkedTo}`}>
              <Tag icon={<LinkOutlined />} color="purple" style={{ marginInlineEnd: 0 }}>{tgt}</Tag>
            </Tooltip>
          ) : (
            <InputNumber
              size="small"
              min={0}
              value={tgt}
              onChange={(v) => setItem(sdlcState, setSdlcState, stageId, roleKey, output.id, { target: v ?? 0 })}
              style={{ width: 64 }}
            />
          )}
          {output.unit && (
            <Text type="secondary" style={{ fontSize: 12 }}>{output.unit}</Text>
          )}
        </div>
        {output.note && (
          <Text type="secondary" style={{ fontSize: 11, marginLeft: 24 }}>{output.note}</Text>
        )}
      </div>
    )
  }
  // 'doc'
  const checked = !!sdlcState?.[stageId]?.[roleKey]?.[output.id]?.checked
  return (
    <div style={{ padding: '4px 0' }}>
      <Checkbox
        checked={checked}
        onChange={(e) => setItem(sdlcState, setSdlcState, stageId, roleKey, output.id, { checked: e.target.checked })}
      >
        <Text delete={checked} style={{ color: checked ? '#8c8c8c' : '#262626', fontSize: 13 }}>
          {output.name}
        </Text>
      </Checkbox>
      {output.note && (
        <div><Text type="secondary" style={{ fontSize: 11, marginLeft: 24 }}>{output.note}</Text></div>
      )}
    </div>
  )
}

function RoleSwimlane({ stageId, roleKey, roleData, sdlcState, setSdlcState }) {
  const role = ROLES[roleKey]
  const inTotal = (roleData.inputs || []).length
  const inDone = (roleData.inputs || []).filter(i => isDocChecked(sdlcState, stageId, roleKey, i.id)).length
  const outTotal = (roleData.outputs || []).length
  const outDone = (roleData.outputs || []).filter(o =>
    o.kind === 'doc'
      ? isDocChecked(sdlcState, stageId, roleKey, o.id)
      : isCountDone(o, sdlcState, stageId, roleKey),
  ).length
  const pct = (inTotal + outTotal) ? Math.round((inDone + outDone) / (inTotal + outTotal) * 100) : 0

  return (
    <div style={{
      background: '#fff',
      border: '1px solid #f0f0f0',
      borderLeft: `4px solid ${role.color}`,
      borderRadius: 8,
      padding: '12px 16px',
      marginBottom: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <div style={{
          width: 30, height: 30, borderRadius: 6,
          background: `${role.color}1a`, color: role.color,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16,
        }}>{role.icon}</div>
        <Text strong style={{ fontSize: 14, flex: 1 }}>{role.name}</Text>
        <Tag style={{ background: '#fafafa', borderColor: '#f0f0f0' }}>
          <Text type="secondary" style={{ fontSize: 11 }}>I {inDone}/{inTotal} · O {outDone}/{outTotal}</Text>
        </Tag>
        <Progress
          percent={pct}
          size="small"
          style={{ width: 80 }}
          strokeColor={role.color}
          showInfo={false}
        />
      </div>
      <Row gutter={[16, 8]}>
        <Col xs={24} md={12}>
          <Space size={4} style={{ marginBottom: 2 }}>
            <ImportOutlined style={{ color: '#1677ff' }} />
            <Text type="secondary" style={{ fontSize: 11 }}>输入</Text>
          </Space>
          {(roleData.inputs || []).length === 0 ? (
            <div><Text type="secondary" style={{ fontSize: 12, fontStyle: 'italic' }}>—</Text></div>
          ) : (
            roleData.inputs.map(i => (
              <InputRow key={i.id} stageId={stageId} roleKey={roleKey} input={i}
                        sdlcState={sdlcState} setSdlcState={setSdlcState} />
            ))
          )}
        </Col>
        <Col xs={24} md={12}>
          <Space size={4} style={{ marginBottom: 2 }}>
            <ExportOutlined style={{ color: '#52c41a' }} />
            <Text type="secondary" style={{ fontSize: 11 }}>产出</Text>
          </Space>
          {(roleData.outputs || []).length === 0 ? (
            <div><Text type="secondary" style={{ fontSize: 12, fontStyle: 'italic' }}>—</Text></div>
          ) : (
            roleData.outputs.map(o => (
              <OutputRow key={o.id} stageId={stageId} roleKey={roleKey} output={o}
                         sdlcState={sdlcState} setSdlcState={setSdlcState} />
            ))
          )}
        </Col>
      </Row>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Rich content renderers (per PHASE_RICH)
// ---------------------------------------------------------------------------

function BriefBanner({ brief }) {
  if (!brief) return null
  return (
    <div style={{
      padding: '10px 14px',
      background: 'linear-gradient(90deg, rgba(22,119,255,0.06), rgba(19,194,194,0.04))',
      border: '1px solid rgba(22,119,255,0.15)',
      borderRadius: 8,
      marginBottom: 12,
      display: 'flex', alignItems: 'center', gap: 8,
    }}>
      <ThunderboltOutlined style={{ color: '#1677ff', fontSize: 16 }} />
      <Text style={{ fontSize: 13, color: '#262626' }}>{brief}</Text>
    </div>
  )
}

function FrameworkRefs({ items }) {
  if (!items || items.length === 0) return null
  return (
    <div style={{ marginBottom: 14 }}>
      <Space size={6} style={{ marginBottom: 6 }}>
        <BookOutlined style={{ color: '#722ed1' }} />
        <Text type="secondary" style={{ fontSize: 12 }}>业界参考框架</Text>
      </Space>
      <Row gutter={[10, 10]}>
        {items.map(f => (
          <Col xs={24} md={8} key={f.name}>
            <div style={{
              padding: '10px 12px',
              background: '#fafafa',
              border: '1px solid #f0f0f0',
              borderRadius: 8,
              height: '100%',
            }}>
              <a href={f.url} target="_blank" rel="noreferrer"
                 style={{ fontSize: 12, fontWeight: 600, color: '#722ed1' }}>
                <LinkOutlined style={{ marginRight: 4 }} />{f.name}
              </a>
              <div style={{ fontSize: 11, color: '#595959', marginTop: 4, lineHeight: 1.5 }}>
                {f.summary}
              </div>
            </div>
          </Col>
        ))}
      </Row>
    </div>
  )
}

function RichTable({ columns, rows }) {
  const tableColumns = columns.map((c, i) => ({
    title: c,
    dataIndex: `c${i}`,
    render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text>,
  }))
  const dataSource = rows.map((r, i) => {
    const obj = { key: i }
    r.forEach((v, j) => obj[`c${j}`] = v)
    return obj
  })
  return (
    <Table
      dataSource={dataSource}
      columns={tableColumns}
      size="small"
      pagination={false}
      bordered
      style={{ marginBottom: 8 }}
    />
  )
}

function SectionTitle({ icon, text }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
      {icon}
      <Text strong style={{ fontSize: 13 }}>{text}</Text>
    </div>
  )
}

function Iso25010Grid({ items }) {
  return (
    <Row gutter={[8, 8]}>
      {items.map(it => (
        <Col xs={24} sm={12} md={6} key={it.name}>
          <div style={{
            padding: '8px 10px',
            background: '#fff',
            border: '1px solid #f0f0f0',
            borderRadius: 6,
            borderLeft: '3px solid #722ed1',
          }}>
            <Text strong style={{ fontSize: 12 }}>{it.name}</Text>
            <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 2, lineHeight: 1.4 }}>{it.sub}</div>
          </div>
        </Col>
      ))}
    </Row>
  )
}

function DefectLifecycleFlow({ states, sideStates }) {
  return (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 0,
        overflowX: 'auto', padding: '8px 0',
      }}>
        {states.map((s, idx) => (
          <div key={s.name} style={{ display: 'flex', alignItems: 'center', flex: '0 0 auto' }}>
            <div style={{
              padding: '6px 12px',
              background: `${s.color}1a`,
              border: `1.5px solid ${s.color}`,
              borderRadius: 6,
              minWidth: 110,
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: s.color }}>{s.name}</div>
              <div style={{ fontSize: 10, color: '#595959', marginTop: 2 }}>{s.desc}</div>
            </div>
            {idx < states.length - 1 && (
              <div style={{ color: '#bfbfbf', fontSize: 16, padding: '0 4px' }}>→</div>
            )}
          </div>
        ))}
      </div>
      {sideStates && sideStates.length > 0 && (
        <div style={{ marginTop: 6, fontSize: 11, color: '#8c8c8c' }}>
          旁路状态：{sideStates.map(s => <Tag key={s} style={{ fontSize: 10, marginRight: 4 }}>{s}</Tag>)}
        </div>
      )}
    </div>
  )
}

function SeverityMatrix({ cols, rows, cells }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
        <thead>
          <tr>
            <th style={{ background: '#fafafa', padding: 8, border: '1px solid #f0f0f0', width: 90 }}></th>
            {cols.map(c => (
              <th key={c} style={{
                background: '#fafafa', padding: 8, border: '1px solid #f0f0f0',
                textAlign: 'center', fontSize: 12,
              }}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={r}>
              <th style={{
                background: '#fafafa', padding: 8, border: '1px solid #f0f0f0',
                textAlign: 'left', fontWeight: 600,
              }}>{r}</th>
              {cells[ri].map((cell, ci) => (
                <td key={ci} style={{
                  background: cell.color, color: '#fff', textAlign: 'center',
                  padding: 8, border: '1px solid #f0f0f0', fontWeight: 600,
                }}>{cell.text}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TestPyramidViz({ layers }) {
  // Render a triangle with layers stacked top→bottom.
  const width = 480, total = 64 * layers.length
  return (
    <Row gutter={16} align="middle">
      <Col xs={24} md={10}>
        <svg width={width} height={total + 40} style={{ display: 'block' }}>
          {layers.map((l, i) => {
            const topW = (i + 1) * 60
            const botW = (i + 2) * 60
            const y = i * 64 + 20
            const cx = width / 2
            return (
              <g key={l.layer}>
                <polygon
                  points={`${cx - topW} ${y} ${cx + topW} ${y} ${cx + botW} ${y + 60} ${cx - botW} ${y + 60}`}
                  fill={i === 0 ? '#ff7a45' : i === 1 ? '#faad14' : '#52c41a'}
                  opacity={0.85}
                  stroke="#fff"
                  strokeWidth={2}
                />
                <text x={cx} y={y + 30} textAnchor="middle" fill="#fff" fontSize={13} fontWeight={700}>
                  {l.layer}
                </text>
                <text x={cx} y={y + 50} textAnchor="middle" fill="#fff" fontSize={11}>
                  ≈ {l.pct}%
                </text>
              </g>
            )
          })}
        </svg>
      </Col>
      <Col xs={24} md={14}>
        <Table
          dataSource={layers.map((l, i) => ({ key: i, ...l }))}
          columns={[
            { title: '层', dataIndex: 'layer', render: (v) => <Text strong style={{ fontSize: 12 }}>{v}</Text> },
            { title: '反馈速度', dataIndex: 'speed', render: (v) => <Tag>{v}</Tag> },
            { title: 'Flaky 风险', dataIndex: 'flaky', render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text> },
            { title: '维护成本', dataIndex: 'maintain', render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text> },
            { title: '工具', dataIndex: 'stack', render: (v) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
          ]}
          size="small"
          pagination={false}
          bordered
        />
      </Col>
    </Row>
  )
}

function TwoListChecklist({ left, right }) {
  return (
    <Row gutter={[16, 12]}>
      <Col xs={24} md={12}>
        <div style={{
          padding: 12, background: '#fff', border: '1px solid #f0f0f0',
          borderLeft: '3px solid #1677ff', borderRadius: 6, height: '100%',
        }}>
          <Text strong style={{ fontSize: 12, color: '#1677ff' }}>{left.title}</Text>
          <ul style={{ margin: '6px 0 0 0', paddingLeft: 22, fontSize: 12 }}>
            {left.items.map((it, i) => <li key={i} style={{ marginBottom: 3, color: '#262626' }}>{it}</li>)}
          </ul>
        </div>
      </Col>
      <Col xs={24} md={12}>
        <div style={{
          padding: 12, background: '#fff', border: '1px solid #f0f0f0',
          borderLeft: '3px solid #52c41a', borderRadius: 6, height: '100%',
        }}>
          <Text strong style={{ fontSize: 12, color: '#52c41a' }}>{right.title}</Text>
          <ul style={{ margin: '6px 0 0 0', paddingLeft: 22, fontSize: 12 }}>
            {right.items.map((it, i) => <li key={i} style={{ marginBottom: 3, color: '#262626' }}>{it}</li>)}
          </ul>
        </div>
      </Col>
    </Row>
  )
}

function AntiPatterns({ items }) {
  if (!items || items.length === 0) return null
  return (
    <div style={{
      padding: '10px 14px',
      background: 'rgba(255,77,79,0.04)',
      border: '1px solid rgba(255,77,79,0.2)',
      borderRadius: 8,
      marginTop: 12,
    }}>
      <Space size={6} style={{ marginBottom: 6 }}>
        <WarningFilled style={{ color: '#ff4d4f' }} />
        <Text strong style={{ fontSize: 12, color: '#ff4d4f' }}>避坑（反模式）</Text>
      </Space>
      <ul style={{ margin: '4px 0 0 0', paddingLeft: 22, fontSize: 12 }}>
        {items.map((it, i) => (
          <li key={i} style={{ marginBottom: 3, color: '#595959' }}>{it}</li>
        ))}
      </ul>
    </div>
  )
}

function RichSection({ section }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <SectionTitle
        icon={<ReadOutlined style={{ color: '#13c2c2' }} />}
        text={section.title}
      />
      {(() => {
        switch (section.kind) {
          case 'kpiCatalog':
          case 'templateCatalog':
          case 'evidenceRules':
          case 'toolStack':
          case 'releaseGate':
            return <RichTable columns={section.columns} rows={section.rows} />
          case 'iso25010':
            return <Iso25010Grid items={section.items} />
          case 'defectLifecycle':
            return <DefectLifecycleFlow states={section.states} sideStates={section.sideStates} />
          case 'severityMatrix':
            return <SeverityMatrix cols={section.cols} rows={section.rows} cells={section.cells} />
          case 'testPyramid':
            return <TestPyramidViz layers={section.layers} />
          case 'twoListChecklist':
            return <TwoListChecklist left={section.left} right={section.right} />
          default:
            return <Text type="secondary">未知 section 类型: {section.kind}</Text>
        }
      })()}
    </div>
  )
}

/**
 * Slim mode — only renders the figures (KPI tables, pyramid, matrix, etc.)
 * plus a tiny `参考` link row. Drops BriefBanner, FrameworkRefs cards, and
 * AntiPatterns box so the actionable parts (deliverables) stay primary.
 */
function RichContentBlock({ phaseId }) {
  const rich = PHASE_RICH[phaseId]
  if (!rich) return null
  const sections = rich.sections || []
  const refs = rich.frameworks || []
  if (sections.length === 0 && refs.length === 0) return null
  return (
    <div style={{ marginBottom: 12 }}>
      {sections.map((s, i) => <RichSection key={i} section={s} />)}
      {refs.length > 0 && (
        <div style={{ marginTop: 8, fontSize: 11, color: '#8c8c8c' }}>
          <BookOutlined style={{ marginRight: 6, color: '#722ed1' }} />
          参考：{refs.map((f, i) => (
            <span key={f.name}>
              <a href={f.url} target="_blank" rel="noreferrer">{f.name}</a>
              {i < refs.length - 1 && <span style={{ color: '#bfbfbf' }}> · </span>}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Detail panels
// ---------------------------------------------------------------------------

function SdlcPanel({ phase, sdlcState, setSdlcState, selectedStageId, setSelectedStageId }) {
  const stage = SDLC_STAGES.find(s => s.id === selectedStageId) || SDLC_STAGES[0]
  const r = sdlcStageReadiness(stage, sdlcState)
  const c = STATUS_COLORS[r.status]
  const roleKeys = ROLE_ORDER.filter(k => stage.roles?.[k])

  return (
    <>
      <Card
        size="small"
        title={<><ApartmentOutlined style={{ color: '#13c2c2' }} /> SDLC 流程标准（{SDLC_STAGES.length} 阶段 · 多角色）</>}
        extra={<Text type="secondary" style={{ fontSize: 11 }}>点击阶段切换详情</Text>}
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
      >
        <ChipStrip
          items={SDLC_STAGES}
          selectedId={selectedStageId}
          onSelect={setSelectedStageId}
          getLabel={() => 'SDLC'}
          getStatus={(it) => sdlcStageReadiness(it, sdlcState).status}
          getPct={(it) => sdlcStageReadiness(it, sdlcState).pct}
          getSubtitle={(it) => {
            const rr = sdlcStageReadiness(it, sdlcState)
            return `${rr.inDone}/${rr.inTotal} · ${rr.outDone}/${rr.outTotal}`
          }}
        />
      </Card>

      <Card
        size="small"
        title={
          <Space size={10}>
            <Text strong style={{ fontSize: 15 }}>{stage.name}</Text>
            <Tag color={c.tag}>{c.text}</Tag>
            <Text type="secondary" style={{ fontSize: 12 }}>{stage.purpose}</Text>
          </Space>
        }
        extra={
          <Space>
            <Text type="secondary" style={{ fontSize: 11 }}>
              输入 {r.inDone}/{r.inTotal} · 产出 {r.outDone}/{r.outTotal}
            </Text>
            <Progress percent={r.pct} size="small" style={{ width: 100 }} strokeColor={c.dot} showInfo={false} />
            <Text style={{ fontSize: 12, color: c.dot, fontWeight: 600 }}>{r.pct}%</Text>
          </Space>
        }
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
      >
        <div style={{ marginBottom: 14, padding: '8px 12px', background: '#f6f4ff', borderRadius: 6 }}>
          <Text type="secondary" style={{ fontSize: 11 }}>本阶段质量门禁</Text>
          <div style={{ fontSize: 13, color: '#722ed1', marginTop: 2 }}>{stage.gate}</div>
        </div>

        {roleKeys.map(roleKey => (
          <RoleSwimlane
            key={roleKey}
            stageId={stage.id}
            roleKey={roleKey}
            roleData={stage.roles[roleKey]}
            sdlcState={sdlcState}
            setSdlcState={setSdlcState}
          />
        ))}
      </Card>

      {/* Tiny refs footer (RACI / ISTQB / SAFe links). */}
      <RichContentBlock phaseId={phase.id} />
    </>
  )
}

function DeliverablesPanel({ phase, done, setDone, qualityEvidence }) {
  const { completed, total, pct } = phaseProgress(phase, done, qualityEvidence)
  const status = pct === 100 ? 'green' : pct > 0 ? 'yellow' : 'gray'
  const c = STATUS_COLORS[status]

  return (
    <Card
      size="small"
      title={
        <Space size={10}>
          <Text strong style={{ fontSize: 15 }}>Phase {phase.displayId} — {phase.name}</Text>
          <Tag color={c.tag}>{c.text}</Tag>
          <Text type="secondary" style={{ fontSize: 12 }}>{phase.goal}</Text>
        </Space>
      }
      extra={
        <Space>
          <Progress percent={pct} size="small" style={{ width: 100 }} strokeColor={c.dot} showInfo={false} />
          <Text style={{ fontSize: 12, color: c.dot, fontWeight: 600 }}>{completed}/{total}</Text>
        </Space>
      }
      style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
    >
      {/* Checklist FIRST — "what to do this phase" is the primary content. */}
      <div style={{ marginBottom: 14 }}>
        <Text strong style={{ fontSize: 13 }}>
          <FileDoneOutlined style={{ color: '#1677ff', marginRight: 6 }} />
          本阶段要做的（证据优先，人工勾选仅记录进度）
        </Text>
        <div style={{
          marginTop: 6, padding: '10px 14px',
          background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0',
        }}>
          {(phase.deliverables || []).map(d => (
            <DeliverableRow
              key={d.id}
              deliverable={d}
              done={done}
              setDone={setDone}
              qualityEvidence={qualityEvidence}
            />
          ))}
        </div>
      </div>

      {/* Visualizations + reference links (slim RichContentBlock). */}
      <RichContentBlock phaseId={phase.id} />
    </Card>
  )
}

function ReviewPanelRich({ phase, done, setDone, qualityEvidence }) {
  return (
    <>
      <ReviewPanelInner phase={phase} done={done} setDone={setDone} qualityEvidence={qualityEvidence} />
      {/* Rich content (just figures + tiny ref line) goes BELOW the
          actionable parts now, not at the top. */}
      <RichContentBlock phaseId={phase.id} />
    </>
  )
}

function ReviewPanelInner({ phase, done, setDone, qualityEvidence }) {
  const reviewColumns = [
    { title: '模块', dataIndex: 'module', width: 130, render: (v) => <Text strong style={{ fontSize: 12 }}>{v}</Text> },
    {
      title: '状态', dataIndex: 'status', width: 110,
      render: (v) => {
        const m = { '完成': 'success', '已有基础': 'processing', '已有工具': 'processing',
          '已有但拒收': 'warning', '雏形中': 'warning', '部分': 'warning',
          'partial': 'warning', '偏弱': 'error' }
        return <Tag color={m[v] || 'default'}>{v}</Tag>
      },
    },
    { title: '缺口', dataIndex: 'gap', render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text> },
    { title: '建议动作', dataIndex: 'action', width: 200, render: (v) => <Text style={{ fontSize: 12, color: '#1677ff' }}>{v}</Text> },
  ]

  const { completed, total, pct } = phaseProgress(phase, done, qualityEvidence)
  const reviewPct = harnessReviewPct()
  const c = STATUS_COLORS[pct === 100 && reviewPct === 100 ? 'green' : (pct > 0 || reviewPct > 0) ? 'yellow' : 'gray']

  return (
    <>
      <Card
        size="small"
        title={
          <Space size={10}>
            <BugOutlined style={{ color: '#fa541c' }} />
            <Text strong style={{ fontSize: 15 }}>Phase {phase.displayId} — {phase.name}</Text>
            <Tag color={c.tag}>{c.text}</Tag>
            <Text type="secondary" style={{ fontSize: 12 }}>{phase.goal}</Text>
          </Space>
        }
        extra={
          <Space>
            <Text type="secondary" style={{ fontSize: 11 }}>
              评审 {reviewPct}% · 改进项 {completed}/{total}
            </Text>
          </Space>
        }
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
      >
        <Text strong style={{ fontSize: 13 }}>
          <FileDoneOutlined style={{ color: '#1677ff', marginRight: 6 }} />
          本阶段要做的（改进项 — 体系运行起来后勾选）
        </Text>
        <div style={{
          marginTop: 6, padding: '10px 14px',
          background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0',
        }}>
          {(phase.deliverables || []).map(d => (
            <DeliverableRow
              key={d.id}
              deliverable={d}
              done={done}
              setDone={setDone}
              qualityEvidence={qualityEvidence}
            />
          ))}
        </div>
      </Card>

      <Card
        size="small"
        title={<><BugOutlined style={{ color: '#fa541c' }} /> qa-harness 现状评审（{reviewPct}%）</>}
        extra={<Text type="secondary" style={{ fontSize: 11 }}>状态加权平均反映体系成熟度</Text>}
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
      >
        <Table
          dataSource={HARNESS_REVIEW}
          columns={reviewColumns}
          rowKey="module"
          size="small"
          pagination={false}
        />
      </Card>
    </>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function QualitySystemPage({ activeProject }) {
  const projectKey = activeProject?.key || 'west-kowloon'
  const projectName = activeProject?.name || projectKey
  const [done, setDone] = useLocalStorage(LS_KEY_DONE, {})
  const [sdlcState, setSdlcState] = useLocalStorage(LS_KEY_SDLC, {})
  const [selectedPhaseId, setSelectedPhaseId] = useLocalStorage(LS_KEY_SELECTED_PHASE, 3)
  const [selectedStageId, setSelectedStageId] = useLocalStorage(LS_KEY_SELECTED_STAGE, 'sdlc-req')
  const [qualityEvidence, setQualityEvidence] = useState(EMPTY_QUALITY_EVIDENCE)
  const [qualityEvidenceLoading, setQualityEvidenceLoading] = useState(true)

  const selectedPhase = useMemo(
    () => PHASES.find(p => p.id === selectedPhaseId) || PHASES[0],
    [selectedPhaseId],
  )

  useEffect(() => {
    let cancelled = false
    async function loadQualityEvidence() {
      setQualityEvidenceLoading(true)
      try {
        const json = await requestJson(`/api/quality/evidence?project=${encodeURIComponent(projectKey)}`)
        if (!cancelled) setQualityEvidence(json)
      } catch (e) {
        if (!cancelled) {
          setQualityEvidence({
            ...EMPTY_QUALITY_EVIDENCE,
            gate: {
              status: 'FAIL',
              trusted: false,
              blockingIssues: [`无法读取 evidence manifest: ${e.message || String(e)}`],
              checkedAt: null,
            },
          })
        }
      } finally {
        if (!cancelled) setQualityEvidenceLoading(false)
      }
    }
    loadQualityEvidence()
    return () => { cancelled = true }
  }, [projectKey])

  return (
    <div style={{ maxWidth: 1400 }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
          <SafetyCertificateOutlined style={{ color: '#1677ff', marginRight: 8 }} />
          Quality System — 流程标准 · 多角色 · 多阶段
          <Tag style={{ marginLeft: 8 }}>{projectName}</Tag>
        </Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          点击 Phase 切换详情。Phase 2 = SDLC 流程标准（8 阶段 · 多角色 RACI），Phase 7 = 度量与持续改进 + qa-harness 评审。
        </Text>
      </div>

      <QualityGateSummary qualityEvidence={qualityEvidence} loading={qualityEvidenceLoading} />

      {/* Phase strip */}
      <Card
        size="small"
        title={<><AimOutlined style={{ color: '#1677ff' }} /> 质量体系建设流程图（{PHASES.length} 阶段 · 点击切换）</>}
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
      >
        <ChipStrip
          items={PHASES}
          selectedId={selectedPhaseId}
          onSelect={setSelectedPhaseId}
          getLabel={(it) => `Phase ${it.displayId}`}
          getStatus={(it) => buildPhaseStatus(it, done, sdlcState, qualityEvidence).status}
          getPct={(it) => buildPhaseStatus(it, done, sdlcState, qualityEvidence).pct}
          getSubtitle={(it) => it.content === 'sdlc' ? '8 阶段' : it.content === 'review' ? '评审' : ''}
        />
      </Card>

      {/* Breadcrumb hint */}
      <div style={{ marginBottom: 12, color: '#8c8c8c', fontSize: 12 }}>
        <Text type="secondary">质量体系建设</Text>
        <RightOutlined style={{ fontSize: 9, margin: '0 6px' }} />
        <Text type="secondary">Phase {selectedPhase.displayId}</Text>
        <RightOutlined style={{ fontSize: 9, margin: '0 6px' }} />
        <Text strong style={{ color: '#1677ff' }}>{selectedPhase.name}</Text>
        {selectedPhase.content === 'sdlc' && (
          <>
            <RightOutlined style={{ fontSize: 9, margin: '0 6px' }} />
            <Text strong style={{ color: '#13c2c2' }}>
              {SDLC_STAGES.find(s => s.id === selectedStageId)?.name}
            </Text>
          </>
        )}
      </div>

      {/* Phase detail panel — fixed min-height keeps the page from collapsing
          when switching between short (Deliverables / Review) and tall (SDLC)
          panels, eliminating the scroll-jump that read as "shake". */}
      <div style={{ minHeight: 720 }}>
        {selectedPhase.content === 'sdlc' ? (
          <SdlcPanel
            phase={selectedPhase}
            sdlcState={sdlcState}
            setSdlcState={setSdlcState}
            selectedStageId={selectedStageId}
            setSelectedStageId={setSelectedStageId}
          />
        ) : selectedPhase.content === 'review' ? (
          <ReviewPanelRich
            phase={selectedPhase}
            done={done}
            setDone={setDone}
            qualityEvidence={qualityEvidence}
          />
        ) : (
          <DeliverablesPanel
            phase={selectedPhase}
            done={done}
            setDone={setDone}
            qualityEvidence={qualityEvidence}
          />
        )}
      </div>
    </div>
  )
}
