<template>
  <div>
    <div class="page-header">
      <h2>持仓分析</h2>
      <p>管理持仓、风险指标与优化建议</p>
    </div>

    <!-- 持仓管理 -->
    <el-card shadow="never" style="margin-bottom:20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-weight:600">持仓管理</span>
          <div>
            <el-button type="primary" size="small" @click="showAddDialog = true">
              <el-icon style="vertical-align:-2px"><Plus /></el-icon> 添加基金
            </el-button>
            <el-button type="success" size="small" :loading="saving" @click="saveHoldings" style="margin-left:8px">
              保存变更
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="localHoldings" size="small" stripe max-height="400" @sort-change="onSortChange">
        <el-table-column prop="fund_code" label="代码" width="90" sortable="custom">
          <template #default="{ row }">
            <el-input v-if="editingCode === row.fund_code" v-model="row.fund_code" size="small" style="width:80px" />
            <span v-else>{{ row.fund_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="fund_name" label="基金名称" min-width="200" sortable="custom">
          <template #default="{ row }">
            <el-input v-if="editingCode === row.fund_code" v-model="row.fund_name" size="small" />
            <span v-else>{{ row.fund_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="shares" label="份额" width="110" sortable="custom">
          <template #default="{ row }">
            <el-input-number v-if="editingCode === row.fund_code" v-model="row.shares" :min="0" :step="100" size="small" controls-position="right" style="width:100px" />
            <span v-else>{{ row.shares.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="cost_basis" label="成本(单价)" width="110" sortable="custom">
          <template #default="{ row }">
            <el-input-number v-if="editingCode === row.fund_code" v-model="row.cost_basis" :min="0" :step="0.1" :precision="4" size="small" controls-position="right" style="width:100px" />
            <span v-else>{{ row.cost_basis ? '¥' + row.cost_basis.toFixed(4) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="account" label="账户" width="100" sortable="custom">
          <template #default="{ row }">
            <el-select v-if="editingCode === row.fund_code" v-model="row.account" size="small" style="width:90px">
              <el-option label="支付宝" value="支付宝" />
              <el-option label="天天基金" value="天天基金" />
              <el-option label="银行" value="银行" />
              <el-option label="证券" value="证券" />
            </el-select>
            <span v-else>{{ row.account }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row, $index }">
            <el-button v-if="editingCode !== row.fund_code" text type="primary" size="small" @click="startEdit(row)">编辑</el-button>
            <el-button v-else text type="primary" size="small" @click="stopEdit(row)">完成</el-button>
            <el-button text type="danger" size="small" @click="removeRow($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!localHoldings.length" style="text-align:center;padding:30px;color:#999">
        暂无持仓，点击"添加基金"录入你的持仓
      </div>
    </el-card>

    <!-- 添加基金对话框 -->
    <el-dialog v-model="showAddDialog" title="添加基金" width="500px">
      <el-form :model="newHolding" label-width="80px" size="small">
        <el-form-item label="基金代码">
          <el-input v-model="newHolding.fund_code" placeholder="输入代码或名称搜索" style="width:220px" @input="debounceSearch" />
          <el-button :icon="Search" style="margin-left:6px" @click="doSearch" />
        </el-form-item>
        <div v-if="searchResults.length" style="margin-bottom:12px;border:1px solid #e8e8e8;border-radius:4px;max-height:150px;overflow:auto">
          <div v-for="f in searchResults" :key="f.code" class="search-item" @click="pickFund(f)">
            {{ f.code }} {{ f.name }} <span style="color:#999">{{ f.type }}</span>
          </div>
        </div>
        <el-form-item label="基金名称">
          <el-input v-model="newHolding.fund_name" disabled />
        </el-form-item>
        <el-form-item label="持有份额">
          <el-input-number v-model="newHolding.shares" :min="0" :step="100" style="width:200px" controls-position="right" />
        </el-form-item>
        <el-form-item label="成本(单价)">
          <el-input-number v-model="newHolding.cost_basis" :min="0" :step="0.1" :precision="4" style="width:200px" controls-position="right" />
        </el-form-item>
        <el-form-item label="账户">
          <el-select v-model="newHolding.account" style="width:200px">
            <el-option label="支付宝" value="支付宝" />
            <el-option label="天天基金" value="天天基金" />
            <el-option label="银行" value="银行" />
            <el-option label="证券" value="证券" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" size="small" @click="addHolding">添加</el-button>
      </template>
    </el-dialog>

    <!-- 风险指标 -->
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
import { ref, computed, onMounted, reactive } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'
import { Search, Plus } from '@element-plus/icons-vue'
import KpiCard from '@/components/KpiCard.vue'
import { portfolioApi, fundApi } from '@/api'
import { ElMessage } from 'element-plus'

const localHoldings = ref([])
const editingCode = ref('')
const saving = ref(false)
const showAddDialog = ref(false)
const searchResults = ref([])
const searchTimer = ref(null)

const newHolding = reactive({
  fund_code: '',
  fund_name: '',
  shares: 0,
  cost_basis: 0,
  account: '支付宝',
})

let searchTimeout = null

function debounceSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(doSearch, 400)
}

async function doSearch() {
  const kw = newHolding.fund_code.trim()
  if (!kw) { searchResults.value = []; return }
  try {
    const res = await fundApi.search(kw)
    searchResults.value = res.data || []
  } catch { searchResults.value = [] }
}

function pickFund(f) {
  newHolding.fund_code = f.code
  newHolding.fund_name = f.name
  searchResults.value = []
}

function addHolding() {
  if (!newHolding.fund_code.trim()) {
    ElMessage.warning('请输入基金代码')
    return
  }
  localHoldings.value.push({
    fund_code: newHolding.fund_code,
    fund_name: newHolding.fund_name,
    shares: newHolding.shares,
    cost_basis: newHolding.cost_basis,
    current_value: 0,
    account: newHolding.account,
  })
  showAddDialog.value = false
  newHolding.fund_code = ''
  newHolding.fund_name = ''
  newHolding.shares = 0
  newHolding.cost_basis = 0
  newHolding.account = '支付宝'
}

function startEdit(row) {
  editingCode.value = row.fund_code
}

function stopEdit() {
  editingCode.value = ''
}


const sortOrder = ref({ prop: '', order: '' })
function onSortChange({ prop, order }) {
  sortOrder.value = { prop, order }
  if (!prop || !order) return
  localHoldings.value.sort((a, b) => {
    const va = a[prop] ?? '', vb = b[prop] ?? ''
    const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb))
    return order === 'ascending' ? cmp : -cmp
  })
}

function removeRow(index) {
  localHoldings.value.splice(index, 1)
}

async function saveHoldings() {
  saving.value = true
  try {
    await portfolioApi.saveHoldings(localHoldings.value)
    ElMessage.success('持仓已保存')
    // 刷新数据
    await loadAllData()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function loadAllData() {
  try {
    const [holdRes, secRes, ovlRes, riskRes] = await Promise.all([
      portfolioApi.holdings(),
      portfolioApi.sectors(),
      portfolioApi.overlap(),
      portfolioApi.risk(),
    ])
    localHoldings.value = holdRes.data || []
    sectors.value = secRes.data || []
    overlaps.value = ovlRes.data || []
    risk.value = riskRes.data || {}
  } catch (e) {
    console.error('持仓分析加载失败:', e)
  }
}

// 原有数据
const sectors = ref([])
const overlaps = ref([])
const risk = ref({ volatility: 0, max_drawdown: 0, sharpe_ratio: 0, var_95: 0 })


const sectorOption = computed(() => {
  if (!sectors.value.length) return { title: { show: true, textStyle: { color: '#999', fontSize: 14 }, text: '暂无行业数据' } }
  return {
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
  }
})

import * as echarts from 'echarts'

onMounted(async () => {
  await loadAllData()
})
</script>

<style scoped>
.search-item {
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s;
}
.search-item:hover {
  background: #ecf5ff;
}
</style>
