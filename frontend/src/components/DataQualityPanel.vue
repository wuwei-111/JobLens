<script setup lang="ts">
import { computed } from 'vue'

import { formatDateTime, formatPercent } from '@/lib/format'
import type { ImportBatch, QualityStats } from '@/types/api'

const props = defineProps<{
  quality: QualityStats | null
  batches: ImportBatch[]
  csvHref: string
}>()

const unknownEducation = computed(() =>
  (props.quality?.unknown_education ?? []).reduce(
    (sum, item) => sum + item.count,
    0,
  ),
)
const unknownExperience = computed(() =>
  (props.quality?.unknown_experience ?? []).reduce(
    (sum, item) => sum + item.count,
    0,
  ),
)
const unknownTotal = computed(
  () => unknownEducation.value + unknownExperience.value,
)
const warnings = computed(() => props.quality?.warnings ?? [])
const duplicateLinks = computed(
  () => props.quality?.duplicate_source_urls.length ?? 0,
)

const checks = computed(() => {
  const data = props.quality
  if (!data) return []
  return [
    {
      key: 'salary_missing',
      label: '面议薪资',
      value: data.salary_missing,
      note: '两端为空，不进入薪资统计',
    },
    {
      key: 'salary_single_bound',
      label: '单边薪资',
      value: data.salary_single_bound,
      note: '只有一边薪资，按已知边界计算',
    },
    {
      key: 'salary_outliers',
      label: '薪资异常',
      value: data.salary_outliers,
      note: '已知边界 < 2,000 或 > 100,000 元/月',
    },
    {
      key: 'unknown_education',
      label: '未知学历',
      value: unknownEducation.value,
      note: '不在规范词表内，导入后原样保留',
    },
    {
      key: 'unknown_experience',
      label: '未知经验',
      value: unknownExperience.value,
      note: '不在规范词表内，导入后原样保留',
    },
    {
      key: 'jobs_without_skills',
      label: '空技能',
      value: data.jobs_without_skills,
      note: '没有任何技能标签的岗位',
    },
    {
      key: 'duplicate_source_urls',
      label: '重复来源链接',
      value: duplicateLinks.value,
      note: '同一链接出现在多条岗位中',
    },
    {
      key: 'demo_records',
      label: '演示记录',
      value: data.demo_records,
      note: '演示数据不能用于新闻结论',
    },
  ]
})

const totalJobs = computed(() => props.quality?.total_jobs ?? 0)
const salaryAvailable = computed(() => props.quality?.salary_available ?? 0)
</script>

<template>
  <section class="quality-panel">
    <header class="quality-head">
      <p class="eyebrow">数据质量 / QUALITY</p>
      <h2>这份数据有多干净？</h2>
      <p>
        质量摘要来自 <code>GET /stats/quality</code>。它检查已入库数据，不替代人工抽样核验。
      </p>
    </header>

    <template v-if="quality">
      <div class="quality-tiles">
        <article class="quality-tile">
          <p class="quality-label">有效岗位</p>
          <p class="quality-value">{{ totalJobs }}</p>
          <p class="quality-hint">
            {{ quality.total_companies }} 家企业 ·
            {{ quality.total_cities }} 个城市
          </p>
        </article>
        <article class="quality-tile">
          <p class="quality-label">薪资有效</p>
          <p class="quality-value">
            {{ salaryAvailable }} / {{ totalJobs }}
          </p>
          <p class="quality-hint">
            面议 {{ quality.salary_missing }} 条 ·
            {{ formatPercent(totalJobs ? salaryAvailable / totalJobs : 0) }}
          </p>
        </article>
        <article class="quality-tile">
          <p class="quality-label">未知枚举</p>
          <p class="quality-value">{{ unknownTotal }}</p>
          <p class="quality-hint">
            学历 {{ unknownEducation }} · 经验 {{ unknownExperience }}
          </p>
        </article>
        <article class="quality-tile" :class="{ attention: warnings.length }">
          <p class="quality-label">质量警告</p>
          <p class="quality-value">{{ warnings.length }}</p>
          <p class="quality-hint">
            {{ warnings.length ? '需要人工复核' : '未发现明显问题' }}
          </p>
        </article>
      </div>

      <div class="quality-body">
        <div class="quality-checks">
          <h3>检查项</h3>
          <div class="data-table-wrap">
            <table class="data-table">
              <caption class="sr-only">数据质量检查项</caption>
              <thead>
                <tr>
                  <th scope="col">检查项</th>
                  <th scope="col" class="num">数量</th>
                  <th scope="col">状态</th>
                  <th scope="col">说明</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="check in checks" :key="check.key">
                  <th scope="row">{{ check.label }}</th>
                  <td class="num">{{ check.value }}</td>
                  <td>
                    <span
                      class="status-tag"
                      :data-tone="check.value > 0 ? 'warn' : 'ok'"
                    >
                      {{ check.value > 0 ? '! 注意' : '✓ 正常' }}
                    </span>
                  </td>
                  <td class="check-note">{{ check.note }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <aside class="quality-warnings" aria-label="质量警告">
          <h3>警告</h3>
          <ul v-if="warnings.length">
            <li v-for="warning in warnings" :key="warning">{{ warning }}</li>
          </ul>
          <p v-else class="quality-clean">未发现明显质量问题。</p>
          <a class="download-link" :href="csvHref" download>
            下载岗位 CSV <span aria-hidden="true">→</span>
          </a>
          <p class="quality-source">
            CSV 含当前全部岗位；如需按筛选导出，可在地址后附加
            <code>?job_type=...</code> 等参数。
          </p>
        </aside>
      </div>

      <section class="batch-section">
        <div class="batch-head">
          <h3>导入批次</h3>
          <p>批次记录写入 <code>import_batches</code>，用于复现与交付说明。</p>
        </div>
        <div v-if="batches.length" class="data-table-wrap">
          <table class="data-table">
            <caption class="sr-only">最近导入批次</caption>
            <thead>
              <tr>
                <th scope="col">批次</th>
                <th scope="col">数据集 / 文件</th>
                <th scope="col" class="num">导入</th>
                <th scope="col" class="num">更新</th>
                <th scope="col" class="num">跳过</th>
                <th scope="col" class="num">失败</th>
                <th scope="col">时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="batch in batches" :key="batch.id">
                <td class="num">#{{ batch.id }}</td>
                <th scope="row" class="batch-name">
                  {{ batch.dataset_name || '未命名数据集' }}
                  <small>{{ batch.source_file || '—' }}</small>
                </th>
                <td class="num">{{ batch.imported }}</td>
                <td class="num">{{ batch.updated }}</td>
                <td class="num">{{ batch.skipped }}</td>
                <td class="num">{{ batch.failed }}</td>
                <td class="batch-time">{{ formatDateTime(batch.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="quality-clean">暂无导入批次记录。</p>
      </section>
    </template>

    <p v-else class="quality-status">质量摘要加载中…</p>
  </section>
</template>

<style scoped>
.quality-panel {
  display: grid;
  gap: 1.5rem;
  min-width: 0;
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid var(--ink);
}

.quality-head {
  display: grid;
  gap: 0.45rem;
  max-width: 68ch;
}

.quality-head h2 {
  font-size: clamp(1.5rem, 3vw, 2rem);
}

.quality-head p {
  color: var(--muted);
  font-size: 0.9rem;
}

.quality-status {
  color: var(--muted);
  font-size: 0.9rem;
  padding: 1rem 0;
}

.quality-tiles {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--hairline-strong);
  border-bottom: 1px solid var(--hairline-strong);
}

.quality-tile {
  padding: 1rem 1.2rem;
  border-left: 1px solid var(--hairline);
}

.quality-tile:first-child {
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
  margin-top: 0.15rem;
  font-family: var(--sans);
  font-size: 1.9rem;
  font-weight: 600;
  letter-spacing: -0.035em;
  line-height: 1.1;
}

.quality-hint {
  font-size: 0.72rem;
  color: var(--muted);
  line-height: 1.5;
}

.quality-tile.attention .quality-value {
  color: var(--accent-ink);
}

.quality-body {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(16rem, 0.75fr);
  gap: 2.5rem;
  min-width: 0;
  align-items: start;
}

.quality-checks,
.quality-warnings,
.batch-section {
  min-width: 0;
}

.quality-checks h3,
.quality-warnings h3,
.batch-section h3 {
  font-family: var(--sans);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink);
  margin-bottom: 0.7rem;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-family: var(--mono);
  font-size: 0.58rem;
  letter-spacing: 0.02em;
  border: 1px solid var(--hairline-strong);
  border-radius: 999px;
  padding: 0.08rem 0.4rem;
  white-space: nowrap;
}

.status-tag[data-tone='ok'] {
  color: var(--green-ink);
  border-color: rgba(46, 117, 101, 0.35);
}

.status-tag[data-tone='warn'] {
  color: var(--accent-ink);
  border-color: rgba(179, 68, 47, 0.35);
}

.check-note {
  color: var(--muted);
  font-size: 0.78rem;
  min-width: 12rem;
}

.quality-warnings {
  border-left: 2px solid var(--accent);
  padding-left: 1.1rem;
}

.quality-warnings ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.65rem;
}

.quality-warnings li {
  position: relative;
  padding-left: 1rem;
  color: var(--ink-soft);
  font-size: 0.84rem;
  line-height: 1.7;
}

.quality-warnings li::before {
  content: '!';
  position: absolute;
  left: 0;
  top: 0.2rem;
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--accent-ink);
}

.quality-clean {
  color: var(--green-ink);
  font-size: 0.84rem;
}

.download-link {
  display: inline-block;
  margin-top: 1.1rem;
  background: var(--ink);
  color: var(--paper);
  text-decoration: none;
  padding: 0.55rem 0.9rem;
  font-size: 0.78rem;
  letter-spacing: 0.02em;
}

.download-link span {
  display: inline-block;
  transition: transform 150ms ease;
}

.download-link:hover span {
  transform: translateX(3px);
}

.quality-source {
  margin-top: 0.7rem;
  font-size: 0.7rem;
  line-height: 1.6;
  color: var(--faint);
}

.batch-section {
  border-top: 1px solid var(--hairline);
  padding-top: 1.25rem;
}

.batch-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.batch-head p {
  color: var(--muted);
  font-size: 0.75rem;
}

.batch-name {
  font-family: var(--sans) !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
  color: var(--ink) !important;
}

.batch-name small {
  display: block;
  font-family: var(--mono);
  font-size: 0.62rem;
  font-weight: 400;
  color: var(--faint);
}

.batch-time {
  font-family: var(--mono);
  font-size: 0.66rem;
  color: var(--muted);
  white-space: nowrap;
}

@media (max-width: 860px) {
  .quality-tiles {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .quality-tile:nth-child(3) {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid var(--hairline);
  }

  .quality-tile:nth-child(4) {
    border-top: 1px solid var(--hairline);
  }

  .quality-body {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .quality-warnings {
    border-left: 0;
    border-top: 1px solid var(--hairline-strong);
    padding: 1rem 0 0;
  }
}

@media (max-width: 640px) {
  .quality-checks .data-table th:last-child,
  .quality-checks .data-table td:last-child {
    display: none;
  }
}

@media (max-width: 560px) {
  .quality-tiles {
    grid-template-columns: 1fr;
  }

  .quality-tile {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid var(--hairline);
  }

  .quality-tile:first-child {
    border-top: 0;
  }

  .quality-value {
    font-size: 1.7rem;
  }
}
</style>
