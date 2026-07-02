<template>
<div>
<div class="page-header"><h2>交易回测</h2><p>按自定义规则通过历史走势分析胜率</p></div>
<el-row :gutter="16">
<el-col :span="24" :lg="12">
<el-card shadow="never">
<template #header><span>策略配置</span></template>
<el-form label-width="90px" size="small">
<el-form-item label="策略名称"><el-input v-model="name" /></el-form-item>
<el-form-item label="目标">
  <el-input v-model="targetCode" placeholder="基金/指数代码" style="width:130px" />
  <el-select v-model="targetType" style="width:80px;margin-left:4px">
    <el-option label="指数" value="index" /><el-option label="基金" value="fund" />
  </el-select>
  <el-button size="small" style="margin-left:4px" @click="loadPresets">预设</el-button>
</el-form-item>
<el-form-item label="起始资金"><el-input-number v-model="capital" :min="10000" :step="50000" style="width:160px" /></el-form-item>
<el-form-item label="每笔金额"><el-input-number v-model="positionSize" :min="1000" :step="10000" style="width:160px" /></el-form-item>
<el-form-item label="回测区间">
  <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width:280px" />
</el-form-item>
</el-form>
<el-divider />
<div style="font-weight:600;margin-bottom:8px">入场条件</div>
<div v-for="(r,i) in entryRules" :key="'e'+i" style="display:flex;align-items:center;margin-bottom:6px">
  <el-select v-model="r.type" style="width:130px" @change="onEntryChange(r)">
    <el-option label="均线金叉/死叉" value="ma_cross" />
    <el-option label="价格跌破均线" value="price_below_ma" />
    <el-option label="RSI低于阈值" value="rsi_below" />
  </el-select>
  <template v-if="r.type==='ma_cross'">
    <el-select v-model="r.direction" style="width:70px;margin-left:4px">
      <el-option label="金叉" value="golden" /><el-option label="死叉" value="death" />
    </el-select>
    <el-input-number v-model="r.params.short" :min="3" :max="60" size="small" style="width:60px;margin-left:4px" />日
    <el-input-number v-model="r.params.long" :min="5" :max="120" size="small" style="width:60px;margin-left:2px" />日
  </template>
  <template v-else-if="r.type==='price_below_ma'">
    <el-input-number v-model="r.params.ma" :min="5" :max="60" size="small" style="width:65px;margin-left:4px" />日均线
  </template>
  <template v-else-if="r.type==='rsi_below'">
    低于<el-input-number v-model="r.params.threshold" :min="10" :max="50" size="small" style="width:60px;margin-left:4px" />
  </template>
  <el-button text type="danger" size="small" style="margin-left:4px" @click="entryRules.splice(i,1)">删除</el-button>
</div>
<el-button size="small" @click="entryRules.push({type:'ma_cross',direction:'golden',params:{short:5,long:20}})">+ 添加入场</el-button>
<el-divider />
<div style="font-weight:600;margin-bottom:8px">出场条件</div>
<div v-for="(r,i) in exitRules" :key="'x'+i" style="display:flex;align-items:center;margin-bottom:6px">
  <el-select v-model="r.type" style="width:130px">
    <el-option label="止盈" value="take_profit" /><el-option label="止损" value="stop_loss" />
    <el-option label="持仓天数" value="holding_days" />
  </el-select>
  <template v-if="r.type==='take_profit'||r.type==='stop_loss'">
    <el-input-number v-model="r.value" :min="1" :max="50" size="small" style="width:70px;margin-left:4px" />%
  </template>
  <template v-else-if="r.type==='holding_days'">
    <el-input-number v-model="r.value" :min="5" :max="365" size="small" style="width:70px;margin-left:4px" />天
  </template>
  <el-button text type="danger" size="small" style="margin-left:4px" @click="exitRules.splice(i,1)">删除</el-button>
</div>
<el-button size="small" @click="exitRules.push({type:'take_profit',value:10})">+ 添加出场</el-button>
<el-divider />
<el-button type="primary" :loading="running" @click="runBacktest" style="width:100%">运行回测</el-button>
</el-card>
</el-col>
<el-col :span="24" :lg="12">
<el-card shadow="never">
<template #header><span>回测结果</span></template>
<div v-if="!result" style="text-align:center;padding:80px 20px;color:var(--text-muted)">
  <el-icon :size="48" color="var(--text-muted)"><TrendCharts /></el-icon>
  <p style="margin-top:12px">配置左侧策略后点击运行回测</p>
</div>
<template v-else>
<div class="kpi-grid" style="grid-template-columns:repeat(3,1fr);gap:8px">
  <KpiCard label="总收益率" :value="result.total_return_pct+'%'" :value-color="result.total_return_pct>=0?'var(--color-success)':'var(--color-danger)'" icon="TrendCharts" icon-bg="var(--color-primary-light)" icon-color="var(--color-primary)" />
  <KpiCard label="胜率" :value="result.win_rate+'%'" icon="DataBoard" icon-bg="#f6ffed" icon-color="var(--color-success)" />
  <KpiCard label="夏普比率" :value="result.sharpe_ratio" icon="Coin" icon-bg="var(--color-accent-light)" icon-color="var(--color-accent)" />
  <KpiCard label="年化收益" :value="result.annualized_return+'%'" icon="TrendCharts" icon-bg="var(--color-primary-light)" icon-color="var(--color-primary)" />
  <KpiCard label="最大回撤" :value="result.max_drawdown+'%'" icon="WarnTriangleFilled" icon-bg="#fff2f0" icon-color="var(--color-danger)" />
  <KpiCard label="交易次数" :value="result.total_trades" icon="Folder" icon-bg="#f0f5ff" icon-color="#2f54eb" />
</div>
<div v-if="result.total_trades>0" style="margin-top:16px">
  <el-card shadow="never"><template #header><span>净值曲线</span></template>
  <div class="chart-container"><v-chart :option="equityOption" autoresize /></div></el-card>
  <el-card shadow="never" style="margin-top:12px">
    <template #header><span>交易明细 ({{result.trades.length}}笔)</span></template>
    <el-table :data="result.trades" size="small" max-height="300" stripe>
      <el-table-column prop="entry_date" label="买入日" width="95" />
      <el-table-column prop="entry_price" label="买入价" width="75" />
      <el-table-column prop="exit_date" label="卖出日" width="95" />
      <el-table-column prop="exit_price" label="卖出价" width="75" />
      <el-table-column label="收益率" width="75"><template #default="{row}"><span :style="{color:row.return_pct>=0?'var(--color-success)':'var(--color-danger)'}">{{row.return_pct}}%</span></template></el-table-column>
      <el-table-column prop="exit_reason" label="原因" width="85" />
    </el-table>
  </el-card>
</div>
</template>
</el-card>
</el-col>
</el-row>
</div>
</template>
<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'
import { TrendCharts } from '@element-plus/icons-vue'
import KpiCard from '@/components/KpiCard.vue'
import { backtestApi } from '@/api'
import { ElMessage } from 'element-plus'
const name = ref('均线策略')
const targetCode = ref('000300')
const targetType = ref('index')
const capital = ref(100000)
const positionSize = ref(10000)
const dateRange = ref(['2020-01-01', ''])
const entryRules = ref([{type:'ma_cross',direction:'golden',params:{short:5,long:20}}])
const exitRules = ref([{type:'take_profit',value:10},{type:'stop_loss',value:-5}])
const running = ref(false)
const result = ref(null)
function onEntryChange(r) {
  if (!r.params) r.params = {}
  if (r.type==='ma_cross'&&!r.params.short){r.params.short=5;r.params.long=20}
  if (r.type==='price_below_ma'&&!r.params.ma) r.params.ma=20
  if (r.type==='rsi_below'&&!r.params.threshold) r.params.threshold=30
}
async function loadPresets() {
  try {
    const res = await backtestApi.presets()
    const p = res.data?.[0]
    if(!p) return
    name.value=p.name;targetCode.value=p.target_code;targetType.value=p.target_type
    capital.value=p.initial_capital;positionSize.value=p.position_size
    entryRules.value=p.entry_rules;exitRules.value=p.exit_rules
    dateRange.value=[p.start_date,p.end_date||'']
  }catch{}
}
async function runBacktest() {
  running.value=true;result.value=null
  try {
    const res = await backtestApi.run({
      name:name.value,target_code:targetCode.value,target_name:targetCode.value,
      target_type:targetType.value,initial_capital:capital.value,
      position_size:positionSize.value,entry_rules:entryRules.value,
      exit_rules:exitRules.value,start_date:dateRange.value?.[0]||'2020-01-01',
      end_date:dateRange.value?.[1]||'',
    })
    result.value = res.data
    if(res.data.total_trades===0) ElMessage.warning('回测完成，未产生交易')
  }catch{ElMessage.error('回测失败')}
  finally{running.value=false}
}
const equityOption = computed(()=>{
  const curve = result.value?.equity_curve||[]
  return {
    tooltip:{trigger:'axis',valueFormatter:v=>'¥'+Number(v).toLocaleString()},
    grid:{left:'3%',right:'3%',bottom:'5%',containLabel:true},
    xAxis:{type:'category',data:curve.map(e=>e.date),axisLabel:{fontSize:10,rotate:30}},
    yAxis:{type:'value',axisLabel:{formatter:'¥{value}'}},
    series:[{type:'line',data:curve.map(e=>e.value),smooth:true,showSymbol:false,
      lineStyle:{width:2,color:'#3B6B9E'},
      areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,
        colorStops:[{offset:0,color:'rgba(59,107,158,0.3)'},{offset:1,color:'rgba(59,107,158,0.02)'}]}}}],
    dataZoom:[{type:'inside'}],
  }
})
</script>
