import { describe, expect, it } from 'vitest'

import {
  formatCompactMoney,
  formatDate,
  formatDateTime,
  formatMoney,
  formatPercent,
  formatSalaryRange,
  ratioLabel,
} from './format'

describe('format helpers', () => {
  it('formats money and negotiable salaries', () => {
    expect(formatMoney(12_500)).toBe('¥12,500')
    expect(formatMoney(null)).toBe('面议')
    expect(formatCompactMoney(10_500)).toBe('¥10.5K')
  })

  it('formats percentages with one decimal and keeps the denominator', () => {
    expect(formatPercent(0.8)).toBe('80.0%')
    expect(ratioLabel(8, 10)).toBe('8 / 10 · 80.0%')
    expect(ratioLabel(0, 0)).toBe('0 / 0 · —')
  })

  it('formats salary ranges', () => {
    expect(formatSalaryRange(10_000, 15_000)).toBe('¥10,000–15,000')
    expect(formatSalaryRange(null, null)).toBe('面议')
    expect(formatSalaryRange(9_000, null)).toBe('¥9,000 起')
    expect(formatSalaryRange(null, 9_000)).toBe('¥9,000 以内')
  })

  it('formats dates and timestamps', () => {
    expect(formatDate('2026-11-13')).toBe('2026-11-13')
    expect(formatDateTime('2026-11-13T05:00:38.366568')).toBe(
      '2026-11-13 05:00',
    )
    expect(formatDate(null)).toBe('—')
  })
})
