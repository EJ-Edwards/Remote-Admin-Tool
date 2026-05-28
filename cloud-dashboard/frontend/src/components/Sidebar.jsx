import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Overview' },
  { to: '/access-logs', label: 'Access Logs' },
  { to: '/sensitive-downloads', label: 'Sensitive Downloads' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/systems', label: 'Systems' },
  { to: '/agents', label: 'Agents' },
  { to: '/users', label: 'Users' },
  { to: '/reports', label: 'Reports' },
  { to: '/settings', label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="flex w-56 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-5">
        <h1 className="text-lg font-semibold text-slate-900">Sentinel Link</h1>
        <p className="text-xs text-slate-500">Access monitoring</p>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === '/'}
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2 text-sm font-medium ${
                isActive ? 'bg-emerald-50 text-accent' : 'text-slate-600 hover:bg-slate-50'
              }`
            }
          >
            {l.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
