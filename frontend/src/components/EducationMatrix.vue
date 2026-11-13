<script setup lang="ts">
import { computed } from 'vue'

import type { GroupedCounts } from '@/types/api'

const props = defineProps<{
  groups: GroupedCounts[]
  columns: string[]
}>()

const orderedColumns = computed(() =>
  props.columns.filter((column) =>
    props.groups.some((group) =>
      group.distribution.some((item) => item.name === column && item.count > 0),
    ),
  ),
)

const maxCount = computed(() => {
  let max = 1
  for (const group of props.groups) {
    for (const item of group.distribution) {
      if (item.count > max) max = item.count
    }
  }
  return max
})

const columnTotals = computed(() => {
  const totals: Record<string, number> = {}
  for (const group of props.groups) {
    for (const item of group.distribution) {
      totals[item.name] = (totals[item.name] ?? 0) + item.count
    }
  }
  return totals
})

const grandTotal = computed(() =>
  props.groups.reduce((sum, group) => sum + group.total, 0),
)

function countFor(group: GroupedCounts, column: string): number {
  return group.distribution.find((item) => item.name === column)?.count ?? 0
}

function tint(count: number): Record<string, string> | undefined {
  if (!count) return undefined
  const alpha = 0.06 + 0.34 * (count / maxCount.value)
  return { backgroundColor: `rgba(231, 111, 81, ${alpha.toFixed(3)})` }
}
</script>

<template>
  <div class="data-table-wrap">
    <table class="data-table matrix-table">
      <caption class="sr-only">
        各岗位类别的学历要求分布
      </caption>
      <thead>
        <tr>
          <th scope="col">岗位类别</th>
          <th v-for="column in orderedColumns" :key="column" scope="col">
            {{ column }}
          </th>
          <th scope="col" class="num">合计</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="group in groups" :key="group.group">
          <th scope="row" class="row-head">
            {{ group.group }}
            <span class="row-n">n={{ group.total }}</span>
          </th>
          <td
            v-for="column in orderedColumns"
            :key="column"
            class="num matrix-cell"
            :style="tint(countFor(group, column))"
            :title="`${group.group} · ${column}：${countFor(group, column)} / ${group.total} 条`"
          >
            <span :class="{ 'cell-empty': !countFor(group, column) }">
              {{ countFor(group, column) || '·' }}
            </span>
          </td>
          <td class="num">{{ group.total }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr class="row-total">
          <th scope="row">合计</th>
          <td v-for="column in orderedColumns" :key="column" class="num">
            {{ columnTotals[column] ?? 0 }}
          </td>
          <td class="num">{{ grandTotal }}</td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<style scoped>
.matrix-table th,
.matrix-table td {
  text-align: center;
}

.matrix-table .row-head {
  text-align: left;
  font-family: var(--sans);
  font-size: 0.84rem;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
  color: var(--ink);
  white-space: nowrap;
}

.row-n {
  font-family: var(--mono);
  font-size: 0.62rem;
  color: var(--faint);
  margin-left: 0.35rem;
}

.matrix-cell {
  transition: background 160ms ease;
  min-width: 3.2rem;
}

.matrix-table tfoot .row-total th {
  font-family: var(--sans);
  font-size: 0.8rem;
  text-transform: none;
  letter-spacing: 0;
  color: var(--ink);
}
</style>
