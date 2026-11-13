<script setup lang="ts">
import { BarChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

echarts.use([
  BarChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
])

const props = withDefaults(
  defineProps<{
    option: EChartsOption
    height?: string
    ariaLabel?: string
  }>(),
  { height: '360px', ariaLabel: '数据图表' },
)

const emit = defineEmits<{
  'chart-click': [
    params: { name?: string; seriesName?: string; dataIndex?: number },
  ]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ReturnType<typeof echarts.init> | null = null
let resizeObserver: ResizeObserver | null = null

function render() {
  chart?.setOption(props.option, true)
}

onMounted(() => {
  if (!chartRef.value) return
  const instance = echarts.init(chartRef.value)
  chart = instance
  instance.on('click', (params) => {
    const event = params as {
      name?: string
      seriesName?: string
      dataIndex?: number
    }
    emit('chart-click', event)
  })
  render()
  resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(chartRef.value)
})

watch(() => props.option, render, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div
    ref="chartRef"
    class="base-chart"
    :style="{ height }"
    role="img"
    :aria-label="ariaLabel"
  />
</template>

<style scoped>
.base-chart {
  width: 100%;
}
</style>
