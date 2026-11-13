<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import BaseChart from '@/components/charts/BaseChart.vue'
import JobDrawer from '@/components/JobDrawer.vue'
import KpiRow from '@/components/KpiRow.vue'
import SegmentedBar from '@/components/SegmentedBar.vue'
import {
  fetchEducationStats,
  fetchExperienceStats,
  fetchOverview,
  fetchSalaryStats,
  fetchSkillsStats,
} from '@/api/stats'
import { useDatasetStatus } from '@/composables/useDatasetStatus'
import {
  chart,
  orderedEducation,
  rankedBarOption,
  salaryHistogramOption,
} from '@/lib/charts'
import { formatMoney, formatPercent, ratioLabel } from '@/lib/format'
import type {
  EducationStats,
  ExperienceStats,
  Overview,
  SalaryStats,
  SkillsStats,
} from '@/types/api'

const overview = ref<Overview | null>(null)
const education = ref<EducationStats | null>(null)
const experience = ref<ExperienceStats | null>(null)
const skills = ref<SkillsStats | null>(null)
const salary = ref<SalaryStats | null>(null)

const {
  isDemoDataset,
  hasDemoRecords,
  demoRecords,
  cityLabel,
  load: loadStatus,
} = useDatasetStatus()

const drawerOpen = ref(false)
const drawerSkill = ref('')
const drawerTitle = computed(() =>
  drawerSkill.value ? `包含「${drawerSkill.value}」的岗位` : '匹配岗位',
)

function openSkill(skill: string) {
  drawerSkill.value = skill
  drawerOpen.value = true
}

const cityDisplay = computed(() =>
  cityLabel.value === '—' ? '目标城市' : cityLabel.value,
)

const loading = ref(true)
const error = ref('')
const progress = ref(0)

const chapterIndex = [
  {
    no: '01',
    title: '学历门槛',
    sub: '本科成为主流，但方向之间并不平均',
    href: '#chapter-education',
  },
  {
    no: '02',
    title: '经验要求',
    sub: '写着“应届生”的岗位，还要经验吗？',
    href: '#chapter-experience',
  },
  {
    no: '03',
    title: '技能需求',
    sub: '高频技能与岗位覆盖率',
    href: '#chapter-skills',
  },
  {
    no: '04',
    title: '薪资待遇',
    sub: '中位月薪与方向之间的差距',
    href: '#chapter-salary',
  },
]

const limitations = computed(() => {
  const city = cityLabel.value === '—' ? '目标城市' : cityLabel.value
  return [
    `样本只覆盖${city}、特定时间与公开渠道，不能代表全国或整个计算机就业市场。`,
    isDemoDataset.value
      ? '演示数据的岗位类别样本量只有 1–2 条，任何类别之间的差异都只是线索，不是稳定结论。'
      : '岗位类别之间的样本量差异会影响横向比较；请结合图表上的样本量阅读。',
    '技能标签由人工归纳，词表之外的技术词会进入“其他”；覆盖率不等于企业真实的技术使用比例。',
    '薪资取月薪区间中点，面议岗位被排除，13/14 薪与补贴未折算进月薪。',
  ]
})

const takeaways = [
  {
    title: '先选方向，再看门槛',
    text: '算法岗的学历与技能要求明显更高。方向选择会放大或缩小其他门槛，先确定方向，再决定补学历还是补技能。',
  },
  {
    title: '把工程习惯当成共同语言',
    text: 'Git、Linux 出现在大量岗位中。它们不是加分项，而是进入技术岗位的默认条件。',
  },
  {
    title: '用岗位反推技能组合',
    text: '先看目标方向的高频技能，再决定学什么。不要只按课程目录堆技能，也不要为了覆盖率去凑关键词。',
  },
]

async function setupReveal() {
  await nextTick()
  const nodes = document.querySelectorAll<HTMLElement>('[data-reveal]')
  if (!nodes.length) return

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    nodes.forEach((node) => node.classList.add('is-visible'))
    return
  }

  observer?.disconnect()
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return
        entry.target.classList.add('is-visible')
        observer?.unobserve(entry.target)
      })
    },
    { threshold: 0.08, rootMargin: '0px 0px -80px 0px' },
  )
  nodes.forEach((node) => observer?.observe(node))
}

let observer: IntersectionObserver | null = null

function updateProgress() {
  const root = document.documentElement
  const max = root.scrollHeight - window.innerHeight
  progress.value = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0
}

onMounted(async () => {
  window.addEventListener('scroll', updateProgress, { passive: true })
  updateProgress()
  void loadStatus()

  try {
    const [overviewData, educationData, experienceData, skillsData, salaryData] =
      await Promise.all([
        fetchOverview(),
        fetchEducationStats(),
        fetchExperienceStats(),
        fetchSkillsStats({}, { limit: 8, perTypeLimit: 8 }),
        fetchSalaryStats(),
      ])
    overview.value = overviewData
    education.value = educationData
    experience.value = experienceData
    skills.value = skillsData
    salary.value = salaryData
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '未知错误'
  } finally {
    loading.value = false
  }
})

watch(loading, (value) => {
  if (!value && !error.value) void setupReveal()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateProgress)
  observer?.disconnect()
  observer = null
})

const totalJobs = computed(() => overview.value?.total_jobs ?? 0)

const dossier = computed(() => {
  const data = overview.value
  if (!data) return []
  return [
    { term: '研究城市', value: `${data.total_cities} 个（${cityLabel.value}）` },
    { term: '岗位类别', value: `${data.total_job_types} 类` },
    { term: '覆盖企业', value: `${data.total_companies} 家` },
    { term: '有效薪资', value: `${data.salary_available} / ${data.total_jobs} 条` },
    { term: '采集时间', value: data.last_collected_at ?? '—' },
  ]
})

const kpis = computed(() => {
  const data = overview.value
  if (!data) return []
  const topSkill = skills.value?.items[0]
  return [
    {
      label: '有效岗位',
      value: String(data.total_jobs),
      hint: `${data.total_companies} 家企业 · ${data.total_job_types} 类岗位`,
    },
    {
      label: '应届可投',
      value: formatPercent(data.fresh_graduate_ratio),
      hint: `${data.fresh_graduate_count} 条岗位`,
    },
    {
      label: '薪资中位数',
      value: formatMoney(data.salary_median),
      hint: `有效薪资 ${data.salary_available} 条`,
    },
    {
      label: '最高频技能',
      value: topSkill?.skill ?? '—',
      hint: topSkill
        ? `${topSkill.count} / ${data.total_jobs} 条岗位`
        : '暂无技能数据',
    },
  ]
})

const educationItems = computed(() =>
  orderedEducation(education.value?.breakdown ?? []),
)

const bachelorItem = computed(() =>
  education.value?.breakdown.find((item) => item.name === '本科'),
)

const masterItem = computed(() =>
  education.value?.breakdown.find((item) => item.name === '硕士'),
)

const educationStat = computed(() => ({
  value: bachelorItem.value ? formatPercent(bachelorItem.value.ratio) : '—',
  label: '岗位要求本科',
}))

const educationStory = computed(() => {
  const edu = education.value
  if (!edu) return { lead: '', second: '', insight: '' }

  const others = edu.breakdown
    .filter(
      (item) => item.name !== '本科' && item.name !== '硕士' && item.count > 0,
    )
    .map((item) => `${item.name} ${item.count} 条`)
    .join('、')

  const allMasterGroups = edu.by_job_type
    .filter((group) => {
      const items = group.distribution.filter((item) => item.count > 0)
      return items.length > 0 && items.every((item) => item.name === '硕士')
    })
    .map((group) => group.group)

  const diversityGroups = edu.by_job_type
    .filter(
      (group) => group.distribution.filter((item) => item.count > 0).length > 1,
    )
    .map((group) => group.group)

  const core = (bachelorItem.value?.count ?? 0) + (masterItem.value?.count ?? 0)

  return {
    lead: `在 ${edu.total} 条岗位中，${bachelorItem.value?.count ?? 0} 条要求本科，${masterItem.value?.count ?? 0} 条要求硕士${others ? `；${others}` : ''}。`,
    second: `把岗位类别拆开，门槛并不整齐：${allMasterGroups.length ? `${allMasterGroups.join('、')}的岗位全部要求硕士` : '硕士要求并没有集中在单一方向'}${diversityGroups.length ? `；${diversityGroups.join('、')}等方向则出现了不止一种学历要求` : ''}。`,
    insight: `本科与硕士合计 ${core} 条，占 ${formatPercent(edu.total ? core / edu.total : 0)}。这不是“学历越高越好”的证据，而是方向差异在样本中的投影。`,
  }
})

const experienceStat = computed(() => ({
  value: experience.value
    ? formatPercent(experience.value.fresh_graduate.ratio)
    : '—',
  label: '岗位接受应届生',
}))

const experienceStory = computed(() => {
  const exp = experience.value
  if (!exp) return { lead: '', second: '', insight: '' }

  const nonFreshGroups = exp.by_job_type
    .filter((group) =>
      group.distribution.some(
        (item) =>
          item.name !== '应届生' && item.name !== '不限' && item.count > 0,
      ),
    )
    .map((group) => group.group)

  const nonFreshExperience = new Set<string>()
  exp.by_job_type.forEach((group) => {
    group.distribution.forEach((item) => {
      if (item.name !== '应届生' && item.name !== '不限' && item.count > 0) {
        nonFreshExperience.add(item.name)
      }
    })
  })

  const freshBreakdown = exp.fresh_graduate.breakdown.filter(
    (item) => item.count > 0,
  )
  const allFresh =
    freshBreakdown.length === 1 && freshBreakdown[0].name === '应届生'

  const freshText = allFresh
    ? `再看标注“接受应届生”的 ${exp.fresh_graduate.count} 条岗位：经验要求全部写为“应届生”。这份样本里，没有出现“应届生岗位仍附加 1 年以上经验”的情况。`
    : `标注“接受应届生”的 ${exp.fresh_graduate.count} 条岗位，经验要求分布为：${freshBreakdown.map((item) => `${item.name}（${item.count} 条）`).join('、')}。`

  return {
    lead: `在 ${exp.total} 条岗位中，${exp.fresh_graduate.count} 条标注“接受应届生”，占 ${formatPercent(exp.fresh_graduate.ratio)}。${
      nonFreshGroups.length
        ? `其余岗位来自${nonFreshGroups.join('、')}，经验要求为${[...nonFreshExperience].join('、')}。`
        : '当前样本中没有要求工作年限的岗位。'
    }`,
    second: freshText,
    insight:
      '经验分布把样本分成两类：面向校招的入口岗，以及少量要求工作年限的社招岗。样本量有限，不能据此推断“市场上所有应届生岗位都不要求经验”。',
  }
})

const topSkills = computed(() => skills.value?.items.slice(0, 8) ?? [])

const skillCategories = computed(() =>
  (skills.value?.categories ?? []).slice(0, 4),
)

const skillStat = computed(() => {
  const top = skills.value?.items[0]
  return {
    value: top ? formatPercent(top.ratio) : '—',
    label: top ? `岗位提到 ${top.skill}` : '最高频技能',
  }
})

const skillStory = computed(() => {
  const data = skills.value
  if (!data) return { lead: '', second: '', insight: '' }

  const [first, second, third] = data.items
  const categories = data.categories
    .slice(0, 2)
    .map((item) => `${item.category} ${item.count} 条`)
    .join('、')

  return {
    lead: first
      ? `${first.skill} 出现在 ${first.count} / ${data.total_jobs} 条岗位中，覆盖率 ${formatPercent(first.ratio)}${second && third ? `；${second.skill} 与 ${third.skill} 各 ${second.count} 条` : ''}。`
      : '当前样本中没有技能数据。',
    second: first
      ? `${isDemoDataset.value ? '头部技能集中，长尾技能大多只出现 1–2 次。' : '头部技能集中，长尾技能出现次数较少。'}技能类别上，${categories}覆盖的岗位最多；类别之间可以重叠，不能相加。`
      : '',
    insight:
      '岗位覆盖率不是关键词词频：同一岗位列出三项数据库技能，在“数据库”类别下仍只计 1 条岗位。',
  }
})

const experienceRows = computed(() => {
  const stats = experience.value
  if (!stats) return []
  return stats.breakdown.map((item) => ({
    name: item.name,
    value: item.count,
    display: ratioLabel(item.count, stats.total),
    emphasis: item.name === '应届生',
  }))
})

const experienceOption = computed(() =>
  rankedBarOption(experienceRows.value, {
    labelWidth: 78,
    deEmphasise: true,
    color: chart.blue,
    emphasisColor: chart.blueDeep,
  }),
)

const salaryStat = computed(() => ({
  value: formatMoney(salary.value?.overall.median ?? null),
  label: '月薪中位数',
}))

const salaryStory = computed(() => {
  const data = salary.value
  if (!data) return { lead: '', second: '', insight: '' }

  const ranked = [...data.by_job_type].sort(
    (a, b) => (b.median ?? 0) - (a.median ?? 0),
  )
  const highest = ranked[0]
  const lowest = ranked[ranked.length - 1]
  const missing = data.total_jobs - data.salary_available
  const multiple =
    highest?.median && data.overall.median
      ? (highest.median / data.overall.median).toFixed(1)
      : null

  return {
    lead: `有效薪资 ${data.salary_available} / ${data.total_jobs} 条，整体中位月薪 ${formatMoney(data.overall.median)}${missing ? `；${missing} 条面议未纳入` : ''}。`,
    second:
      highest && lowest
        ? `${highest.group}的中位月薪最高，为 ${formatMoney(highest.median)}${multiple ? `，约为整体中位的 ${multiple} 倍` : ''}；${lowest.group}最低，为 ${formatMoney(lowest.median)}。`
        : '',
    insight: isDemoDataset.value
      ? '但多数类别只有 1 条有效薪资，区间会退化为一个点。这里的方向差异是线索，不是稳定的行业结论。'
      : '各类别的有效薪资样本量不同；样本较少的类别，区间会因个别岗位而波动。这里的方向差异是线索，不是稳定的行业结论。',
  }
})

const histogramOption = computed(() =>
  salaryHistogramOption(salary.value?.distribution ?? []),
)

const salaryMissing = computed(
  () =>
    (salary.value?.total_jobs ?? 0) - (salary.value?.salary_available ?? 0),
)

const conclusionFindings = computed(() => {
  const edu = education.value
  const exp = experience.value
  const skillData = skills.value
  const salaryData = salary.value
  if (!edu || !exp || !skillData || !salaryData) return []

  const bachelor = edu.breakdown.find((item) => item.name === '本科')
  const master = edu.breakdown.find((item) => item.name === '硕士')
  const top = skillData.items[0]
  const highest = [...salaryData.by_job_type].sort(
    (a, b) => (b.median ?? 0) - (a.median ?? 0),
  )[0]

  const nonFreshGroups = exp.by_job_type
    .filter((group) =>
      group.distribution.some(
        (item) => item.name !== '应届生' && item.name !== '不限' && item.count > 0,
      ),
    )
    .map((group) => group.group)

  return [
    {
      figure: bachelor ? formatPercent(bachelor.ratio) : '—',
      title: '岗位要求本科',
      text: `${bachelor?.count ?? 0} / ${edu.total} 条；硕士 ${master?.count ?? 0} 条。`,
    },
    {
      figure: formatPercent(exp.fresh_graduate.ratio),
      title: '岗位接受应届生',
      text: `${exp.fresh_graduate.count} / ${exp.total} 条${nonFreshGroups.length ? `；非应届岗位来自${nonFreshGroups.join('、')}` : ''}。`,
    },
    {
      figure: top ? formatPercent(top.ratio) : '—',
      title: top ? `岗位提到 ${top.skill}` : '最高频技能',
      text: top
        ? `${top.count} / ${skillData.total_jobs} 条；工具技能是最普遍的共同语言。`
        : '暂无技能数据。',
    },
    {
      figure: formatMoney(salaryData.overall.median),
      title: '月薪中位数',
      text: `有效薪资 ${salaryData.salary_available} 条；${highest?.group ?? '—'}中位 ${formatMoney(highest?.median ?? null)}。`,
    },
  ]
})
</script>

<template>
  <div class="feature">
    <div class="reading-progress" aria-hidden="true">
      <span :style="{ transform: `scaleX(${progress})` }" />
    </div>

    <p v-if="loading" class="status">正在整理样本数据…</p>
    <p v-else-if="error" class="status status-error">
      数据加载失败：{{ error }}。请确认后端已启动，并已导入数据。
    </p>

    <template v-else>
      <section class="feature-hero">
        <div class="hero-copy reveal">
          <p class="hero-report">2026 GRADUATE RECRUITMENT REPORT</p>
          <p class="hero-kicker">
            <span>JobLens</span>
            <i aria-hidden="true" />
            就业观察 · 数据新闻
          </p>
          <h1 class="hero-title">
            <span>学历之外，</span>
            <em>企业还看重什么？</em>
          </h1>
          <p class="hero-dek">
            透过招聘数据，观察计算机类应届生的求职竞争力。基于{{ cityDisplay }}
            {{ overview?.total_jobs ?? 0 }} 条公开招聘岗位样本的调查分析。
          </p>
          <div class="hero-byline">
            <span>JobLens 数据小组</span>
            <span>2026 年 11 月</span>
            <span>样本 {{ overview?.total_jobs ?? 0 }} 条</span>
          </div>
        </div>

        <aside class="hero-dossier reveal" style="animation-delay: 120ms">
          <p class="dossier-label">样本档案 / DOSSIER</p>
          <dl>
            <div v-for="row in dossier" :key="row.term">
              <dt>{{ row.term }}</dt>
              <dd>{{ row.value }}</dd>
            </div>
          </dl>
          <div v-if="isDemoDataset" class="stamp" aria-label="演示样本">
            <span>DEMO</span>
            <span>演示样本</span>
          </div>
        </aside>
      </section>

      <KpiRow :items="kpis" />

      <section class="preface" data-reveal>
        <div class="preface-copy">
          <p class="eyebrow">导语 / PREFACE</p>
          <p class="preface-lead">
            如果把招聘启事当作一份公开的用人声明，学历、经验、技能与薪资，就是它最常写下的四项条件。
          </p>
          <p v-if="isDemoDataset">
            我们把这四项条件拆开，放回{{ cityDisplay }}计算机类应届生岗位的样本里。样本很小，所以它更像一次结构演示：看看招聘要求如何被数据描述，也看看这些描述不能证明什么。
          </p>
          <p v-else>
            我们把这四项条件拆开，放回{{ cityDisplay }}计算机类应届生岗位的样本里，看看招聘要求如何被数据描述，也看看这些描述不能证明什么。
          </p>
          <p v-if="isDemoDataset" class="demo-note">
            当前版本使用 {{ demoRecords }} 条虚构演示数据，企业名称均标注“（虚构）”。正式采集完成后，页面会直接读取真实样本。
          </p>
          <p v-else-if="hasDemoRecords" class="demo-note">
            当前数据集含 {{ demoRecords }} 条演示记录；正式结论应以真实采集数据重新计算。
          </p>
        </div>

        <nav class="chapter-index" aria-label="报告章节">
          <p class="index-label">本报告章节 / CONTENTS</p>
          <a v-for="item in chapterIndex" :key="item.no" :href="item.href">
            <span class="index-no">{{ item.no }}</span>
            <span class="index-title">{{ item.title }}</span>
            <span class="index-sub">{{ item.sub }}</span>
          </a>
        </nav>
      </section>

      <section id="chapter-education" class="feature-chapter education" data-reveal>
        <header class="chapter-head">
          <p class="chapter-label">
            <span class="chapter-no">01</span>
            <span>EDUCATION / 学历门槛</span>
          </p>
          <h2>本科是主流，<br />但门槛并不平均</h2>
          <p class="chapter-question">“不同技术方向，对学历的要求一样吗？”</p>
        </header>

        <div class="chapter-body">
          <div class="chapter-copy">
            <div class="chapter-stat">
              <span class="stat-figure">{{ educationStat.value }}</span>
              <span class="stat-label">{{ educationStat.label }}</span>
            </div>
            <p>{{ educationStory.lead }}</p>
            <p>{{ educationStory.second }}</p>
            <p class="chapter-insight">{{ educationStory.insight }}</p>
            <RouterLink class="chapter-more" to="/education-experience">
              查看完整学历与经验分析 <span aria-hidden="true">→</span>
            </RouterLink>
          </div>

          <figure class="chapter-figure">
            <div class="figure-plate">
              <SegmentedBar
                :items="educationItems"
                :total="education?.total ?? 0"
              />
            </div>
            <figcaption>
              图 01 · 学历要求构成。分段长度按岗位数占比绘制；分母为
              {{ education?.total ?? 0 }} 条岗位。
            </figcaption>
          </figure>
        </div>
      </section>

      <section
        id="chapter-experience"
        class="feature-chapter experience reverse"
        data-reveal
      >
        <header class="chapter-head">
          <p class="chapter-label">
            <span class="chapter-no">02</span>
            <span>EXPERIENCE / 经验要求</span>
          </p>
          <h2>写着“应届生”，<br />真的不需要经验吗？</h2>
          <p class="chapter-question">“接受应届生的岗位，是否还附加工作年限？”</p>
        </header>

        <div class="chapter-body">
          <figure class="chapter-figure">
            <div class="figure-plate">
              <BaseChart
                :option="experienceOption"
                height="200px"
                aria-label="经验要求分布条形图"
              />
            </div>
            <figcaption>
              图 02 · 经验要求分布。高亮“应届生”，其余档位以灰色作背景对照。
            </figcaption>
          </figure>

          <div class="chapter-copy">
            <div class="chapter-stat">
              <span class="stat-figure">{{ experienceStat.value }}</span>
              <span class="stat-label">{{ experienceStat.label }}</span>
            </div>
            <p>{{ experienceStory.lead }}</p>
            <p>{{ experienceStory.second }}</p>
            <p class="chapter-insight">{{ experienceStory.insight }}</p>
            <RouterLink class="chapter-more" to="/education-experience">
              看完整的经验分析 <span aria-hidden="true">→</span>
            </RouterLink>
          </div>
        </div>
      </section>

      <section
        id="chapter-skills"
        class="feature-chapter skills wide"
        data-reveal
      >
        <header class="chapter-head">
          <p class="chapter-label">
            <span class="chapter-no">03</span>
            <span>SKILLS / 技能需求</span>
          </p>
          <h2>企业反复提到的，<br />不只是编程语言</h2>
          <p class="chapter-question">“哪些技能出现在最多的岗位里？”</p>
        </header>

        <div class="skill-intro">
          <div class="chapter-stat">
            <span class="stat-figure">{{ skillStat.value }}</span>
            <span class="stat-label">{{ skillStat.label }}</span>
          </div>
          <p>
            技能覆盖率按岗位数计算；同一岗位里的重复技能只计一次，不用关键词词频。
          </p>
        </div>

        <div class="skill-wall">
          <button
            v-for="(skill, index) in topSkills"
            :key="skill.skill"
            type="button"
            class="skill-row"
            :aria-label="`查看包含 ${skill.skill} 的岗位`"
            @click="openSkill(skill.skill)"
          >
            <span class="skill-meta">
              <span class="skill-rank">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="skill-name">{{ skill.skill }}</span>
              <span class="skill-category">{{ skill.category }}</span>
            </span>
            <span class="skill-meter" aria-hidden="true">
              <i :style="{ width: formatPercent(skill.ratio) }" />
            </span>
            <span class="skill-value">
              {{ skill.count }} / {{ totalJobs }} · {{ formatPercent(skill.ratio) }}
            </span>
          </button>
        </div>

        <div class="skill-summary">
          <p>{{ skillStory.lead }}</p>
          <p>{{ skillStory.second }}</p>
          <p class="chapter-insight">{{ skillStory.insight }}</p>
          <div class="skill-categories">
            <span
              v-for="category in skillCategories"
              :key="category.category"
            >
              {{ category.category }} · {{ category.count }}/{{ totalJobs }}
            </span>
          </div>
          <p class="figure-caption">
            图 03 · 高频技能与岗位覆盖率。分母为 {{ totalJobs }} 条岗位；类别覆盖可重叠，不能相加。
          </p>
          <RouterLink class="chapter-more" to="/skills">
            查看完整技能图谱 <span aria-hidden="true">→</span>
          </RouterLink>
        </div>
      </section>

      <section id="chapter-salary" class="feature-chapter salary" data-reveal>
        <header class="chapter-head">
          <p class="chapter-label">
            <span class="chapter-no">04</span>
            <span>SALARY / 薪资待遇</span>
          </p>
          <h2>薪资的分化，<br />沿着技术方向展开</h2>
          <p class="chapter-question">“不同方向的月薪差距有多大？”</p>
        </header>

        <div class="chapter-body">
          <div class="chapter-copy">
            <div class="chapter-stat">
              <span class="stat-figure">{{ salaryStat.value }}</span>
              <span class="stat-label">{{ salaryStat.label }}</span>
            </div>
            <p>{{ salaryStory.lead }}</p>
            <p>{{ salaryStory.second }}</p>
            <p class="chapter-insight">{{ salaryStory.insight }}</p>
            <RouterLink class="chapter-more" to="/salary">
              看完整薪资分布 <span aria-hidden="true">→</span>
            </RouterLink>
          </div>

          <figure class="chapter-figure">
            <div class="figure-plate">
              <BaseChart
                :option="histogramOption"
                height="300px"
                aria-label="月薪中点分布直方图"
              />
            </div>
            <figcaption>
              图 04 · 月薪中点分布。有效薪资
              {{ salary?.salary_available ?? 0 }} 条；面议
              {{ salaryMissing }} 条不纳入。
            </figcaption>
          </figure>
        </div>
      </section>

      <section id="conclusion" class="conclusion" data-reveal>
        <header class="conclusion-head">
          <p class="eyebrow">结论 / CONCLUSION</p>
          <h2>数据能说明什么，<br />不能说明什么</h2>
        </header>

        <div class="conclusion-grid">
          <div class="conclusion-findings">
            <h3>在这份样本里，我们看到了</h3>
            <ol>
              <li v-for="finding in conclusionFindings" :key="finding.title">
                <span class="finding-figure">{{ finding.figure }}</span>
                <span class="finding-text">
                  <strong>{{ finding.title }}</strong>
                  <small>{{ finding.text }}</small>
                </span>
              </li>
            </ol>
          </div>

          <div class="conclusion-limits">
            <h3>它不能替你回答的</h3>
            <ul>
              <li v-for="item in limitations" :key="item">{{ item }}</li>
            </ul>
            <p class="conclusion-note">
              以上结论仅描述这 {{ totalJobs }} 条{{ isDemoDataset ? '演示' : '' }}样本；{{ isDemoDataset ? '正式数据导入后需要重新计算。' : '不代表整体就业市场。' }}
            </p>
          </div>
        </div>

        <div class="takeaways">
          <p class="eyebrow">阅读提示 / TAKEAWAYS</p>
          <div class="takeaway-grid">
            <div v-for="(item, index) in takeaways" :key="item.title">
              <span>0{{ index + 1 }}</span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.text }}</p>
            </div>
          </div>
          <p class="takeaway-note">
            {{ isDemoDataset ? '这些是基于样本的阅读提示，不是因果结论；样本量很小，请谨慎使用。' : '这些是基于样本的阅读提示，不是因果结论；请结合样本量谨慎使用。' }}
          </p>
        </div>

        <div class="conclusion-cta">
          <RouterLink class="cta-primary" to="/about-data">阅读数据说明</RouterLink>
          <RouterLink class="cta-secondary" to="/salary">
            继续查看薪资分析 <span aria-hidden="true">→</span>
          </RouterLink>
        </div>
      </section>

      <footer class="colophon">
        <div>
          <p class="colophon-brand">JOBLENS · SEE BEYOND THE JOB MARKET</p>
          <p>
            一个以数据分析和新闻叙事为核心的交互式数据新闻作品。样本数据不代表整体就业市场。
          </p>
        </div>
        <div class="colophon-meta">
          <span>{{ isDemoDataset ? '演示样本' : '样本' }} {{ totalJobs }} 条 · {{ cityLabel }}</span>
          <span>2026.11</span>
          <RouterLink to="/about-data">数据说明 →</RouterLink>
        </div>
      </footer>

      <JobDrawer
        v-model:open="drawerOpen"
        :title="drawerTitle"
        :query="{ skill: drawerSkill }"
      />
    </template>
  </div>
</template>

<style scoped>
.feature {
  display: grid;
}

.reading-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 60;
  height: 2px;
  pointer-events: none;
}

.reading-progress span {
  display: block;
  height: 100%;
  background: var(--accent);
  transform-origin: 0 50%;
}

/* ---------- hero ---------- */

.feature-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(17rem, 0.75fr);
  gap: 3rem;
  align-items: stretch;
  padding-bottom: 3.25rem;
  border-bottom: 1px solid var(--hairline);
}

.hero-copy {
  display: grid;
  gap: 1.15rem;
  align-content: start;
}

.hero-report {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.18em;
  color: var(--faint);
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  color: var(--muted);
}

.hero-kicker span {
  color: var(--accent-ink);
}

.hero-kicker i {
  display: inline-block;
  width: 2.5rem;
  height: 1px;
  background: var(--hairline-strong);
}

.hero-title {
  font-size: clamp(2.9rem, 7vw, 5.4rem);
  line-height: 1.03;
  letter-spacing: -0.035em;
  font-weight: 600;
  display: grid;
  gap: 0.1em;
}

.hero-title span {
  display: block;
}

.hero-title em {
  display: block;
  font-style: normal;
  color: var(--accent-display);
  background: linear-gradient(
    transparent 72%,
    rgba(231, 111, 81, 0.13) 72%,
    rgba(231, 111, 81, 0.13) 94%,
    transparent 94%
  );
  width: fit-content;
  max-width: 100%;
}

.hero-dek {
  max-width: 52ch;
  color: var(--ink-soft);
  font-size: 1.12rem;
  line-height: 1.8;
}

.hero-byline {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.2rem;
  font-family: var(--mono);
  font-size: 0.66rem;
  letter-spacing: 0.06em;
  color: var(--muted);
  padding-top: 0.4rem;
}

.hero-byline span + span::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 3px;
  margin-right: 1.2rem;
  border-radius: 50%;
  background: var(--hairline-strong);
  vertical-align: 0.2em;
}

.hero-dossier {
  position: relative;
  border-left: 1px solid var(--hairline);
  padding: 0.2rem 0 4.5rem 1.6rem;
  display: grid;
  gap: 1.1rem;
  align-content: start;
}

.dossier-label {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.14em;
  color: var(--accent-ink);
}

.hero-dossier dl {
  display: grid;
  gap: 0;
}

.hero-dossier dl > div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--hairline);
  font-size: 0.84rem;
}

.hero-dossier dt {
  color: var(--muted);
}

.hero-dossier dd {
  margin: 0;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.stamp {
  position: absolute;
  right: 0;
  bottom: 0.4rem;
  display: grid;
  gap: 0.1rem;
  padding: 0.5rem 0.7rem;
  border: 2px solid var(--accent-ink);
  color: var(--accent-ink);
  transform: rotate(-3deg);
  font-family: var(--serif);
  line-height: 1.1;
  text-align: center;
  opacity: 0.85;
}

.stamp span:first-child {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.18em;
}

.stamp span:last-child {
  font-size: 0.8rem;
}

/* ---------- preface ---------- */

.preface {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(18rem, 0.95fr);
  gap: 3rem;
  padding: 3rem 0;
  border-bottom: 1px solid var(--hairline-strong);
}

.preface-copy {
  display: grid;
  gap: 1rem;
  align-content: start;
  max-width: 62ch;
}

.preface-lead {
  font-family: var(--serif);
  font-size: clamp(1.3rem, 2.4vw, 1.6rem);
  line-height: 1.5;
  color: var(--ink);
}

.preface-lead::first-letter {
  float: left;
  font-family: var(--serif);
  font-size: 3.2em;
  line-height: 0.78;
  padding: 0.08em 0.12em 0 0;
  color: var(--accent-display);
}

.preface-copy > p:not(.eyebrow):not(.preface-lead) {
  color: var(--ink-soft);
  font-size: 0.95rem;
  line-height: 1.85;
}

.demo-note {
  border-left: 2px solid var(--accent);
  padding-left: 0.8rem;
  font-family: var(--mono);
  font-size: 0.68rem !important;
  line-height: 1.7 !important;
  color: var(--muted) !important;
}

.chapter-index {
  display: grid;
  gap: 0;
  align-content: start;
  border-top: 2px solid var(--ink);
  padding-top: 1rem;
}

.index-label {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.14em;
  color: var(--accent-ink);
  margin-bottom: 0.5rem;
}

.chapter-index a {
  display: grid;
  grid-template-columns: 2.4rem minmax(0, 1fr);
  grid-template-rows: auto auto;
  column-gap: 0.8rem;
  align-items: baseline;
  padding: 0.8rem 0.4rem;
  border-bottom: 1px solid var(--hairline);
  text-decoration: none;
  transition: background 160ms ease, padding-left 160ms ease;
}

.chapter-index a:hover {
  background: rgba(231, 111, 81, 0.05);
  padding-left: 0.7rem;
}

.index-no {
  grid-row: 1 / 3;
  font-family: var(--serif);
  font-size: 1.35rem;
  line-height: 1;
  color: var(--hairline-strong);
  transition: color 160ms ease;
}

.chapter-index a:hover .index-no {
  color: var(--accent-display);
}

.index-title {
  font-family: var(--serif);
  font-size: 1.12rem;
  color: var(--ink);
}

.index-sub {
  font-size: 0.78rem;
  color: var(--muted);
  line-height: 1.5;
}

/* ---------- chapters ---------- */

.feature-chapter {
  padding: 4rem 0 4.5rem;
  border-bottom: 1px solid var(--hairline-strong);
  scroll-margin-top: 5.5rem;
}

.education,
.salary {
  --chapter: var(--accent-ink);
  --chapter-mark: var(--accent);
}

.experience {
  --chapter: var(--blue);
  --chapter-mark: var(--blue);
}

.skills {
  --chapter: var(--green-ink);
  --chapter-mark: var(--green);
}

.chapter-head {
  display: grid;
  gap: 0.8rem;
  max-width: 62rem;
  margin-bottom: 2rem;
}

.chapter-label {
  display: flex;
  align-items: baseline;
  gap: 0.8rem;
  font-family: var(--mono);
  font-size: 0.64rem;
  letter-spacing: 0.14em;
  color: var(--chapter);
}

.chapter-no {
  font-family: var(--serif);
  font-size: 2rem;
  line-height: 0.8;
}

.chapter-head h2 {
  font-size: clamp(2rem, 4.6vw, 3.4rem);
}

.chapter-question {
  font-family: var(--serif);
  font-size: clamp(1.05rem, 1.8vw, 1.24rem);
  color: var(--ink-soft);
  border-left: 2px solid var(--chapter);
  padding-left: 0.85rem;
}

.chapter-body {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 3rem;
  align-items: start;
}

.reverse .chapter-body {
  grid-template-columns: minmax(0, 1.08fr) minmax(0, 0.92fr);
}

.chapter-copy {
  display: grid;
  gap: 1.05rem;
  align-content: start;
  max-width: 54ch;
}

.chapter-stat {
  display: grid;
  gap: 0.15rem;
  margin-bottom: 0.1rem;
}

.stat-figure {
  font-family: var(--sans);
  font-size: clamp(3rem, 6vw, 4.6rem);
  font-weight: 600;
  letter-spacing: -0.05em;
  line-height: 0.9;
  color: var(--chapter);
}

.stat-label {
  font-family: var(--mono);
  font-size: 0.64rem;
  letter-spacing: 0.1em;
  color: var(--muted);
}

.chapter-copy > p {
  color: var(--ink-soft);
  font-size: 0.97rem;
  line-height: 1.85;
}

.chapter-insight {
  border-left: 2px solid var(--chapter-mark);
  padding-left: 0.9rem;
  color: var(--ink) !important;
  font-size: 0.91rem !important;
}

.chapter-insight::before {
  content: '数据解读';
  display: block;
  font-family: var(--mono);
  font-size: 0.58rem;
  letter-spacing: 0.12em;
  color: var(--chapter);
  margin-bottom: 0.25rem;
}

.chapter-more {
  justify-self: start;
  font-family: var(--mono);
  font-size: 0.66rem;
  letter-spacing: 0.06em;
  color: var(--chapter);
  text-decoration: none;
  border-bottom: 1px solid currentColor;
  padding-bottom: 0.15rem;
}

.chapter-more span {
  display: inline-block;
  transition: transform 160ms ease;
}

.chapter-more:hover span {
  transform: translateX(3px);
}

.chapter-figure {
  display: grid;
  gap: 0.7rem;
  margin: 0;
}

.figure-plate {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: 6px;
  padding: 1.1rem;
}

.chapter-figure figcaption,
.figure-caption {
  font-family: var(--mono);
  font-size: 0.63rem;
  line-height: 1.65;
  letter-spacing: 0.02em;
  color: var(--muted);
}

/* ---------- skills ---------- */

.skill-intro {
  display: flex;
  align-items: baseline;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.skill-intro p {
  max-width: 44ch;
  color: var(--muted);
  font-size: 0.8rem;
  line-height: 1.7;
}

.skill-wall {
  display: grid;
  border-top: 1px solid var(--hairline-strong);
  margin-top: 1rem;
}

.skill-row {
  display: grid;
  grid-template-columns: minmax(12rem, 0.9fr) minmax(0, 1.4fr) 9rem;
  gap: 1.5rem;
  align-items: center;
  width: 100%;
  padding: 0.85rem 0.2rem;
  border: 0;
  border-bottom: 1px solid var(--hairline);
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 160ms ease;
}

.skill-row:hover {
  background: rgba(76, 154, 134, 0.06);
}

.skill-meta {
  display: flex;
  align-items: baseline;
  gap: 0.65rem;
  min-width: 0;
}

.skill-rank {
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--faint);
}

.skill-name {
  font-family: var(--serif);
  font-size: clamp(1.2rem, 2vw, 1.45rem);
  color: var(--ink);
  white-space: nowrap;
}

.skill-category {
  font-family: var(--mono);
  font-size: 0.55rem;
  letter-spacing: 0.02em;
  color: var(--muted);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  padding: 0.08rem 0.38rem;
  white-space: nowrap;
}

.skill-meter {
  height: 8px;
  overflow: hidden;
  border-radius: 4px;
  background: #dcebe6;
}

.skill-meter i {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: var(--green);
  transition: width 480ms ease;
}

.skill-value {
  font-family: var(--mono);
  font-size: 0.66rem;
  color: var(--muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.skill-summary {
  display: grid;
  gap: 1rem;
  max-width: 70ch;
  margin-top: 1.6rem;
}

.skill-summary > p:not(.chapter-insight):not(.figure-caption) {
  color: var(--ink-soft);
  font-size: 0.95rem;
  line-height: 1.85;
}

.skill-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 0.55rem;
}

.skill-categories span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-family: var(--mono);
  font-size: 0.6rem;
  letter-spacing: 0.02em;
  color: var(--muted);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
}

.skill-categories span::before {
  content: '';
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--green);
}

/* ---------- conclusion ---------- */

.conclusion {
  padding: 4rem 0 2rem;
  scroll-margin-top: 5.5rem;
}

.conclusion-head {
  display: grid;
  gap: 0.6rem;
  margin-bottom: 2.5rem;
}

.conclusion-head h2 {
  font-size: clamp(2rem, 4.6vw, 3.2rem);
}

.conclusion-grid {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 3rem;
}

.conclusion h3 {
  font-family: var(--serif);
  font-size: 1.25rem;
  margin-bottom: 0.8rem;
}

.conclusion-findings ol {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  border-top: 1px solid var(--hairline-strong);
}

.conclusion-findings li {
  display: grid;
  grid-template-columns: 5.2rem minmax(0, 1fr);
  gap: 1rem;
  align-items: baseline;
  padding: 1rem 0;
  border-bottom: 1px solid var(--hairline);
}

.finding-figure {
  font-family: var(--sans);
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: var(--accent-display);
  font-variant-numeric: tabular-nums;
}

.finding-text {
  display: grid;
  gap: 0.2rem;
}

.finding-text strong {
  font-family: var(--serif);
  font-size: 1rem;
  font-weight: 600;
}

.finding-text small {
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.6;
}

.conclusion-limits ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.9rem;
}

.conclusion-limits li {
  border-left: 2px solid var(--hairline-strong);
  padding-left: 0.9rem;
  color: var(--ink-soft);
  font-size: 0.88rem;
  line-height: 1.75;
}

.conclusion-note {
  margin-top: 1.1rem;
  font-family: var(--mono);
  font-size: 0.66rem;
  line-height: 1.7;
  color: var(--muted);
}

.takeaways {
  margin-top: 3rem;
  border-top: 1px solid var(--hairline);
  padding-top: 1.5rem;
}

.takeaway-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.takeaway-grid > div {
  border-top: 1px solid var(--hairline-strong);
  padding-top: 0.8rem;
}

.takeaway-grid span {
  font-family: var(--mono);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  color: var(--accent-ink);
}

.takeaway-grid h3 {
  font-size: 1.05rem;
  margin: 0.25rem 0 0.3rem;
}

.takeaway-grid p {
  color: var(--ink-soft);
  font-size: 0.84rem;
  line-height: 1.7;
}

.takeaway-note {
  margin-top: 1rem;
  font-family: var(--mono);
  font-size: 0.64rem;
  color: var(--muted);
}

.conclusion-cta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem 1.5rem;
  align-items: center;
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid var(--ink);
}

.cta-primary {
  background: var(--ink);
  color: var(--paper);
  text-decoration: none;
  padding: 0.65rem 1.1rem;
  font-size: 0.84rem;
  letter-spacing: 0.02em;
}

.cta-secondary {
  color: var(--accent-ink);
  text-decoration: none;
  font-size: 0.84rem;
  border-bottom: 1px solid rgba(231, 111, 81, 0.45);
  padding-bottom: 0.15rem;
}

/* ---------- colophon ---------- */

.colophon {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  flex-wrap: wrap;
  border-top: 1px solid var(--hairline-strong);
  padding: 1.75rem 0 0.5rem;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.7;
}

.colophon-brand {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  color: var(--ink);
  margin-bottom: 0.4rem;
}

.colophon-meta {
  display: grid;
  gap: 0.15rem;
  text-align: right;
  font-family: var(--mono);
  font-size: 0.64rem;
}

.colophon-meta a {
  color: var(--accent-ink);
  text-decoration: none;
}

/* ---------- reveal ---------- */

[data-reveal] {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 550ms ease, transform 550ms ease;
}

[data-reveal].is-visible {
  opacity: 1;
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  [data-reveal] {
    opacity: 1;
    transform: none;
    transition: none;
  }

  .skill-meter i {
    transition: none;
  }
}

/* ---------- responsive ---------- */

@media (max-width: 900px) {
  .feature-hero {
    grid-template-columns: minmax(0, 1fr);
    gap: 2rem;
    padding-bottom: 2.5rem;
  }

  .hero-dossier {
    border-left: 0;
    border-top: 1px solid var(--hairline);
    padding: 1.2rem 0 0;
  }

  .stamp {
    position: static;
    justify-self: end;
    margin-top: 0.5rem;
  }

  .preface {
    grid-template-columns: minmax(0, 1fr);
    gap: 2rem;
  }

  .chapter-body,
  .reverse .chapter-body {
    grid-template-columns: minmax(0, 1fr);
    gap: 2rem;
  }

  .reverse .chapter-body .chapter-figure {
    order: 0;
  }

  .reverse .chapter-body .chapter-copy {
    order: 1;
  }

  .chapter-copy {
    max-width: 62ch;
  }

  .conclusion-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 2rem;
  }

  .takeaway-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 1rem;
  }

  .skill-row {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr) 8rem;
    gap: 1rem;
  }
}

@media (max-width: 640px) {
  .hero-title {
    font-size: clamp(2.45rem, 11vw, 3.5rem);
  }

  .hero-dek {
    font-size: 1.02rem;
  }

  .feature-chapter {
    padding: 2.75rem 0 3.25rem;
  }

  .chapter-head h2 {
    font-size: clamp(1.8rem, 9vw, 2.6rem);
  }

  .chapter-question {
    font-size: 1rem;
  }

  .chapter-copy > p,
  .skill-summary > p:not(.chapter-insight):not(.figure-caption) {
    font-size: 0.93rem;
  }

  .stat-figure {
    font-size: clamp(2.8rem, 14vw, 3.8rem);
  }

  .skill-row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.45rem 0.8rem;
    padding: 0.8rem 0;
  }

  .skill-meta {
    grid-column: 1 / -1;
  }

  .skill-meter {
    grid-column: 1;
  }

  .skill-value {
    grid-column: 2;
    font-size: 0.62rem;
  }

  .conclusion-findings li {
    grid-template-columns: 4.2rem minmax(0, 1fr);
    gap: 0.75rem;
  }

  .finding-figure {
    font-size: 1.25rem;
  }

  .colophon {
    flex-direction: column;
  }

  .colophon-meta {
    text-align: left;
  }
}
</style>
