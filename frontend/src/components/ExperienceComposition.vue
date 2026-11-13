<script setup lang="ts">
import { computed } from 'vue'

import { formatPercent } from '@/lib/format'
import type { CountItem } from '@/types/api'

const props = withDefaults(
  defineProps<{
    items: CountItem[]
    total: number
    label?: string
  }>(),
  { label: '经验要求构成' },
)

const colors: Record<string, { fill: string; ink: string }> = {
  不限: { fill: '#c3c0b6', ink: '#20252b' },
  应届生: { fill: '#315a7d', ink: '#ffffff' },
  '1年以内': { fill: '#d99a86', ink: '#20252b' },
  '1-3年': { fill: '#b0533a', ink: '#ffffff' },
  '3-5年': { fill: '#96382a', ink: '#ffffff' },
  '5年以上': { fill: '#74271c', ink: '#ffffff' },
  未披露: { fill: '#cfcac0', ink: '#20252b' },
  其他: { fill: '#8a8f98', ink: '#ffffff' },
}

const segments = computed(() =>
  props.items
    .filter((item) => item.count > 0)
    .map((item) => {
      const palette = colors[item.name] ?? { fill: '#8a8f98', ink: '#ffffff' }
      return {
        ...item,
        width: props.total > 0 ? item.count / props.total : 0,
        fill: palette.fill,
        ink: palette.ink,
      }
    }),
)

const ariaLabel = computed(
  () =>
    `${props.label}：${segments.value
      .map((item) => `${item.name} ${item.count} 条 ${formatPercent(item.width)}`)
      .join('，')}`,
)
</script>

<template>
  <div class="experience-composition">
    <div class="experience-strip" role="img" :aria-label="ariaLabel">
      <span
        v-for="segment in segments"
        :key="segment.name"
        class="experience-segment"
        :style="{
          flexGrow: segment.count,
          background: segment.fill,
          color: segment.ink,
        }"
        :title="`${segment.name}：${segment.count} 条 · ${formatPercent(segment.width)}`"
      >
        <span v-if="segment.width >= 0.12" class="segment-label">
          {{ segment.name }}
          <b>{{ formatPercent(segment.width) }}</b>
        </span>
      </span>
    </div>

    <ul class="experience-legend">
      <li v-for="segment in segments" :key="segment.name">
        <span class="swatch" :style="{ background: segment.fill }" />
        <span class="legend-name">{{ segment.name }}</span>
        <span class="legend-value">
          {{ segment.count }} 条
          <b>{{ formatPercent(segment.width) }}</b>
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.experience-composition {
  display: grid;
  gap: 1.15rem;
}

.experience-strip {
  display: flex;
  gap: 2px;
  height: 38px;
  width: 100%;
}

.experience-segment {
  flex-basis: 0;
  min-width: 2px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding: 0 0.6rem;
  overflow: hidden;
  transition: filter 160ms ease;
}

.experience-segment:hover {
  filter: brightness(1.06);
}

.segment-label {
  font-size: 0.72rem;
  white-space: nowrap;
  letter-spacing: 0.01em;
}

.segment-label b {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  margin-left: 0.3rem;
}

.experience-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr));
  gap: 0.45rem 1.5rem;
}

.experience-legend li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.82rem;
  padding: 0.32rem 0;
  border-bottom: 1px solid var(--hairline);
}

.swatch {
  width: 9px;
  height: 9px;
  border-radius: 2px;
  flex: 0 0 auto;
}

.legend-name {
  color: var(--ink);
  white-space: nowrap;
}

.legend-value {
  margin-left: auto;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.legend-value b {
  color: var(--ink);
  font-weight: 600;
  margin-left: 0.35rem;
}

@media (max-width: 560px) {
  .experience-segment {
    padding: 0 0.35rem;
  }

  .experience-legend {
    grid-template-columns: 1fr;
  }
}
</style>
