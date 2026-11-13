<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import BaseChart from '@/components/charts/BaseChart.vue'
import ChartCard from '@/components/ChartCard.vue'
import FilterBar from '@/components/FilterBar.vue'
import JobDrawer from '@/components/JobDrawer.vue'
import KpiRow from '@/components/KpiRow.vue'
import SkillMatrix from '@/components/SkillMatrix.vue'
import { fetchSkillsStats } from '@/api/stats'
import { useAsyncData } from '@/composables/useAsyncData'
import { useDatasetStatus } from '@/composables/useDatasetStatus'
import { useStatsFilters } from '@/composables/useStatsFilters'
import { rankedBarOption } from '@/lib/charts'
import { formatPercent, ratioLabel } from '@/lib/format'

const { filters } = useStatsFilters()
const {
  datasetLabel,
  isDemoDataset,
  load: loadStatus,
} = useDatasetStatus()

const { data, loading, error, load } = useAsyncData(() =>
  fetchSkillsStats(filters.value, { limit: 12, perTypeLimit: 8 }),
)

onMounted(() => {
  void loadStatus()
  void load()
})
watch(filters, load, { deep: true })

const skills = computed(() => data.value)

const drawerOpen = ref(false)
const drawerSkill = ref('')
const drawerTitle = computed(() =>
  drawerSkill.value ? `包含「${drawerSkill.value}」的岗位` : '匹配岗位',
)

function openSkill(skill: string) {
  drawerSkill.value = skill
  drawerOpen.value = true
}

function onSkillClick(params: { name?: string }) {
  if (params.name) openSkill(params.name)
}

function clearFilters() {
  filters.value = {}
}

const kpis = computed(() => {
  const stats = skills.value
  if (!stats) return []
  const top = stats.items[0]
  return [
    {
      label: '技能标签',
      value: String(stats.total_skills),
      hint: '规范化后的去重技能词',
    },
    {
      label: '最高频技能',
      value: top?.skill ?? '—',
      hint: top ? ratioLabel(top.count, stats.total_jobs) : '暂无数据',
    },
    {
      label: '覆盖岗位',
      value: String(stats.total_jobs),
      hint: '当前筛选后的样本',
    },
    {
      label: '技能类别',
      value: String(stats.categories.length),
      hint: '按后端词表归类',
    },
  ]
})

const topRows = computed(() => {
  const stats = skills.value
  if (!stats) return []
  return stats.items.map((item) => ({
    name: item.skill,
    value: item.count,
    display: ratioLabel(item.count, stats.total_jobs),
  }))
})

const topOption = computed(() =>
  rankedBarOption(topRows.value, { labelWidth: 118 }),
)

const categoryRows = computed(() => {
  const stats = skills.value
  if (!stats) return []
  return stats.categories.map((item) => ({
    name: item.category,
    value: item.count,
    display: ratioLabel(item.count, stats.total_jobs),
  }))
})

const categoryOption = computed(() =>
  rankedBarOption(categoryRows.value, { labelWidth: 112 }),
)

const topHeight = computed(
  () => `${Math.max(180, topRows.value.length * 32 + 24)}px`,
)

const categoryHeight = computed(
  () => `${Math.max(170, categoryRows.value.length * 32 + 24)}px`,
)

const topInsight = computed(() => {
  const stats = skills.value
  if (!stats || stats.items.length === 0) return '当前筛选条件下没有技能数据。'
  if (stats.total_jobs <= 1) {
    return `当前筛选下只有 ${stats.total_jobs} 条岗位，排行榜更接近该岗位的技能清单，而不是频率比较。`
  }
  const [first, second, third] = stats.items
  const ties = stats.items.filter((item) => item.count === first.count)
  const tieText =
    ties.length > 1
      ? `${ties.map((item) => item.skill).join('、')}并列出现于 ${first.count} 条岗位`
      : `${first.skill}出现在 ${first.count} 条岗位`
  const nextText =
    second && third && second.count < first.count
      ? `；紧随其后的是 ${second.skill}（${second.count} 条）与 ${third.skill}（${third.count} 条）`
      : ''
  const tailText = isDemoDataset.value
    ? '头部技能集中，长尾技能则大多只出现 1–2 次，说明不同技术方向的分工已经写进招聘要求。'
    : '头部技能集中，长尾技能出现次数较少；不同技术方向的分工已经写进招聘要求。'
  return `${tieText}，覆盖率为 ${formatPercent(first.ratio)}${nextText}。${tailText}`
})

const categoryInsight = computed(() => {
  const stats = skills.value
  if (!stats || stats.categories.length === 0) return '当前筛选条件下没有类别数据。'
  const top = stats.categories.filter(
    (item) => item.count === stats.categories[0].count,
  )
  const names = top.map((item) => `${item.category}（${item.count} 条）`).join('、')
  return `${names}覆盖的岗位最多。一条岗位可能同时列出多个类别的技能，因此各类别覆盖数存在重叠，不能相加，也不构成 100% 的构成比。`
})

const matrixInsight = computed(() => {
  const stats = skills.value
  if (!stats || stats.by_job_type.length === 0) return ''
  const shared = stats.by_job_type
    .filter((group) => group.total_jobs >= 2)
    .map((group) => {
      const common = group.skills
        .filter((skill) => skill.count === group.total_jobs)
        .map((skill) => skill.skill)
      return common.length
        ? `${group.job_type}的 ${group.total_jobs} 条岗位都提到${common.join('、')}`
        : ''
    })
    .filter(Boolean)
  if (!shared.length) {
    return isDemoDataset.value
      ? '矩阵展示各岗位类别的高频技能。样本量很小时，单元格更多是方向差异的示意，而不是稳定的行业结论。'
      : '矩阵展示各岗位类别的高频技能。单元格数字应结合样本量阅读，不能当作行业普遍规律。'
  }
  return `${shared.slice(0, 2).join('；')}。矩阵用于观察方向差异，不能把单元格数字当作行业普遍规律。`
})
</script>

<template>
  <div>
    <section class="page-intro">
      <p class="eyebrow">第三部分 / 03 · 技能需求</p>
      <h1>技术栈的信号：<br />企业反复提到哪些词？</h1>
      <p class="lead">
        职位描述里的技能标签，是招聘方对“能上手做什么”的最小共识。我们统计包含某项技能的岗位数，而不是关键词出现的次数。
      </p>
      <p class="intro-meta">
        <span>研究问题 03</span>
        <span>分母：当前筛选后的岗位数</span>
        <span>{{ datasetLabel }}</span>
      </p>
    </section>

    <FilterBar v-model="filters" :total="skills?.total_jobs ?? null" />

    <p v-if="loading && !data" class="status">正在读取技能数据…</p>
    <p v-else-if="error" class="status status-error">
      数据加载失败：{{ error }}
    </p>

    <template v-else-if="skills">
      <template v-if="skills.total_jobs > 0">
      <KpiRow :items="kpis" />

      <div class="stack" :class="{ refreshing: loading }">
        <ChartCard
          index="图 01"
          title="高频技能排行"
          question="哪些技术词出现在最多的岗位里？"
          note="技能频率 = 包含该技能的岗位数 / 当前筛选岗位数，同一岗位内重复技能已去重。点击条形或数据表中的技能名可查看岗位。"
        >
          <BaseChart
            class="clickable-chart"
            :option="topOption"
            :height="topHeight"
            aria-label="高频技能排行条形图，点击条形可查看包含该技能的岗位"
            @chart-click="onSkillClick"
          />
          <template #table>
            <div class="data-table-wrap">
              <table class="data-table">
                <caption class="sr-only">高频技能排行</caption>
                <thead>
                  <tr>
                    <th scope="col">排名</th>
                    <th scope="col">技能</th>
                    <th scope="col">类别</th>
                    <th scope="col" class="num">岗位数</th>
                    <th scope="col" class="num">覆盖率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(item, index) in skills.items"
                    :key="item.skill"
                  >
                    <td class="num">{{ index + 1 }}</td>
                    <th scope="row">
                      <button
                        type="button"
                        class="skill-link"
                        @click="openSkill(item.skill)"
                      >
                        {{ item.skill }}
                      </button>
                    </th>
                    <td>{{ item.category }}</td>
                    <td class="num">{{ item.count }}</td>
                    <td class="num">{{ formatPercent(item.ratio) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <template #insight>
            <p>{{ topInsight }}</p>
          </template>
        </ChartCard>

        <ChartCard
          index="图 02"
          title="技能类别覆盖"
          question="语言、框架、数据库与工具，哪一类最普遍？"
          note="类别覆盖 = 至少包含一项该类别技能的岗位数 / 当前筛选岗位数；类别之间可重叠，不可相加。"
        >
          <BaseChart
            :option="categoryOption"
            :height="categoryHeight"
            aria-label="技能类别覆盖条形图"
          />
          <template #table>
            <div class="data-table-wrap">
              <table class="data-table">
                <caption class="sr-only">技能类别覆盖</caption>
                <thead>
                  <tr>
                    <th scope="col">技能类别</th>
                    <th scope="col" class="num">覆盖岗位</th>
                    <th scope="col" class="num">覆盖率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in skills.categories"
                    :key="item.category"
                  >
                    <th scope="row">{{ item.category }}</th>
                    <td class="num">{{ item.count }}</td>
                    <td class="num">{{ formatPercent(item.ratio) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <template #insight>
            <p>{{ categoryInsight }}</p>
          </template>
        </ChartCard>

        <ChartCard
          index="图 03"
          title="岗位类别 × 高频技能"
          question="不同技术方向，工具链有什么不同？"
          note="行为岗位类别，列为样本中覆盖率最高的技能；单元格为包含该技能的岗位数。空白表示 0。"
        >
          <SkillMatrix
            v-if="skills.by_job_type.length"
            :groups="skills.by_job_type"
            :limit="8"
          />
          <p v-else class="status">当前筛选下没有可展示的岗位类别。</p>
          <template #insight>
            <p>{{ matrixInsight }}</p>
          </template>
        </ChartCard>

        <section class="method-note">
          <p class="eyebrow">口径提示</p>
          <h2>别把“技能标签数”当成“岗位数”</h2>
          <p>
            同一岗位列出 Java、MySQL、Redis 三项数据库相关技能时，在“数据库”类别下仍然只计 1 条岗位。技能排行与类别覆盖的分母始终是岗位数；类别之间可以重叠，因此覆盖率之和会超过 100%。
          </p>
        </section>
      </div>
      </template>

      <section v-else class="empty-state">
        <p class="eyebrow">筛选结果为空</p>
        <h2>当前条件下没有技能数据</h2>
        <p>试试减少筛选条件，或清除筛选查看全部样本。</p>
        <button type="button" class="empty-clear" @click="clearFilters">
          清除筛选
        </button>
      </section>

      <JobDrawer
        v-model:open="drawerOpen"
        :title="drawerTitle"
        :query="{ ...filters, skill: drawerSkill }"
      />
    </template>
  </div>
</template>

<style scoped>
.method-note {
  display: grid;
  gap: 0.55rem;
  border-top: 1px solid var(--hairline-strong);
  padding-top: 1.4rem;
  max-width: 66ch;
}

.method-note h2 {
  font-size: 1.3rem;
}

.method-note p:last-child {
  color: var(--ink-soft);
  font-size: 0.92rem;
}

.clickable-chart {
  cursor: pointer;
}

.skill-link {
  border: 0;
  background: none;
  padding: 0;
  font: inherit;
  color: var(--accent-ink);
  cursor: pointer;
  border-bottom: 1px solid rgba(231, 111, 81, 0.4);
}

.skill-link:hover {
  color: var(--accent-deep);
}
</style>
