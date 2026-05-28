const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function getToken() {
  return localStorage.getItem('sentinel_token')
}

export function setToken(token) {
  localStorage.setItem('sentinel_token', token)
}

export function clearToken() {
  localStorage.removeItem('sentinel_token')
}

export async function api(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('text/csv')) return res.text()
  return res.json()
}
