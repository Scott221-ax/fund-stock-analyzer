<template>
  <div>
    <div class="page-header">
      <h2>持仓分析</h2>
      <p>持仓诊断、风险指标与优化建议</p>
    </div>

    <div class="kpi-grid">
      <KpiCard label="波动率" :value="`${risk.volatility}%`" sub="年化" icon="DataBoard" icon-bg="#f0f5ff" icon-color="#2f54eb" />
      <KpiCard label="最大回撤" :value="`${risk.max_drawdown}%`" icon="WarnTriangleFilled" icon-bg="#fff2f0" icon-color="#ff4d4f" />
      <KpiCard label="夏普比率" :value="risk.sharpe_ratio" icon="TrendCharts" icon-bg="#f6ffed" icon-color="#52c41a" />
      <KpiCard label="VaR(95%)" :value="`${risk.var_95}%`" sub="日风险价值" icon="Warning" icon-bg="#fff7e6" icon-color="#fa8c16" />
    </div>

    <div class="card-grid">
      <el-card shadow="never">
        <template #header><span style="font-weight: 600">行业暴露</span></template>
        <div class="chart-container">
          <v-chart :option="sectorOption" autoresize />
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header><span style="font-weight: 600">持仓重叠</span></template>
        <el-table :data="overlaps" size="small" stripe>
          <el-table-column prop="stock" label="股票" width="120" />
          <el-table-column prop="funds" label="持有基金数" width="120" />
          <el-table-column prop="total_ratio" label="总占比(%)">
            <template #default="{ row }">{{ row.total_ratio }}%</template>
          </el-table-column>
        </el-table>
        <div v-if="!overlaps.length" style="text-align:center;padding:40px;color:#999">暂无重叠数据</div>
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header><span style="font-weight: 600">调仓建议</span></template>
      <el-empty description="接入完整分析数据后生成调仓建议" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'
import KpiCard from '@/components/KpiCard.vue'
import { portfolioApi } from '@/api'

const sectors = ref([])
const overlaps = ref([])
const risk = ref({ volatility: 0, max_drawdown: 0, sharpe_ratio: 0, var_95: 0 })

const sectorOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  yAxis: {
    type: 'category',
    data: sectors.value.map(s => s.sector).reverse(),
    axisLine: { show: false },
  },
  series: [{
    type: 'bar',
    data: sectors.value.map(s => s.ratio).reverse(),
    barWidth: '60%',
    itemStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
        { offset: 0, color: '#409eff' },
        { offset: 1, color: '#7ec2f3' },
      ]),
      borderRadius: [0, 4, 4, 0],
    },
    label: { show: true, position: 'right', formatter: '{c}%' },
  }],
}))

import * as echarts from 'echarts'

onMounted(async () => {
  try {
    const [secRes, ovlRes, riskRes] = await Promise.all([
      portfolioApi.sectors(),
      portfolioApi.overlap(),
      portfolioApi.risk(),
    ])
    sectors.value = secRes.data || []
    overlaps.value = ovlRes.data || []
    risk.value = riskRes.data || {}
  } catch (e) {
    console.error('持仓分析加载失败:', e)
  }
})
</script>
