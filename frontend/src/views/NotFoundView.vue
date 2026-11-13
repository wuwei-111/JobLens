<template>
  <section class="page-intro">
    <p class="eyebrow">404</p>
    <h1>页面不存在</h1>
    <p class="lead">你访问的页面可能已移动或尚未实现。</p>
    <RouterLink class="text-link" to="/">返回首页</RouterLink>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
