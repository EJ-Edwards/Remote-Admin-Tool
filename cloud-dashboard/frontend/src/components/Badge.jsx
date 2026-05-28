const styles = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-amber-100 text-amber-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
  open: 'bg-red-100 text-red-800',
  acknowledged: 'bg-amber-100 text-amber-800',
  resolved: 'bg-emerald-100 text-emerald-800',
  approved: 'bg-emerald-100 text-emerald-800',
  pending: 'bg-amber-100 text-amber-800',
  active: 'bg-emerald-100 text-emerald-800',
  offline: 'bg-slate-200 text-slate-600',
}

export default function Badge({ label, variant = 'low' }) {
  const cls = styles[variant] || styles.low
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {label}
    </span>
  )
}
