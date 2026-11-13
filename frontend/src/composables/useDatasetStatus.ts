import { computed, ref } from 'vue'

import { fetchFilterMeta } from '@/api/meta'
import { fetchQualityStats } from '@/api/stats'
import type { FilterMeta, QualityStats } from '@/types/api'

/**
 * Shared dataset status. App.vue loads it once; pages read the same module-level
 * state. Demo mode is derived from the quality endpoint so replacing the data
 * removes the demo banner automatically. VITE_DEMO_MODE can force it either way.
 */
const quality = ref<QualityStats | null>(null)
const meta = ref<FilterMeta | null>(null)
const loading = ref(false)
const error = ref('')
let started = false

const forceDemo = import.meta.env.VITE_DEMO_MODE === 'true'
const forceReal = import.meta.env.VITE_DEMO_MODE === 'false'

const totalJobs = computed(() => quality.value?.total_jobs ?? 0)
const demoRecords = computed(() => quality.value?.demo_records ?? 0)
const hasDemoRecords = computed(() => !forceReal && demoRecords.value > 0)
const isDemoDataset = computed(
  () =>
    forceDemo ||
    (!forceReal &&
      demoRecords.value > 0 &&
      demoRecords.value === totalJobs.value),
)
const cityLabel = computed(() => {
  const cities = meta.value?.cities ?? []
  if (cities.length === 1) return cities[0]
  if (cities.length > 1) return '多城市'
  return '—'
})
const datasetLabel = computed(() => {
  if (isDemoDataset.value) return '演示样本 · 虚构数据'
  return totalJobs.value ? `样本 ${totalJobs.value} 条` : '样本数据'
})

async function load(): Promise<void> {
  if (started) return
  started = true
  loading.value = true
  error.value = ''
  try {
    const [qualityResult, metaResult] = await Promise.allSettled([
      fetchQualityStats(),
      fetchFilterMeta(),
    ])
    if (qualityResult.status === 'fulfilled') {
      quality.value = qualityResult.value
    } else {
      error.value =
        qualityResult.reason instanceof Error
          ? qualityResult.reason.message
          : '未知错误'
      started = false
    }
    if (metaResult.status === 'fulfilled') {
      meta.value = metaResult.value
    } else {
      // Keep charts usable; retry the shared meta load on the next call.
      started = false
    }
  } finally {
    loading.value = false
  }
}

export function useDatasetStatus() {
  return {
    quality,
    meta,
    loading,
    error,
    totalJobs,
    demoRecords,
    hasDemoRecords,
    isDemoDataset,
    cityLabel,
    datasetLabel,
    load,
  }
}
