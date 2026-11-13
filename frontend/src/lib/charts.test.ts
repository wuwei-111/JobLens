import { describe, expect, it } from 'vitest'

import {
  chart,
  orderedEducation,
  rankedBarOption,
  salaryHistogramOption,
  salaryRangeOption,
} from './charts'

describe('chart options', () => {
  it('orders education levels by the canonical vocabulary', () => {
    const ordered = orderedEducation([
      { name: '硕士', count: 1, ratio: 0.1 },
      { name: '不限', count: 1, ratio: 0.1 },
      { name: '本科', count: 2, ratio: 0.2 },
    ])
    expect(ordered.map((item) => item.name)).toEqual(['不限', '本科', '硕士'])
  })

  it('builds a ranked bar option with the chapter color and direct labels', () => {
    const option = rankedBarOption(
      [{ name: 'Git', value: 8, display: '8 / 10 · 80.0%' }],
      { color: chart.green, emphasisColor: chart.greenDeep },
    ) as any

    expect(option.yAxis.data).toEqual(['Git'])
    expect(option.series[0].data[0].value).toBe(8)
    expect(option.series[0].data[0].itemStyle.color).toBe(chart.green)
    expect(option.series[0].label.formatter({ dataIndex: 0 })).toBe(
      '8 / 10 · 80.0%',
    )
    expect(option.tooltip.formatter({ dataIndex: 0 })).toContain('Git')
  })

  it('builds a histogram with fixed bins and counts', () => {
    const option = salaryHistogramOption([
      { label: '8K以下', range_min: null, range_max: 8000, count: 0, ratio: 0 },
      { label: '8-12K', range_min: 8000, range_max: 12000, count: 3, ratio: 0.3 },
      { label: '12-16K', range_min: 12000, range_max: 16000, count: 2, ratio: 0.2 },
      { label: '16-20K', range_min: 16000, range_max: 20000, count: 1, ratio: 0.1 },
      { label: '20-30K', range_min: 20000, range_max: 30000, count: 2, ratio: 0.2 },
      { label: '30K以上', range_min: 30000, range_max: null, count: 0, ratio: 0 },
    ]) as any

    expect(option.xAxis.data[1]).toBe('8-12K')
    expect(option.series[0].data).toEqual([0, 3, 2, 1, 2, 0])
    expect(option.series[0].label.formatter({ value: 3 })).toBe('3')
    expect(option.series[0].label.formatter({ value: 0 })).toBe('')
  })

  it('builds a salary range option with a median dot', () => {
    const option = salaryRangeOption([
      {
        group: '算法工程',
        count: 2,
        avg: 25_750,
        median: 25_750,
        p25: 24_375,
        p75: 27_125,
        min: 23_000,
        max: 28_500,
      },
    ]) as any

    expect(option.legend.data).toEqual(['月薪区间（P25–P75）', '中位月薪'])
    expect(option.series[1].data[0]).toBe(2_750)
    expect(option.series[2].data[0]).toEqual([25_750, 0])
  })
})
