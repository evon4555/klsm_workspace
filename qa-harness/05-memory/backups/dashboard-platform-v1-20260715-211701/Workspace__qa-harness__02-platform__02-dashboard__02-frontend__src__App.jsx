import { useEffect, useState } from 'react'
import { Layout, Menu, ConfigProvider, theme, Typography } from 'antd'
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

const { Sider, Content } = Layout
const { Text } = Typography

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

export default function App() {
  const [activeKey, setActiveKey] = useState(pageKeyFromUrl)
  const [collapsed, setCollapsed] = useState(false)

  const PageComponent = pageMap[activeKey]

  useEffect(() => {
    const onPopState = () => setActiveKey(pageKeyFromUrl())
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  function handleMenuClick(e) {
    const nextKey = e.key
    setActiveKey(nextKey)
    const url = new URL(window.location.href)
    if (nextKey === DEFAULT_PAGE_KEY) {
      url.searchParams.delete('page')
    } else {
      url.searchParams.set('page', nextKey)
    }
    window.history.pushState({}, '', `${url.pathname}${url.search}${url.hash}`)
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
                  letterSpacing: 0.5,
                }}
              >
                QA Dashboard
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
          <Content
            style={{
              padding: 24,
              minHeight: 280,
              overflow: 'auto',
            }}
          >
            {PageComponent ? <PageComponent /> : (
              <div style={{ textAlign: 'center', padding: 100, color: '#999' }}>
                Coming soon...
              </div>
            )}
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}
