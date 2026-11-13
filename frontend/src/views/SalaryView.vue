<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import BaseChart from '@/components/charts/BaseChart.vue'
import ChartCard from '@/components/ChartCard.vue'
import FilterBar from '@/components/FilterBar.vue'
import KpiRow from '@/components/KpiRow.vue'
import SalaryTable from '@/components/SalaryTable.vue'
import { fetchSalaryStats } from '@/api/stats'
import { useAsyncData } from '@/composables/useAsyncData'
import { salaryHistogramOption, salaryRangeOption } from '@/lib/charts'
import {
  formatCompactMoney,
  formatMoney,
  formatPercent,
} from '@/lib/format'
import type { SalaryGroup } from '@/types/api'

const filter = ref('')

const { data, loading, error, load } = useAsyncData(() =>
  fetchSalaryStats({ job_type: filter.value || undefined }),
)

onMounted(load)
watch(filter, load)

const salary = computed(() => data.value)

const educationOrder = ['不限', '大专', '本科', '本科及以上', '硕士', '硕士及以上', '博士', '其他', '未知']
const experienceOrder = ['不限', '应届生', '1年以内', '1-3年', '3-5年', '5年以上', '其他', '未知']

function sortedGroups(groups: SalaryGroup[], order: string[]): SalaryGroup[] {
  const position = new Map(order.map((name, index) => [name, index]))
  return [...groups].sort(
    (a, b) =>
      (position.get(a.group) ?? order.length) -
      (position.get(b.group) ?? order.length),
  )
}

const educationGroups = computed(() =>
  sortedGroups(salary.value?.by_education ?? [], educationOrder),
)

const experienceGroups = computed(() =>
  sortedGroups(salary.value?.by_experience ?? [], experienceOrder),
)

const kpis = computed(() => {
  const stats = salary.value
  if (!stats) return []
  return [
    {
      label: '有效薪资样本',
      value: `${stats.salary_available} / ${stats.total_jobs}`,
      hint: `面议 ${stats.total_jobs - stats.salary_available} 条，不参与统计`,
    },
    {
      label: '中位月薪',
      value: formatMoney(stats.overall.median),
      hint: '月薪区间中点',
    },
    {
      label: '平均月薪',
      value: formatMoney(stats.overall.avg),
      hint: '受高薪岗位影响',
    },
    {
      label: 'P25 – P75',
      value: `${formatCompactMoney(stats.overall.p25)}–${formatCompactMoney(stats.overall.p75).replace('¥', '')}`,
      hint: '月薪中点 · 四分位区间',
    },
  ]
})

const histogramOption = computed(() =>
  salaryHistogramOption(salary.value?.distribution ?? []),
)

const rangeOption = computed(() =>
  salaryRangeOption(salary.value?.by_job_type ?? []),
)

const rangeHeight = computed(() => {
  const rows = salary.value?.by_job_type.length ?? 0
  return `${Math.max(190, rows * 42 + 72)}px`
})

const histogramInsight = computed(() => {
  const stats = salary.value
  if (!stats || stats.overall.count === 0) return '当前筛选条件下没有有效薪资数据。'
  const middle = stats.distribution
    .filter((bin) => ['8-12K', '12-16K'].includes(bin.label))
    .reduce((sum, bin) => sum + bin.count, 0)
  const available = stats.overall.count
  const middleText =
    middle > 0
      ? `${middle} 条的月薪中点落在 8–16K 区间，占 ${formatPercent(middle / available)}`
      : '没有岗位的月薪中点落在 8–16K 区间'
  const missing = stats.total_jobs - stats.salary_available
  const missingText = missing > 0 ? `；另有 ${missing} 条薪资面议，未进入本图。` : '。'
  return `${available} 条有效薪资岗位中，${middleText}。整体中位月薪为 ${formatMoney(stats.overall.median)}${missingText}`
})

const rangeInsight = computed(() => {
  const groups = salary.value?.by_job_type ?? []
  if (groups.length === 0) return '当前筛选条件下没有可比较的岗位类别。'
  const ranked = [...groups].sort((a, b) => (b.median ?? 0) - (a.median ?? 0))
  if (ranked.length === 1) {
    const only = ranked[0]
    return `当前筛选下只有${only.group}一类岗位，中位月薪为 ${formatMoney(only.median)}，有效薪资样本 ${only.count} 条。没有其他类别可供横向比较。`
  }
  const highest = ranked[0]
  const lowest = ranked[ranked.length - 1]
  if (!highest || !lowest) return ''
  const ratio =
    highest.median && lowest.median
      ? (highest.median / lowest.median).toFixed(1)
      : null
  return `${highest.group}的中位月薪最高，为 ${formatMoney(highest.median)}；${lowest.group}最低，为 ${formatMoney(lowest.median)}${ratio ? `，相差约 ${ratio} 倍` : ''}。多数类别只有 1 条有效薪资，区间会退化为一个点，比较时应同时看样本量。`
})

const educationInsight = computed(() => {
  const groups = educationGroups.value
  if (groups.length === 0) return '当前筛选条件下没有有效薪资样本。'
  if (groups.length === 1) {
    const only = groups[0]
    return `当前筛选下只有${only.group}组有有效薪资，中位月薪为 ${formatMoney(only.median)}，样本 ${only.count} 条；缺少可对比的学历组。`
  }
  const bachelor = groups.find((group) => group.group === '本科')
  const master = groups.find((group) => group.group === '硕士')
  if (!bachelor || !master) {
    return `当前筛选下可比较的学历组为${groups.map((group) => group.group).join('、')}，但样本结构不足以做本科与硕士的对照。`
  }
  const gap = (master.median ?? 0) - (bachelor.median ?? 0)
  return `硕士组的中位月薪为 ${formatMoney(master.median)}，本科组为 ${formatMoney(bachelor.median)}，相差 ${formatMoney(gap)}。但硕士组只有 ${master.count} 条样本，且集中在算法方向，学历与方向的影响在这份样本里纠缠在一起。`
})

const experienceInsight = computed(() => {
  const groups = experienceGroups.value
  if (groups.length === 0) return '当前筛选条件下没有有效薪资样本。'
  const fresh = groups.find((group) => group.group === '应届生')
  const others = groups.filter((group) => group.group !== '应届生')
  if (!fresh) {
    return `当前筛选下没有应届生组的有效薪资；可比较的经验组为${groups.map((group) => group.group).join('、')}。`
  }
  const rest = others
    .map((group) => `${group.group} ${formatMoney(group.median)}（${group.count} 条）`)
    .join('、')
  if (others.length === 0) {
    return `应届生组的中位月薪为 ${formatMoney(fresh.median)}，共 ${fresh.count} 条有效薪资；当前筛选下没有非应届岗位可供对比。`
  }
  return `应届生组的中位月薪为 ${formatMoney(fresh.median)}，共 ${fresh.count} 条有效薪资；${rest}。非应届组每条经验档位只有 1 条样本，这里的差异不能解释为“工作年限的回报”。`
})
</script>

<template>
  <div>
    <section class="page-intro">
      <p class="eyebrow">第四部分 / 04 · 薪资待遇</p>
      <h1>价格的分层：<br />方向、学历与经验</h1>
      <p class="lead">
        薪资是招聘启事里最敏感的数字。我们统一取月薪区间中点，把“面议”排除在外，观察不同岗位、学历与经验之间的价格差。
      </p>
      <p class="intro-meta">
        <span>研究问题 04</span>
        <span>口径：月薪区间中点</span>
        <span>面议岗位不参与薪资统计</span>
      </p>
    </section>

    <FilterBar v-model="filter" :total="salary?.total_jobs ?? null" />

    <p v-if="loading && !data" class="status">正在读取薪资数据…</p>
    <p v-else-if="error" class="status status-error">
      数据加载失败：{{ error }}
    </p>

    <template v-else-if="salary">
      <KpiRow :items="kpis" />

      <div class="stack" :class="{ refreshing: loading }">
        <ChartCard
          index="图 01"
          title="月薪中点分布"
          question="样本岗位的薪资，主要集中在哪些区间？"
          note="区间按固定边界划分，单位为元/月；每根柱子的数字为岗位数。面议岗位不纳入。"
        >
          <BaseChart
            :option="histogramOption"
            height="320px"
            aria-label="月薪中点分布直方图"
          />
          <template #table>
            <div class="data-table-wrap">
              <table class="data-table">
                <caption class="sr-only">月薪中点分布</caption>
                <thead>
                  <tr>
                    <th scope="col">月薪区间</th>
                    <th scope="col" class="num">岗位数</th>
                    <th scope="col" class="num">占比</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="bin in salary.distribution"
                    :key="bin.label"
                  >
                    <th scope="row">{{ bin.label }}</th>
                    <td class="num">{{ bin.count }}</td>
                    <td class="num">{{ formatPercent(bin.ratio) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <template #insight>
            <p>{{ histogramInsight }}</p>
          </template>
        </ChartCard>

        <ChartCard
          index="图 02"
          title="不同岗位类别的薪资区间"
          question="技术方向之间的价格差有多大？"
          note="条形为月薪中点的 P25–P75 区间，圆点为中位数；仅 1 条样本时区间退化为一个点。右侧标注中位月薪，n 为有效薪资条数。"
        >
          <BaseChart
            :option="rangeOption"
            :height="rangeHeight"
            aria-label="不同岗位类别的薪资区间图"
          />
          <template #table>
            <div class="data-table-wrap">
              <table class="data-table">
                <caption class="sr-only">不同岗位类别的薪资汇总</caption>
                <thead>
                  <tr>
                    <th scope="col">岗位类别</th>
                    <th scope="col" class="num">样本</th>
                    <th scope="col" class="num">中位</th>
                    <th scope="col" class="num">P25</th>
                    <th scope="col" class="num">P75</th>
                    <th scope="col" class="num">平均</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="group in salary.by_job_type"
                    :key="group.group"
                  >
                    <th scope="row">{{ group.group }}</th>
                    <td class="num">{{ group.count }}</td>
                    <td class="num">{{ formatMoney(group.median) }}</td>
                    <td class="num">{{ formatMoney(group.p25) }}</td>
                    <td class="num">{{ formatMoney(group.p75) }}</td>
                    <td class="num">{{ formatMoney(group.avg) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <template #insight>
            <p>{{ rangeInsight }}</p>
          </template>
        </ChartCard>

        <ChartCard
          index="图 03"
          title="学历与经验：薪资对照"
          question="学历与工作年限，分别对应怎样的价格？"
          note="表中为月薪中点的中位数与四分位区间。样本量写在“样本”列；样本很小时，分位数不稳定，应谨慎解读。"
        >
          <div class="two-col salary-panels">
            <section>
              <h4 class="panel-label">按学历要求</h4>
              <SalaryTable
                :groups="educationGroups"
                caption="按学历要求的薪资汇总"
              />
              <p class="panel-insight">{{ educationInsight }}</p>
            </section>
            <section>
              <h4 class="panel-label">按经验要求</h4>
              <SalaryTable
                :groups="experienceGroups"
                caption="按经验要求的薪资汇总"
              />
              <p class="panel-insight">{{ experienceInsight }}</p>
            </section>
          </div>
        </ChartCard>

        <section class="caliber-note">
          <p class="eyebrow">口径说明</p>
          <h2>为什么用“月薪中点”？</h2>
          <p>
            招聘信息通常给出“10–15K”这样的区间，而不是确定值。我们用 <code>(下限 + 上限) / 2</code> 作为岗位月薪的近似值；只有单边薪资时按已知边界计算，两端都缺失（面议）则排除。13 薪、14 薪与补贴不折算进月薪，以免不同计薪口径混在一起。
          </p>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.salary-panels {
  gap: 3rem;
}

.panel-label {
  font-family: var(--mono);
  font-size: 0.66rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.6rem;
}

.panel-insight {
  margin-top: 0.8rem;
  padding-top: 0.7rem;
  border-top: 1px solid var(--hairline);
  color: var(--ink-soft);
  font-size: 0.86rem;
  line-height: 1.7;
}

.caliber-note {
  display: grid;
  gap: 0.55rem;
  border-top: 1px solid var(--hairline-strong);
  padding-top: 1.4rem;
  max-width: 68ch;
}

.caliber-note h2 {
  font-size: 1.3rem;
}

.caliber-note p:last-child {
  color: var(--ink-soft);
  font-size: 0.92rem;
}
</style>
