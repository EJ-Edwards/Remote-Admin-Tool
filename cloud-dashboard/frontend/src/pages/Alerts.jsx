import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import Badge from '../components/Badge'
import DataTable from '../components/DataTable'

export default function Alerts() {
  const [rows, setRows] = useState([])
  const load = () => api('/alerts').then(setRows).catch(console.error)
  useEffect(() => { load() }, [])

  const act = async (id, action) => {
    await api(`/alerts/${id}/${action}`, { method: 'PATCH' })
    load()
  }

  const cols = [
    { key: 'created_at', label: 'Time', render: (r) => new Date(r.created_at).toLocaleString() },
    { key: 'title', label: 'Alert' },
    { key: 'severity', label: 'Severity', render: (r) => <Badge label={r.severity} variant={r.severity} /> },
    { key: 'status', label: 'Status', render: (r) => <Badge label={r.status} variant={r.status} /> },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) =>
        r.status === 'open' ? (
          <div className="flex gap-2">
            <button type="button" className="text-xs text-accent" onClick={() => act(r.id, 'acknowledge')}>
              Acknowledge
            </button>
            <button type="button" className="text-xs text-slate-600" onClick={() => act(r.id, 'resolve')}>
              Resolve
            </button>
          </div>
        ) : null,
    },
  ]
  return (
    <div>
      <h2 className="text-xl font-semibold">Alerts</h2>
      <div className="mt-4">
        <DataTable columns={cols} rows={rows} emptyMessage="No alerts." />
      </div>
    </div>
  )
}
