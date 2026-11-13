<script setup lang="ts">
import { computed } from 'vue'

import { formatMoney } from '@/lib/format'
import type { SalaryGroup } from '@/types/api'

const props = defineProps<{
  groups: SalaryGroup[]
  caption: string
}>()

const domainMax = computed(() => {
  const highest = Math.max(...props.groups.map((group) => group.p75 ?? 0), 1)
  return Math.ceil((highest * 1.08) / 1000) * 1000
})

function percent(value: number | null): string {
  if (!value) return '0%'
  return `${Math.min(100, (value / domainMax.value) * 100).toFixed(2)}%`
}

function rangeWidth(group: SalaryGroup): string {
  const p25 = group.p25 ?? 0
  const p75 = group.p75 ?? 0
  return `${Math.max(0.8, ((p75 - p25) / domainMax.value) * 100).toFixed(2)}%`
}
</script>

<template>
  <div class="data-table-wrap">
    <table class="data-table salary-table">
      <caption class="sr-only">{{ caption }}</caption>
      <thead>
        <tr>
          <th scope="col">分组</th>
          <th scope="col" class="num">样本</th>
          <th scope="col" class="num">中位月薪</th>
          <th scope="col">四分位区间（月薪中点）</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="group in groups" :key="group.group">
          <th scope="row" class="row-head">{{ group.group }}</th>
          <td class="num">{{ group.count }}</td>
          <td class="num median">{{ formatMoney(group.median) }}</td>
          <td>
            <div class="rail-wrap">
              <div class="rail" aria-hidden="true">
                <span class="rail-track" />
                <span
                  class="rail-range"
                  :style="{
                    left: percent(group.p25),
                    width: rangeWidth(group),
                  }"
                />
                <span
                  class="rail-dot"
                  :style="{ left: percent(group.median) }"
                />
              </div>
              <span class="rail-caption">
                {{ formatMoney(group.p25) }} – {{ formatMoney(group.p75) }}
              </span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.salary-table .row-head {
  text-align: left;
  font-family: var(--sans);
  font-size: 0.84rem;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
  color: var(--ink);
  white-space: nowrap;
}

.median {
  font-weight: 600;
}

.rail-wrap {
  display: grid;
  gap: 0.3rem;
  min-width: 10rem;
}

.rail {
  position: relative;
  height: 8px;
  width: 100%;
}

.rail-track {
  position: absolute;
  inset: 3px 0;
  background: var(--hairline);
}

.rail-range {
  position: absolute;
  top: 2px;
  height: 4px;
  background: var(--accent);
  border-radius: 2px;
}

.rail-dot {
  position: absolute;
  top: 0;
  width: 8px;
  height: 8px;
  margin-left: -4px;
  border-radius: 50%;
  background: var(--ink);
  box-shadow: 0 0 0 2px var(--paper);
}

.rail-caption {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.02em;
  color: var(--faint);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 640px) {
  .rail {
    display: none;
  }

  .rail-wrap {
    min-width: 0;
    gap: 0;
  }
}
</style>
