<template>
  <div class="factor-mining-page">

    <!-- 页面标题（始终可见，不随 Tab 切换）-->
    <div class="page-header">
      <h2>因子发掘</h2>
      <p>通过自定义因子表达式，探索 α 因子在基金市场的统计显著性</p>
    </div>

    <!-- ══ Tab 导航 ══════════════════════════════════════════════ -->
    <el-tabs v-model="activeTab" class="mining-tabs">

      <!-- ╔══════════════════════════════════════════════════════╗
           ║  Tab 1 — 因子发掘工作台                              ║
           ╚══════════════════════════════════════════════════════╝ -->
      <el-tab-pane name="mining">
        <template #label>
          <span class="tab-label">
            <el-icon><MagicStick /></el-icon>
            因子发掘
          </span>
        </template>

        <el-row :gutter="20" class="workspace" align="top">

          <!-- ── 左：因子配置面板 ───────────────────────────── -->
          <el-col :span="24" :lg="9">
            <el-card shadow="never" class="config-card">
              <template #header>
                <div class="card-header-row">
                  <span class="card-title">因子配置</span>
                </div>
              </template>

              <el-form :model="form" label-position="top" size="small" class="factor-form">

                <el-form-item label="基础数据源">
                  <el-select v-model="form.dataSource" placeholder="选择数据源" style="width:100%">
                    <el-option label="基金日线净值" value="fund_nav" />
                    <el-option label="基金季度持仓" value="fund_position" />
                    <el-option label="基础估值数据（PE/PB/股息率）" value="valuation" />
                  </el-select>
                </el-form-item>

                <el-form-item>
                  <template #label>
                    <div class="label-row">
                      <span>因子表达式</span>
                      <el-tooltip
                        content="支持对 Close、Volume 等字段调用内置函数，返回截面因子值"
                        placement="top"
                      >
                        <el-icon style="cursor:help;color:#94a3b8"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                  </template>
                  <el-input
                    v-model="form.expression"
                    type="textarea"
                    :rows="4"
                    :autosize="false"
                    class="expr-input"
                    placeholder="(Close - MA(Close, 20)) / Std(Close, 20)"
                    resize="none"
                  />
                  <div class="expr-chips">
                    <el-tag
                      v-for="ex in EXAMPLES"
                      :key="ex.label"
                      size="small"
                      class="expr-chip"
                      @click="form.expression = ex.value"
                    >
                      {{ ex.label }}
                    </el-tag>
                  </div>
                </el-form-item>

                <el-collapse v-model="fnHintOpen" class="fn-hint-collapse">
                  <el-collapse-item title="可用函数与字段" name="fns">
                    <div class="fn-grid">
                      <div v-for="fn in FUNCTIONS" :key="fn.name" class="fn-item">
                        <span class="fn-name">{{ fn.name }}</span>
                        <span class="fn-desc">{{ fn.desc }}</span>
                      </div>
                    </div>
                  </el-collapse-item>
                </el-collapse>

                <el-divider style="margin:16px 0" />

                <el-form-item label="回测时间范围">
                  <el-date-picker
                    v-model="form.dateRange"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    value-format="YYYY-MM-DD"
                    style="width:100%"
                  />
                </el-form-item>

                <el-form-item label="调仓周期">
                  <el-select v-model="form.rebalancePeriod" style="width:100%">
                    <el-option label="月度（每月末调仓）" value="monthly" />
                    <el-option label="周度（每周末调仓）" value="weekly" />
                  </el-select>
                </el-form-item>

                <el-form-item label="预测窗期">
                  <el-select v-model="form.predictionWindow" style="width:100%">
                    <el-option label="5 个交易日" :value="5" />
                    <el-option label="20 个交易日（约 1 个月）" :value="20" />
                  </el-select>
                </el-form-item>

                <el-button
                  type="primary"
                  :loading="running"
                  style="width:100%;height:40px;font-size:15px;letter-spacing:1px"
                  @click="runMining"
                >
                  <el-icon v-if="!running" style="margin-right:6px"><MagicStick /></el-icon>
                  {{ running ? '发掘中…' : '开始发掘' }}
                </el-button>

              </el-form>
            </el-card>
          </el-col>

          <!-- ── 右：发掘结果看板 ──────────────────────────── -->
          <el-col :span="24" :lg="15">

            <!-- 空态 -->
            <template v-if="!result && !running">
              <div class="result-empty">
                <div class="empty-icon-wrap">
                  <el-icon :size="56" color="#dbeafe"><DataLine /></el-icon>
                </div>
                <p class="empty-title">尚未发掘</p>
                <p class="empty-sub">填写左侧因子配置，点击「开始发掘」生成分析报告</p>
              </div>
            </template>

            <!-- 加载中 -->
            <template v-else-if="running">
              <div class="result-empty">
                <el-icon :size="48" class="spin-icon" color="#3b82f6"><Loading /></el-icon>
                <p class="empty-title" style="color:#3b82f6">正在计算中…</p>
                <p class="empty-sub">正在对全市场基金按因子分层并回测，请稍候</p>
              </div>
            </template>

            <!-- 结果看板 -->
            <template v-else-if="result">

              <el-card shadow="never" class="result-card chart-card">
                <template #header>
                  <div class="card-header-row">
                    <span class="card-title">五组分层回测净值曲线</span>
                    <span class="card-badge">{{ result.expression }}</span>
                  </div>
                </template>
                <div class="chart-wrap">
                  <v-chart :option="equityOption" autoresize class="equity-chart" />
                </div>
                <div class="chart-legend">
                  <span v-for="(color, key) in Q_COLORS" :key="key" class="legend-chip">
                    <span class="legend-dot" :style="{ background: color }"></span>
                    {{ key }}（因子{{ key === 'Q1' ? '最低' : key === 'Q5' ? '最高' : '' }}组）
                  </span>
                </div>
              </el-card>

              <el-card shadow="never" class="result-card metrics-card">
                <template #header>
                  <div class="card-header-row">
                    <span class="card-title">因子有效性指标</span>
                    <el-tag
                      :type="result.metrics.ic_mean > 0 ? 'success' : 'danger'"
                      size="small"
                      style="margin-left:auto"
                    >
                      {{ result.metrics.ic_mean > 0.05 ? '因子有效' : result.metrics.ic_mean > 0 ? '因子较弱' : '因子无效' }}
                    </el-tag>
                  </div>
                </template>

                <div class="metrics-grid">
                  <div class="metric-cell">
                    <el-statistic
                      title="IC 均值"
                      :value="result.metrics.ic_mean"
                      :precision="4"
                      :value-style="{ color: result.metrics.ic_mean >= 0 ? '#CF1E1E' : '#2A7D3F', fontSize: '28px', fontWeight: 700, fontFamily: 'var(--font-mono)' }"
                    />
                    <p class="metric-hint">信息系数（越高越好，>0.03 视为有效）</p>
                  </div>
                  <div class="metric-cell">
                    <el-statistic
                      title="IC/IR（信息比率）"
                      :value="result.metrics.ic_ir"
                      :precision="2"
                      :value-style="{ color: '#1A5FB4', fontSize: '28px', fontWeight: 700, fontFamily: 'var(--font-mono)' }"
                    />
                    <p class="metric-hint">IC 均值 / IC 标准差（>0.5 视为显著）</p>
                  </div>
                  <div class="metric-cell">
                    <el-statistic
                      title="IC 胜率"
                      :value="result.metrics.win_rate"
                      :precision="1"
                      suffix="%"
                      :value-style="{ color: '#7D44A5', fontSize: '28px', fontWeight: 700, fontFamily: 'var(--font-mono)' }"
                    />
                    <p class="metric-hint">IC > 0 的期数占比（>55% 视为稳定）</p>
                  </div>
                  <div class="metric-cell">
                    <el-statistic
                      title="Q5-Q1 年化超额"
                      :value="result.metrics.long_short_return"
                      :precision="1"
                      suffix="%"
                      :value-style="{ color: result.metrics.long_short_return >= 0 ? '#CF1E1E' : '#2A7D3F', fontSize: '28px', fontWeight: 700, fontFamily: 'var(--font-mono)' }"
                    />
                    <p class="metric-hint">最高因子组相对最低组的年化超额收益</p>
                  </div>
                </div>
              </el-card>

            </template>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ╔══════════════════════════════════════════════════════╗
           ║  Tab 2 — 多因子相关性矩阵                            ║
           ╚══════════════════════════════════════════════════════╝ -->
      <el-tab-pane name="correlation">
        <template #label>
          <span class="tab-label">
            <el-icon><Grid /></el-icon>
            相关性矩阵
          </span>
        </template>

        <div class="corr-tab-body">
          <!-- 说明区 -->
          <div class="corr-tip">
            <el-icon color="#3b82f6"><InfoFilled /></el-icon>
            <span>
              热力图展示五个主流量化因子之间的截面 Pearson 相关系数。
              深蓝代表强负相关，深红代表强正相关，白色代表近零相关。
            </span>
          </div>

          <!-- 热力图卡片（居中，限最大宽度，保持正方形感）-->
          <div class="corr-chart-wrap">
            <CorrelationHeatmap />
          </div>
        </div>
      </el-tab-pane>

    </el-tabs>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'
import { ElMessage } from 'element-plus'
import { factorApi } from '@/api'
import CorrelationHeatmap from '@/components/CorrelationHeatmap.vue'

// ── 当前激活的 Tab ─────────────────────────────────────────
const activeTab = ref('mining')

// ── 已验证调色盘（5 分位，adjacent ΔE≥17.7 protan）─────────
const Q_COLORS = {
  Q1: '#CF1E1E',
  Q2: '#7D44A5',
  Q3: '#C75000',
  Q4: '#2A7D3F',
  Q5: '#1A5FB4',
}

// ── 表单 ────────────────────────────────────────────────────
const form = reactive({
  dataSource:       'fund_nav',
  expression:       '(Close - MA(Close, 20)) / Std(Close, 20)',
  dateRange:        ['2020-01-01', ''],
  rebalancePeriod:  'monthly',
  predictionWindow: 20,
})

const running    = ref(false)
const result     = ref(null)
const fnHintOpen = ref([])

const EXAMPLES = [
  { label: '动量因子',   value: 'Momentum(Close, 20)' },
  { label: '均值回归',   value: '(Close - MA(Close, 20)) / Std(Close, 20)' },
  { label: 'RSI 因子',   value: 'RSI(14)' },
  { label: '成交量异动', value: '(Volume - MA(Volume, 20)) / MA(Volume, 20)' },
]

const FUNCTIONS = [
  { name: 'MA(field, n)',       desc: 'n 日移动平均' },
  { name: 'Std(field, n)',      desc: 'n 日滚动标准差' },
  { name: 'Momentum(field, n)', desc: 'n 日动量（收益率）' },
  { name: 'RSI(n)',             desc: 'n 日 RSI 指标' },
  { name: 'Rank(field)',        desc: '截面排名因子' },
  { name: 'Close',              desc: '收盘净值/价格' },
  { name: 'Volume',             desc: '成交量' },
  { name: 'PE / PB',            desc: '市盈率 / 市净率' },
]

// ── 运行因子发掘 ────────────────────────────────────────────
async function runMining() {
  if (!form.expression.trim()) {
    ElMessage.warning('请输入因子表达式')
    return
  }
  running.value = true
  result.value  = null
  try {
    const res = await factorApi.mine({
      data_source:       form.dataSource,
      expression:        form.expression.trim(),
      start_date:        form.dateRange?.[0] || '2020-01-01',
      end_date:          form.dateRange?.[1] || '',
      rebalance_period:  form.rebalancePeriod,
      prediction_window: form.predictionWindow,
    })
    result.value = res.data
    ElMessage.success('因子发掘完成')
  } catch {
    ElMessage.error('发掘失败，请检查表达式或网络连接')
  } finally {
    running.value = false
  }
}

// ── ECharts 净值曲线配置 ────────────────────────────────────
const equityOption = computed(() => {
  if (!result.value) return {}
  const { dates, groups } = result.value

  const series = Object.keys(Q_COLORS).map((q) => ({
    name:       q,
    type:       'line',
    data:       groups[q] || [],
    color:      Q_COLORS[q],
    smooth:     true,
    showSymbol: false,
    lineStyle:  { width: q === 'Q5' ? 2.5 : 1.8, color: Q_COLORS[q] },
    endLabel: {
      show:      true,
      formatter: '{a}',
      color:     Q_COLORS[q],
      fontSize:  11,
      fontWeight: q === 'Q5' ? 700 : 500,
    },
    emphasis: { lineStyle: { width: q === 'Q5' ? 3.5 : 2.5 } },
  }))

  return {
    tooltip: {
      trigger: 'axis',
      borderColor: 'transparent',
      backgroundColor: 'rgba(255,255,255,0.97)',
      extraCssText: 'box-shadow:0 4px 20px rgba(15,23,42,.12);border-radius:10px;padding:10px 14px',
      formatter(params) {
        const date = params[0]?.axisValue || ''
        const rows = params
          .sort((a, b) => b.value - a.value)
          .map(p => {
            const pct  = ((p.value - 1) * 100).toFixed(1)
            const sign = pct >= 0 ? '+' : ''
            return `<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
              <span style="width:8px;height:8px;border-radius:50%;background:${p.color};flex-shrink:0"></span>
              <span style="flex:1;color:#475569;font-size:12px">${p.seriesName}</span>
              <span style="font-weight:700;color:${Q_COLORS[p.seriesName]};font-family:monospace;font-size:12px">${sign}${pct}%</span>
            </div>`
          }).join('')
        return `<div style="font-family:-apple-system,'PingFang SC',sans-serif">
          <div style="font-size:12px;color:#94a3b8;margin-bottom:6px">${date}</div>${rows}</div>`
      },
    },
    grid:  { left: '3%', right: '10%', bottom: '8%', top: '5%', containLabel: true },
    xAxis: {
      type:      'category',
      data:       dates,
      axisLabel: { fontSize: 10, color: '#94a3b8', rotate: 20 },
      axisLine:  { lineStyle: { color: '#e2e8f0' } },
      axisTick:  { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type:      'value',
      axisLabel: { formatter: v => v.toFixed(2), fontSize: 10, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      axisLine:  { show: false },
      axisTick:  { show: false },
    },
    series,
    dataZoom: [{ type: 'inside' }],
  }
})
</script>

<style scoped>
/* ── 页面容器 ─────────────────────────────────────────────── */
.factor-mining-page { max-width: 1400px; }

/* ══ Tab 样式 ═══════════════════════════════════════════════ */
.mining-tabs {
  /* 去掉 el-tabs 默认 border-bottom 分割线 */
}

/* Tab 导航栏整体 */
.mining-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

/* Tab 导航背景：与卡片融合的浅灰底 */
.mining-tabs :deep(.el-tabs__nav-wrap)::after {
  background-color: var(--border-color);
  height: 1px;
}

/* 每个 Tab 标签 */
.mining-tabs :deep(.el-tabs__item) {
  font-size:   14px;
  font-weight: 500;
  color:       var(--text-muted);
  padding:     0 20px;
  height:      44px;
  line-height: 44px;
  transition:  color 0.2s;
}
.mining-tabs :deep(.el-tabs__item:hover) {
  color: var(--text-primary);
}
.mining-tabs :deep(.el-tabs__item.is-active) {
  color:       var(--color-primary);
  font-weight: 700;
}

/* 激活指示器（下划线）*/
.mining-tabs :deep(.el-tabs__active-bar) {
  height:        3px;
  border-radius: 2px;
  background:    linear-gradient(90deg, var(--color-primary), #3b82f6);
}

/* Tab 标签内容（图标 + 文字）*/
.tab-label {
  display:     flex;
  align-items: center;
  gap:         6px;
}

/* ── 工作区（Tab 1 内部）────────────────────────────────── */
.workspace { align-items: flex-start; }

/* ── 通用卡片标题行 ─────────────────────────────────────── */
.card-header-row {
  display:     flex;
  align-items: center;
  gap:         10px;
}
.card-title {
  font-size:     15px;
  font-weight:   700;
  color:         var(--text-primary);
  letter-spacing: -0.2px;
}
.card-badge {
  font-size:     11px;
  color:         var(--text-muted);
  background:    var(--bg-table-header);
  padding:       2px 8px;
  border-radius: 10px;
  margin-left:   auto;
  max-width:     200px;
  overflow:      hidden;
  text-overflow: ellipsis;
  white-space:   nowrap;
  font-family:   var(--font-mono);
}

/* ── 因子配置表单 ─────────────────────────────────────────── */
.factor-form :deep(.el-form-item) { margin-bottom: 16px; }
.factor-form :deep(.el-form-item__label) {
  font-size:    13px;
  font-weight:  600;
  color:        var(--text-primary);
  padding-bottom: 6px;
}
.label-row {
  display:     flex;
  align-items: center;
  gap:         6px;
  font-size:   13px;
  font-weight: 600;
  color:       var(--text-primary);
}

/* 因子表达式输入框 */
.expr-input :deep(.el-textarea__inner) {
  font-family:   var(--font-mono) !important;
  font-size:     13px !important;
  line-height:   1.7;
  color:         #1e293b;
  background:    #fafbff;
  border:        1px solid #e2e8f0;
  border-radius: 8px;
  transition:    border-color 0.2s, box-shadow 0.2s;
  resize:        none !important;
}
.expr-input :deep(.el-textarea__inner:focus) {
  border-color: #3b82f6;
  box-shadow:   0 0 0 3px rgba(59,130,246,0.12);
  outline:      none;
}

.expr-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.expr-chip {
  cursor:        pointer;
  border-radius: 6px !important;
  font-family:   var(--font-mono) !important;
  font-size:     11px !important;
  background:    #eff6ff !important;
  color:         #1d4ed8 !important;
  border-color:  #bfdbfe !important;
  transition:    background 0.15s, transform 0.1s;
}
.expr-chip:hover { background: #dbeafe !important; transform: translateY(-1px); }

/* 函数提示折叠 */
.fn-hint-collapse { border: none !important; }
.fn-hint-collapse :deep(.el-collapse-item__header) {
  background: transparent; font-size: 12px; color: var(--text-muted); border: none; height: 32px;
}
.fn-hint-collapse :deep(.el-collapse-item__content),
.fn-hint-collapse :deep(.el-collapse-item__wrap) { border: none; padding-bottom: 0; }

.fn-grid {
  display:               grid;
  grid-template-columns: 1fr 1fr;
  gap:                   4px 12px;
  padding:               4px 0;
}
.fn-item {
  display:       flex;
  flex-direction: column;
  padding:       4px 6px;
  border-radius: 4px;
  background:    #f8fafc;
}
.fn-name { font-family: var(--font-mono); font-size: 11px; font-weight: 600; color: #1d4ed8; }
.fn-desc { font-size: 11px; color: var(--text-muted); margin-top: 1px; }

/* ── 空/加载 态 ───────────────────────────────────────────── */
.result-empty {
  display:         flex;
  flex-direction:  column;
  align-items:     center;
  justify-content: center;
  min-height:      400px;
  text-align:      center;
}
.empty-icon-wrap {
  width:           90px;
  height:          90px;
  border-radius:   50%;
  background:      #eff6ff;
  display:         flex;
  align-items:     center;
  justify-content: center;
  margin-bottom:   16px;
}
.empty-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0 0 6px; }
.empty-sub   { font-size: 13px; color: var(--text-muted); max-width: 300px; line-height: 1.6; }

.spin-icon { animation: spin 1.2s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 结果卡片 ─────────────────────────────────────────────── */
.result-card { margin-bottom: 20px; }
.result-card :deep(.el-card__body) { padding: 16px 20px; }

.chart-wrap   { height: 350px; }
.equity-chart { width: 100%; height: 100%; }

.chart-legend {
  display:      flex;
  flex-wrap:    wrap;
  gap:          10px 20px;
  margin-top:   12px;
  padding-top:  12px;
  border-top:   1px solid #f1f5f9;
}
.legend-chip {
  display:     flex;
  align-items: center;
  gap:         6px;
  font-size:   12px;
  color:       var(--text-secondary);
}
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

.metrics-card :deep(.el-card__body) { padding: 20px 24px; }
.metrics-grid {
  display:               grid;
  grid-template-columns: repeat(4, 1fr);
  gap:                   0;
}
.metric-cell {
  padding:      12px 16px;
  border-right: 1px solid #f1f5f9;
  text-align:   center;
}
.metric-cell:last-child { border-right: none; }
.metric-cell :deep(.el-statistic__head) {
  font-size: 12px !important; color: var(--text-muted) !important; font-weight: 500; margin-bottom: 8px;
}
.metric-cell :deep(.el-statistic__number) { line-height: 1.2; }
.metric-hint { font-size: 11px; color: #cbd5e1; margin: 6px 0 0; line-height: 1.4; }

/* ══ Tab 2 — 相关性矩阵布局 ════════════════════════════════ */
.corr-tab-body { display: flex; flex-direction: column; gap: 16px; }

/* 说明条 */
.corr-tip {
  display:       flex;
  align-items:   flex-start;
  gap:           8px;
  padding:       10px 16px;
  background:    #eff6ff;
  border:        1px solid #bfdbfe;
  border-radius: 10px;
  font-size:     13px;
  color:         #1e40af;
  line-height:   1.6;
}
.corr-tip .el-icon { flex-shrink: 0; margin-top: 2px; }

/* 热力图容器：居中，最大宽度保持正方形感 */
.corr-chart-wrap {
  max-width: 780px;
  margin:    0 auto;
  width:     100%;
}

/* ── 响应式 ───────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .metric-cell:nth-child(2) { border-right: none; }
  .metric-cell:nth-child(3) { border-top: 1px solid #f1f5f9; }
}
@media (max-width: 768px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-wrap   { height: 260px; }
  .result-empty { min-height: 240px; }
  .mining-tabs :deep(.el-tabs__item) { padding: 0 12px; font-size: 13px; }
}
</style>
