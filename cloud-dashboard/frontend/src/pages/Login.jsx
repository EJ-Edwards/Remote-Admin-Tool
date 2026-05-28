import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, setToken } from '../lib/api'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const { access_token } = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setToken(access_token)
      navigate('/')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <form onSubmit={submit} className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Sign in</h1>
        <p className="mt-1 text-sm text-slate-500">Sentinel Link cloud dashboard</p>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        <label className="mt-6 block text-sm font-medium text-slate-700">Email</label>
        <input
          type="email"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <label className="mt-4 block text-sm font-medium text-slate-700">Password</label>
        <input
          type="password"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button
          type="submit"
          className="mt-6 w-full rounded-lg bg-accent py-2.5 text-sm font-medium text-white hover:bg-accent-dark"
        >
          Sign in
        </button>
        <p className="mt-4 text-center text-sm text-slate-500">
          No account? <Link to="/signup" className="text-accent">Sign up</Link>
        </p>
      </form>
    </div>
  )
}
