<template>
  <section class="page-intro">
    <p class="eyebrow">第三部分</p>
    <h1>技能：企业究竟需要什么样的技术人才？</h1>
    <p class="lead">
      编程语言、开发框架、数据库与工具中，哪些技能出现频率最高？不同岗位类别的技能要求有何差异？
    </p>
  </section>

  <section class="panel">
    <h2>规划中的图表</h2>
    <ul class="plan-list">
      <li>高频技能排行榜（条形图）</li>
      <li>技能类别分布图</li>
      <li>不同岗位类别技能需求对比（分组柱状图 / 热力图）</li>
      <li>岗位详情中的技能标签</li>
    </ul>
    <p class="muted">
      数据接口已就绪：<code>GET /api/v1/stats/skills</code>，可返回总体排行、技能类别、
      分岗位类别 Top 技能以及明确的岗位占比分母。
    </p>
  </section>
</template>
