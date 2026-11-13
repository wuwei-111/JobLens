import { describe, expect, it } from 'vitest'

import {
  countRawExperience,
  groupExperienceBreakdown,
  isCanonicalExperience,
} from './experience'

describe('groupExperienceBreakdown', () => {
  it('groups raw JD excerpts under 其他 and recomputes ratios', () => {
    const items = [
      { name: '应届生', count: 2, ratio: 0.2 },
      { name: '未披露', count: 6, ratio: 0.6 },
      { name: '其他', count: 1, ratio: 0.1 },
      { name: '1. 本科及以上，3年以上后端经验', count: 1, ratio: 0.1 },
    ]

    const grouped = groupExperienceBreakdown(items, 10)

    expect(grouped).toEqual([
      { name: '应届生', count: 2, ratio: 0.2 },
      { name: '未披露', count: 6, ratio: 0.6 },
      { name: '其他', count: 2, ratio: 0.2 },
    ])
  })

  it('keeps canonical labels and drops empty categories', () => {
    const items = [
      { name: '1-3年', count: 3, ratio: 0.75 },
      { name: '5年以上', count: 1, ratio: 0.25 },
    ]

    expect(groupExperienceBreakdown(items, 4)).toEqual([
      { name: '1-3年', count: 3, ratio: 0.75 },
      { name: '5年以上', count: 1, ratio: 0.25 },
    ])
  })
})

describe('countRawExperience', () => {
  it('counts only non-canonical labels', () => {
    expect(
      countRawExperience([
        { name: '应届生', count: 5, ratio: 0.5 },
        { name: '其他', count: 2, ratio: 0.2 },
        { name: '2. 工作经验：3年以上', count: 3, ratio: 0.3 },
      ]),
    ).toBe(3)
  })

  it('recognises the canonical vocabulary', () => {
    expect(isCanonicalExperience('未披露')).toBe(true)
    expect(isCanonicalExperience('未单独披露工作年限')).toBe(false)
  })
})
