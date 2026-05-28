import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import Badge from '../components/Badge'
import DataTable from '../components/DataTable'

export default function Users() {
  const [rows, setRows] = useState([])
  useEffect(() => {
    api('/users').then(setRows).catch(console.error)
  }, [])
  const cols = [
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role', render: (r) => <Badge label={r.role} variant="low" /> },
  ]
  return (
    <div>
      <h2 className="text-xl font-semibold">Users</h2>
      <div className="mt-4">
        <DataTable columns={cols} rows={rows} />
      </div>
    </div>
  )
}
