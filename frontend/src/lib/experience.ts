import type { CountItem } from '@/types/api'

/**
 * Canonical experience labels used by the API. Anything else is a raw JD
 * excerpt kept in the database (e.g. "1. 本科及以上…3年以上后端开发经验").
 *
 * Charts and narrative copy group those excerpts under "其他" so a handful of
 * long sentences do not turn the experience chart into a 20-row list. The raw
 * values stay available in the job detail, the filter and the quality summary.
 */
export const EXPERIENCE_ORDER = [
  '不限',
  '应届生',
  '1年以内',
  '1-3年',
  '3-5年',
  '5年以上',
  '未披露',
  '其他',
] as const

const CANONICAL_EXPERIENCE = new Set<string>(EXPERIENCE_ORDER)

export function isCanonicalExperience(name: string): boolean {
  return CANONICAL_EXPERIENCE.has(name)
}

export function groupExperienceBreakdown(
  items: CountItem[],
  total: number,
): CountItem[] {
  const counts = new Map<string, number>()
  for (const item of items) {
    const key = isCanonicalExperience(item.name) ? item.name : '其他'
    counts.set(key, (counts.get(key) ?? 0) + item.count)
  }

  return EXPERIENCE_ORDER.filter((name) => (counts.get(name) ?? 0) > 0).map(
    (name) => {
      const count = counts.get(name) ?? 0
      return {
        name,
        count,
        ratio: total > 0 ? count / total : 0,
      }
    },
  )
}

/** Number of records whose experience label is a raw JD excerpt. */
export function countRawExperience(items: CountItem[]): number {
  return items
    .filter((item) => !isCanonicalExperience(item.name))
    .reduce((sum, item) => sum + item.count, 0)
}
