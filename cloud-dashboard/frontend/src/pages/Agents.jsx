import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import Badge from '../components/Badge'
import DataTable from '../components/DataTable'

export default function Agents() {
  const [rows, setRows] = useState([])
  const [token, setToken] = useState('')
  const load = () => api('/agents').then(setRows).catch(console.error)
  useEffect(() => { load() }, [])

  const createToken = async () => {
    const res = await api('/agents/enrollment-tokens', {
      method: 'POST',
      body: JSON.stringify({ name: 'default' }),
    })
    setToken(res.token)
  }

  const cols = [
    { key: 'agent_name', label: 'Agent' },
    { key: 'status', label: 'Status', render: (r) => <Badge label={r.status} variant={r.status} /> },
    { key: 'version', label: 'Version' },
    { key: 'last_seen_at', label: 'Last Seen', render: (r) => r.last_seen_at ? new Date(r.last_seen_at).toLocaleString() : '—' },
  ]
  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Agents</h2>
        <button type="button" onClick={createToken} className="rounded-lg bg-accent px-3 py-1.5 text-sm text-white">
          Generate enrollment token
        </button>
      </div>
      {token && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
          <p className="font-medium text-amber-900">Enrollment token (copy now):</p>
          <code className="mt-2 block break-all text-amber-800">{token}</code>
        </div>
      )}
      <div className="mt-4">
        <DataTable columns={cols} rows={rows} emptyMessage="No agents enrolled." />
      </div>
    </div>
  )
}
