/**
 * Shared ECharts configuration for the JobLens editorial charts.
 *
 * Charts encode magnitude, so each one uses a single hue on a white plate.
 * Education levels use a validated ordinal rust ramp; the homepage may pass
 * the blue (experience) or green (skills) chapter hue into the ranked-bar
 * helper. Text always uses ink tokens, never the series color.
 *
 * Validated against the white chart plate #ffffff and paper #f7f6f2:
 *   accent #e76f51 — 3.09:1 on white (marks only)
 *   blue #315a7d — 6.72:1; green #4c9a86 — 3.35:1 on white
 *   ordinal #d99a86..#74271c — monotone L, light end 2.18:1 on paper
 */
import type { EChartsOption } from 'echarts'

import type { CountItem, SalaryBin, SalaryGroup } from '@/types/api'
import { formatMoney, formatPercent } from './format'

export const chart = {
  ink: '#20252b',
  inkSoft: '#454b52',
  muted: '#676e79',
  faint: '#8a8f98',
  hairline: '#e5e1d8',
  accent: '#e76f51',
  accentDeep: '#b3442f',
  blue: '#315a7d',
  blueDeep: '#24445f',
  green: '#4c9a86',
  greenDeep: '#2e7565',
  deemphasis: '#cfcac0',
  paper: '#f7f6f2',
  surface: '#ffffff',
  font: "'Avenir Next', 'Segoe UI Variable', 'Segoe UI', 'Source Han Sans SC', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif",
} as const

/** Ordered rust steps for education levels. 不限 is deliberately neutral. */
export const educationColors: Record<string, { fill: string; ink: string }> = {
  不限: { fill: '#c3c0b6', ink: '#20252b' },
  大专: { fill: '#d99a86', ink: '#20252b' },
  本科: { fill: '#b0533a', ink: '#ffffff' },
  本科及以上: { fill: '#a5432e', ink: '#ffffff' },
  硕士: { fill: '#96382a', ink: '#ffffff' },
  硕士及以上: { fill: '#852f22', ink: '#ffffff' },
  博士: { fill: '#74271c', ink: '#ffffff' },
  其他: { fill: '#8a8f98', ink: '#ffffff' },
  未知: { fill: '#d3cec2', ink: '#20252b' },
}

const tooltipBase = {
  backgroundColor: chart.ink,
  borderWidth: 0,
  padding: [8, 10] as [number, number],
  textStyle: { color: chart.paper, fontSize: 12, fontFamily: chart.font },
  extraCssText:
    'border-radius: 3px; box-shadow: 0 8px 24px rgba(32, 37, 43, 0.2);',
}

const axisLabel = {
  color: chart.muted,
  fontSize: 11,
  fontFamily: chart.font,
}

export interface RankedRow {
  name: string
  value: number
  /** Text shown at the bar tip, e.g. “8 / 10 · 80.0%”. */
  display: string
  /** Highlight this row against the de-emphasised rest. */
  emphasis?: boolean
}

interface RankedOptions {
  labelWidth?: number
  /** When true, non-emphasised rows are gray (one story bar, rest context). */
  deEmphasise?: boolean
  /** Chapter hue for the bars. Defaults to the site accent. */
  color?: string
  /** Hover/emphasis step for the chapter hue. */
  emphasisColor?: string
}

/** Horizontal ranked bars with direct labels and no x-axis decoration. */
export function rankedBarOption(
  rows: RankedRow[],
  options: RankedOptions = {},
): EChartsOption {
  const max = Math.max(...rows.map((row) => row.value), 1)
  const barColor = options.color ?? chart.accent
  const emphasisColor = options.emphasisColor ?? chart.accentDeep

  return {
    animationDuration: 480,
    grid: { left: options.labelWidth ?? 96, right: 118, top: 6, bottom: 6 },
    tooltip: {
      trigger: 'item',
      ...tooltipBase,
      formatter: (params: unknown) => {
        const { dataIndex } = params as { dataIndex: number }
        const row = rows[dataIndex]
        return `<div style="font-weight:600;margin-bottom:2px">${row.name}</div><div>${row.display}</div>`
      },
    },
    xAxis: { type: 'value', show: false, max: max * 1.12 },
    yAxis: {
      type: 'category',
      inverse: true,
      data: rows.map((row) => row.name),
      axisLine: { show: false },
      axisTick: { show: false },
      // Long free-text experience values are kept in the data; truncate the
      // axis label and show the full text in the tooltip.
      axisLabel: {
        ...axisLabel,
        width: options.labelWidth ?? 96,
        overflow: 'truncate',
      },
    },
    series: [
      {
        type: 'bar',
        barWidth: 12,
        data: rows.map((row) => ({
          value: row.value,
          itemStyle: {
            color:
              options.deEmphasise && !row.emphasis
                ? chart.deemphasis
                : barColor,
            borderRadius: [0, 4, 4, 0],
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 8,
          color: chart.inkSoft,
          fontSize: 11,
          fontFamily: chart.font,
          formatter: (params: unknown) => {
            const { dataIndex } = params as { dataIndex: number }
            return rows[dataIndex].display
          },
        },
        emphasis: {
          itemStyle: { color: emphasisColor },
        },
      },
    ],
  }
}

/** Fixed-bin salary histogram. Counts are labelled on the caps. */
export function salaryHistogramOption(bins: SalaryBin[]): EChartsOption {
  const total = bins.reduce((sum, bin) => sum + bin.count, 0)

  return {
    animationDuration: 480,
    grid: { left: 44, right: 20, top: 30, bottom: 34 },
    tooltip: {
      trigger: 'item',
      ...tooltipBase,
      formatter: (params: unknown) => {
        const { dataIndex } = params as { dataIndex: number }
        const bin = bins[dataIndex]
        return `<div style="font-weight:600;margin-bottom:2px">${bin.label}</div><div>${bin.count} 条 · ${formatPercent(bin.ratio)}</div><div style="opacity:.72;margin-top:2px">分母：${total} 条有效薪资</div>`
      },
    },
    xAxis: {
      type: 'category',
      data: bins.map((bin) => bin.label),
      axisLine: { lineStyle: { color: chart.hairline } },
      axisTick: { show: false },
      axisLabel,
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: chart.hairline, width: 1 } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel,
    },
    series: [
      {
        type: 'bar',
        barWidth: 26,
        data: bins.map((bin) => bin.count),
        itemStyle: { color: chart.accent, borderRadius: [4, 4, 0, 0] },
        label: {
          show: true,
          position: 'top',
          color: chart.inkSoft,
          fontSize: 11,
          fontFamily: chart.font,
          formatter: (params: unknown) => {
            const value = (params as { value: number }).value
            return value > 0 ? String(value) : ''
          },
        },
      },
    ],
  }
}

/**
 * Salary interval per group: bar = P25–P75 of monthly midpoints, dot = median.
 * A single-record group collapses to a dot, which is honest for this demo sample.
 */
export function salaryRangeOption(groups: SalaryGroup[]): EChartsOption {
  const sorted = [...groups].sort(
    (a, b) => (b.median ?? 0) - (a.median ?? 0),
  )
  const highest = Math.max(...sorted.map((group) => group.p75 ?? 0), 1)
  const max = Math.ceil((highest * 1.18) / 1000) * 1000

  return {
    animationDuration: 480,
    grid: { left: 138, right: 96, top: 42, bottom: 22 },
    media: [
      {
        query: { maxWidth: 520 },
        option: {
          grid: { left: 112, right: 74, top: 38, bottom: 20 },
          legend: {
            itemGap: 10,
            textStyle: { fontSize: 10 },
          },
          xAxis: {
            axisLabel: {
              fontSize: 10,
              hideOverlap: true,
              showMaxLabel: false,
              formatter: (value: number) => `¥${Math.round(value / 1000)}K`,
            },
          },
          yAxis: {
            axisLabel: { fontSize: 10 },
          },
        },
      },
    ],
    legend: {
      top: 0,
      left: 0,
      itemWidth: 12,
      itemHeight: 8,
      itemGap: 18,
      textStyle: { color: chart.muted, fontSize: 11, fontFamily: chart.font },
      data: ['月薪区间（P25–P75）', '中位月薪'],
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...tooltipBase,
      formatter: (params: unknown) => {
        const list = params as { dataIndex: number }[]
        const group = sorted[list[0]?.dataIndex ?? 0]
        if (!group) return ''
        return [
          `<div style="font-weight:600;margin-bottom:3px">${group.group}</div>`,
          `<div>中位月薪 ${formatMoney(group.median)}／月</div>`,
          `<div>四分位区间 ${formatMoney(group.p25)} – ${formatMoney(group.p75)}</div>`,
          `<div>样本 ${group.count} 条 · 平均 ${formatMoney(group.avg)}</div>`,
        ].join('')
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max,
      interval: 10000,
      splitLine: { lineStyle: { color: chart.hairline, width: 1 } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        ...axisLabel,
        hideOverlap: true,
        showMaxLabel: false,
        formatter: (value: number) => `¥${Math.round(value / 1000)}K`,
      },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: sorted.map((group) => group.group),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        ...axisLabel,
        lineHeight: 14,
        formatter: (value: string, index: number) => {
          const group = sorted[index]
          // Two lines keep long job-type names readable without widening the
          // axis label gutter further.
          return `${value}\n{n=${group?.count ?? 0}}`
        },
      },
    },
    series: [
      {
        name: '__base',
        type: 'bar',
        stack: 'salary',
        silent: true,
        barWidth: 14,
        itemStyle: { color: 'transparent' },
        data: sorted.map((group) => group.p25 ?? 0),
      },
      {
        name: '月薪区间（P25–P75）',
        type: 'bar',
        stack: 'salary',
        barWidth: 14,
        itemStyle: { color: chart.accent, borderRadius: 4 },
        data: sorted.map((group) =>
          Math.max((group.p75 ?? 0) - (group.p25 ?? 0), 1),
        ),
        label: {
          show: true,
          position: 'right',
          distance: 12,
          color: chart.inkSoft,
          fontSize: 11,
          fontFamily: chart.font,
          formatter: (params: unknown) => {
            const { dataIndex } = params as { dataIndex: number }
            const group = sorted[dataIndex]
            return `${formatMoney(group.median)}／月`
          },
        },
      },
      {
        name: '中位月薪',
        type: 'scatter',
        symbolSize: 9,
        itemStyle: {
          color: chart.ink,
          borderColor: chart.surface,
          borderWidth: 2,
        },
        data: sorted.map((group, index) => [group.median ?? 0, index]),
        z: 4,
      },
    ],
  }
}

/** Education items in the backend's canonical order, zero counts dropped. */
export function orderedEducation(items: CountItem[]): CountItem[] {
  const order = [
    '不限',
    '大专',
    '本科',
    '本科及以上',
    '硕士',
    '硕士及以上',
    '博士',
    '其他',
    '未知',
  ]
  const position = new Map(order.map((name, index) => [name, index]))
  return [...items]
    .filter((item) => item.count > 0)
    .sort(
      (a, b) =>
        (position.get(a.name) ?? order.length) -
        (position.get(b.name) ?? order.length),
    )
}
