export function formatDate(value?: string | number | null) {
  if (!value) return '未同步'
  const date = typeof value === 'number' && value < 10_000_000_000 ? new Date(value * 1000) : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function compactNumber(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return '--'
  return new Intl.NumberFormat('zh-CN', {
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(value)
}

export function percent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return '--'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

export function assetUrl(path?: string | null) {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  const base = import.meta.env.VITE_API_ORIGIN || 'http://127.0.0.1:8000'
  return `${base}${path}`
}
