import { Typography, Card, Form, Input, Select, Switch, Button, Table, Tag, Space, Row, Col, Divider, Empty } from 'antd'
import { MailOutlined, PlusOutlined, BellOutlined, ClockCircleOutlined } from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

// Sample data for the notification rules table
const sampleRules = [
  {
    key: '1',
    name: 'Nightly Run Failure',
    trigger: 'on_failure',
    recipients: 'team@example.com',
    enabled: true,
  },
  {
    key: '2',
    name: 'Weekly Summary',
    trigger: 'scheduled',
    recipients: 'manager@example.com',
    enabled: false,
  },
]

const columns = [
  { title: 'Rule Name', dataIndex: 'name', key: 'name' },
  {
    title: 'Trigger',
    dataIndex: 'trigger',
    key: 'trigger',
    render: (t) => {
      const colorMap = { on_failure: 'red', on_success: 'green', always: 'blue', scheduled: 'purple' }
      return <Tag color={colorMap[t] || 'default'}>{t.replace('_', ' ').toUpperCase()}</Tag>
    },
  },
  { title: 'Recipients', dataIndex: 'recipients', key: 'recipients' },
  {
    title: 'Enabled',
    dataIndex: 'enabled',
    key: 'enabled',
    render: (v) => <Switch checked={v} size="small" />,
  },
  {
    title: 'Action',
    key: 'action',
    render: () => <Button type="link" size="small">Edit</Button>,
  },
]

export default function EmailNotificationPage({ activeProject }) {
  const projectName = activeProject?.name || activeProject?.key || 'West Kowloon'
  return (
    <div style={{ maxWidth: 1200 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
          Email Notification
          <Tag style={{ marginLeft: 8 }}>{projectName}</Tag>
        </Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          Configure automated email alerts for test results
        </Text>
      </div>

      <Row gutter={24}>
        <Col span={16}>
          <Card
            title={<><BellOutlined /> Notification Rules</>}
            extra={<Button type="primary" icon={<PlusOutlined />} size="small">Add Rule</Button>}
          >
            <Table
              dataSource={sampleRules}
              columns={columns}
              size="small"
              pagination={false}
            />
          </Card>
        </Col>

        <Col span={8}>
          <Card title={<><MailOutlined /> SMTP Settings</>}>
            <Form layout="vertical" size="small">
              <Form.Item label="SMTP Server">
                <Input placeholder="smtp.example.com" disabled />
              </Form.Item>
              <Form.Item label="Port">
                <Input placeholder="587" disabled />
              </Form.Item>
              <Form.Item label="Username">
                <Input placeholder="notifications@example.com" disabled />
              </Form.Item>
              <Form.Item label="Password">
                <Input.Password placeholder="********" disabled />
              </Form.Item>
              <Button type="primary" block disabled>
                Save Settings
              </Button>
            </Form>
          </Card>

          <Card
            title={<><ClockCircleOutlined /> Recent Notifications</>}
            style={{ marginTop: 16 }}
          >
            <Empty
              description="No notifications sent yet"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </Card>
        </Col>
      </Row>

      <Divider />
      <Paragraph type="secondary" style={{ textAlign: 'center', fontSize: 12 }}>
        This feature is under development. Configuration will be available in a future release.
      </Paragraph>
    </div>
  )
}
