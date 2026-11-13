/** Shared number and text formatting. Keep denominators visible in labels. */

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return Math.round(value).toLocaleString('zh-CN')
}

export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return '面议'
  return `¥${formatNumber(value)}`
}

/** Compact money for tight KPI tiles, e.g. ¥10.5K. */
export function formatCompactMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const thousands = value / 1000
  const display = Number.isInteger(thousands)
    ? String(thousands)
    : thousands.toFixed(1)
  return `¥${display}K`
}

/** Percent with one decimal, as required by the project's data notes. */
export function formatPercent(ratio: number, digits = 1): string {
  return `${(ratio * 100).toFixed(digits)}%`
}

/** “8 / 10 · 80.0%” — always shows the denominator. */
export function ratioLabel(count: number, total: number): string {
  if (!total) return `${count} / 0 · —`
  return `${count} / ${total} · ${formatPercent(count / total)}`
}

export function truncate(value: string, max: number): string {
  return value.length > max ? `${value.slice(0, max)}…` : value
}
