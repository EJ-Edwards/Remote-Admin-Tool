import { clearToken } from '../lib/api'
import { useNavigate } from 'react-router-dom'

export default function TopNav({ user }) {
  const navigate = useNavigate()
  const logout = () => {
    clearToken()
    navigate('/login')
  }
  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <div />
      <div className="flex items-center gap-4">
        {user && (
          <span className="text-sm text-slate-600">
            {user.name} <span className="text-slate-400">({user.role})</span>
          </span>
        )}
        <button
          type="button"
          onClick={logout}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
        >
          Log out
        </button>
      </div>
    </header>
  )
}
