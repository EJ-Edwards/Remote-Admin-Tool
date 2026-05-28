import { useEffect, useState } from 'react'
import { api, getToken } from '../lib/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
import Badge from '../components/Badge'
import DataTable from '../components/DataTable'

const cols = [
  { key: 'occurred_at', label: 'Time', render: (r) => new Date(r.occurred_at).toLocaleString() },
  { key: 'user_email', label: 'User', render: (r) => r.user_email || '—' },
  { key: 'event_type', label: 'Action' },
  { key: 'resource_name', label: 'Resource', render: (r) => r.resource_name || '—' },
  { key: 'result', label: 'Result' },
  { key: 'ip_address', label: 'IP', render: (r) => r.ip_address || '—' },
  { key: 'risk_level', label: 'Risk', render: (r) => <Badge label={r.risk_level} variant={r.risk_level} /> },
]

export default function AccessLogs() {
  const [rows, setRows] = useState([])
  useEffect(() => {
    api('/audit-events').then(setRows).catch(console.error)
  }, [])
  const exportCsv = async () => {
    const res = await fetch(`${API_URL}/audit-events/export`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'audit-events.csv'
    a.click()
  }
  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Access Logs</h2>
        <button type="button" onClick={exportCsv} className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm hover:bg-white">
          Export CSV
        </button>
      </div>
      <div className="mt-4">
        <DataTable columns={cols} rows={rows} emptyMessage="No access events recorded yet." />
      </div>
    </div>
  )
}
