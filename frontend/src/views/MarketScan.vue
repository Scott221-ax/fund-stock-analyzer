<template>
  <div>
    <div class="page-header">
      <h2>市场扫描</h2>
      <p>指数估值、行业热度与资金流向</p>
    </div>

    <div class="kpi-grid">
      <KpiCard
        label="股债性价比"
        :value="overview.stock_bond_ratio?.toFixed(2)"
        sub=">2 时股票相对债券有吸引力"
        icon="DataBoard"
        icon-bg="#f0f5ff"
        icon-color="#2f54eb"
      />
      <KpiCard
        label="北向资金(今日)"
        :value="`${overview.north_flow || 0} 亿`"
        :icon="overview.north_flow >= 0 ? 'Top' : 'Bottom'"
        :icon-bg="(overview.north_flow || 0) >= 0 ? '#f6ffed' : '#fff2f0'"
        :icon-color="(overview.north_flow || 0) >= 0 ? '#52c41a' : '#ff4d4f'"
      />
    </div>

    <div class="card-grid">
      <el-card shadow="never">
        <template #header><span style="font-weight: 600">指数估值</span></template>
        <el-table :data="overview.indices || []" size="small" stripe>
          <el-table-column prop="index_name" label="指数" width="100" />
          <el-table-column prop="pe" label="PE" width="70" />
          <el-table-column label="PE 分位" width="90">
            <template #default="{ row }">
              <el-tag :type="tagType(row.pe_percentile)" size="small">{{ row.pe_percentile }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="pb" label="PB" width="70" />
          <el-table-column label="PB 分位" width="90">
            <template #default="{ row }">
              <el-tag :type="tagType(row.pb_percentile)" size="small">{{ row.pb_percentile }}%</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="yield_ratio" label="股息率(%)" width="100" />
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header><span style="font-weight: 600">低估指数推荐</span></template>
        <el-table :data="undervalued" size="small" stripe>
          <el-table-column prop="index" label="指数" width="120" />
          <el-table-column prop="pe_percentile" label="PE 分位" width="80">
            <template #default="{ row }">{{ row.pe_percentile }}%</template>
          </el-table-column>
          <el-table-column prop="reason" label="推荐理由" min-width="200" />
        </el-table>
        <div v-if="!undervalued.length" style="text-align:center;padding:40px;color:#999">暂无数据</div>
      </el-card>
    </div>

    <div class="card-grid">
      <el-card shadow="never">
        <template #header><span style="font-weight: 600">热门行业</span></template>
        <div class="chart-container">
          <v-chart :option="sectorBarOption" autoresize />
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header><span style="font-weight: 600">北向资金流向</span></template>
        <div class="chart-container">
          <v-chart :option="northFlowOption" autoresize />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'
import KpiCard from '@/components/KpiCard.vue'
import { marketApi } from '@/api'

const overview = ref({ indices: [], stock_bond_ratio: 0, north_flow: 0 })
const sectors = ref([])
const undervalued = ref([])
const northFlow = ref([])

function tagType(p) {
  if (p <= 30) return 'success'
  if (p <= 60) return 'warning'
  return 'danger'
}

const sectorBarOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
  yAxis: {
    type: 'category',
    data: sectors.value.map(s => s.sector).reverse(),
    axisLine: { show: false },
  },
  series: [{
    type: 'bar',
    data: sectors.value.map(s => ({
      value: s.change_pct,
      itemStyle: { color: s.change_pct >= 0 ? '#52c41a' : '#ff4d4f' },
    })).reverse(),
    barWidth: '50%',
    label: { show: true, position: 'right', formatter: '{c}%' },
  }],
}))

const northFlowOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
  xAxis: {
    type: 'category',
    data: northFlow.value.map(n => n.date),
    axisLabel: { rotate: 30, fontSize: 11 },
  },
  yAxis: { type: 'value', axisLabel: { formatter: '{value}亿' } },
  series: [{
    type: 'bar',
    data: northFlow.value.map(n => ({
      value: n.value,
      itemStyle: { color: n.value >= 0 ? '#52c41a' : '#ff4d4f' },
    })),
    barWidth: '60%',
  }],
}))

onMounted(async () => {
  try {
    const [ovvRes, secRes, undRes, nfRes] = await Promise.all([
      marketApi.overview(),
      marketApi.sectors(),
      marketApi.undervalued(),
      marketApi.northFlow(),
    ])
    overview.value = ovvRes.data || {}
    sectors.value = secRes.data || []
    undervalued.value = undRes.data || []
    northFlow.value = nfRes.data || []
  } catch (e) {
    console.error('市场扫描加载失败:', e)
  }
})
</script>
