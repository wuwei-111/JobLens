<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchOverview } from '@/api/stats'
import { formatPercent } from '@/lib/format'
import type { Overview } from '@/types/api'

const overview = ref<Overview | null>(null)
const error = ref('')

onMounted(async () => {
  try {
    overview.value = await fetchOverview()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '未知错误'
  }
})

const qualityRows = computed(() => {
  const data = overview.value
  if (!data) return []
  return [
    {
      label: '岗位记录',
      value: `${data.total_jobs} 条`,
      note: '当前导入演示数据集',
    },
    {
      label: '薪资有效',
      value: `${data.salary_available} 条`,
      note: `占 ${formatPercent(
        data.total_jobs ? data.salary_available / data.total_jobs : 0,
      )}；面议 ${data.total_jobs - data.salary_available} 条`,
    },
    {
      label: '技能标签',
      value: `${data.total_skills} 项`,
      note: '规范化、去重后的技能词',
    },
    {
      label: '岗位类别',
      value: `${data.total_job_types} 类`,
      note: `覆盖 ${data.total_companies} 家企业`,
    },
  ]
})

const fields = [
  ['id', '招聘记录唯一标识', '必填'],
  ['company / position', '企业名称、岗位名称', '必填'],
  ['job_type', '岗位类别（白名单归一）', '必填'],
  ['city', '招聘城市', '必填'],
  ['salary_min / max', '月薪下限 / 上限（元）', '可空（面议）'],
  ['education', '学历要求（统一词表）', '必填'],
  ['experience', '经验要求（统一词表）', '必填'],
  ['is_fresh_graduate', '是否接受应届生', '必填'],
  ['skills', '技能关键词数组', '1–10 项'],
  ['source / source_url', '来源名称与原始链接', '必填'],
  ['collected_at', '采集日期', '必填'],
]
</script>

<template>
  <div>
    <section class="page-intro">
      <p class="eyebrow">第五部分 / 05 · 数据说明</p>
      <h1>数据从哪来，<br />结论站得住吗？</h1>
      <p class="lead">
        数据新闻的可信度来自透明的采集与方法。这一页说明当前演示样本的状态、统计口径，以及它明确不能回答的问题。
      </p>
      <p class="intro-meta">
        <span>最后更新 2026-11-13</span>
        <span>演示数据集 v0.2.0</span>
        <span>JobLens 数据小组</span>
      </p>
    </section>

    <section class="demo-banner">
      <div class="demo-number">
        <span class="demo-figure">{{ overview?.total_jobs ?? '—' }}</span>
        <span class="demo-unit">条</span>
      </div>
      <div class="demo-copy">
        <p class="eyebrow">当前数据状态 / Demo</p>
        <h2>这是虚构演示数据，不是新闻结论</h2>
        <p>
          仓库当前包含 10 条手工构造的招聘记录，企业名称均标注“（虚构）”，来源链接指向 example.com。它们用于验证导入、统计、图表与页面流程；正式数据采集完成后会替换为真实、可核验的样本。
        </p>
      </div>
    </section>

    <p v-if="error" class="status status-error">数据加载失败：{{ error }}</p>

    <section v-if="qualityRows.length" class="quality-band">
      <div v-for="row in qualityRows" :key="row.label" class="quality-item">
        <p class="quality-label">{{ row.label }}</p>
        <p class="quality-value">{{ row.value }}</p>
        <p class="quality-note">{{ row.note }}</p>
      </div>
    </section>

    <section class="method-section">
      <div class="section-side">
        <span class="section-no">01</span>
        <h2>数据范围</h2>
      </div>
      <dl class="definition-list">
        <dt>研究对象</dt>
        <dd>计算机类应届毕业生岗位，以及明确接受应届生投递的岗位</dd>
        <dt>地域范围</dt>
        <dd>杭州（单城市）</dd>
        <dt>时间范围</dt>
        <dd>演示数据采集日期 2026-11-13</dd>
        <dt>样本规模</dt>
        <dd>10 条演示记录；正式目标为 200～500 条可核验岗位</dd>
        <dt>来源</dt>
        <dd>演示数据（虚构）；正式采集优先使用公开招聘信息，逐条保留来源链接与采集时间</dd>
        <dt>岗位类别</dt>
        <dd>后端开发、前端开发、算法工程、数据分析、测试开发、大数据开发、运维开发、嵌入式开发</dd>
      </dl>
    </section>

    <section class="method-section">
      <div class="section-side">
        <span class="section-no">02</span>
        <h2>字段与清洗</h2>
      </div>
      <div>
        <div class="data-table-wrap">
          <table class="data-table fields-table">
            <caption class="sr-only">数据字段说明</caption>
            <thead>
              <tr>
                <th scope="col">字段</th>
                <th scope="col">说明</th>
                <th scope="col">约束</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="[field, description, rule] in fields" :key="field">
                <th scope="row"><code>{{ field }}</code></th>
                <td>{{ description }}</td>
                <td>{{ rule }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="section-note">
          导入时对学历、经验做别名归一，技能去重并保留首次写法；原始值仍保留在 JSON 文件中。学历统一为：不限 / 大专 / 本科 / 本科及以上 / 硕士 / 硕士及以上 / 博士 / 其他。经验统一为：不限 / 应届生 / 1年以内 / 1-3年 / 3-5年 / 5年以上 / 其他。
        </p>
      </div>
    </section>

    <section class="method-section">
      <div class="section-side">
        <span class="section-no">03</span>
        <h2>统计口径</h2>
      </div>
      <div class="caliber-list">
        <div>
          <h3>薪资</h3>
          <p>
            岗位月薪 =（salary_min + salary_max）/ 2。只有单边薪资时按已知边界计算；两端均为空（面议）则不进入薪资统计。13/14 薪不折算进月薪。
          </p>
        </div>
        <div>
          <h3>技能频率</h3>
          <p>
            包含某技能的岗位数 / 当前筛选后的岗位数，而不是关键词出现次数。技能类别覆盖同样以岗位计数；一条岗位可属于多个类别，类别覆盖率不可相加。
          </p>
        </div>
        <div>
          <h3>占比与分母</h3>
          <p>
            所有百分比都由后端返回的计数与分母计算，页面不自行更换分母。筛选后，图表与文字同步使用筛选后的样本量。
          </p>
        </div>
        <div>
          <h3>分位区间</h3>
          <p>
            P25、中位数、P75 均基于月薪中点。样本量很小时分位数不稳定，页面同时展示样本量，避免只读区间不看分母。
          </p>
        </div>
      </div>
    </section>

    <section class="method-section">
      <div class="section-side">
        <span class="section-no">04</span>
        <h2>局限与边界</h2>
      </div>
      <div class="limits">
        <p>
          样本只代表特定城市、特定招聘渠道与特定时间段的公开信息，不能推断全国就业市场，也不能推断未出现在样本中的企业。
        </p>
        <p>
          演示数据的岗位类别样本量只有 1–2 条，任何类别之间的差异都只是线索，不是稳定结论。正式采集后需要重新计算，并做人工抽样核验。
        </p>
        <p>
          招聘启事中的技能标签由人工归纳，可能受词表规模影响；词表之外的技术词会进入“其他”类别。技能覆盖率不等于企业真实的技术使用比例。
        </p>
        <p>
          本项目不采集个人联系方式，不绕过登录或反爬限制；数据仅用于课程数据分析与可视化展示。
        </p>
      </div>
    </section>

    <section class="method-section">
      <div class="section-side">
        <span class="section-no">05</span>
        <h2>复现与更新</h2>
      </div>
      <div class="reproduce">
        <p>在项目根目录执行一键启动，首次运行会自动准备 Python 与前端依赖：</p>
        <pre><code>npm run dev</code></pre>
        <p>重新导入演示数据（在 <code>backend/</code> 目录）：</p>
        <pre><code>python -m scripts.import_sample --on-conflict update</code></pre>
        <p class="section-note">
          更完整的架构、接口与统计定义见仓库 <code>docs/architecture.md</code> 与 <code>docs/data-dictionary.md</code>。
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.demo-banner {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 2rem;
  align-items: center;
  border-top: 2px solid var(--accent);
  border-bottom: 1px solid var(--hairline);
  padding: 1.75rem 0;
  margin-bottom: 1.5rem;
}

.demo-number {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
  color: var(--accent-display);
}

.demo-figure {
  font-family: var(--sans);
  font-size: clamp(4rem, 9vw, 6.5rem);
  font-weight: 600;
  letter-spacing: -0.06em;
  line-height: 0.85;
}

.demo-unit {
  font-size: 1rem;
  color: var(--muted);
}

.demo-copy {
  display: grid;
  gap: 0.45rem;
}

.demo-copy h2 {
  font-size: clamp(1.35rem, 3vw, 1.9rem);
}

.demo-copy p:last-child {
  color: var(--ink-soft);
  font-size: 0.92rem;
  max-width: 68ch;
}

.quality-band {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--hairline-strong);
  border-bottom: 1px solid var(--hairline-strong);
  margin-bottom: 3rem;
}

.quality-item {
  padding: 1rem 1.2rem;
  border-left: 1px solid var(--hairline);
}

.quality-item:first-child {
  border-left: 0;
  padding-left: 0;
}

.quality-label {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}

.quality-value {
  font-family: var(--sans);
  font-size: 1.4rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-top: 0.15rem;
}

.quality-note {
  font-size: 0.72rem;
  color: var(--muted);
  line-height: 1.5;
}

.method-section {
  display: grid;
  grid-template-columns: 12rem minmax(0, 1fr);
  gap: 2.5rem;
  padding: 2rem 0 2.5rem;
  border-top: 1px solid var(--hairline);
}

.section-side {
  display: grid;
  gap: 0.35rem;
  align-content: start;
}

.section-no {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  color: var(--accent-ink);
}

.section-side h2 {
  font-size: 1.35rem;
}

.section-note {
  margin-top: 0.9rem;
  font-size: 0.8rem;
  color: var(--muted);
  line-height: 1.7;
}

.fields-table tbody th {
  text-transform: none;
  letter-spacing: 0;
  font-family: var(--mono);
  font-size: 0.74rem;
  font-weight: 500;
  color: var(--ink);
}

.fields-table tbody th code {
  background: none;
  padding: 0;
}

.caliber-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem 2.5rem;
}

.caliber-list h3 {
  font-family: var(--sans);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-ink);
  margin-bottom: 0.35rem;
}

.caliber-list p {
  color: var(--ink-soft);
  font-size: 0.9rem;
}

.limits {
  display: grid;
  gap: 0.9rem;
  max-width: 70ch;
}

.limits p {
  color: var(--ink-soft);
  font-size: 0.92rem;
  padding-left: 1rem;
  border-left: 2px solid var(--hairline-strong);
}

.reproduce {
  display: grid;
  gap: 0.65rem;
  max-width: 66ch;
}

.reproduce p {
  font-size: 0.9rem;
  color: var(--ink-soft);
}

.reproduce pre {
  margin: 0;
  background: var(--ink);
  color: var(--paper);
  padding: 0.8rem 1rem;
  border-radius: 3px;
  overflow-x: auto;
}

.reproduce pre code {
  background: none;
  padding: 0;
  font-size: 0.8rem;
  color: inherit;
}

@media (max-width: 860px) {
  .quality-band {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .quality-item:nth-child(3) {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid var(--hairline);
  }

  .quality-item:nth-child(4) {
    border-top: 1px solid var(--hairline);
  }

  .method-section {
    grid-template-columns: 1fr;
    gap: 1.2rem;
  }

  .caliber-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .demo-banner {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .quality-band {
    grid-template-columns: 1fr;
  }

  .quality-item {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid var(--hairline);
  }

  .quality-item:first-child {
    border-top: 0;
  }
}
</style>
