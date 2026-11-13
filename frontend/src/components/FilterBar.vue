<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchFilterMeta } from '@/api/meta'
import type { FilterMeta } from '@/types/api'

const props = withDefaults(
  defineProps<{
    modelValue: string
    total?: number | null
  }>(),
  { total: null },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const meta = ref<FilterMeta | null>(null)

onMounted(async () => {
  try {
    meta.value = await fetchFilterMeta()
  } catch {
    // A missing meta endpoint should not block the charts; keep “全部岗位”.
    meta.value = null
  }
})

function onChange(event: Event) {
  emit('update:modelValue', (event.target as HTMLSelectElement).value)
}
</script>

<template>
  <div class="filter-bar">
    <div class="filter-control">
      <label for="job-type-filter">岗位类别</label>
      <select id="job-type-filter" :value="props.modelValue" @change="onChange">
        <option value="">全部岗位</option>
        <option
          v-for="jobType in meta?.job_types ?? []"
          :key="jobType"
          :value="jobType"
        >
          {{ jobType }}
        </option>
      </select>
    </div>

    <p class="filter-sample">
      当前样本 <strong>{{ props.total ?? '—' }}</strong> 条
    </p>

    <button
      v-if="props.modelValue"
      type="button"
      class="filter-reset"
      @click="emit('update:modelValue', '')"
    >
      清除筛选
    </button>
  </div>
</template>
