<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'

import { useDatasetStatus } from '@/composables/useDatasetStatus'

const navItems = [
  { to: '/', label: '首页', index: '01' },
  { to: '/education-experience', label: '学历与经验', index: '02' },
  { to: '/skills', label: '技能需求', index: '03' },
  { to: '/salary', label: '薪资待遇', index: '04' },
  { to: '/about-data', label: '数据说明', index: '05' },
]

const {
  isDemoDataset,
  hasDemoRecords,
  demoRecords,
  totalJobs,
  cityLabel,
  loading: statusLoading,
  load,
} = useDatasetStatus()

onMounted(() => {
  void load()
})

const footerSample = computed(() => {
  if (statusLoading.value && !totalJobs.value) return '数据加载中'
  if (!totalJobs.value) return '数据集未导入'
  return `${isDemoDataset.value ? '演示样本' : '样本'} ${totalJobs.value} 条 · ${cityLabel.value}`
})
</script>

<template>
  <div class="app-shell">
    <a class="skip-link" href="#main-content">跳到主内容</a>

    <p v-if="isDemoDataset" class="demo-strip">
      <span class="demo-dot" aria-hidden="true" />
      <span>演示数据 · {{ demoRecords }} 条虚构招聘记录，仅用于界面与流程展示</span>
      <RouterLink to="/about-data">查看数据说明</RouterLink>
    </p>
    <p v-else-if="hasDemoRecords" class="demo-strip">
      <span class="demo-dot" aria-hidden="true" />
      <span>数据提醒 · 当前数据集含 {{ demoRecords }} 条演示记录</span>
      <RouterLink to="/about-data">查看数据说明</RouterLink>
    </p>

    <header class="site-header">
      <div class="header-inner">
        <RouterLink class="brand" to="/">
          <span class="brand-mark">JL</span>
          <span class="brand-text">
            <span class="brand-name">JobLens</span>
            <span class="brand-sub">DATA JOURNALISM</span>
          </span>
        </RouterLink>

        <nav class="site-nav" aria-label="主导航">
          <RouterLink v-for="item in navItems" :key="item.to" :to="item.to">
            <span class="nav-index" aria-hidden="true">{{ item.index }}</span>
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>
    </header>

    <main id="main-content" class="site-main" tabindex="-1">
      <RouterView />
    </main>

    <footer class="site-footer">
      <div class="footer-inner">
        <div>
          <p class="footer-brand">JobLens · 招聘观察</p>
          <p>
            一个以数据分析和新闻叙事为核心的交互式数据新闻作品。样本数据不代表整体就业市场。
          </p>
        </div>
        <div class="footer-meta">
          <span>计算机类应届生招聘调查</span>
          <span>{{ footerSample }}</span>
          <span>2026.11</span>
        </div>
      </div>
    </footer>
  </div>
</template>
