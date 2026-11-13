<script setup lang="ts">
import { computed } from 'vue'

import type { JobTypeSkillGroup } from '@/types/api'

const props = withDefaults(
  defineProps<{
    groups: JobTypeSkillGroup[]
    limit?: number
  }>(),
  { limit: 8 },
)

const skills = computed(() => {
  const totals = new Map<string, number>()
  for (const group of props.groups) {
    for (const skill of group.skills) {
      totals.set(skill.skill, (totals.get(skill.skill) ?? 0) + skill.count)
    }
  }
  return [...totals.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh-CN'))
    .slice(0, props.limit)
    .map(([skill]) => skill)
})

const rows = computed(() =>
  [...props.groups].sort((a, b) => b.total_jobs - a.total_jobs),
)

const maxCount = computed(() => {
  let max = 1
  for (const group of rows.value) {
    for (const skill of group.skills) {
      if (skill.count > max) max = skill.count
    }
  }
  return max
})

function countFor(group: JobTypeSkillGroup, skill: string): number {
  return group.skills.find((item) => item.skill === skill)?.count ?? 0
}

function tint(count: number): Record<string, string> | undefined {
  if (!count) return undefined
  const alpha = 0.08 + 0.4 * (count / maxCount.value)
  return { backgroundColor: `rgba(231, 111, 81, ${alpha.toFixed(3)})` }
}
</script>

<template>
  <div class="skill-matrix">
    <div class="data-table-wrap">
      <table class="data-table matrix-table">
        <caption class="sr-only">
          各岗位类别的 Top 技能覆盖矩阵
        </caption>
        <thead>
          <tr>
            <th scope="col">岗位类别</th>
            <th v-for="skill in skills" :key="skill" scope="col">
              {{ skill }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="group in rows" :key="group.job_type">
            <th scope="row" class="row-head">
              {{ group.job_type }}
              <span class="row-n">n={{ group.total_jobs }}</span>
            </th>
            <td
              v-for="skill in skills"
              :key="skill"
              class="num matrix-cell"
              :style="tint(countFor(group, skill))"
              :title="`${group.job_type} · ${skill}：${countFor(group, skill)} / ${group.total_jobs} 条岗位`"
            >
              <span :class="{ 'cell-empty': !countFor(group, skill) }">
                {{ countFor(group, skill) || '·' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="matrix-legend">
      <span class="legend-label">技能覆盖岗位数</span>
      <span class="legend-scale" aria-hidden="true">
        <i v-for="step in 4" :key="step" :style="{ opacity: 0.18 + step * 0.2 }" />
      </span>
      <span class="legend-hint">色深表示包含该技能的岗位数，空白表示 0</span>
    </div>
  </div>
</template>

<style scoped>
.skill-matrix {
  display: grid;
  gap: 0.9rem;
}

.matrix-table th,
.matrix-table td {
  text-align: center;
}

.skill-matrix thead th {
  text-transform: none;
  letter-spacing: 0.02em;
  font-size: 0.68rem;
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
  min-width: 2.9rem;
  transition: background 160ms ease;
}

.matrix-legend {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  flex-wrap: wrap;
  font-size: 0.7rem;
  color: var(--faint);
}

.legend-label {
  font-family: var(--mono);
  letter-spacing: 0.06em;
}

.legend-scale {
  display: inline-flex;
  gap: 2px;
}

.legend-scale i {
  width: 18px;
  height: 8px;
  background: var(--accent);
  border-radius: 1px;
}
</style>
