import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { api, getToken } from './lib/api'
import Layout from './components/Layout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import AccessLogs from './pages/AccessLogs'
import SensitiveDownloads from './pages/SensitiveDownloads'
import Alerts from './pages/Alerts'
import Systems from './pages/Systems'
import Agents from './pages/Agents'
import Users from './pages/Users'
import Reports from './pages/Reports'
import Settings from './pages/Settings'

function PrivateRoutes() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!getToken()) {
      setLoading(false)
      return
    }
    api('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])
  if (loading) return <p className="p-8 text-slate-500">Loading...</p>
  if (!user) return <Navigate to="/login" replace />
  return (
    <Routes>
      <Route element={<Layout user={user} />}>
        <Route index element={<Dashboard />} />
        <Route path="access-logs" element={<AccessLogs />} />
        <Route path="sensitive-downloads" element={<SensitiveDownloads />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="systems" element={<Systems />} />
        <Route path="agents" element={<Agents />} />
        <Route path="users" element={<Users />} />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/*" element={<PrivateRoutes />} />
      </Routes>
    </BrowserRouter>
  )
}
