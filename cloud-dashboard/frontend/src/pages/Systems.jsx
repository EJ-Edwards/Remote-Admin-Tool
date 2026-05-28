import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import Badge from '../components/Badge'
import DataTable from '../components/DataTable'

export default function Systems() {
  const [rows, setRows] = useState([])
  useEffect(() => {
    api('/systems').then(setRows).catch(console.error)
  }, [])
  const cols = [
    { key: 'name', label: 'System' },
    { key: 'type', label: 'Type' },
    { key: 'status', label: 'Status', render: (r) => <Badge label={r.status} variant={r.status} /> },
    { key: 'last_seen_at', label: 'Last Seen', render: (r) => r.last_seen_at ? new Date(r.last_seen_at).toLocaleString() : '—' },
  ]
  return (
    <div>
      <h2 className="text-xl font-semibold">Systems</h2>
      <div className="mt-4">
        <DataTable columns={cols} rows={rows} emptyMessage="No systems registered." />
      </div>
    </div>
  )
}
