import { describe, expect, it } from 'vitest'

import { filtersFromQuery, filtersToQuery, hasFilters } from './filters'

describe('filter URL helpers', () => {
  it('reads only the supported filter keys and takes the first array value', () => {
    expect(
      filtersFromQuery({
        job_type: '后端开发',
        education: ['本科', '硕士'],
        city: null,
        q: 'search',
      }),
    ).toEqual({ job_type: '后端开发', education: '本科' })
  })

  it('serializes only non-empty filters', () => {
    expect(
      filtersToQuery({
        job_type: '后端开发',
        experience: undefined,
        city: '',
      }),
    ).toEqual({ job_type: '后端开发' })
  })

  it('detects active filters', () => {
    expect(hasFilters({})).toBe(false)
    expect(hasFilters({ education: '本科' })).toBe(true)
  })
})
