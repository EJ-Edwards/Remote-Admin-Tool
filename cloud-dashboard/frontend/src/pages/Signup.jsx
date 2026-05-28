import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, setToken } from '../lib/api'

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    workspace_name: 'My Workspace',
  })
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const { access_token } = await api('/auth/signup', {
        method: 'POST',
        body: JSON.stringify(form),
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
        <h1 className="text-2xl font-semibold text-slate-900">Create account</h1>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        {['name', 'email', 'password', 'workspace_name'].map((field) => (
          <div key={field} className="mt-4">
            <label className="block text-sm font-medium capitalize text-slate-700">
              {field.replace('_', ' ')}
            </label>
            <input
              type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form[field]}
              onChange={(e) => setForm({ ...form, [field]: e.target.value })}
              required
            />
          </div>
        ))}
        <button
          type="submit"
          className="mt-6 w-full rounded-lg bg-accent py-2.5 text-sm font-medium text-white hover:bg-accent-dark"
        >
          Sign up
        </button>
        <p className="mt-4 text-center text-sm text-slate-500">
          Have an account? <Link to="/login" className="text-accent">Sign in</Link>
        </p>
      </form>
    </div>
  )
}
