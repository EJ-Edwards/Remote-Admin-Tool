import { useEffect, useState } from 'react'
import { api, getToken } from '../lib/api'
import DataTable from '../components/DataTable'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Reports() {
  const [rows, setRows] = useState([])
  const load = () => api('/reports').then(setRows).catch(console.error)
  useEffect(() => { load() }, [])

  const create = async () => {
    const title = `Audit report ${new Date().toLocaleDateString()}`
    await api('/reports', { method: 'POST', body: JSON.stringify({ title, report_type: 'csv' }) })
    load()
  }

  const cols = [
    { key: 'title', label: 'Title' },
    { key: 'report_type', label: 'Type' },
    { key: 'created_at', label: 'Created', render: (r) => new Date(r.created_at).toLocaleString() },
    {
      key: 'download',
      label: 'Download',
      render: (r) =>
        r.download_url ? (
          <button
            type="button"
            className="text-accent"
            onClick={async () => {
              const res = await fetch(`${API_URL}${r.download_url}`, {
                headers: { Authorization: `Bearer ${getToken()}` },
              })
              const blob = await res.blob()
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `${r.title}.csv`
              a.click()
            }}
          >
            CSV
          </button>
        ) : '—',
    },
  ]
  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Reports</h2>
        <button type="button" onClick={create} className="rounded-lg bg-accent px-3 py-1.5 text-sm text-white">
          Generate CSV report
        </button>
      </div>
      <p className="mt-2 text-sm text-slate-500">PDF export coming soon.</p>
      <div className="mt-4">
        <DataTable columns={cols} rows={rows} emptyMessage="No reports yet." />
      </div>
    </div>
  )
}
