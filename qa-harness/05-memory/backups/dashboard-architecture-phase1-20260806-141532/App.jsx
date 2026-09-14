import { useEffect, useState } from 'react'
import { Layout, Menu, ConfigProvider, theme, Typography, Select, Space, Tag, Alert, Modal, Button } from 'antd'
import {
  ExperimentOutlined,
  MailOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  DashboardOutlined,
  SettingOutlined,
  SafetyCertificateOutlined,
  ProjectOutlined,
  AuditOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons'

import DashboardPage from './pages/DashboardPage'
import TestRunPage from './pages/TestRunPage'
import EmailNotificationPage from './pages/EmailNotificationPage'
import PerformanceTestPage from './pages/PerformanceTestPage'
import ApiMonitorPage from './pages/ApiMonitorPage'
import QualitySystemPage from './pages/QualitySystemPage'
import PackageHealthPage from './pages/PackageHealthPage'
import ZenTaoDashboardPage from './pages/ZenTaoDashboardPage'
import QADecisionCenterPage from './pages/QADecisionCenterPage'
import { fetchProjects } from './api'

const { Sider, Content, Header } = Layout
const { Text } = Typography

const DEFAULT_PROJECT_KEY = 'west-kowloon'
const PROJECT_STORAGE_KEY = 'qa-dashboard.activeProject'

const FALLBACK_PROJECTS = [
  {
    key: 'west-kowloon',
    name: 'West Kowloon',
    kind: 'customer',
    workspace: 'west-kowloon',
    zentaoProductId: 146,
    zentaoExecutionId: 614,
  },
  {
    key: 'standard product',
    name: 'Standard Product',
    kind: 'baseline',
    workspace: 'standard product',
    zentaoProductId: 22,
    zentaoExecutionId: 640,
  },
  {
    key: 'jockey club',
    name: 'Jockey Club',
    kind: 'customer',
    workspace: 'jockey club',
    zentaoProductId: null,
    zentaoExecutionId: null,
  },
]

const menuItems = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: 'test-run',
    icon: <ExperimentOutlined />,
    label: 'Test Run',
  },
  {
    key: 'qa-decision',
    icon: <AuditOutlined />,
    label: 'QA Decision Center',
  },
  {
    key: 'email',
    icon: <MailOutlined />,
    label: 'Email Notification',
  },
  {
    key: 'performance',
    icon: <ThunderboltOutlined />,
    label: 'Performance Test',
  },
  {
    key: 'api-monitor',
    icon: <ApiOutlined />,
    label: 'API Monitor',
  },
  {
    key: 'quality-system',
    icon: <SafetyCertificateOutlined />,
    label: 'Quality System',
  },
  {
    key: 'package-health',
    icon: <FolderOpenOutlined />,
    label: 'Package Health',
  },
  {
    key: 'zentao',
    icon: <ProjectOutlined />,
    label: 'ZenTao Integration',
  },
  {
    type: 'divider',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
]

const pageMap = {
  'dashboard': DashboardPage,
  'test-run': TestRunPage,
  'qa-decision': QADecisionCenterPage,
  'email': EmailNotificationPage,
  'performance': PerformanceTestPage,
  'api-monitor': ApiMonitorPage,
  'quality-system': QualitySystemPage,
  'package-health': PackageHealthPage,
  'zentao': ZenTaoDashboardPage,
}

const DEFAULT_PAGE_KEY = 'dashboard'

function pageKeyFromUrl() {
  if (typeof window === 'undefined') return DEFAULT_PAGE_KEY
  const page = new URLSearchParams(window.location.search).get('page')
  return pageMap[page] ? page : DEFAULT_PAGE_KEY
}

function projectKeyFromUrlOrStorage() {
  if (typeof window === 'undefined') return DEFAULT_PROJECT_KEY
  const urlProject = new URLSearchParams(window.location.search).get('project')
  if (urlProject) return urlProject
  try {
    return localStorage.getItem(PROJECT_STORAGE_KEY) || DEFAULT_PROJECT_KEY
  } catch {
    return DEFAULT_PROJECT_KEY
  }
}

function hasPersistedProjectChoice() {
  if (typeof window === 'undefined') return false
  const urlProject = new URLSearchParams(window.location.search).get('project')
  if (urlProject) return true
  try {
    return Boolean(localStorage.getItem(PROJECT_STORAGE_KEY))
  } catch {
    return false
  }
}

export default function App() {
  const [activeKey, setActiveKey] = useState(pageKeyFromUrl)
  const [collapsed, setCollapsed] = useState(false)
  const [projects, setProjects] = useState(FALLBACK_PROJECTS)
  const [projectError, setProjectError] = useState(null)
  const [activeProjectKey, setActiveProjectKey] = useState(projectKeyFromUrlOrStorage)
  const [projectChoiceCommitted, setProjectChoiceCommitted] = useState(hasPersistedProjectChoice)
  const [projectPickerOpen, setProjectPickerOpen] = useState(() => !hasPersistedProjectChoice())

  const PageComponent = pageMap[activeKey]
  const activeProject = (
    projects.find(p => p.key === activeProjectKey)
    || FALLBACK_PROJECTS.find(p => p.key === activeProjectKey)
    || FALLBACK_PROJECTS[0]
  )

  function syncUrl(nextPageKey, nextProjectKey, replace = false) {
    const url = new URL(window.location.href)
    if (nextPageKey === DEFAULT_PAGE_KEY) {
      url.searchParams.delete('page')
    } else {
      url.searchParams.set('page', nextPageKey)
    }
    url.searchParams.set('project', nextProjectKey)
    const nextUrl = `${url.pathname}${url.search}${url.hash}`
    if (replace) {
      window.history.replaceState({}, '', nextUrl)
    } else {
      window.history.pushState({}, '', nextUrl)
    }
  }

  useEffect(() => {
    const onPopState = () => {
      setActiveKey(pageKeyFromUrl())
      setActiveProjectKey(projectKeyFromUrlOrStorage())
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    let cancelled = false
    async function loadProjects() {
      try {
        const json = await fetchProjects()
        if (cancelled) return
        const loaded = json.projects && json.projects.length ? json.projects : FALLBACK_PROJECTS
        setProjects(loaded)
        setProjectError(null)
        const known = loaded.some(p => p.key === activeProjectKey)
        if (!known) {
          setActiveProjectKey(json.defaultProject || DEFAULT_PROJECT_KEY)
        }
      } catch (e) {
        if (!cancelled) {
          setProjectError(e.message || String(e))
          setProjects(FALLBACK_PROJECTS)
        }
      }
    }
    loadProjects()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!projectChoiceCommitted) return
    try {
      localStorage.setItem(PROJECT_STORAGE_KEY, activeProjectKey)
    } catch {
      // ignored
    }
  }, [activeProjectKey, projectChoiceCommitted])

  function handleMenuClick(e) {
    const nextKey = e.key
    setActiveKey(nextKey)
    syncUrl(nextKey, activeProjectKey)
  }

  function handleProjectChange(nextProjectKey) {
    setActiveProjectKey(nextProjectKey)
    setProjectChoiceCommitted(true)
    setProjectPickerOpen(false)
    syncUrl(activeKey, nextProjectKey)
  }

  function openProjectPicker() {
    setProjectPickerOpen(true)
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 8,
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        {/* Sidebar */}
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={240}
          style={{
            background: 'linear-gradient(180deg, #001529 0%, #002140 100%)',
            boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
          }}
        >
          {/* Logo area */}
          <div
            style={{
              height: 64,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              gap: 10,
            }}
          >
            <DashboardOutlined
              style={{ color: '#1677ff', fontSize: collapsed ? 24 : 22 }}
            />
            {!collapsed && (
              <Text
                strong
                style={{
                  color: '#fff',
                  fontSize: 15,
                  whiteSpace: 'nowrap',
                  letterSpacing: 0,
                }}
              >
                QA Platform
              </Text>
            )}
          </div>

          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[activeKey]}
            onClick={handleMenuClick}
            items={menuItems}
            style={{
              background: 'transparent',
              borderRight: 'none',
              marginTop: 8,
            }}
          />
        </Sider>

        {/* Main content */}
        <Layout style={{ background: '#f5f7fa' }}>
          <Header
            style={{
              height: 56,
              padding: '0 24px',
              background: '#fff',
              borderBottom: '1px solid #f0f0f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16,
            }}
          >
            <Space size={12} wrap>
              <ProjectOutlined style={{ color: '#1677ff' }} />
              <Text strong>Project</Text>
              <Select
                size="middle"
                value={activeProject.key}
                onChange={handleProjectChange}
                style={{ width: 240 }}
                optionFilterProp="label"
                showSearch
                options={projects.map(p => ({
                  value: p.key,
                  label: `${p.name} (${p.key})`,
                }))}
              />
              <Tag color={activeProject.kind === 'baseline' ? 'blue' : 'green'}>
                {activeProject.kind || 'project'}
              </Tag>
              {activeProject.zentaoProductId ? (
                <Tag>ZenTao product {activeProject.zentaoProductId}</Tag>
              ) : (
                <Tag color="default">ZenTao product not mapped</Tag>
              )}
              <Button size="small" onClick={openProjectPicker}>
                Change Project
              </Button>
            </Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {activeProject.root || activeProject.workspace}
            </Text>
          </Header>
          <Content
            style={{
              padding: 24,
              minHeight: 280,
              overflow: 'auto',
            }}
          >
            {projectError && (
              <Alert
                type="warning"
                showIcon
                message="Using local project fallback"
                description={projectError}
                style={{ marginBottom: 16 }}
              />
            )}
            {PageComponent ? (
              <PageComponent
                activeProject={activeProject}
                activeProjectKey={activeProject.key}
                projects={projects}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 100, color: '#999' }}>
                Coming soon...
              </div>
            )}
          </Content>
        </Layout>
        <Modal
          title="Select Project"
          open={projectPickerOpen}
          closable={projectChoiceCommitted}
          maskClosable={projectChoiceCommitted}
          keyboard={projectChoiceCommitted}
          footer={null}
          onCancel={() => {
            if (projectChoiceCommitted) setProjectPickerOpen(false)
          }}
          width={560}
        >
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Text type="secondary">
              Choose once for this dashboard session. All tabs inherit the same project context.
            </Text>
            {projects.map((p) => (
              <Button
                key={p.key}
                block
                size="large"
                type={p.key === activeProject.key ? 'primary' : 'default'}
                onClick={() => handleProjectChange(p.key)}
                style={{ height: 'auto', padding: '10px 14px', textAlign: 'left' }}
              >
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                  <Space>
                    <Text strong style={{ color: p.key === activeProject.key ? '#fff' : undefined }}>
                      {p.name}
                    </Text>
                    <Tag color={p.kind === 'baseline' ? 'blue' : 'green'}>{p.kind || 'project'}</Tag>
                    {p.zentaoProductId ? (
                      <Tag>ZenTao product {p.zentaoProductId}</Tag>
                    ) : (
                      <Tag color="default">ZenTao not mapped</Tag>
                    )}
                  </Space>
                  <Text
                    type={p.key === activeProject.key ? undefined : 'secondary'}
                    style={{ color: p.key === activeProject.key ? 'rgba(255,255,255,0.85)' : undefined }}
                  >
                    {p.root || p.workspace}
                  </Text>
                </Space>
              </Button>
            ))}
          </Space>
        </Modal>
      </Layout>
    </ConfigProvider>
  )
}
