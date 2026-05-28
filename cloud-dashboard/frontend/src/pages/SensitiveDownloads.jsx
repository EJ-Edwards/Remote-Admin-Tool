import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import Badge from '../components/Badge'
import DataTable from '../components/DataTable'

const SENSITIVE = new Set(['customer_data', 'financial_data', 'private_report', 'sensitive'])

export default function SensitiveDownloads() {
  const [rows, setRows] = useState([])
  useEffect(() => {
    api('/audit-events')
      .then((events) =>
        setRows(events.filter(
          (e) => e.event_type === 'file.downloaded' && SENSITIVE.has(e.resource_category),
        )),
      )
      .catch(console.error)
  }, [])
  const cols = [
    { key: 'occurred_at', label: 'Time', render: (r) => new Date(r.occurred_at).toLocaleString() },
    { key: 'user_email', label: 'User', render: (r) => r.user_email || '—' },
    { key: 'resource_name', label: 'File/Resource' },
    { key: 'resource_category', label: 'Category' },
    { key: 'ip_address', label: 'IP', render: (r) => r.ip_address || '—' },
    { key: 'risk_level', label: 'Risk', render: (r) => <Badge label={r.risk_level} variant={r.risk_level} /> },
    { key: 'result', label: 'Status' },
  ]
  return (
    <div>
      <h2 className="text-xl font-semibold">Sensitive Downloads</h2>
      <p className="mt-1 text-sm text-slate-500">Downloads flagged by resource category</p>
      <div className="mt-4">
        <DataTable columns={cols} rows={rows} emptyMessage="No sensitive downloads recorded." />
      </div>
    </div>
  )
}
