<template>
  <section class="page-intro">
    <p class="eyebrow">第二部分</p>
    <h1>学历与经验：进入企业的第一道门槛</h1>
    <p class="lead">
      企业对应届生的学历要求如何分布？标注“接受应届生”的岗位，是否仍然要求实习或项目经验？
    </p>
  </section>

  <section class="panel">
    <h2>规划中的图表</h2>
    <ul class="plan-list">
      <li>学历要求分布环形图</li>
      <li>不同岗位类别的学历要求对比柱状图</li>
      <li>工作经验要求分布横向柱状图</li>
      <li>应届生岗位的经验要求对比图</li>
    </ul>
    <p class="muted">
      数据接口已就绪：<code>GET /api/v1/stats/education</code> 与
      <code>GET /api/v1/stats/experience</code>，支持岗位类别、学历、经验、城市筛选。
      页面图表与新闻解读待实现。
    </p>
  </section>
</template>
