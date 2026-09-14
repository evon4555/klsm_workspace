import { useRef, useEffect } from 'react'
import { Card } from 'antd'
import { CodeOutlined } from '@ant-design/icons'

export default function LiveLog({
  lines,
  embedded = false,
  emptyText = 'Waiting for log output...',
}) {
  const logRef = useRef(null)

  useEffect(() => {
    const el = logRef.current
    if (!el) return

    const currentLeft = el.scrollLeft
    el.scrollTop = el.scrollHeight
    el.scrollLeft = currentLeft
  }, [lines])

  if (!embedded && (!lines || lines.length === 0)) return null

  const content = lines && lines.length > 0 ? lines.join('\n') : emptyText
  const pre = (
    <pre
      ref={logRef}
      style={{
        maxHeight: embedded ? 460 : 400,
        minHeight: embedded ? 180 : undefined,
        overflowX: 'auto',
        overflowY: 'auto',
        background: '#1a1a2e',
        color: '#d4d4d4',
        padding: 16,
        margin: 0,
        borderRadius: embedded ? 8 : '0 0 12px 12px',
        fontSize: 13,
        lineHeight: 1.6,
        fontFamily: '"Cascadia Code", "Fira Code", "Consolas", monospace',
      }}
    >
      {content}
    </pre>
  )

  if (embedded) return pre

  return (
    <Card
      title={<><CodeOutlined /> Live Log</>}
      style={{
        marginTop: 16,
        borderRadius: 12,
        border: 'none',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        overflow: 'hidden',
      }}
      styles={{ body: { padding: 0 } }}
    >
      {pre}
    </Card>
  )
}
