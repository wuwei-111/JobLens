<script setup lang="ts">
import { computed, ref, useSlots } from 'vue'

defineProps<{
  index: string
  title: string
  question?: string
  note?: string
}>()

const slots = useSlots()
const hasTable = computed(() => Boolean(slots.table))
const showTable = ref(false)
</script>

<template>
  <figure class="chart-card" :aria-label="title">
    <header class="chart-head">
      <p class="chart-index">{{ index }}</p>
      <div class="chart-heading">
        <h3>{{ title }}</h3>
        <p v-if="question" class="chart-question">{{ question }}</p>
      </div>
      <div v-if="hasTable" class="view-toggle" role="group" aria-label="视图切换">
        <button
          type="button"
          :class="{ active: !showTable }"
          :aria-pressed="!showTable"
          @click="showTable = false"
        >
          图表
        </button>
        <button
          type="button"
          :class="{ active: showTable }"
          :aria-pressed="showTable"
          @click="showTable = true"
        >
          数据表
        </button>
      </div>
    </header>

    <div v-show="!showTable" class="chart-body">
      <slot />
    </div>
    <div v-show="showTable" class="chart-body chart-table">
      <slot name="table" />
    </div>

    <div v-if="slots.insight" class="chart-insight">
      <slot name="insight" />
    </div>

    <figcaption v-if="note" class="chart-note">{{ note }}</figcaption>
  </figure>
</template>

<style scoped>
.chart-card {
  display: grid;
  border-top: 2px solid var(--ink);
  padding-top: 1rem;
  margin: 0;
  scroll-margin-top: 6rem;
}

.chart-head {
  display: grid;
  grid-template-columns: 3.4rem minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: start;
  padding-bottom: 0.75rem;
}

.chart-index {
  font-family: var(--mono);
  font-size: 0.66rem;
  letter-spacing: 0.1em;
  color: var(--accent-ink);
  padding-top: 0.5rem;
  white-space: nowrap;
}

.chart-heading {
  display: grid;
  gap: 0.25rem;
}

.chart-heading h3 {
  font-size: clamp(1.2rem, 2.2vw, 1.5rem);
}

.chart-question {
  color: var(--muted);
  font-size: 0.85rem;
  line-height: 1.6;
  max-width: 58ch;
}

.view-toggle {
  display: inline-flex;
  border: 1px solid var(--hairline-strong);
  border-radius: 2px;
  overflow: hidden;
}

.view-toggle button {
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 0.68rem;
  font-family: var(--mono);
  letter-spacing: 0.06em;
  padding: 0.3rem 0.65rem;
  cursor: pointer;
  transition: background 140ms ease, color 140ms ease;
}

.view-toggle button + button {
  border-left: 1px solid var(--hairline-strong);
}

.view-toggle button.active {
  background: var(--ink);
  color: var(--paper);
}

.view-toggle button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.chart-body {
  padding: 1rem 1rem 0.75rem;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: 6px;
}

.chart-table {
  padding: 0.4rem 0.55rem;
}

.chart-insight {
  position: relative;
  border-top: 1px solid var(--hairline);
  padding: 0.9rem 0 0 3.2rem;
  color: var(--ink-soft);
  font-size: 0.92rem;
  line-height: 1.75;
  display: grid;
  gap: 0.4rem;
}

.chart-insight::before {
  content: '解读';
  position: absolute;
  left: 0;
  top: 0.98rem;
  font-family: var(--mono);
  font-size: 0.6rem;
  letter-spacing: 0.12em;
  color: var(--accent-ink);
}

.chart-insight :deep(strong) {
  color: var(--ink);
  font-weight: 600;
}

.chart-note {
  margin-top: 0.8rem;
  font-size: 0.72rem;
  line-height: 1.6;
  color: var(--faint);
  border-top: 1px dotted var(--hairline);
  padding-top: 0.6rem;
}

@media (max-width: 640px) {
  .chart-head {
    grid-template-columns: 1fr auto;
    gap: 0.5rem 0.75rem;
  }

  .chart-body {
    padding: 0.6rem;
  }

  .chart-index {
    grid-column: 1 / -1;
    padding-top: 0;
  }

  .chart-heading {
    grid-column: 1;
  }

  .view-toggle {
    align-self: start;
  }

  .chart-insight {
    padding-left: 0;
    padding-top: 1.9rem;
  }

  .chart-insight::before {
    top: 0.7rem;
  }
}
</style>
