<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'

import ChartCard from '@/components/ChartCard.vue'
import EducationMatrix from '@/components/EducationMatrix.vue'
import ExperienceComposition from '@/components/ExperienceComposition.vue'
import FilterBar from '@/components/FilterBar.vue'
import SegmentedBar from '@/components/SegmentedBar.vue'
import { fetchEducationStats, fetchExperienceStats } from '@/api/stats'
import { useAsyncData } from '@/composables/useAsyncData'
import { useDatasetStatus } from '@/composables/useDatasetStatus'
import { useStatsFilters } from '@/composables/useStatsFilters'
import { orderedEducation } from '@/lib/charts'
import {
  countRawExperience,
  groupExperienceBreakdown,
} from '@/lib/experience'
import { formatPercent } from '@/lib/format'

const { filters } = useStatsFilters()
const {
  datasetLabel,
  isDemoDataset,
  load: loadStatus,
} = useDatasetStatus()

const { data, loading, error, load } = useAsyncData(async () => {
  const [education, experience] = await Promise.all([
    fetchEducationStats(filters.value),
    fetchExperienceStats(filters.value),
  ])
  return { education, experience }
})

onMounted(() => {
  void loadStatus()
  void load()
})
watch(filters, load, { deep: true })

const education = computed(() => data.value?.education ?? null)
const experience = computed(() => data.value?.experience ?? null)

const educationItems = computed(() =>
  orderedEducation(education.value?.breakdown ?? []),
)

const educationColumns = computed(() =>
  educationItems.value.map((item) => item.name),
)

// Raw JD excerpts are grouped under "其他" for display only. The API keeps the
// original values so filters and job details still show the source text.
const experienceItems = computed(() =>
  groupExperienceBreakdown(
    experience.value?.breakdown ?? [],
    experience.value?.total ?? 0,
  ),
)

const rawExperienceCount = computed(() =>
  countRawExperience(experience.value?.breakdown ?? []),
)

const experienceNote = computed(() =>
  rawExperienceCount.value
    ? `“其他”包含 ${rawExperienceCount.value} 条未能归一的原文摘句，原文仍保留在岗位详情与质量摘要中；分母为当前筛选后的岗位数。`
    : '高亮“应届生”；分母为当前筛选后的岗位数。',
)

const educationInsight = computed(() => {
  const stats = education.value
  if (!stats || stats.total === 0) return '当前筛选条件下没有岗位。'
  const items = stats.breakdown
    .map((item) => `${item.name} ${item.count} 条（${formatPercent(item.ratio)}）`)
    .join('，')

  const core = stats.breakdown.filter(
    (item) =>
      (item.name === '本科' || item.name === '硕士') && item.count > 0,
  )
  const coreCount = core.reduce((sum, item) => sum + item.count, 0)
  const coreText =
    core.length > 1
      ? `本科与硕士要求合计 ${coreCount} 条，占 ${formatPercent(coreCount / stats.total)}，学历门槛主要集中在这两档。`
      : ''

  return `在 ${stats.total} 条岗位中，${items}。${coreText}`
})

const matchInsight = computed(() => {
  const stats = education.value
  if (!stats || stats.by_job_type.length === 0) return ''

  const allMaster = stats.by_job_type
    .filter((group) => {
      const items = group.distribution.filter((item) => item.count > 0)
      return items.length > 0 && items.every((item) => item.name === '硕士')
    })
    .map((group) => group.group)

  const masterGroups = stats.by_job_type
    .filter((group) =>
      group.distribution.some((item) => item.name === '硕士' && item.count > 0),
    )
    .map((group) => group.group)

  const diversity = stats.by_job_type
    .filter((group) => group.distribution.filter((item) => item.count > 0).length > 1)
    .map((group) => group.group)

  const masterText = allMaster.length
    ? `${allMaster.join('、')}的岗位全部要求硕士`
    : masterGroups.length
      ? `硕士要求出现在${masterGroups.join('、')}`
      : '没有岗位要求硕士'

  const diversityText = diversity.length
    ? `；${diversity.slice(0, 3).join('、')}等方向则出现了不止一种学历要求`
    : ''
  const caveat = isDemoDataset.value
    ? '每个岗位类别只有 1–2 条样本，横向差异只能作为线索，不足以代表整个方向。'
    : '不同岗位类别的样本量不同，横向差异只能作为线索，不足以代表整个方向。'

  return `${masterText}${diversityText}。${caveat}`
})

// Only these labels state an actual number of years. "未披露" and "其他" must
// not be read as "要求工作年限", otherwise the narrative would overclaim.
const EXPLICIT_EXPERIENCE_YEARS = new Set(['1年以内', '1-3年', '3-5年', '5年以上'])

const experienceInsight = computed(() => {
  const stats = experience.value
  if (!stats || stats.total === 0) return '当前筛选条件下没有岗位。'

  const items = experienceItems.value.filter((item) => item.count > 0)
  const breakdownText = items
    .map((item) => `${item.name} ${item.count} 条（${formatPercent(item.ratio)}）`)
    .join('，')
  const yearItems = items.filter((item) => EXPLICIT_EXPERIENCE_YEARS.has(item.name))
  const yearCount = yearItems.reduce((sum, item) => sum + item.count, 0)
  const undisclosed = items.find((item) => item.name === '未披露')?.count ?? 0

  if (!yearCount) {
    return `在 ${stats.total} 条岗位中，经验标注为：${breakdownText}。没有岗位明确写出 1 年以上的工作年限要求；其中 ${undisclosed} 条标注“未披露”，只说明招聘页没有单独写出年限，不等于“经验不限”。`
  }

  const yearsText = yearItems
    .map((item) => `${item.name} ${item.count} 条`)
    .join('、')
  return `在 ${stats.total} 条岗位中，经验标注为：${breakdownText}。其中明确写出工作年限要求的有 ${yearCount} 条（${yearsText}）；其余岗位未写明年限。`
})

const freshText = computed(() => {
  const stats = experience.value
  if (!stats) return ''
  const fresh = stats.fresh_graduate
  if (!fresh.count) return '当前筛选条件下没有标注“接受应届生”的岗位。'

  const freshBreakdown = groupExperienceBreakdown(fresh.breakdown, fresh.count)
  const explicit =
    freshBreakdown.find((item) => item.name === '应届生')?.count ?? 0
  const undisclosed =
    freshBreakdown.find((item) => item.name === '未披露')?.count ?? 0
  const other = freshBreakdown.find((item) => item.name === '其他')?.count ?? 0
  const scope = isDemoDataset.value ? '在这份演示样本里' : '在这份样本里'

  if (!undisclosed && !other) {
    return `${fresh.count} 条标注“接受应届生”的岗位，经验要求全部写为“应届生”。${scope}，没有出现“应届生岗位仍附加 1 年以上经验”的情况。`
  }

  return `${fresh.count} 条标注“接受应届生”的岗位中，${explicit} 条明确要求最高学历毕业后无全职工作经验，${undisclosed} 条未单独披露工作年限${other ? `，${other} 条原文提及工作经历或年限` : ''}。${scope}，“未披露”不等于“经验不限”。`
})

function clearFilters() {
  filters.value = {}
}
</script>

<template>
  <div>
    <section class="page-intro">
      <p class="eyebrow">第二部分 / 02 · 学历与经验</p>
      <h1>第一道门槛：<br />学历，还是经验？</h1>
      <p class="lead">
        招聘启事上的“本科”“硕士”“不限”与“应届生”，构成了求职者最先遇到的两道筛子。我们把它们拆开看。
      </p>
      <p class="intro-meta">
        <span>研究问题 01 / 02</span>
        <span>分母：当前筛选后的岗位数</span>
        <span>{{ datasetLabel }}</span>
      </p>
    </section>

    <FilterBar v-model="filters" :total="education?.total ?? null" />

    <p v-if="loading && !data" class="status">正在读取学历与经验数据…</p>
    <p v-else-if="error" class="status status-error">
      数据加载失败：{{ error }}
    </p>

    <div v-else-if="data" class="stack" :class="{ refreshing: loading }">
      <section v-if="education && education.total === 0" class="empty-state">
        <p class="eyebrow">筛选结果为空</p>
        <h2>当前条件下没有岗位</h2>
        <p>试试减少筛选条件，或清除筛选查看全部样本。</p>
        <button type="button" class="empty-clear" @click="clearFilters">
          清除筛选
        </button>
      </section>

      <template v-else>
      <ChartCard
        index="图 01"
        title="学历要求构成"
        question="企业写下的最低学历门槛，在样本中如何分配？"
        note="分段条按岗位数占比绘制；学历为导入时规范化后的标准值。"
      >
        <SegmentedBar
          :items="educationItems"
          :total="education?.total ?? 0"
        />
        <template #table>
          <div class="data-table-wrap">
            <table class="data-table">
              <caption class="sr-only">学历要求分布</caption>
              <thead>
                <tr>
                  <th scope="col">学历</th>
                  <th scope="col" class="num">岗位数</th>
                  <th scope="col" class="num">占比</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in educationItems" :key="item.name">
                  <th scope="row">{{ item.name }}</th>
                  <td class="num">{{ item.count }}</td>
                  <td class="num">{{ formatPercent(item.ratio) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <template #insight>
          <p>{{ educationInsight }}</p>
        </template>
      </ChartCard>

      <ChartCard
        index="图 02"
        title="岗位类别 × 学历要求"
        question="不同技术方向，对学历的偏好是否一致？"
        note="单元格为岗位数；色深仅用于辅助阅读，数值以数字为准。n 为该岗位类别在当前筛选下的样本量。"
      >
        <EducationMatrix
          v-if="education?.by_job_type.length"
          :groups="education.by_job_type"
          :columns="educationColumns"
        />
        <p v-else class="status">当前筛选下没有可展示的岗位类别。</p>
        <template #insight>
          <p>{{ matchInsight }}</p>
        </template>
      </ChartCard>

      <ChartCard
        index="图 03"
        title="经验要求分布"
        question="样本中的岗位，是校招入口还是社招岗位？"
        :note="experienceNote"
      >
        <ExperienceComposition
          :items="experienceItems"
          :total="experience?.total ?? 0"
          label="经验要求构成"
        />
        <template #table>
          <div class="data-table-wrap">
            <table class="data-table experience-table">
              <caption class="sr-only">经验要求分布</caption>
              <thead>
                <tr>
                  <th scope="col">经验要求</th>
                  <th scope="col" class="num">岗位数</th>
                  <th scope="col" class="num">占比</th>
                  <th scope="col" class="share-col">分布</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in experienceItems" :key="item.name">
                  <th scope="row">{{ item.name }}</th>
                  <td class="num">{{ item.count }}</td>
                  <td class="num">{{ formatPercent(item.ratio) }}</td>
                  <td class="share-col">
                    <span class="share-track" aria-hidden="true">
                      <span
                        class="share-fill"
                        :style="{ width: formatPercent(item.ratio) }"
                      />
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <template #insight>
          <p>{{ experienceInsight }}</p>
        </template>
      </ChartCard>

      <section v-if="experience" class="fresh-panel">
        <div class="fresh-figure">
          <span class="fresh-count">{{ experience.fresh_graduate.count }}</span>
          <span class="fresh-total">/ {{ experience.total }} 条</span>
          <span class="fresh-ratio">
            {{ formatPercent(experience.fresh_graduate.ratio) }}
          </span>
        </div>
        <div class="fresh-copy">
          <p class="eyebrow">应届生专项</p>
          <h2>“应届生岗位”还要经验吗？</h2>
          <p>{{ freshText }}</p>
        </div>
      </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.experience-table .share-col {
  width: 42%;
}

.share-track {
  display: block;
  height: 7px;
  width: 100%;
  background: var(--hairline);
  border-radius: 4px;
  overflow: hidden;
}

.share-fill {
  display: block;
  height: 100%;
  background: var(--blue);
  border-radius: 4px;
}

.fresh-panel {
  display: grid;
  grid-template-columns: minmax(9rem, 0.32fr) minmax(0, 1fr);
  gap: 2.5rem;
  align-items: center;
  border-top: 2px solid var(--ink);
  border-bottom: 1px solid var(--hairline);
  padding: 2rem 0;
}

.fresh-figure {
  display: grid;
  grid-template-columns: auto auto;
  align-items: baseline;
  justify-content: start;
  gap: 0.2rem 0.4rem;
}

.fresh-count {
  font-family: var(--sans);
  font-size: clamp(3.6rem, 8vw, 5.6rem);
  font-weight: 600;
  letter-spacing: -0.05em;
  line-height: 0.9;
  color: var(--accent-display);
}

.fresh-total {
  color: var(--muted);
  font-size: 1rem;
}

.fresh-ratio {
  grid-column: 1 / -1;
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  color: var(--muted);
  padding-top: 0.5rem;
}

.fresh-copy {
  display: grid;
  gap: 0.55rem;
}

.fresh-copy h2 {
  font-size: clamp(1.35rem, 2.6vw, 1.8rem);
}

.fresh-copy p:last-child {
  color: var(--ink-soft);
  font-size: 0.95rem;
  max-width: 62ch;
}

@media (max-width: 760px) {
  .fresh-panel {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }
}
</style>
