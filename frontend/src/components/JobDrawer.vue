<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

import { fetchJobs } from '@/api/jobs'
import { formatSalaryRange } from '@/lib/format'
import type { JobOut, JobQuery } from '@/types/api'

const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    query?: JobQuery
  }>(),
  {
    title: '匹配岗位',
    query: () => ({}),
  },
)

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const jobs = ref<JobOut[]>([])
const loading = ref(false)
const error = ref('')
const closeButton = ref<HTMLButtonElement | null>(null)
const drawerRef = ref<HTMLElement | null>(null)
let previousBodyOverflow = ''
let previousFocus: HTMLElement | null = null
let loadedQueryKey = ''

const statusText = computed(() => {
  if (loading.value) return '正在加载岗位'
  if (error.value) return `加载失败：${error.value}`
  return `共 ${jobs.value.length} 条岗位`
})

async function loadForCurrentQuery() {
  loadedQueryKey = JSON.stringify(props.query)
  loading.value = true
  error.value = ''
  try {
    const result = await fetchJobs({ ...props.query, page_size: 50 })
    jobs.value = result.items
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '未知错误'
    jobs.value = []
  } finally {
    loading.value = false
  }
}

function close() {
  emit('update:open', false)
}

function onKeydown(event: KeyboardEvent) {
  if (!props.open) return
  if (event.key === 'Escape') {
    close()
    return
  }
  if (event.key !== 'Tab' || !drawerRef.value) return

  const focusable = Array.from(
    drawerRef.value.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  )
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      previousFocus = document.activeElement as HTMLElement | null
      previousBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', onKeydown)
      loadedQueryKey = ''
      await loadForCurrentQuery()
      await nextTick()
      closeButton.value?.focus()
    } else {
      document.body.style.overflow = previousBodyOverflow
      window.removeEventListener('keydown', onKeydown)
      previousFocus?.focus()
    }
  },
  { immediate: true },
)

watch(
  () => JSON.stringify(props.query),
  (key) => {
    if (props.open && key !== loadedQueryKey) void loadForCurrentQuery()
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = previousBodyOverflow
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="drawer-backdrop" @click.self="close">
        <aside
          ref="drawerRef"
          class="drawer"
          role="dialog"
          aria-modal="true"
          aria-labelledby="job-drawer-title"
        >
          <header class="drawer-head">
            <div>
              <p class="eyebrow">岗位样本 / JOBS</p>
              <h2 id="job-drawer-title">{{ title }}</h2>
              <p class="drawer-sub" aria-live="polite">{{ statusText }}</p>
            </div>
            <button
              ref="closeButton"
              type="button"
              class="drawer-close"
              aria-label="关闭岗位列表"
              @click="close"
            >
              ×
            </button>
          </header>

          <div class="drawer-body">
            <p v-if="loading" class="drawer-status">正在读取岗位…</p>
            <p v-else-if="error" class="drawer-status drawer-error">
              数据加载失败：{{ error }}
            </p>
            <p v-else-if="!jobs.length" class="drawer-status">
              当前没有匹配岗位。
            </p>

            <article v-for="job in jobs" :key="job.id" class="job-card">
              <header class="job-card-head">
                <h3>{{ job.position }}</h3>
                <p class="job-company">{{ job.company }}</p>
              </header>

              <p class="job-meta">
                <span>{{ job.job_type }}</span>
                <span>{{ job.city }}</span>
                <span>{{ formatSalaryRange(job.salary_min, job.salary_max) }}</span>
                <span>{{ job.education }} · {{ job.experience }}</span>
              </p>

              <p v-if="job.description" class="job-description">
                {{ job.description }}
              </p>

              <ul v-if="job.skills.length" class="job-skills">
                <li v-for="skill in job.skills" :key="skill">{{ skill }}</li>
              </ul>

              <a
                v-if="job.source_url"
                class="job-source"
                :href="job.source_url"
                target="_blank"
                rel="noopener noreferrer"
              >
                查看原始招聘 <span aria-hidden="true">→</span>
              </a>
            </article>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  justify-content: flex-end;
  background: rgba(32, 37, 43, 0.38);
  backdrop-filter: blur(2px);
}

.drawer {
  display: flex;
  flex-direction: column;
  width: min(92vw, 580px);
  height: 100%;
  background: var(--paper);
  border-left: 1px solid var(--hairline-strong);
  box-shadow: -24px 0 60px rgba(32, 37, 43, 0.14);
}

.drawer-head {
  position: relative;
  display: grid;
  gap: 0.35rem;
  padding: 1.5rem 1.5rem 1.1rem;
  border-bottom: 2px solid var(--ink);
  background: var(--paper);
}

.drawer-head h2 {
  font-size: clamp(1.45rem, 3vw, 2rem);
  padding-right: 2.5rem;
}

.drawer-sub {
  font-family: var(--mono);
  font-size: 0.64rem;
  letter-spacing: 0.04em;
  color: var(--muted);
}

.drawer-close {
  position: absolute;
  top: 1.3rem;
  right: 1.3rem;
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border: 1px solid var(--hairline-strong);
  border-radius: 2px;
  background: transparent;
  color: var(--ink);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  transition: background 150ms ease, color 150ms ease;
}

.drawer-close:hover {
  background: var(--ink);
  color: var(--paper);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 1.5rem 2.5rem;
}

.drawer-status {
  color: var(--muted);
  font-size: 0.9rem;
  padding: 1.5rem 0;
}

.drawer-error {
  color: var(--danger);
}

.job-card {
  padding: 1.25rem 0 1.35rem;
  border-top: 1px solid var(--hairline);
}

.job-card:first-of-type {
  border-top: 0;
}

.job-card-head {
  display: grid;
  gap: 0.15rem;
}

.job-card-head h3 {
  font-size: 1.15rem;
}

.job-company {
  font-family: var(--mono);
  font-size: 0.64rem;
  letter-spacing: 0.04em;
  color: var(--muted);
}

.job-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem 0.8rem;
  margin-top: 0.55rem;
  font-family: var(--mono);
  font-size: 0.64rem;
  color: var(--ink-soft);
}

.job-meta span + span::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 3px;
  margin-right: 0.8rem;
  border-radius: 50%;
  background: var(--hairline-strong);
  vertical-align: 0.2em;
}

.job-description {
  margin-top: 0.6rem;
  color: var(--ink-soft);
  font-size: 0.86rem;
  line-height: 1.7;
}

.job-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  list-style: none;
  padding: 0;
  margin: 0.65rem 0 0;
}

.job-skills li {
  font-family: var(--mono);
  font-size: 0.58rem;
  color: var(--muted);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  padding: 0.1rem 0.4rem;
}

.job-source {
  display: inline-block;
  margin-top: 0.7rem;
  color: var(--accent-ink);
  font-size: 0.76rem;
  text-decoration: none;
  border-bottom: 1px solid rgba(231, 111, 81, 0.45);
}

.job-source span {
  display: inline-block;
  transition: transform 150ms ease;
}

.job-source:hover span {
  transform: translateX(3px);
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 200ms ease;
}

.drawer-enter-active .drawer,
.drawer-leave-active .drawer {
  transition: transform 260ms cubic-bezier(0.2, 0.7, 0.2, 1);
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .drawer,
.drawer-leave-to .drawer {
  transform: translateX(100%);
}

@media (max-width: 640px) {
  .drawer {
    width: 100%;
  }

  .drawer-head {
    padding: 1.2rem 1rem 1rem;
  }

  .drawer-close {
    top: 1rem;
    right: 1rem;
  }

  .drawer-body {
    padding: 0 1rem 2rem;
  }
}
</style>
