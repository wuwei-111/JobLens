<template>
  <section class="page-intro">
    <p class="eyebrow">第四部分</p>
    <h1>薪资：不同岗位的待遇差异</h1>
    <p class="lead">
      样本岗位的月薪如何分布？不同技术方向、学历要求与经验要求对应的薪资水平有何差异？
    </p>
  </section>

  <section class="panel">
    <h2>规划中的图表</h2>
    <ul class="plan-list">
      <li>整体薪资分布直方图（固定区间，单位为月薪）</li>
      <li>不同岗位类别薪资对比图（均值 / 中位数）</li>
      <li>不同学历要求的薪资箱线图</li>
      <li>不同经验要求岗位的薪资差异图</li>
    </ul>
    <p class="muted">
      数据接口已就绪：<code>GET /api/v1/stats/salary</code>。薪资口径为月薪区间中点，
      面议岗位不参与薪资统计。页面筛选与图表待实现。
    </p>
  </section>
</template>
