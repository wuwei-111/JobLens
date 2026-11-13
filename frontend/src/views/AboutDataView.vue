<template>
  <section class="page-intro">
    <p class="eyebrow">数据说明</p>
    <h1>数据来源、口径与局限</h1>
    <p class="lead">
      数据新闻的可信度来自透明的采集与方法说明。本页将在正式数据采集完成后补齐具体数值与链接。
    </p>
  </section>

  <section class="panel">
    <h2>数据来源与采集</h2>
    <dl class="definition-list">
      <dt>研究城市</dt>
      <dd>待确定（建议只研究一个城市）</dd>
      <dt>岗位范围</dt>
      <dd>计算机类应届毕业生岗位及明确接受应届生投递的岗位</dd>
      <dt>数据来源</dt>
      <dd>公开招聘信息，逐条保留来源链接与采集时间</dd>
      <dt>样本规模</dt>
      <dd>目标 200～500 条有效记录；当前仓库仅包含 40 条虚构演示数据</dd>
    </dl>
  </section>

  <section class="panel">
    <h2>统计口径</h2>
    <ul class="plan-list">
      <li>薪资：月薪区间中点 =（salary_min + salary_max）/ 2；面议岗位不纳入薪资统计。</li>
      <li>技能频率：包含某技能的岗位数 / 有效岗位总数，而不是关键词出现次数。</li>
      <li>占比：均以后端返回的明确分母计算，页面不得自行更换分母。</li>
      <li>学历与经验：导入时按统一词表规范化，原始值仍保留在 JSON 数据文件中。</li>
    </ul>
  </section>

  <section class="panel">
    <h2>局限性</h2>
    <p>
      样本仅代表特定城市、特定招聘渠道与特定时间段的公开招聘信息，不能推断全国就业市场。
      所有结论均限定在本数据集范围内，并需在页面中展示样本量。
    </p>
    <p class="muted">
      详见 <code>docs/data-dictionary.md</code> 与 <code>docs/architecture.md</code>。
    </p>
  </section>
</template>
