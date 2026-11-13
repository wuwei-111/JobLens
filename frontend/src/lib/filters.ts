import type { LocationQuery, LocationQueryRaw } from 'vue-router'

import type { StatsFilters } from '@/types/api'

export const FILTER_KEYS = [
  'job_type',
  'education',
  'experience',
  'city',
] as const

export type FilterKey = (typeof FILTER_KEYS)[number]

function firstQueryValue(value: LocationQuery[string]): string | null {
  if (Array.isArray(value)) return value[0] ?? null
  return typeof value === 'string' ? value : null
}

export function filtersFromQuery(query: LocationQuery): StatsFilters {
  const entries: [FilterKey, string][] = []
  for (const key of FILTER_KEYS) {
    const value = firstQueryValue(query[key])
    if (value && value.trim()) entries.push([key, value])
  }
  return Object.fromEntries(entries) as StatsFilters
}

export function filtersToQuery(filters: StatsFilters): LocationQueryRaw {
  const query: Record<string, string> = {}
  for (const key of FILTER_KEYS) {
    const value = filters[key]
    if (value) query[key] = value
  }
  return query
}

export function hasFilters(filters: StatsFilters): boolean {
  return FILTER_KEYS.some((key) => Boolean(filters[key]))
}
