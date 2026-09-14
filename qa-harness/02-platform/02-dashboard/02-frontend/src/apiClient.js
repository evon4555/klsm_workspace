export class ApiError extends Error {
  constructor(message, status, payload = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export async function requestJson(input, init) {
  const response = await fetch(input, init)
  const contentType = response.headers.get('content-type') || ''
  let payload = null
  if (contentType.includes('application/json')) {
    payload = await response.json()
  } else {
    const text = await response.text()
    payload = text ? { message: text } : null
  }
  if (!response.ok) {
    const detail = payload?.detail || payload?.error || payload?.message
    throw new ApiError(detail || `HTTP ${response.status}`, response.status, payload)
  }
  return payload
}
