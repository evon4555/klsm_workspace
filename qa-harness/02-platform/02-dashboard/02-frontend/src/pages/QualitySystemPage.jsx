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
  PM:       { key: 'PM',       name: 'Product Manager',  short: 'PM',  color: '#1677ff', icon: <CrownOutlined /> },
  Designer: { key: 'Designer', name: 'UI/UX Designer',   short: 'UI',  color: '#eb2f96', icon: <HighlightOutlined /> },
  Dev:      { key: 'Dev',      name: 'Developer',        short: 'DEV', color: '#52c41a', icon: <CodeOutlined /> },
  QA:       { key: 'QA',       name: 'Quality Assurance', short: 'QA', color: '#fa8c16', icon: <ExperimentOutlined /> },
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
  // Original Phase 1 (Current-State Assessment) intentionally omitted per product call.
  // `id` stays at the original number to keep localStorage keys stable
  // (deliverable ids `p2-d1`, selectedPhaseId persisted, etc.).
  // `displayId` is the renumbered 1..N shown in the UI.
  {
    id: 2, displayId: 1, name: 'Quality Goals & Metrics', goal: 'Align quality goals with business objectives', content: 'deliverables',
    input: 'Business objectives, release cadence, and risk categories',
    output: 'Quality goals and core metrics',
    actions: 'Define 5-8 metrics, such as defect escape rate, evidence completeness, automation coverage, and release pass rate',
    deliverables: [
      { id: 'p2-d1', name: 'Quality goals (annual / project level)' },
      { id: 'p2-d2', name: 'Core quality metric definitions' },
      { id: 'p2-d3', name: 'Defined metric data sources' },
    ],
  },
  {
    id: 3, displayId: 2, name: 'Process Standards & Roles', goal: 'Standardize the SDLC and role responsibilities', content: 'sdlc',
    input: 'SDLC process, team roles, and compliance requirements',
    output: 'Process map, stage responsibilities, and quality gates',
    actions: 'Define roles, inputs, outputs, and gates for all 8 SDLC stages',
  },
  {
    id: 4, displayId: 3, name: 'Deliverables & Templates', goal: 'Standardize test asset formats', content: 'deliverables',
    input: 'Historical documents, best practices, and project examples',
    output: 'Templates for test strategies, test cases, requirement reviews, reports, and retrospectives',
    actions: 'Standardize formats and required fields',
    deliverables: [
      { id: 'p4-d1', name: 'Test strategy template' },
      { id: 'p4-d2', name: 'Test case template' },
      { id: 'p4-d3', name: 'Requirement review checklist' },
      { id: 'p4-d4', name: 'Test report template' },
      { id: 'p4-d5', name: 'Retrospective template' },
    ],
  },
  {
    id: 5, displayId: 4, name: 'Execution & Evidence', goal: 'Define what "tested" means', content: 'deliverables',
    input: 'Test cases, environments, data, and builds',
    output: 'Execution records, screenshots, logs, and defect records',
    actions: 'Require the complete set of results, evidence, and defect records',
    deliverables: [
      { id: 'p5-d1', name: 'Execution result recording standard' },
      { id: 'p5-d2', name: 'Evidence upload standard (screenshots / logs)' },
      { id: 'p5-d3', name: 'Defect logging standard' },
      { id: 'p5-d4', name: 'Evidence folder convention' },
    ],
  },
  {
    id: 6, displayId: 5, name: 'Automation & Platform', goal: 'Cover critical execution paths', content: 'deliverables',
    input: 'Critical business flows and regression scenarios',
    output: 'Automation framework, regression suite, dashboard, and reports',
    actions: 'Cover critical paths first instead of pursuing total automation',
    deliverables: [
      { id: 'p6-d1', name: 'Behave + Playwright framework' },
      { id: 'p6-d2', name: 'Core regression suite' },
      { id: 'p6-d3', name: 'Automation results displayed in the dashboard' },
      { id: 'p6-d4', name: 'Evidence recorded automatically in dashboard.db' },
    ],
  },
  {
    id: 7, displayId: 6, name: 'Quality Gates & Release Readiness', goal: 'Block releases that do not meet the standard', content: 'deliverables',
    input: 'Test cases, automation, reports, and defect status',
    output: 'Gate checks, CI gates, and release-readiness decisions',
    actions: 'Integrate gate.py into CI and the release workflow',
    deliverables: [
      { id: 'p7-d1', name: 'All gate.py checks pass' },
      { id: 'p7-d2', name: 'CI gate integration' },
      { id: 'p7-d3', name: 'Release-readiness checklist' },
      { id: 'p7-d4', name: 'Go / No-Go decision process' },
    ],
  },
  {
    id: 8, displayId: 7, name: 'Metrics & Continuous Improvement', goal: 'Close the quality-governance feedback loop', content: 'review',
    input: 'Defects, execution results, production issues, and retrospectives',
    output: 'Quality dashboard, retrospective records, improvement actions, and qa-harness assessment',
    actions: 'Use retrospectives to feed issues back into templates, skills, and automation',
    deliverables: [
      { id: 'p8-d1', name: 'Quality dashboard (metric visualization) is live' },
      { id: 'p8-d2', name: 'Release / quarterly retrospective process is active' },
      { id: 'p8-d3', name: 'Improvement actions track owner, due date, and status' },
      { id: 'p8-d4', name: 'Improvements feed back into templates, gates, and automation' },
      { id: 'p8-d5', name: 'All qa-harness assessment items are green' },
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
    id: 'sdlc-req', name: 'Requirements',
    purpose: 'Understand business needs → define scope → align test coverage',
    gate: 'PRD approved + test points recorded + test cases reviewed',
    roles: {
      PM: {
        inputs: [
          { id: 'req-pm-i1', name: 'Business objectives', from: 'Operations' },
          { id: 'req-pm-i2', name: 'Customer interview findings', from: 'Operations' },
          { id: 'req-pm-i3', name: 'Relevant historical data', from: 'BI' },
        ],
        outputs: [
          { id: 'req-pm-o1', name: 'PRD', kind: 'doc' },
          { id: 'req-pm-o2', name: 'Low-fidelity prototype / flowchart', kind: 'doc',
            note: 'The Designer produces the high-fidelity Figma design' },
          { id: 'req-pm-o3', name: 'Acceptance criteria', kind: 'doc' },
          { id: 'req-pm-o4', name: 'Requirement review minutes', kind: 'doc' },
        ],
      },
      Designer: {
        inputs: [
          { id: 'req-ui-i1', name: 'PRD', from: 'PM' },
          { id: 'req-ui-i2', name: 'User personas', from: 'PM / Operations' },
        ],
        outputs: [
          { id: 'req-ui-o1', name: 'User journey / information architecture', kind: 'doc' },
          { id: 'req-ui-o2', name: 'Figma design (high fidelity)', kind: 'doc',
            note: 'QA needs this during this stage to write test cases' },
        ],
      },
      Dev: {
        inputs: [
          { id: 'req-dev-i1', name: 'PRD', from: 'PM' },
        ],
        outputs: [
          { id: 'req-dev-o1', name: 'Technical feasibility assessment', kind: 'doc' },
          { id: 'req-dev-o2', name: 'Effort estimate', kind: 'doc' },
        ],
      },
      QA: {
        inputs: [
          { id: 'req-qa-i1', name: 'Mind map', from: 'PM' },
          { id: 'req-qa-i2', name: 'PRD', from: 'PM' },
          { id: 'req-qa-i3', name: 'Figma design', from: 'Designer' },
          { id: 'req-qa-i4', name: 'Relevant historical defects', from: 'QA / Customer' },
        ],
        outputs: [
          { id: 'req-qa-o1', name: 'Test cases', kind: 'count', defaultTarget: 0, note: 'Estimated from requirement granularity; the target can be populated through the ZenTao API' },
          { id: 'req-qa-o2', name: 'Peer-review record for test cases', kind: 'doc', note: 'At least 1 QA and 1 developer participate' },
          { id: 'req-qa-o3', name: 'Test points / risk record', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-design', name: 'Design',
    purpose: 'Translate architecture, APIs, and data flows into a test strategy',
    gate: 'Test strategy approved + approach defined for critical scenarios',
    roles: {
      PM: {
        inputs: [{ id: 'des-pm-i1', name: 'Baselined PRD', from: 'PM' }],
        outputs: [{ id: 'des-pm-o1', name: 'Design walkthrough + PRD consistency confirmation', kind: 'doc' }],
      },
      Designer: {
        inputs: [{ id: 'des-ui-i1', name: 'PRD', from: 'PM' }],
        outputs: [
          { id: 'des-ui-o1', name: 'Interaction details / edge-state design', kind: 'doc' },
          { id: 'des-ui-o2', name: 'Design guidelines / design tokens', kind: 'doc' },
        ],
      },
      Dev: {
        inputs: [
          { id: 'des-dev-i1', name: 'PRD', from: 'PM' },
          { id: 'des-dev-i2', name: 'Design specification', from: 'Designer' },
        ],
        outputs: [
          { id: 'des-dev-o1', name: 'System architecture diagram', kind: 'doc' },
          { id: 'des-dev-o2', name: 'API documentation (Swagger)', kind: 'doc' },
          { id: 'des-dev-o3', name: 'Data model / table schema', kind: 'doc' },
          { id: 'des-dev-o4', name: 'Data-flow diagram / state machine', kind: 'doc' },
        ],
      },
      QA: {
        inputs: [
          { id: 'des-qa-i1', name: 'System architecture diagram', from: 'Dev' },
          { id: 'des-qa-i2', name: 'API documentation', from: 'Dev' },
          { id: 'des-qa-i3', name: 'Data-flow diagram / state machine', from: 'Dev' },
          { id: 'des-qa-i4', name: 'Permission / role definitions', from: 'PM' },
        ],
        outputs: [
          { id: 'des-qa-o1', name: 'Test strategy', kind: 'doc' },
          { id: 'des-qa-o2', name: 'API test approach', kind: 'doc' },
          { id: 'des-qa-o3', name: 'Non-functional test approach (performance / security)', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [{ id: 'des-ops-i1', name: 'Architecture diagram', from: 'Dev' }],
        outputs: [{ id: 'des-ops-o1', name: 'Environment deployment plan', kind: 'doc' }],
      },
    },
  },
  {
    id: 'sdlc-dev', name: 'Development',
    purpose: 'QA tracks development outputs → prepares automation and smoke tests',
    gate: 'Developer testing passed + smoke scripts ready + critical APIs testable',
    roles: {
      PM: {
        inputs: [],
        outputs: [{ id: 'dev-pm-o1', name: 'Requirement clarification responses', kind: 'doc' }],
      },
      Designer: {
        inputs: [],
        outputs: [{ id: 'dev-ui-o1', name: 'Design walkthrough (implementation vs design)', kind: 'doc' }],
      },
      Dev: {
        inputs: [
          { id: 'dev-dev-i1', name: 'Baselined requirements + design', from: 'PM / Designer' },
        ],
        outputs: [
          { id: 'dev-dev-o1', name: 'Implementation complete', kind: 'doc' },
          { id: 'dev-dev-o2', name: 'Unit-test coverage', kind: 'count', defaultTarget: 60, unit: '%', note: 'Line coverage ≥ 60%' },
          { id: 'dev-dev-o3', name: 'Code review passed', kind: 'doc' },
          { id: 'dev-dev-o4', name: 'CI build is green', kind: 'doc' },
        ],
      },
      QA: {
        inputs: [
          { id: 'dev-qa-i1', name: 'API documentation (latest)', from: 'Dev' },
          { id: 'dev-qa-i2', name: 'System architecture diagram (latest)', from: 'Dev' },
          { id: 'dev-qa-i3', name: 'Database schema / test data', from: 'Dev' },
          { id: 'dev-qa-i4', name: 'Developer test / smoke-test report', from: 'Dev' },
        ],
        outputs: [
          { id: 'dev-qa-o1', name: 'Automated test scripts', kind: 'count', defaultTarget: 0,
            linkedTo: 'req-qa-o1', note: '1:1 with test cases; target = test case count (automatically synchronized)' },
          { id: 'dev-qa-o2', name: 'API smoke-test scripts', kind: 'count', defaultTarget: 0 },
          { id: 'dev-qa-o3', name: 'Test-data scripts', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [
          { id: 'dev-ops-o1', name: 'CI pipeline configuration', kind: 'doc' },
          { id: 'dev-ops-o2', name: 'Test environment available (SIT)', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-testdesign', name: 'Test Design',
    purpose: 'Refine cases + prepare data so requirement-stage cases are executable',
    gate: 'Boundary / exception / permission scenarios covered + test data ready + test cases baselined',
    roles: {
      PM: {
        inputs: [],
        outputs: [{ id: 'td-pm-o1', name: 'Test case review participation', kind: 'doc' }],
      },
      Dev: {
        inputs: [],
        outputs: [{ id: 'td-dev-o1', name: 'Technical clarification', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'td-qa-i1', name: 'Requirements + risk list', from: 'PM / QA' },
          { id: 'td-qa-i2', name: 'Historical defect repository (ZenTao)', from: 'QA' },
          { id: 'td-qa-i3', name: 'Test cases drafted during requirements', from: 'QA' },
        ],
        outputs: [
          // No new count here — Test Cases lives in Requirements to avoid double-counting.
          // Test Design is refinement work on top of it.
          { id: 'td-qa-o1', name: 'Test case refinement (boundary / exception / permission)', kind: 'doc' },
          { id: 'td-qa-o2', name: 'Test dataset design', kind: 'doc' },
          { id: 'td-qa-o3', name: 'Final test case baseline / version confirmed', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-execute', name: 'Test Execution',
    purpose: 'Execute test cases + collect evidence + log defects',
    gate: '100% execution + every defect assigned + complete evidence',
    roles: {
      PM: {
        inputs: [],
        outputs: [
          { id: 'ex-pm-o1', name: 'Defect priority decision', kind: 'doc' },
          { id: 'ex-pm-o2', name: 'UAT acceptance', kind: 'doc' },
        ],
      },
      Dev: {
        inputs: [{ id: 'ex-dev-i1', name: 'Defect record (ZenTao)', from: 'QA' }],
        outputs: [{ id: 'ex-dev-o1', name: 'Defect fix + test handoff', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'ex-qa-i1', name: 'Test environment (SIT / UAT) available', from: 'DevOps' },
          { id: 'ex-qa-i2', name: 'Testable build', from: 'Dev' },
          { id: 'ex-qa-i3', name: 'Test data ready', from: 'QA' },
        ],
        outputs: [
          { id: 'ex-qa-o1', name: 'Execution records (Pass / Fail)', kind: 'count', defaultTarget: 0,
            linkedTo: 'req-qa-o1', note: 'Target = test case count (automatically synchronized)' },
          { id: 'ex-qa-o2', name: 'Defect records (ZenTao)', kind: 'count', defaultTarget: 0, note: 'Can be retrieved automatically through the ZenTao API' },
          { id: 'ex-qa-o3', name: 'Screenshot / log evidence', kind: 'doc' },
          { id: 'ex-qa-o4', name: 'Daily report / progress update', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [{ id: 'ex-ops-o1', name: 'Stable test environment', kind: 'doc' }],
      },
    },
  },
  {
    id: 'sdlc-regress', name: 'Regression',
    purpose: 'Ensure fixes do not introduce new issues',
    gate: 'All high-risk regression paths pass',
    roles: {
      Dev: {
        inputs: [],
        outputs: [{ id: 'rg-dev-o1', name: 'Developer verification of defect fixes', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'rg-qa-i1', name: 'Fixed defect list (ZenTao)', from: 'QA' },
          { id: 'rg-qa-i2', name: 'Impact scope', from: 'Dev' },
        ],
        outputs: [
          { id: 'rg-qa-o1', name: 'Regression plan', kind: 'doc' },
          { id: 'rg-qa-o2', name: 'Automated regression runs', kind: 'count', defaultTarget: 0 },
          { id: 'rg-qa-o3', name: 'Regression report', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-release', name: 'Execution Review',
    purpose: 'Provide a QA-readiness conclusion without replacing the business release decision',
    gate: 'Clear execution outcome + risk owner sign-off',
    roles: {
      PM: {
        inputs: [],
        outputs: [
          { id: 'rl-pm-o1', name: 'Go / No-Go decision', kind: 'doc' },
          { id: 'rl-pm-o2', name: 'Release announcement / user notification', kind: 'doc' },
        ],
      },
      Dev: {
        inputs: [],
        outputs: [{ id: 'rl-dev-o1', name: 'Release package / deployment scripts', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'rl-qa-i1', name: 'All test cases executed', from: 'QA' },
          { id: 'rl-qa-i2', name: 'Outstanding defect status confirmed', from: 'QA + PM' },
        ],
        outputs: [
          { id: 'rl-qa-o1', name: 'QA Readiness Report', kind: 'doc' },
          { id: 'rl-qa-o2', name: 'Execution-risk acceptance record', kind: 'doc' },
          { id: 'rl-qa-o3', name: 'Execution-review checklist passed', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [
          { id: 'rl-ops-o1', name: 'Production deployment', kind: 'doc' },
          { id: 'rl-ops-o2', name: 'Monitoring and alerts ready', kind: 'doc' },
        ],
      },
    },
  },
  {
    id: 'sdlc-postrelease', name: 'Post-Release Feedback',
    purpose: 'Monitor + review + feed improvements back into the system',
    gate: 'Issues closed + improvements completed',
    roles: {
      PM: {
        inputs: [{ id: 'po-pm-i1', name: 'Production data / user feedback', from: 'Ops / SRE' }],
        outputs: [{ id: 'po-pm-o1', name: 'Data review + improvement tracking', kind: 'doc' }],
      },
      Dev: {
        inputs: [],
        outputs: [{ id: 'po-dev-o1', name: 'Production defect fixes', kind: 'doc' }],
      },
      QA: {
        inputs: [
          { id: 'po-qa-i1', name: 'Production monitoring data', from: 'DevOps / SRE' },
          { id: 'po-qa-i2', name: 'User / customer-service feedback', from: 'Operations' },
        ],
        outputs: [
          { id: 'po-qa-o1', name: 'Production issue retrospective', kind: 'doc' },
          { id: 'po-qa-o2', name: 'Production defect analysis', kind: 'doc' },
          { id: 'po-qa-o3', name: 'Improvement actions (with owner / due date)', kind: 'doc' },
        ],
      },
      DevOps: {
        inputs: [],
        outputs: [
          { id: 'po-ops-o1', name: 'Monitoring-alert closure', kind: 'doc' },
          { id: 'po-ops-o2', name: 'SLA report', kind: 'doc' },
        ],
      },
    },
  },
]

const HARNESS_REVIEW = [
  { module: 'Process Standards', status: 'Partial', gap: 'Still needs consistent enforcement in real projects', action: 'Enforce it through project gates' },
  { module: 'Template System', status: 'Partial', gap: 'QA Readiness Report must connect to 06-execution-review', action: 'Generate execution-review reports and risk-acceptance records' },
  { module: 'Automation Platform', status: 'Foundation ready', gap: 'Project home page / SKU details are not automated', action: 'Complete critical-path coverage' },
  { module: 'Evidence System', status: 'Present but rejected', gap: 'The gate reports issues with comments, screenshots, and status', action: 'Make gate.py pass first' },
  { module: 'Quality Gates', status: 'Tooling ready', gap: 'Current status is OVERALL FAIL and CI is not integrated', action: 'Fix failures and integrate with CI' },
  { module: 'Metrics Dashboard', status: 'Early stage', gap: 'Metric definitions are not fully automated', action: 'Aggregate stage metrics automatically' },
  { module: 'Retrospective Loop', status: 'Weak', gap: 'Missing execution review, post-release feedback, and sign-off flow', action: 'Instantiate the execution-review template' },
  { module: 'Continuous Operations', status: 'Weak', gap: 'Not a Git repository and has no .gitignore', action: 'Establish versioning and auditability' },
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
  // ---- Phase 2 / id=3  Process Standards & Roles (SDLC) --------------------
  3: {
    brief: 'Define who does what, what comes in, what goes out, and where the gate sits at every SDLC stage. RACI is the industry-standard language.',
    frameworks: [
      { name: 'RACI Matrix', url: 'https://www.pmi.org/learning/library/raci-matrix-creating-clarity-9534',
        summary: 'PMI responsibility matrix: Responsible / Accountable / Consulted / Informed' },
      { name: 'ISTQB Foundation', url: 'https://www.istqb.org/',
        summary: 'International baseline for the seven testing activities and role responsibilities (CTFL syllabus)' },
      { name: 'SAFe Agile Roles', url: 'https://scaledagileframework.com/',
        summary: 'Role definitions for scaled Agile delivery (PO / SM / Dev / QA / RTE...)' },
    ],
    sections: [],
    antiPatterns: [
      'Everyone is responsible, so no one is responsible — each RACI item must have exactly one Accountable owner',
      'The role list exists but is never referenced in PRs or reviews — it becomes a formality',
      'Only QA is defined in detail while every other role gets one sentence — cross-functional collaboration has no foundation',
    ],
  },

  // ---- Phase 1 / id=2  Quality Goals & Metrics -----------------------------
  2: {
    brief: 'Turn "is quality good?" into measurable quality data. North-star metrics drive priorities across the system.',
    frameworks: [
      { name: 'DORA Four Keys', url: 'https://dora.dev/guides/dora-metrics-four-keys/',
        summary: 'Four software-delivery performance metrics defined by Google DORA; the industry benchmark for elite teams includes on-demand deployment, recovery within one hour, and CFR of 0-15%' },
      { name: 'ISO/IEC 25010:2023', url: 'https://www.iso.org/standard/35733.html',
        summary: 'Eight quality characteristics and 31 sub-characteristics: a global software-quality benchmark' },
      { name: 'ISTQB Defect Metrics', url: 'https://www.istqb.org/',
        summary: 'Classic QA metrics such as Defect Escape Rate (DER), Defect Removal Efficiency (DRE), and defect density' },
    ],
    sections: [
      {
        kind: 'kpiCatalog', title: 'KPI Catalog (Your North Star)',
        columns: ['Metric', 'Formula', 'Team Target', 'Elite Benchmark', 'Data Source', 'Category'],
        rows: [
          ['Deployment Frequency (DF)', 'Production deployments / week',        '≥ 1 per day', 'On demand', 'CI/CD',              'DORA'],
          ['Lead Time for Changes (LT)', 'Commit → production elapsed time',      '< 1 day',     '< 1 hour', 'CI/CD',              'DORA'],
          ['Change Failure Rate (CFR)', 'Failed deployments / total deployments', '< 15%',       '0-15%',    'CI/CD + monitoring', 'DORA'],
          ['Mean Time to Restore (MTTR)', 'Incident start → service restored',    '< 1 day',     '< 1 hour', 'Monitoring alerts',  'DORA'],
          ['Defect Escape Rate (DER)', 'Post-release defects / total defects',    '< 5%',        '< 1%',     'ZenTao',             'QA'],
          ['Defect Removal Efficiency (DRE)', 'Pre-release defects / total defects', '≥ 95%',    '≥ 99%',    'ZenTao',             'QA'],
          ['Automation Coverage', 'Automated cases / total cases',                '≥ 50%',       '≥ 80%',    'dashboard.db',       'QA'],
          ['Evidence Completeness', 'Cases with complete evidence / executed cases', '100%',     '100%',     'gate.py',            'QA'],
        ],
      },
      {
        kind: 'iso25010', title: 'ISO 25010 Eight Quality Characteristics — Test Objective Breakdown',
        items: [
          { name: 'Functional Suitability', sub: 'Completeness / correctness / appropriateness' },
          { name: 'Performance Efficiency', sub: 'Time behavior / resource utilization / capacity' },
          { name: 'Compatibility', sub: 'Co-existence / interoperability' },
          { name: 'Interaction Capability', sub: 'Learnability / operability / user-error protection / aesthetics / accessibility' },
          { name: 'Reliability', sub: 'Maturity / availability / fault tolerance / recoverability' },
          { name: 'Security', sub: 'Confidentiality / integrity / non-repudiation / accountability / authenticity' },
          { name: 'Maintainability', sub: 'Modularity / reusability / analyzability / modifiability / testability' },
          { name: 'Portability', sub: 'Adaptability / installability / replaceability' },
        ],
      },
    ],
    antiPatterns: [
      'Metrics are displayed but drive no action — a dashboard without linked improvements is decoration',
      'Counting cases without measuring coverage or escapes — more cases do not mean better testing',
      'Metrics rely on manual collection — the process will break without automation',
      'Every metric is important means there is no north star — choose 3-5',
    ],
  },

  // ---- Phase 3 / id=4  Deliverables & Templates ----------------------------
  4: {
    brief: 'Templates reduce onboarding effort and keep outputs consistent. IEEE 829 and ISTQB provide industry baselines.',
    frameworks: [
      { name: 'IEEE 829-2008', url: 'https://standards.ieee.org/ieee/829/4453/',
        summary: 'Eight standard test document types: Master Plan / Level Plan / Design Spec / Case Spec / Procedure Spec / Item Transmittal Report / Log / Incident Report / Summary Report' },
      { name: 'ISTQB Foundation Test Process', url: 'https://www.istqb.org/',
        summary: 'Seven testing activities: planning / monitoring / analysis / design / implementation / execution / completion' },
    ],
    sections: [
      {
        kind: 'templateCatalog', title: 'Template Catalog (Mapped to IEEE 829)',
        columns: ['Template', 'IEEE 829 Mapping', 'Key Sections', 'Owner'],
        rows: [
          ['Test Strategy',             'Master Test Plan',        'Scope / Approach / Risks / Schedule / Resources',               'Test Manager'],
          ['Test Cases',                'Test Case Specification', 'Preconditions / Steps / Expected / Actual / Pass or Fail',       'QA'],
          ['Requirement Review Checklist', '—',                    'Testability / completeness / boundaries / permissions / data interference', 'QA Lead'],
          ['Test Report',               'Test Summary Report',     'Execution statistics / defect distribution / risks / Go-No-Go recommendation', 'Test Manager'],
          ['Retrospective Report',       '—',                       'Went well / Didn\'t / Improve / Owners',                         'Team'],
          ['Defect Report',              'Test Incident Report',    'Title / steps / expected / actual / severity / priority / environment / screenshot', 'QA'],
        ],
      },
    ],
    antiPatterns: [
      'Templates are too heavy → form fatigue → the team skips them',
      'Templates sit unmaintained in a wiki → become outdated → teams create their own forks',
      'No owner → no one is accountable for template quality',
    ],
  },

  // ---- Phase 4 / id=5  Execution & Evidence -------------------------------
  5: {
    brief: '"Tested" does not merely mean "run." Results, evidence, and defect records are all required, and an audit trail is fundamental.',
    frameworks: [
      { name: 'ISTQB Defect Lifecycle', url: 'https://www.istqb.org/',
        summary: 'Standard defect workflow: New → Assigned → Open → Fixed → Retest → Verified → Closed' },
      { name: 'Severity × Priority Matrix', url: 'https://www.istqb.org/',
        summary: 'Severity measures technical impact; Priority measures business urgency. They are independent, and the matrix determines handling order.' },
    ],
    sections: [
      {
        kind: 'defectLifecycle', title: 'Defect Lifecycle (ISTQB Standard)',
        states: [
          { name: 'New', color: '#1677ff', desc: 'Newly discovered and unassigned' },
          { name: 'Assigned', color: '#13c2c2', desc: 'Assigned to a developer' },
          { name: 'Open', color: '#fa8c16', desc: 'Confirmed by development and awaiting a fix' },
          { name: 'Fixed', color: '#722ed1', desc: 'Fixed and awaiting QA verification' },
          { name: 'Verified', color: '#52c41a', desc: 'Verified by QA' },
          { name: 'Closed', color: '#389e0d', desc: 'Closed and archived' },
        ],
        sideStates: ['Reopened', 'Rejected', 'Deferred', 'Duplicate'],
      },
      {
        kind: 'severityMatrix', title: 'Severity × Priority Handling Matrix',
        cols: ['P1 Immediate', 'P2 Current Release', 'P3 Next Release'],
        rows: ['S1 Critical', 'S2 Major', 'S3 Moderate', 'S4 Minor'],
        cells: [
          [{ text: 'Fix immediately', color: '#ff4d4f' }, { text: 'Required this release', color: '#ff7a45' }, { text: 'Required next release', color: '#fa8c16' }],
          [{ text: 'Fix immediately', color: '#ff4d4f' }, { text: 'Required this release', color: '#ff7a45' }, { text: 'Schedule', color: '#faad14' }],
          [{ text: 'Required this release', color: '#ff7a45' }, { text: 'Schedule', color: '#faad14' }, { text: 'Schedule or reject', color: '#d9d9d9' }],
          [{ text: 'Schedule', color: '#faad14' }, { text: 'Schedule or reject', color: '#d9d9d9' }, { text: 'May reject', color: '#bfbfbf' }],
        ],
      },
      {
        kind: 'evidenceRules', title: 'Evidence Standard by Test Type',
        columns: ['Test Type', 'Required Evidence', 'Optional Evidence'],
        rows: [
          ['Functional Testing', 'Step screenshots + result screenshots', 'Screen recording'],
          ['API Testing', 'Request + response + status code', 'Network capture log'],
          ['Performance Testing', 'Locust summary + Grafana screenshots', 'Raw Prometheus queries'],
          ['Compatibility Testing', 'Device screenshots (including user agent)', 'BrowserStack link'],
          ['Security Testing', 'Tool report + reproduction steps', 'CVE reference'],
        ],
      },
    ],
    antiPatterns: [
      'Pass / Fail has no reason → retrospectives have no evidence',
      'A defect has no owner or due date → it stagnates in the system',
      'Evidence is an unread ZIP archive → effectively no evidence',
      '"It passed when rerun" without a flaky marker → the same issue returns next time',
    ],
  },

  // ---- Phase 5 / id=6  Automation & Platform ------------------------------
  6: {
    brief: 'The test pyramid is economics, not dogma: more lower-level tests and fewer top-level tests produce faster feedback at lower cost.',
    frameworks: [
      { name: 'Mike Cohn Test Pyramid', url: 'https://martinfowler.com/bliki/TestPyramid.html',
        summary: 'Introduced by Cohn in Succeeding with Agile (2009): a wide base, narrow top, and the commonly cited 70/20/10 ratio' },
      { name: 'Practical Test Pyramid (Fowler)', url: 'https://martinfowler.com/articles/practical-test-pyramid.html',
        summary: 'Fowler treats E2E as a second line of defense: an E2E failure indicates both a defect and a unit-test gap' },
      { name: 'Testing Honeycomb (Microservices)', url: 'https://engineering.atspotify.com/2018/01/testing-of-microservices/',
        summary: 'In microservice architectures, the integration layer becomes thicker and forms a honeycomb shape' },
    ],
    sections: [
      {
        kind: 'testPyramid', title: 'Test Pyramid — Target Ratio',
        layers: [
          { layer: 'E2E / UI',           pct: 10, speed: 'Slow (minutes)',       flaky: 'High',   maintain: 'High',   stack: 'Behave + Playwright' },
          { layer: 'Integration / API',  pct: 20, speed: 'Medium (seconds)',     flaky: 'Medium', maintain: 'Medium', stack: 'requests + pytest' },
          { layer: 'Unit',               pct: 70, speed: 'Fast (milliseconds)', flaky: 'Low',    maintain: 'Low',    stack: 'pytest / Vitest' },
        ],
      },
      {
        kind: 'toolStack', title: 'Current Tool Stack',
        columns: ['Layer', 'Tools', 'Current Status'],
        rows: [
          ['E2E', 'Behave + Playwright', 'Implemented'],
          ['API', 'requests + pytest', 'Partial'],
          ['Unit', 'pytest / Vitest', 'Owned by development'],
          ['Performance', 'Locust + Prometheus + Grafana', 'Implemented'],
          ['Logging', 'Loki', 'Implemented'],
          ['Dashboard', 'FastAPI + Vite + Ant Design', 'Implemented'],
        ],
      },
    ],
    antiPatterns: [
      'Ice Cream Cone (inverted pyramid) — too many E2E tests and too few unit tests → slow and flaky',
      'Using Selenium / Playwright to test backend logic → use unit tests instead',
      'Hard-coded CSS selectors → every UI change breaks tests; use data-testid',
      'Using sleep() instead of explicit waits → slow and flaky',
    ],
  },

  // ---- Phase 6 / id=7  Quality Gates & Release Readiness ------------------
  7: {
    brief: 'A gate is insurance, not obstruction. DoR and DoD give the team a shared definition of "ready."',
    frameworks: [
      { name: 'Scrum Guide — DoD', url: 'https://scrumguides.org/scrum-guide.html#done',
        summary: 'The Scrum Guide requires a shared Definition of Done; Sutherland extends the concept to readiness in Be Ready to be Done' },
      { name: 'Definition of Ready (DoR)', url: 'https://www.scrum.org/resources/blog/walking-through-definition-ready',
        summary: 'Entry criteria for a Sprint ensure work is actionable. DoR is optional but strongly recommended.' },
      { name: 'ISTQB Risk-Based Testing', url: 'https://www.istqb.org/',
        summary: 'Risk-based testing + Go / No-Go decision matrix' },
    ],
    sections: [
      {
        kind: 'twoListChecklist', title: 'DoR vs DoD',
        left: {
          title: 'Definition of Ready (DoR) — Ready for Delivery',
          items: [
            'PRD reviewed and approved',
            'Acceptance criteria are clear',
            'Technical approach is clarified',
            'Test points are identified',
            'Dependencies are ready (API / data / environment)',
            'The story can be delivered within one Sprint',
          ],
        },
        right: {
          title: 'Definition of Done (DoD) — Delivery Complete',
          items: [
            'Code merged into the main branch',
            'Unit-test coverage ≥ 60%',
            'All P0 / P1 defects closed',
            'All test cases executed',
            'QA Readiness Report generated and signed',
            'gate.py OVERALL PASS',
            'Release risks recorded',
          ],
        },
      },
      {
        kind: 'releaseGate', title: 'Execution Review Gate (Thresholds + Data Sources)',
        columns: ['Metric', 'Threshold', 'Current', 'Data Source'],
        rows: [
          ['Execution Rate', '100%', '—', 'dashboard.db'],
          ['Open P0 Defects', '0', '—', 'ZenTao'],
          ['Open P1 Defects', '0', '—', 'ZenTao'],
          ['Regression Pass Rate', '≥ 95%', '—', 'dashboard.db'],
          ['gate.py Status', 'OVERALL PASS', 'FAIL', 'gate.py'],
          ['Execution Review Sign-Off', 'Owner signed', '—', 'QA Readiness Report'],
        ],
      },
    ],
    antiPatterns: [
      'A gate that is too loose is not a gate',
      'DoD exists in a wiki but does not block PRs → it is only decoration',
      'Ignoring risk and forcing a Go decision → one incident can erase the value of ten gates',
      'A gate checks tests but ignores defect status → P0 defects slip through',
    ],
  },

  // ---- Phase 7 / id=8  Metrics & Continuous Improvement -------------------
  8: {
    brief: 'Metrics without improvement are data noise. Retrospective → action → updates to templates, gates, and automation creates the feedback loop.',
    frameworks: [
      { name: 'Toyota / Lean — PDCA', url: 'https://en.wikipedia.org/wiki/PDCA',
        summary: 'Plan → Do → Check → Act: the Deming cycle and a foundational improvement framework' },
      { name: 'Google SRE — Blameless Postmortem', url: 'https://sre.google/sre-book/postmortem-culture/',
        summary: 'A blameless postmortem culture that focuses on systems, not people' },
      { name: 'DORA — Generative Culture', url: 'https://dora.dev/research/2022/',
        summary: 'Westrum culture model: information flow, shared responsibility, and systems thinking drive high performance' },
    ],
    sections: [],
    antiPatterns: [
      'A retrospective only says "be more careful next time" — no concrete action, owner, or due date',
      'Improvement actions are written and forgotten — not added to a Sprint, OKR, or gate',
      'The dashboard is built but not maintained — stale data → no readers → a downward spiral',
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
  green:  { tag: 'success', dot: '#52c41a', bg: 'rgba(82,196,26,0.12)',  border: '#52c41a', text: 'Complete' },
  yellow: { tag: 'warning', dot: '#faad14', bg: 'rgba(250,173,20,0.12)', border: '#faad14', text: 'In Progress' },
  gray:   { tag: 'default', dot: '#bfbfbf', bg: 'rgba(0,0,0,0.04)',      border: '#d9d9d9', text: 'Not Started' },
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
  'Complete': 100,
  'Foundation ready': 70, 'Tooling ready': 70,
  'Partial': 50, 'Early stage': 50,
  'Present but rejected': 30,
  'Weak': 10,
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
              {trusted ? 'Trusted' : 'Blocked'}
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
    ? <Tag color="success" style={{ margin: 0, fontSize: 11 }}>Evidence-backed</Tag>
    : hasPackage
      ? <Tag color="error" style={{ margin: 0, fontSize: 11 }}>Evidence blocked</Tag>
      : checked
        ? <Tag color="warning" style={{ margin: 0, fontSize: 11 }}>Manual</Tag>
        : <Tag style={{ margin: 0, fontSize: 11 }}>No evidence</Tag>
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
            <Tooltip title={`Target synchronized automatically from ${output.linkedTo}`}>
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
            <Text type="secondary" style={{ fontSize: 11 }}>Inputs</Text>
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
            <Text type="secondary" style={{ fontSize: 11 }}>Outputs</Text>
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
        <Text type="secondary" style={{ fontSize: 12 }}>Industry Reference Frameworks</Text>
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
          Alternate states: {sideStates.map(s => <Tag key={s} style={{ fontSize: 10, marginRight: 4 }}>{s}</Tag>)}
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
            { title: 'Layer', dataIndex: 'layer', render: (v) => <Text strong style={{ fontSize: 12 }}>{v}</Text> },
            { title: 'Feedback Speed', dataIndex: 'speed', render: (v) => <Tag>{v}</Tag> },
            { title: 'Flaky Risk', dataIndex: 'flaky', render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text> },
            { title: 'Maintenance Cost', dataIndex: 'maintain', render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text> },
            { title: 'Tools', dataIndex: 'stack', render: (v) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
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
        <Text strong style={{ fontSize: 12, color: '#ff4d4f' }}>Pitfalls (Anti-Patterns)</Text>
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
            return <Text type="secondary">Unknown section type: {section.kind}</Text>
        }
      })()}
    </div>
  )
}

/**
 * Slim mode — only renders the figures (KPI tables, pyramid, matrix, etc.)
 * plus a tiny `References` link row. Drops BriefBanner, FrameworkRefs cards, and
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
          References: {refs.map((f, i) => (
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
        title={<><ApartmentOutlined style={{ color: '#13c2c2' }} /> SDLC Process Standard ({SDLC_STAGES.length} Stages · Multiple Roles)</>}
        extra={<Text type="secondary" style={{ fontSize: 11 }}>Select a stage to view details</Text>}
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
              Inputs {r.inDone}/{r.inTotal} · Outputs {r.outDone}/{r.outTotal}
            </Text>
            <Progress percent={r.pct} size="small" style={{ width: 100 }} strokeColor={c.dot} showInfo={false} />
            <Text style={{ fontSize: 12, color: c.dot, fontWeight: 600 }}>{r.pct}%</Text>
          </Space>
        }
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
      >
        <div style={{ marginBottom: 14, padding: '8px 12px', background: '#f6f4ff', borderRadius: 6 }}>
          <Text type="secondary" style={{ fontSize: 11 }}>Quality gate for this stage</Text>
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
          Actions for This Phase (Evidence Takes Priority; Manual Checks Only Record Progress)
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
    { title: 'Module', dataIndex: 'module', width: 130, render: (v) => <Text strong style={{ fontSize: 12 }}>{v}</Text> },
    {
      title: 'Status', dataIndex: 'status', width: 140,
      render: (v) => {
        const m = { 'Complete': 'success', 'Foundation ready': 'processing', 'Tooling ready': 'processing',
          'Present but rejected': 'warning', 'Early stage': 'warning',
          'Partial': 'warning', 'Weak': 'error' }
        return <Tag color={m[v] || 'default'}>{v}</Tag>
      },
    },
    { title: 'Gap', dataIndex: 'gap', render: (v) => <Text style={{ fontSize: 12 }}>{v}</Text> },
    { title: 'Recommended Action', dataIndex: 'action', width: 220, render: (v) => <Text style={{ fontSize: 12, color: '#1677ff' }}>{v}</Text> },
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
              Assessment {reviewPct}% · Improvements {completed}/{total}
            </Text>
          </Space>
        }
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
      >
        <Text strong style={{ fontSize: 13 }}>
          <FileDoneOutlined style={{ color: '#1677ff', marginRight: 6 }} />
          Actions for This Phase (Check Improvements After the System Is Operating)
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
        title={<><BugOutlined style={{ color: '#fa541c' }} /> Current qa-harness Assessment ({reviewPct}%)</>}
        extra={<Text type="secondary" style={{ fontSize: 11 }}>The weighted status average reflects system maturity</Text>}
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
              blockingIssues: [`Unable to read the evidence manifest: ${e.message || String(e)}`],
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
          Quality System — Process Standards · Multiple Roles · Multiple Stages
          <Tag style={{ marginLeft: 8 }}>{projectName}</Tag>
        </Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Select a phase to view details. Phase 2 covers the eight-stage, multi-role RACI-based SDLC process standard; Phase 7 covers metrics, continuous improvement, and the qa-harness assessment.
        </Text>
      </div>

      <QualityGateSummary qualityEvidence={qualityEvidence} loading={qualityEvidenceLoading} />

      {/* Phase strip */}
      <Card
        size="small"
        title={<><AimOutlined style={{ color: '#1677ff' }} /> Quality System Build Flow ({PHASES.length} Phases · Select to Switch)</>}
        style={{ borderRadius: 12, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', marginBottom: 16 }}
      >
        <ChipStrip
          items={PHASES}
          selectedId={selectedPhaseId}
          onSelect={setSelectedPhaseId}
          getLabel={(it) => `Phase ${it.displayId}`}
          getStatus={(it) => buildPhaseStatus(it, done, sdlcState, qualityEvidence).status}
          getPct={(it) => buildPhaseStatus(it, done, sdlcState, qualityEvidence).pct}
          getSubtitle={(it) => it.content === 'sdlc' ? '8 stages' : it.content === 'review' ? 'Assessment' : ''}
        />
      </Card>

      {/* Breadcrumb hint */}
      <div style={{ marginBottom: 12, color: '#8c8c8c', fontSize: 12 }}>
        <Text type="secondary">Quality System Build</Text>
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
