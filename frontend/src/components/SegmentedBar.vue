<script setup lang="ts">
import { computed } from 'vue'

import { educationColors } from '@/lib/charts'
import { formatPercent } from '@/lib/format'
import type { CountItem } from '@/types/api'

const props = defineProps<{
  items: CountItem[]
  total: number
}>()

const segments = computed(() =>
  props.items
    .filter((item) => item.count > 0)
    .map((item) => {
      const colors = educationColors[item.name] ?? {
        fill: '#8a8274',
        ink: '#ffffff',
      }
      return {
        ...item,
        width: props.total ? item.count / props.total : 0,
        fill: colors.fill,
        ink: colors.ink,
      }
    }),
)

const ariaLabel = computed(
  () =>
    `学历构成：${segments.value
      .map((item) => `${item.name} ${formatPercent(item.width)}`)
      .join('，')}`,
)
</script>

<template>
  <div class="segmented-wrap">
    <div class="segmented-bar" role="img" :aria-label="ariaLabel">
      <span
        v-for="segment in segments"
        :key="segment.name"
        class="segment"
        :style="{
          flexGrow: segment.count,
          background: segment.fill,
          color: segment.ink,
        }"
        :title="`${segment.name}：${segment.count} 条 · ${formatPercent(segment.width)}`"
      >
        <span v-if="segment.width >= 0.16" class="segment-label">
          {{ segment.name }}
          <b>{{ formatPercent(segment.width) }}</b>
        </span>
      </span>
    </div>

    <ul class="segment-legend">
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
.segmented-wrap {
  display: grid;
  gap: 1.1rem;
}

.segmented-bar {
  display: flex;
  gap: 2px;
  height: 32px;
  width: 100%;
}

.segment {
  flex-basis: 0;
  min-width: 2px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding: 0 0.55rem;
  overflow: hidden;
  transition: filter 160ms ease;
}

.segment:hover {
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
  margin-left: 0.25rem;
}

.segment-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.4rem 1.5rem;
}

.segment-legend li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.82rem;
  padding: 0.28rem 0;
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
  .segment-legend {
    grid-template-columns: 1fr;
  }

  .segment {
    padding: 0 0.35rem;
  }
}
</style>
