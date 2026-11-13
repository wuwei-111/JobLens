<script setup lang="ts">
defineProps<{
  items: { label: string; value: string; hint?: string }[]
}>()
</script>

<template>
  <div class="kpi-band" role="list">
    <article v-for="item in items" :key="item.label" class="kpi" role="listitem">
      <p class="kpi-label">{{ item.label }}</p>
      <p class="kpi-value">{{ item.value }}</p>
      <p v-if="item.hint" class="kpi-hint">{{ item.hint }}</p>
    </article>
  </div>
</template>
