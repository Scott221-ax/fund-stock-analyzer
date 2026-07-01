<template>
  <div>
    <div class="page-header">
      <h2>总览</h2>
      <p>持仓总览与市场速览</p>
    </div>

    <div class="kpi-grid">
      <KpiCard
        label="总资产"
        :value="`¥${summary.total_value.toFixed(2)}`"
        icon="Coin"
        icon-bg="#e6f7ff"
        icon-color="#1890ff"
      />
      <KpiCard
        label="总收益"
        :value="`¥${summary.total_return.toFixed(2)}`"
        :sub="`${summary.total_return_pct.toFixed(2)}%`"
        icon="TrendCharts"
        :icon-bg="summary.total_return >= 0 ? '#f6ffed' : '#fff2f0'"
        :icon-color="summary.total_return >= 0 ? '#52c41a' : '#ff4d4f'"
        :value-color="summary.total_return >= 0 ? '#52c41a' : '#ff4d4f'"
      />
      <KpiCard
        label="持有基金数"
        :value="summary.fund_count"
        icon="Folder"
        icon-bg="#f0f5ff"
        icon-color="#2f54eb"
      />
      <KpiCard
        label="市场估值分位"
        :value="`${marketAvgPercentile.toFixed(0)}%`"
        sub="主要指数 PE 历史百分位均值"
        icon="DataBoard"
        icon-bg="#fff7e6"
        icon-color="#fa8c16"
      />
    </div>

    <div class="card-grid">
      <el-card shadow="never">
        <template #header><span style="font-weight: 600">资产配置</span></template>
        <div class="chart-container">
          <v-chart :option="pieOption" autoresize />
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header><span style="font-weight: 600">主要指数估值</span></template>
        <el-table :data="marketIndices" size="small" stripe>
          <el-table-column prop="index_name" label="指数" width="100" />
          <el-table-column prop="pe" label="PE" width="70" />
          <el-table-column label="PE 分位" width="90">
            <template #default="{ row }">
              <el-tag :type="tagType(row.pe_percentile)" size="small">
                {{ row.pe_percentile }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="pb" label="PB" width="70" />
          <el-table-column label="PB 分位" width="90">
            <template #default="{ row }">
              <el-tag :type="tagType(row.pb_percentile)" size="small">
                {{ row.pb_percentile }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="yield_ratio" label="股息率(%)" width="100" />
        </el-table>
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header><span style="font-weight: 600">持仓基金</span></template>
      <el-table :data="summary.holdings" size="small" stripe>
        <el-table-column prop="fund_code" label="代码" width="90" sortable />
        <el-table-column prop="fund_name" label="基金名称" min-width="180" sortable />
        <el-table-column label="持有份额" width="100">
          <template #default="{ row }">{{ row.shares.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="成本" width="90">
          <template #default="{ row }">¥{{ row.cost_basis.toFixed(4) }}</template>
        </el-table-column>
        <el-table-column label="当前价" width="90">
          <template #default="{ row }">¥{{ row.current_value.toFixed(4) }}</template>
        </el-table-column>
        <el-table-column label="收益" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.current_value >= row.cost_basis ? '#52c41a' : '#ff4d4f' }">
              {{ ((row.current_value - row.cost_basis) / row.cost_basis * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'
import KpiCard from '@/components/KpiCard.vue'
import { portfolioApi, marketApi } from '@/api'

const summary = ref({ total_value: 0, total_return: 0, total_return_pct: 0, fund_count: 0, holdings: [] })
const allocation = ref({})
const marketIndices = ref([])

const marketAvgPercentile = computed(() => {
  if (!marketIndices.value.length) return 0
  return marketIndices.value.reduce((s, i) => s + i.pe_percentile, 0) / marketIndices.value.length
})

const pieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['50%', '50%'],
    data: [
      { value: allocation.value.equity || 0, name: '股票', itemStyle: { color: '#409eff' } },
      { value: allocation.value.bond || 0, name: '债券', itemStyle: { color: '#67c23a' } },
      { value: allocation.value.commodity || 0, name: '商品', itemStyle: { color: '#e6a23c' } },
      { value: allocation.value.monetary || 0, name: '货币', itemStyle: { color: '#909399' } },
    ],
    label: { show: true, formatter: '{b}\n{d}%', fontSize: 12 },
    emphasis: { scale: true },
  }],
  grid: { containLabel: true },
}))

function tagType(percentile) {
  if (percentile <= 30) return 'success'
  if (percentile <= 60) return 'warning'
  return 'danger'
}

onMounted(async () => {
  try {
    const [sumRes, allocRes, mkRes] = await Promise.all([
      portfolioApi.summary(),
      portfolioApi.allocation(),
      marketApi.overview(),
    ])
    summary.value = sumRes.data || {}
    allocation.value = allocRes.data || {}
    marketIndices.value = mkRes.data?.indices || []
  } catch (e) {
    console.error('Dashboard 加载失败:', e)
  }
})
</script>
