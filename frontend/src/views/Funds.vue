<template>
  <div>
    <div class="page-header">
      <h2>基金池</h2>
      <p>基金搜索、评价与对比</p>
    </div>

    <el-card shadow="never" style="margin-bottom:20px">
      <el-input
        v-model="keyword"
        placeholder="输入基金代码或名称搜索..."
        :prefix-icon="Search"
        clearable
        style="max-width:400px"
        @keyup.enter="doSearch"
      >
        <template #append>
          <el-button @click="doSearch">搜索</el-button>
        </template>
      </el-input>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight: 600">搜索结果</span></template>
      <el-table :data="fundList" size="small" stripe @row-click="selectFund">
        <el-table-column prop="code" label="代码" width="100" />
        <el-table-column prop="name" label="基金名称" min-width="220" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="selectFund(row)">评价</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!fundList.length" description="搜索基金以查看结果" />
    </el-card>

    <el-dialog v-model="showEval" :title="selectedFund?.name || '基金评价'" width="600px">
      <template v-if="evalResult">
        <div class="kpi-grid" style="grid-template-columns:repeat(3,1fr);margin-bottom:16px">
          <KpiCard label="综合评分" :value="evalResult.score" icon="Star" icon-bg="#fff7e6" icon-color="#fa8c16" />
          <KpiCard label="夏普比率" :value="evalResult.sharpe" icon="TrendCharts" icon-bg="#f6ffed" icon-color="#52c41a" />
          <KpiCard label="最大回撤" :value="`${evalResult.max_drawdown}%`" icon="WarnTriangleFilled" icon-bg="#fff2f0" icon-color="#ff4d4f" />
        </div>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="代码">{{ evalResult.code }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ evalResult.name }}</el-descriptions-item>
          <el-descriptions-item label="风险等级">{{ evalResult.risk_level }}</el-descriptions-item>
          <el-descriptions-item label="综合费率">{{ evalResult.fee_rate }}%</el-descriptions-item>
          <el-descriptions-item label="同类排名">{{ evalResult.return_rank }}%</el-descriptions-item>
        </el-descriptions>
      </template>
      <el-empty v-else description="暂无评价数据" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import KpiCard from '@/components/KpiCard.vue'
import { fundApi } from '@/api'

const keyword = ref('')
const fundList = ref([])
const selectedFund = ref(null)
const showEval = ref(false)
const evalResult = ref(null)

async function doSearch() {
  if (!keyword.value.trim()) return
  try {
    const res = await fundApi.search(keyword.value)
    fundList.value = res.data || []
  } catch (e) {
    console.error('搜索失败:', e)
  }
}

async function selectFund(fund) {
  selectedFund.value = fund
  showEval.value = true
  try {
    const res = await fundApi.evaluate(fund.code)
    evalResult.value = res.data || null
  } catch (e) {
    evalResult.value = null
  }
}
</script>
