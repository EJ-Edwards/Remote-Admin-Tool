import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function Settings() {
  const [settings, setSettings] = useState({ alert_email: '', sensitive_categories: '' })
  const [saved, setSaved] = useState(false)
  useEffect(() => {
    api('/settings').then(setSettings).catch(console.error)
  }, [])
  const save = async (e) => {
    e.preventDefault()
    await api('/settings', { method: 'PATCH', body: JSON.stringify(settings) })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }
  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-semibold">Settings</h2>
      <form onSubmit={save} className="mt-6 space-y-4 rounded-xl border border-slate-200 bg-white p-6">
        <div>
          <label className="text-sm font-medium text-slate-700">Alert email</label>
          <input
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            value={settings.alert_email || ''}
            onChange={(e) => setSettings({ ...settings, alert_email: e.target.value })}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700">Sensitive categories (comma-separated)</label>
          <input
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            value={settings.sensitive_categories || ''}
            onChange={(e) => setSettings({ ...settings, sensitive_categories: e.target.value })}
          />
        </div>
        <button type="submit" className="rounded-lg bg-accent px-4 py-2 text-sm text-white">
          Save
        </button>
        {saved && <p className="text-sm text-emerald-600">Saved.</p>}
      </form>
    </div>
  )
}
