<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchOverview } from '@/api/stats'
import type { Overview } from '@/types/api'

const overview = ref<Overview | null>(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    overview.value = await fetchOverview()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '未知错误'
  } finally {
    loading.value = false
  }
})

const formatMoney = (value: number | null) =>
  value === null ? '—' : `¥${Math.round(value).toLocaleString('zh-CN')}`

const stats = computed(() => {
  const data = overview.value
  if (!data) return []
  return [
    { label: '有效岗位', value: data.total_jobs.toLocaleString('zh-CN'), hint: '条记录' },
    {
      label: '覆盖企业',
      value: data.total_companies.toLocaleString('zh-CN'),
      hint: '家',
    },
    {
      label: '薪资中位数',
      value: formatMoney(data.salary_median),
      hint: '元/月（区间中点）',
    },
    {
      label: '应届生可投',
      value: `${Math.round(data.fresh_graduate_ratio * 100)}%`,
      hint: `${data.fresh_graduate_count} 条岗位`,
    },
  ]
})
</script>

<template>
  <section class="page-intro">
    <p class="eyebrow">交互式数据新闻</p>
    <h1>学历之外，企业还看重什么？</h1>
    <p class="lead">
      基于某城市计算机类应届毕业生招聘岗位的数据调查。我们收集公开招聘信息，从学历、经验、技能与薪资四个维度观察企业真实的招聘要求。
    </p>
  </section>

  <p v-if="loading" class="status">正在加载数据概览…</p>
  <p v-else-if="error" class="status status-error">
    数据加载失败：{{ error }}。请确认后端已启动，且已导入数据集。
  </p>
  <div v-else class="stats-grid">
    <article v-for="stat in stats" :key="stat.label" class="stat-card">
      <p class="stat-label">{{ stat.label }}</p>
      <p class="stat-value">{{ stat.value }}</p>
      <p class="stat-hint">{{ stat.hint }}</p>
    </article>
  </div>

  <section v-if="overview" class="panel">
    <h2>数据范围</h2>
    <p>
      当前数据集覆盖 {{ overview.total_job_types }} 类岗位、{{ overview.total_cities }}
      个城市、{{ overview.total_skills }} 项技能；其中
      {{ overview.salary_available }} 条岗位包含有效薪资。
      <template v-if="overview.last_collected_at">
        最近采集时间：{{ overview.last_collected_at }}。
      </template>
    </p>
    <p class="muted">
      初始框架已完成数据导入、数据库、查询与统计 API。新闻叙事与图表将在后续迭代接入，详见
      <code>docs/TODO.md</code>。
    </p>
  </section>
</template>
