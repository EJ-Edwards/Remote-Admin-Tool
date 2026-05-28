import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import StatCard from '../components/StatCard'

export default function Dashboard() {
  const [s, setS] = useState(null)
  useEffect(() => {
    api('/dashboard/summary').then(setS).catch(console.error)
  }, [])
  if (!s) return <p className="text-slate-500">Loading...</p>
  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900">Overview</h2>
      <p className="mt-1 text-sm text-slate-500">Workspace activity at a glance</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard title="Total Systems" value={s.total_systems} />
        <StatCard title="Active Agents" value={s.active_agents} />
        <StatCard title="Access Events Today" value={s.access_events_today} />
        <StatCard title="Sensitive Downloads" value={s.sensitive_downloads} />
        <StatCard title="Failed Access Attempts" value={s.failed_access_attempts} />
        <StatCard title="Open Alerts" value={s.open_alerts} />
      </div>
    </div>
  )
}
