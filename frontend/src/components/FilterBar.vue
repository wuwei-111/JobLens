<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { useDatasetStatus } from '@/composables/useDatasetStatus'
import { hasFilters, type FilterKey } from '@/lib/filters'
import type { StatsFilters } from '@/types/api'

const props = withDefaults(
  defineProps<{
    modelValue: StatsFilters
    total?: number | null
  }>(),
  { total: null },
)

const emit = defineEmits<{
  'update:modelValue': [value: StatsFilters]
}>()

const { meta, load } = useDatasetStatus()

onMounted(() => {
  void load()
})

// Keep a local draft so two rapid select changes merge instead of overwriting
// each other with a stale prop object.
const draft = ref<StatsFilters>({ ...props.modelValue })

watch(
  () => props.modelValue,
  (value) => {
    draft.value = { ...value }
  },
  { deep: true },
)

const controls = computed<
  { key: FilterKey; label: string; all: string; options: string[] }[]
>(() => [
  {
    key: 'job_type',
    label: '岗位类别',
    all: '全部岗位',
    options: meta.value?.job_types ?? [],
  },
  {
    key: 'education',
    label: '学历',
    all: '全部学历',
    options: meta.value?.educations ?? [],
  },
  {
    key: 'experience',
    label: '经验',
    all: '全部经验',
    options: meta.value?.experiences ?? [],
  },
  {
    key: 'city',
    label: '城市',
    all: '全部城市',
    options: meta.value?.cities ?? [],
  },
])

// Some experience values are raw JD excerpts (up to 200 chars). Keep the
// value intact for filtering but shorten the option label.
function optionLabel(value: string): string {
  return value.length > 28 ? `${value.slice(0, 28)}…` : value
}

function update(key: FilterKey, event: Event) {
  const value = (event.target as HTMLSelectElement).value
  const next = { ...draft.value } as StatsFilters
  const mutable = next as Record<string, string | undefined>
  if (value) mutable[key] = value
  else delete mutable[key]
  draft.value = next
  emit('update:modelValue', next)
}

function clear() {
  draft.value = {}
  emit('update:modelValue', {})
}
</script>

<template>
  <div class="filter-bar">
    <div
      v-for="control in controls"
      :key="control.key"
      class="filter-control"
    >
      <label :for="`filter-${control.key}`">{{ control.label }}</label>
      <select
        :id="`filter-${control.key}`"
        :value="draft[control.key] ?? ''"
        @change="update(control.key, $event)"
      >
        <option value="">{{ control.all }}</option>
        <option
          v-for="option in control.options"
          :key="option"
          :value="option"
        >
          {{ optionLabel(option) }}
        </option>
      </select>
    </div>

    <p class="filter-sample" aria-live="polite">
      当前样本 <strong>{{ props.total ?? '—' }}</strong> 条
    </p>

    <button
      v-if="hasFilters(draft)"
      type="button"
      class="filter-reset"
      @click="clear"
    >
      清除筛选
    </button>
  </div>
</template>
