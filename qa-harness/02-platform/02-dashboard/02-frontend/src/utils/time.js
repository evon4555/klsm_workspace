export function parseDashboardTime(iso) {
  if (!iso) return null
  const raw = String(iso).trim()
  if (!raw) return null

  const value = raw.replace(' ', 'T')
  const hasExplicitZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)
  const date = new Date(hasExplicitZone ? value : `${value}Z`)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDashboardTime(iso, { withYear = false } = {}) {
  const date = parseDashboardTime(iso)
  if (!date) return 'N/A'

  return new Intl.DateTimeFormat('en-US', {
    year: withYear ? 'numeric' : undefined,
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

export function dashboardTimeValue(iso) {
  return parseDashboardTime(iso)?.getTime() || 0
}
