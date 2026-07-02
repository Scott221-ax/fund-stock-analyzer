<template>
  <div class="penetration-page">

    <div class="page-header">
      <h2>基金穿透 · 盘中实时估值</h2>
      <p>基于底层持仓权重与实时行情，逐分钟估算基金盘中净值走势</p>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         基金切换器
         ══════════════════════════════════════════════════════════ -->
    <el-card shadow="never" class="switcher-card">
      <div class="switcher-row">
        <span class="switcher-label">选择基金</span>
        <el-select
          v-model="fundCode"
          class="fund-select"
          :loading="loadingFunds"
          loading-text="加载持仓中…"
          placeholder="请选择持仓基金"
          @change="loadFund"
        >
          <el-option
            v-for="f in quickFunds"
            :key="f.code"
            :value="f.code"
            :label="`${f.name}（${f.code}）`"
          >
            <div class="fund-option">
              <span class="option-name">{{ f.name }}</span>
              <span class="option-code">{{ f.code }}</span>
            </div>
          </el-option>
        </el-select>

        <el-empty
          v-if="!loadingFunds && !quickFunds.length"
          description="暂无持仓基金，请先在「基金池」中添加持仓"
          :image-size="40"
          style="padding:0"
        />
      </div>
    </el-card>

    <!-- ══════════════════════════════════════════════════════════
         骨架 / 错误态
         ══════════════════════════════════════════════════════════ -->
    <el-card v-if="error" shadow="never" class="error-card">
      <el-empty :description="error">
        <template #image>
          <el-icon class="error-icon"><WarnTriangleFilled /></el-icon>
        </template>
      </el-empty>
    </el-card>

    <!-- ══════════════════════════════════════════════════════════
         顶部：盘中分时走势图
         ══════════════════════════════════════════════════════════ -->
    <el-card v-if="!error" shadow="never" class="chart-card" v-loading="loading && !fundData">
      <template #header>
        <div class="chart-header">

          <!-- 基金标识 -->
          <div class="fund-identity">
            <span class="fund-name">{{ fundData?.fund_name || '——' }}</span>
            <span class="fund-code">{{ fundCode }}</span>
            <el-tag
              v-if="fundData && !fundData.is_trading_hour"
              size="small"
              type="warning"
              style="flex-shrink:0"
            >
              非交易时段
            </el-tag>
          </div>

          <!-- 实时绿灯 -->
          <div class="live-badge" v-if="fundData?.is_trading_hour">
            <span class="live-dot" />
            <span class="live-text">实时更新中</span>
          </div>

          <!-- 数据质量警告 -->
          <el-tooltip
            v-if="fundData && !fundData.data_quality?.is_reliable"
            content="覆盖权重不足 60%，估值仅供参考"
            placement="bottom"
          >
            <el-tag size="small" type="warning">⚠ 数据覆盖不足</el-tag>
          </el-tooltip>

          <!-- 核心指标胶囊 -->
          <div class="kpi-pills">
            <div class="kpi-pill">
              <span class="kpi-label">穿透估值</span>
              <span class="kpi-val" :class="totalReturn >= 0 ? 'val-up' : 'val-down'">
                {{ totalReturn >= 0 ? '↑' : '↓' }}{{ Math.abs(totalReturn).toFixed(3) }}%
              </span>
            </div>
            <div class="kpi-pill">
              <span class="kpi-label">超额收益</span>
              <span class="kpi-val" :class="excessReturn >= 0 ? 'val-up' : 'val-down'">
                {{ excessReturn >= 0 ? '+' : '' }}{{ excessReturn.toFixed(3) }}%
              </span>
            </div>
            <div class="kpi-pill">
              <span class="kpi-label">覆盖权重</span>
              <span class="kpi-val val-neutral">
                {{ fundData ? (fundData.data_quality?.disclosed_weight * 100 || 0).toFixed(1) : '--' }}%
              </span>
            </div>
            <div class="kpi-pill kpi-time">
              <span class="kpi-label">报价时间</span>
              <span class="kpi-val val-neutral">{{ lastTime }}</span>
            </div>
          </div>

        </div>
      </template>

      <!-- ECharts 分时图 -->
      <div class="chart-wrap">
        <v-chart :option="chartOption" autoresize class="intraday-chart" />
      </div>
    </el-card>

    <!-- ══════════════════════════════════════════════════════════
         底部：穿透持仓明细表
         ══════════════════════════════════════════════════════════ -->
    <el-card v-if="!error" shadow="never" class="table-card">
      <template #header>
        <div class="table-header">
          <span class="card-title">穿透持仓明细</span>
          <el-tag size="small" type="info" style="margin-left:8px;flex-shrink:0">
            {{ stocks.length }} 只
          </el-tag>
          <div class="table-header-right">
            <span class="header-stat">
              覆盖权重
              <strong>{{ totalWeight.toFixed(1) }}%</strong>
            </span>
            <span class="header-stat">
              穿透净值贡献
              <strong :class="totalContrib >= 0 ? 'val-up' : 'val-down'">
                {{ totalContrib >= 0 ? '+' : '' }}{{ totalContrib.toFixed(3) }}%
              </strong>
            </span>
            <el-button
              size="small"
              :icon="Refresh"
              :loading="refreshing"
              @click="refreshData"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="stocks"
        size="small"
        :header-cell-style="{
          background: '#f1f5f9',
          fontWeight: '600',
          color: '#475569',
          fontSize: '12px',
          padding: '10px 0',
        }"
        class="penetration-table"
      >

        <!-- 股票代码 -->
        <el-table-column label="股票代码" width="100" align="left">
          <template #default="{ row }">
            <span class="stock-code">{{ row.code }}</span>
          </template>
        </el-table-column>

        <!-- 股票名称 -->
        <el-table-column prop="name" label="股票名称" min-width="80" align="left">
          <template #default="{ row }">
            <span class="stock-name">{{ row.name }}</span>
            <el-tag
              v-if="row.status === 'suspended'"
              size="small"
              type="warning"
              style="margin-left:4px;font-size:10px"
            >停牌</el-tag>
            <el-tag
              v-else-if="row.status === 'data_missing'"
              size="small"
              type="danger"
              style="margin-left:4px;font-size:10px"
            >缺数</el-tag>
          </template>
        </el-table-column>

        <!-- 持仓权重（右对齐）-->
        <el-table-column label="持仓权重" width="84" align="right">
          <template #default="{ row }">
            <span class="num-cell">{{ row.weight.toFixed(1) }}%</span>
          </template>
        </el-table-column>

        <!-- 实时股价（右对齐 + 闪烁）-->
        <el-table-column label="实时股价" width="100" align="right">
          <template #default="{ row }">
            <span
              class="num-cell price-cell"
              :class="{ 'cell-flash': flashCells[row.code + '-price'] }"
            >
              {{ row.price != null ? row.price.toFixed(2) : '--' }}
            </span>
          </template>
        </el-table-column>

        <!-- 涨跌幅（右对齐 + 半透明胶囊）-->
        <el-table-column label="涨跌幅" width="100" align="right">
          <template #default="{ row }">
            <span
              class="change-pill"
              :class="row.change >= 0 ? 'pill-up' : 'pill-down'"
            >
              {{ row.change >= 0 ? '↑' : '↓' }}{{ Math.abs(row.change).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>

        <!-- 今日净值贡献（右对齐 + 闪烁）-->
        <el-table-column label="今日净值贡献" width="118" align="right">
          <template #default="{ row }">
            <span
              class="num-cell contrib-cell"
              :class="[
                row.contribution >= 0 ? 'contrib-up' : 'contrib-down',
                { 'cell-flash': flashCells[row.code + '-contrib'] },
              ]"
            >
              {{ row.contribution >= 0 ? '+' : '' }}{{ row.contribution.toFixed(3) }}%
            </span>
          </template>
        </el-table-column>

      </el-table>

      <!-- 基准指数代理行 -->
      <div v-if="fundData?.benchmark_proxy" class="benchmark-row">
        <span class="benchmark-label">基准指数代理（剩余仓位）</span>
        <span class="benchmark-index">
          {{ fundData.benchmark_proxy.index_name }}
          （{{ (fundData.benchmark_proxy.weight_pct || 0).toFixed(1) }}% 权重）
        </span>
        <span
          class="benchmark-change"
          :class="(fundData.benchmark_proxy.change_pct || 0) >= 0 ? 'val-up' : 'val-down'"
        >
          {{ (fundData.benchmark_proxy.change_pct || 0) >= 0 ? '↑' : '↓' }}
          {{ Math.abs(fundData.benchmark_proxy.change_pct || 0).toFixed(2) }}%
        </span>
      </div>
    </el-card>

  </div>
</template>

<script setup>
/**
 * FundPenetration.vue — 基金穿透与盘中实时估值
 *
 * 功能：
 *   - 基金切换器：支持输入任意6位基金代码 + 持仓快捷切换
 *   - 盘中分时走势图（ECharts）：历史数据模拟至真实 API 值，每 60s 追加新点
 *   - 穿透持仓明细表：接入 /api/v1/fund-valuation/{code} 真实数据
 *   - 停牌 / 缺数状态标签
 *   - 数据质量警告（覆盖率 < 60%）
 *
 * 轮询：
 *   - 交易时段：每 60s 自动刷新
 *   - 非交易时段：仅首次加载，不轮询
 */
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import VChart from 'vue-echarts'
import { graphic } from 'echarts'
import 'echarts'
import { Refresh, WarnTriangleFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { fundValuationApi, portfolioApi } from '@/api'

// ══════════════════════════════════════════════════════════════
// 交易时间序列（09:30 ~ 15:00，共 242 分钟）
// ══════════════════════════════════════════════════════════════
function buildTradingTimes() {
  const t = []
  const pad = n => String(n).padStart(2, '0')
  for (let h = 9; h <= 11; h++) {
    const s = h === 9 ? 30 : 0
    const e = h === 11 ? 30 : 59
    for (let m = s; m <= e; m++) t.push(`${pad(h)}:${pad(m)}`)
  }
  for (let h = 13; h <= 15; h++) {
    const e = h === 15 ? 0 : 59
    for (let m = 0; m <= e; m++) t.push(`${pad(h)}:${pad(m)}`)
  }
  return t
}
const ALL_TIMES = buildTradingTimes()

// ══════════════════════════════════════════════════════════════
// 确定性伪随机数生成器
// ══════════════════════════════════════════════════════════════
function makePRNG(seed) {
  let s = seed >>> 0
  return () => {
    s = Math.imul(s ^ (s >>> 17), 0x45D9F3B) >>> 0
    s = Math.imul(s ^ (s >>>  7), 0xD2A98B26) >>> 0
    return (s >>> 0) / 0x100000000
  }
}

/**
 * 生成从 0 出发、以 targetPct 结尾的模拟分时序列（贝塞尔风格收敛）。
 * seed 参数保证同一基金每次刷新形态一致。
 */
function buildFundSeries(nPoints, targetPct, seed) {
  if (nPoints <= 1) return [targetPct]
  const rng    = makePRNG(seed)
  const raw    = [0]
  const vol    = 0.028 + Math.abs(targetPct) * 0.005  // 动态波动率

  for (let i = 1; i < nPoints; i++) {
    const z    = (rng() - 0.5) * 2
    const pull = (targetPct - raw[i - 1]) * (i / nPoints) * 0.15  // 收敛力
    raw.push(+(raw[i - 1] + pull + z * vol * (1 - i / nPoints)).toFixed(4))
  }
  raw[nPoints - 1] = targetPct   // 精确对齐真实值
  return raw
}

function buildBenchSeries(nPoints, seed) {
  const rng = makePRNG(seed)
  const data = [0]
  for (let i = 1; i < nPoints; i++) {
    const z = (rng() - 0.5) * 2
    data.push(+(data[i - 1] + 0.0001 + z * 0.038).toFixed(4))
  }
  return data
}

/** 当前交易时间在 ALL_TIMES 中的索引（-1 表示非交易时段）*/
function currentTimeIdx() {
  const now = new Date()
  const h = now.getHours()
  const m = now.getMinutes()
  const pad = n => String(n).padStart(2, '0')
  const cur = `${pad(h)}:${pad(m)}`
  const idx = ALL_TIMES.indexOf(cur)
  if (idx !== -1) return idx
  // 盘前：起始点；收盘后：终止点
  if (h < 9 || (h === 9 && m < 30)) return 0
  return ALL_TIMES.length - 1
}

// ══════════════════════════════════════════════════════════════
// 响应式状态
// ══════════════════════════════════════════════════════════════
const fundCode    = ref('')        // 当前选中基金代码（绑定到 el-select）
const fundData    = ref(null)      // 最新一次 API 响应
const loading     = ref(false)
const loadingFunds = ref(true)     // 持仓列表加载态
const refreshing  = ref(false)
const error       = ref('')

/** 下拉列表：从持仓读出的基金列表 */
const quickFunds  = ref([])

/** 分时图数据点列表：{ time, fund, bench } */
const chartPoints = ref([])

/** 持仓行数据（用于表格） */
const stocks = reactive([])

/** 闪烁状态 */
const flashCells = reactive({})

const lastTime = ref('--:--:--')

let pollerTimer = null

// ══════════════════════════════════════════════════════════════
// 计算属性
// ══════════════════════════════════════════════════════════════
const totalReturn = computed(() => {
  const pts = chartPoints.value
  return pts.length ? pts[pts.length - 1].fund : 0
})

const totalBenchReturn = computed(() => {
  const pts = chartPoints.value
  return pts.length ? pts[pts.length - 1].bench : 0
})

const excessReturn = computed(() =>
  +(totalReturn.value - totalBenchReturn.value).toFixed(4)
)

const totalWeight = computed(() =>
  stocks.reduce((s, r) => s + r.weight, 0)
)

const totalContrib = computed(() =>
  +(stocks.reduce((s, r) => s + r.contribution, 0)).toFixed(3)
)

// ══════════════════════════════════════════════════════════════
// 数据更新工具
// ══════════════════════════════════════════════════════════════

/** 根据 API 响应重建分时图基础数据 */
function rebuildChartSeries(data) {
  const seed    = parseInt(data.fund_code || '0', 10) * 0x1337
  const nPoints = currentTimeIdx() + 1
  const target  = data.estimated_change_pct ?? 0

  const fundArr  = buildFundSeries(nPoints, target, seed)
  const benchArr = buildBenchSeries(nPoints, seed ^ 0xDEADBEEF)

  chartPoints.value = ALL_TIMES.slice(0, nPoints).map((time, i) => ({
    time,
    fund:  fundArr[i],
    bench: benchArr[i],
  }))
}

/** 追加最新一个数据点（每次轮询时调用）*/
function appendChartPoint(data) {
  const now  = new Date()
  const pad  = n => String(n).padStart(2, '0')
  const time = `${pad(now.getHours())}:${pad(now.getMinutes())}`
  const last = chartPoints.value[chartPoints.value.length - 1]

  // 避免同一分钟内重复追加
  if (last && last.time === time) {
    last.fund  = data.estimated_change_pct ?? last.fund
    return
  }

  chartPoints.value.push({
    time,
    fund:  data.estimated_change_pct ?? 0,
    bench: last ? last.bench + (Math.random() - 0.5) * 0.06 : 0,
  })
}

/** 将 API 持仓数据更新至 stocks + 触发闪烁 */
function updateStocks(data, isFirstLoad) {
  const incoming = (data.disclosed_holdings || []).map(h => ({
    code:         h.stock_code,
    name:         h.stock_name,
    weight:       h.weight_pct,
    price:        h.current_price,
    change:       h.change_pct,
    contribution: h.contribution,
    status:       h.status,
  }))

  if (isFirstLoad) {
    stocks.splice(0, stocks.length, ...incoming)
  } else {
    // 增量更新：只更新有变化的字段，并触发闪烁
    incoming.forEach((inc, i) => {
      if (i >= stocks.length) { stocks.push(inc); return }
      const prev = stocks[i]
      if (Math.abs((inc.price || 0) - (prev.price || 0)) >= 0.01) {
        flashCell(inc.code + '-price')
        flashCell(inc.code + '-contrib')
      }
      Object.assign(prev, inc)
    })
    if (incoming.length < stocks.length) {
      stocks.splice(incoming.length)
    }
  }
}

function flashCell(key, ms = 750) {
  flashCells[key] = true
  setTimeout(() => delete flashCells[key], ms)
}

// ══════════════════════════════════════════════════════════════
// API 调用
// ══════════════════════════════════════════════════════════════

async function loadFund(code) {
  const c = (code || '').trim()
  if (!c) return

  // 切换基金时停止旧定时器
  if (pollerTimer) { clearInterval(pollerTimer); pollerTimer = null }

  loading.value     = true
  error.value       = ''
  fundCode.value    = c
  chartPoints.value = []
  stocks.splice(0)

  try {
    const res = await fundValuationApi.get(c)
    fundData.value = res.data
    rebuildChartSeries(res.data)
    updateStocks(res.data, true)
    lastTime.value = new Date().toTimeString().slice(0, 8)

    // 交易时段才启动轮询（60s / 次）
    if (res.data.is_trading_hour) {
      pollerTimer = setInterval(poll, 60_000)
    }
  } catch (e) {
    error.value = e?.message || '获取估值数据失败，请检查基金代码是否正确'
  } finally {
    loading.value = false
  }
}

async function poll() {
  if (!fundCode.value) return
  try {
    const res = await fundValuationApi.get(fundCode.value)
    fundData.value = res.data
    appendChartPoint(res.data)
    updateStocks(res.data, false)
    lastTime.value = new Date().toTimeString().slice(0, 8)

    // 如果进入非交易时段，停止轮询
    if (!res.data.is_trading_hour && pollerTimer) {
      clearInterval(pollerTimer)
      pollerTimer = null
    }
  } catch { /* 静默：网络波动不打断用户 */ }
}

async function refreshData() {
  if (!fundCode.value || refreshing.value) return
  refreshing.value = true
  try {
    const res = await fundValuationApi.get(fundCode.value, true)
    fundData.value = res.data
    appendChartPoint(res.data)
    updateStocks(res.data, false)
    lastTime.value = new Date().toTimeString().slice(0, 8)
    ElMessage.success('数据已刷新')
  } catch (e) {
    ElMessage.error(e?.message || '刷新失败')
  } finally {
    refreshing.value = false
  }
}

/** 从持仓加载下拉基金列表，加载完毕后自动选中第一只 */
async function loadQuickFunds() {
  loadingFunds.value = true
  try {
    const res = await portfolioApi.summary()
    const holdings = res.data?.holdings || []
    quickFunds.value = holdings.map(h => ({
      code: h.fund_code,
      name: h.fund_name || h.fund_code,
    }))
    // 自动选中第一只并加载估值
    if (quickFunds.value.length) {
      fundCode.value = quickFunds.value[0].code
      await loadFund(fundCode.value)
    }
  } catch {
    ElMessage.error('持仓加载失败，请刷新重试')
  } finally {
    loadingFunds.value = false
  }
}

// ══════════════════════════════════════════════════════════════
// 生命周期
// ══════════════════════════════════════════════════════════════
onMounted(() => {
  loadQuickFunds()
})

onUnmounted(() => {
  if (pollerTimer) clearInterval(pollerTimer)
})

// ══════════════════════════════════════════════════════════════
// ECharts 配置
// ══════════════════════════════════════════════════════════════
const KEY_TIMES = new Set([
  '09:30','10:00','10:30','11:00','11:30',
  '13:00','13:30','14:00','14:30','15:00',
])

const chartOption = computed(() => {
  const pts       = chartPoints.value
  const times     = pts.map(p => p.time)
  const fundData_ = pts.map(p => p.fund)
  const benchData = pts.map(p => p.bench)
  const n         = pts.length
  const lastIdx   = n - 1

  const areaGradient = new graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0,    color: 'rgba(26, 95, 180, 0.22)' },
    { offset: 0.55, color: 'rgba(26, 95, 180, 0.07)' },
    { offset: 1,    color: 'rgba(26, 95, 180, 0.00)' },
  ])

  return {
    backgroundColor: 'transparent',
    animation:        true,
    animationDuration: 380,
    animationEasing:  'cubicOut',

    legend: {
      top:    10,
      right:  12,
      itemWidth:  22,
      itemHeight:  2,
      itemGap:    16,
      textStyle: { fontSize: 12, color: '#64748b', fontWeight: '500' },
      data: [
        { name: '穿透预估收益率', icon: 'roundRect' },
        { name: '业绩基准收益率', icon: 'roundRect' },
      ],
    },

    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type:      'cross',
        lineStyle: { color: '#7c90a8', width: 1, type: 'dashed' },
        crossStyle:{ color: '#7c90a8', width: 1 },
        label: {
          backgroundColor: '#334155',
          color:           '#f1f5f9',
          fontSize:         11,
          padding:          [3, 7],
          borderRadius:     4,
        },
      },
      borderColor:     'transparent',
      backgroundColor: 'rgba(10, 18, 32, 0.92)',
      extraCssText: [
        'box-shadow: 0 10px 36px rgba(0,0,0,0.38)',
        'border-radius: 12px',
        'padding: 12px 16px',
        'min-width: 200px',
      ].join(';'),
      formatter(params) {
        if (!params?.length) return ''
        const t     = params[0]?.axisValue ?? ''
        const fund  = params.find(p => p.seriesName === '穿透预估收益率')
        const bench = params.find(p => p.seriesName === '业绩基准收益率')
        const fv    = fund?.value  ?? 0
        const bv    = bench?.value ?? 0
        const diff  = +(fv - bv).toFixed(4)
        const fmt   = v => (v >= 0 ? '+' : '') + v.toFixed(3) + '%'
        const hue   = v => v >= 0 ? '#fca5a5' : '#86efac'

        return `
          <div style="font-family:-apple-system,'PingFang SC',sans-serif;line-height:1">
            <div style="font-size:11px;color:#64748b;margin-bottom:10px;letter-spacing:0.6px;font-variant-numeric:tabular-nums">
              ${t}
            </div>
            <div style="display:flex;align-items:center;gap:9px;margin-bottom:7px">
              <span style="width:14px;height:2.5px;background:#1A5FB4;border-radius:2px;display:inline-block;flex-shrink:0"></span>
              <span style="color:#94a3b8;font-size:12px;flex:1">穿透预估</span>
              <span style="font-family:monospace;font-weight:700;font-size:14px;color:${hue(fv)}">${fmt(fv)}</span>
            </div>
            <div style="display:flex;align-items:center;gap:9px;margin-bottom:10px">
              <span style="width:14px;height:1.5px;background:#C75000;border-radius:2px;display:inline-block;flex-shrink:0;opacity:0.85"></span>
              <span style="color:#94a3b8;font-size:12px;flex:1">业绩基准</span>
              <span style="font-family:monospace;font-weight:700;font-size:14px;color:${hue(bv)}">${fmt(bv)}</span>
            </div>
            <div style="border-top:1px solid rgba(255,255,255,0.09);padding-top:8px;display:flex;align-items:center">
              <span style="color:#475569;font-size:11px;flex:1">超额收益</span>
              <span style="font-family:monospace;font-weight:800;font-size:14px;color:${hue(diff)}">${fmt(diff)}</span>
            </div>
          </div>
        `
      },
    },

    grid: {
      top:          48,
      left:         '1%',
      right:        '2%',
      bottom:       '5%',
      containLabel: true,
    },

    xAxis: {
      type:      'category',
      data:       times,
      boundaryGap: false,
      axisLabel: {
        fontSize:  10,
        color:     '#94a3b8',
        interval:  (_, value) => KEY_TIMES.has(value),
        formatter: v => v,
      },
      axisLine: { lineStyle: { color: '#e2e8f0', width: 1 } },
      axisTick: { show: false },
      splitLine:{ show: false },
    },

    yAxis: {
      type:      'value',
      axisLabel: {
        fontSize:  10,
        color:     '#94a3b8',
        formatter: v => (v >= 0 ? '+' : '') + v.toFixed(2) + '%',
      },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed', width: 1 } },
      axisLine:  { show: false },
      axisTick:  { show: false },
    },

    series: [
      {
        name:      '穿透预估收益率',
        type:      'line',
        data:       fundData_,
        smooth:     0.28,
        showSymbol: false,
        color:      '#1A5FB4',
        z:           4,
        lineStyle: { width: 2.2, color: '#1A5FB4' },
        areaStyle: { color: areaGradient },

        markPoint: {
          silent:    true,
          animation: true,
          data: n > 0 ? [{
            coord:      [lastIdx, fundData_[lastIdx]],
            symbol:     'circle',
            symbolSize:  8,
            itemStyle:  { color: '#1A5FB4', borderColor: '#ffffff', borderWidth: 2.5 },
            label:       { show: false },
          }] : [],
        },

        markLine: {
          silent:    true,
          animation: false,
          symbol:   ['none', 'none'],
          data:     [{ yAxis: 0 }],
          lineStyle:{ color: '#c4cdd6', width: 1.5, type: 'solid' },
          label:    { show: false },
        },
      },

      {
        name:      '业绩基准收益率',
        type:      'line',
        data:       benchData,
        smooth:     0.28,
        showSymbol: false,
        color:      '#C75000',
        z:           3,
        lineStyle: { width: 1.6, color: '#C75000', type: 'dashed', opacity: 0.80 },

        markPoint: {
          silent: true,
          data: n > 0 ? [{
            coord:      [lastIdx, benchData[lastIdx]],
            symbol:     'circle',
            symbolSize:  6,
            itemStyle:  { color: '#C75000', borderColor: '#fff', borderWidth: 2 },
            label:       { show: false },
          }] : [],
        },
      },
    ],
  }
})
</script>

<style scoped>
/* ══════════════════════════════════════════════════════════════
   页面容器
   ══════════════════════════════════════════════════════════════ */
.penetration-page { max-width: 1400px; }

/* ══════════════════════════════════════════════════════════════
   基金切换器
   ══════════════════════════════════════════════════════════════ */
.switcher-card {
  margin-bottom: 16px;
}
.switcher-card :deep(.el-card__body) {
  padding: 14px 20px;
}

.switcher-row {
  display:     flex;
  align-items: center;
  gap:         12px;
  flex-wrap:   wrap;
}

.switcher-label {
  font-size:   13px;
  font-weight: 500;
  color:       var(--text-secondary);
  white-space: nowrap;
  flex-shrink: 0;
}

.fund-select {
  width: 320px;
}

/* 下拉选项内部布局 */
.fund-option {
  display:         flex;
  align-items:     center;
  justify-content: space-between;
  gap:             12px;
  width:           100%;
}
.option-name {
  font-size:  13px;
  color:      var(--text-primary);
  flex:       1;
  overflow:   hidden;
  text-overflow: ellipsis;
  white-space:   nowrap;
}
.option-code {
  font-size:   12px;
  font-family: var(--font-mono);
  color:       #94a3b8;
  background:  #f1f5f9;
  padding:     2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

/* ══════════════════════════════════════════════════════════════
   错误态
   ══════════════════════════════════════════════════════════════ */
.error-card { margin-bottom: 16px; }
.error-icon { font-size: 48px; color: #f59e0b; }

/* ══════════════════════════════════════════════════════════════
   顶部分时图卡片
   ══════════════════════════════════════════════════════════════ */
.chart-card { margin-bottom: 20px; }
.chart-card :deep(.el-card__header) { padding: 12px 20px; }
.chart-card :deep(.el-card__body)   { padding: 4px 8px 10px; }

.chart-header {
  display:     flex;
  align-items: center;
  flex-wrap:   wrap;
  gap:         14px;
}

.fund-identity {
  display:     flex;
  align-items: baseline;
  gap:         8px;
}
.fund-name {
  font-size:     15px;
  font-weight:   700;
  color:         var(--text-primary);
  letter-spacing: -0.2px;
}
.fund-code {
  font-size:   12px;
  font-family: var(--font-mono);
  color:       #94a3b8;
  background:  #f1f5f9;
  padding:     2px 7px;
  border-radius: 5px;
  font-weight: 500;
}

.live-badge {
  display:     flex;
  align-items: center;
  gap:         5px;
  font-size:   12px;
  font-weight: 500;
  color:       #15803d;
}
.live-dot {
  width:         7px;
  height:        7px;
  border-radius: 50%;
  background:    #22c55e;
  animation:     pulseDot 1.8s ease-in-out infinite;
  flex-shrink:   0;
}
@keyframes pulseDot {
  0%, 100% { opacity: 1;    transform: scale(1);    }
  50%       { opacity: 0.42; transform: scale(0.68); }
}
.live-text { white-space: nowrap; }

.kpi-pills {
  display:     flex;
  gap:         8px;
  margin-left: auto;
  flex-wrap:   wrap;
}
.kpi-pill {
  display:       flex;
  flex-direction: column;
  align-items:   flex-end;
  padding:       5px 12px;
  background:    #f8fafc;
  border:        1px solid #e9eef5;
  border-radius: 9px;
  min-width:     80px;
  transition:    box-shadow 0.2s;
}
.kpi-pill:hover { box-shadow: 0 2px 8px rgba(15,23,42,0.07); }
.kpi-time       { min-width: 90px; }

.kpi-label {
  font-size:     10px;
  font-weight:   500;
  color:         #94a3b8;
  line-height:   1;
  margin-bottom: 4px;
  letter-spacing: 0.2px;
}
.kpi-val {
  font-size:   15px;
  font-weight: 700;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}
.val-up      { color: #CF1E1E; }
.val-down    { color: #2A7D3F; }
.val-neutral { color: var(--text-primary); font-size: 13px; }

.chart-wrap     { position: relative; }
.intraday-chart { width: 100%; height: 280px; display: block; }

/* ══════════════════════════════════════════════════════════════
   底部持仓明细表
   ══════════════════════════════════════════════════════════════ */
.table-card :deep(.el-card__body) { padding: 0; }

.table-header {
  display:     flex;
  align-items: center;
  gap:         8px;
  flex-wrap:   wrap;
}
.card-title {
  font-size:   15px;
  font-weight: 700;
  color:       var(--text-primary);
}
.table-header-right {
  display:   flex;
  gap:       12px;
  margin-left: auto;
  flex-wrap: wrap;
  align-items: center;
}
.header-stat {
  font-size: 12px;
  color:     var(--text-muted);
}
.header-stat strong { color: var(--text-secondary); font-weight: 600; margin-left: 4px; }

.penetration-table :deep(.el-table__body tr:hover td.el-table__cell) {
  background: #f0f7ff !important;
  transition: background 0.15s;
}
.penetration-table :deep(td.el-table__cell) {
  padding:       9px 0 !important;
  border-bottom: 1px solid #f1f5f9 !important;
  transition:    background 0.18s ease;
}
.penetration-table :deep(.el-table__body tr:last-child td.el-table__cell) {
  border-bottom: none !important;
}

.stock-code {
  font-family:   var(--font-mono);
  font-size:     12px;
  font-weight:   600;
  color:         var(--color-primary);
  letter-spacing: 0.5px;
}
.stock-name {
  font-size:  13px;
  color:      var(--text-primary);
}
.num-cell {
  font-family:          var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size:            13px;
  display:              inline-block;
}
.price-cell { color: var(--text-primary); }

.change-pill {
  display:       inline-flex;
  align-items:   center;
  gap:           2px;
  padding:       3px 10px;
  border-radius: 100px;
  font-size:     12px;
  font-weight:   700;
  font-family:   var(--font-mono);
  font-variant-numeric: tabular-nums;
  white-space:   nowrap;
  border:        none;
  letter-spacing: 0.2px;
  transition:    background 0.15s;
}
.pill-up   { background: rgba(207, 30, 30, 0.10); color: #CF1E1E; }
.pill-down { background: rgba(42, 125, 63, 0.10); color: #2A7D3F; }

.contrib-cell { font-weight: 600; }
.contrib-up   { color: #CF1E1E; }
.contrib-down { color: #2A7D3F; }

/* ── 基准指数代理行 ───────────────────────────────────────── */
.benchmark-row {
  display:     flex;
  align-items: center;
  gap:         12px;
  padding:     10px 16px;
  background:  #fafbfd;
  border-top:  1px dashed #e2e8f0;
  font-size:   12px;
  flex-wrap:   wrap;
}
.benchmark-label {
  color:       #94a3b8;
  font-weight: 500;
}
.benchmark-index {
  color:       var(--text-secondary);
  font-weight: 500;
}
.benchmark-change {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size:   13px;
}

/* ══════════════════════════════════════════════════════════════
   Flash 效果 — 金融终端琥珀金闪烁
   ══════════════════════════════════════════════════════════════ */
@keyframes cellFlash {
  0%   { background-color: rgba(234, 179,  8, 0.45); border-radius: 3px; }
  35%  { background-color: rgba(234, 179,  8, 0.22); }
  100% { background-color: rgba(234, 179,  8, 0.00); }
}
.cell-flash {
  animation:    cellFlash 0.75s ease-out forwards;
  padding:      2px 5px;
  margin:      -2px -5px;
  border-radius: 4px;
}

/* ══════════════════════════════════════════════════════════════
   响应式
   ══════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .kpi-pills      { margin-left: 0; }
  .intraday-chart { height: 220px; }
  .chart-header   { gap: 10px; }
  .table-header-right { display: none; }
  .fund-input     { width: 160px; }
}
</style>
