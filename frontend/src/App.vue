<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/education-experience', label: '学历与经验' },
  { to: '/skills', label: '技能需求' },
  { to: '/salary', label: '薪资待遇' },
  { to: '/about-data', label: '数据说明' },
]
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">JL</span>
        <span>JobLens</span>
      </RouterLink>
      <nav class="site-nav" aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to">
          {{ item.label }}
        </RouterLink>
      </nav>
    </header>

    <main class="site-main">
      <RouterView />
    </main>

    <footer class="site-footer">
      <p>数据新闻课程项目 · 样本数据不代表整体就业市场</p>
    </footer>
  </div>
</template>
