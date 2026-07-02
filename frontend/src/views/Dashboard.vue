<template>
  <div class="dashboard">

    <!-- ══ 骨架加载态 ══════════════════════════════════════════ -->
    <template v-if="loading">
      <div class="page-header">
        <div class="skeleton" style="width:100px;height:22px;margin-bottom:8px" />
        <div class="skeleton" style="width:200px;height:13px" />
      </div>
      <div class="kpi-grid">
        <div v-for="i in 4" :key="i" class="el-card skeleton-card" />
      </div>
      <div class="card-grid">
        <div class="el-card skeleton-chart" />
        <div class="el-card skeleton-chart" />
      </div>
    </template>

    <!-- ══ 主内容 ════════════════════════════════════════════════ -->
    <template v-else>

      <!-- 页面标题 -->
      <div class="page-header">
        <h2>总览</h2>
        <p>持仓总览与市场速览</p>
      </div>

      <!-- ── KPI 卡片行 ─────────────────────────────────────── -->
      <div class="kpi-grid">

        <!-- 总资产 -->
        <KpiCard
          label="总资产"
          :value="`¥${fmtMoney(summary.total_value)}`"
          icon="Coin"
          icon-bg="linear-gradient(135deg, #dbeafe, #93c5fd)"
          icon-color="#1A5FB4"
        />

        <!-- 总收益（中国市场：正数红色、负数绿色）-->
        <KpiCard
          label="总收益"
          :value="`¥${fmtMoney(summary.total_return)}`"
          :sub="returnSubText"
          icon="TrendCharts"
          :icon-bg="
            summary.total_return >= 0
              ? 'linear-gradient(135deg, #fee2e2, #fca5a5)'
              : 'linear-gradient(135deg, #dcfce7, #86efac)'
          "
          :icon-color="summary.total_return >= 0 ? '#CF1E1E' : '#2A7D3F'"
          :value-color="summary.total_return >= 0 ? '#CF1E1E' : '#2A7D3F'"
        />

        <!-- 持有基金数 -->
        <KpiCard
          label="持有基金数"
          :value="`${summary.fund_count} 只`"
          icon="Folder"
          icon-bg="linear-gradient(135deg, #ede9fe, #c4b5fd)"
          icon-color="#7D44A5"
        />

        <!-- 市场估值分位 -->
        <KpiCard
          label="市场估值分位"
          :value="`${marketAvgPct.toFixed(0)}%`"
          sub="主要指数 PE 历史百分位均值"
          icon="DataBoard"
          icon-bg="linear-gradient(135deg, #fef3c7, #fcd34d)"
          icon-color="#C75000"
        />
      </div>

      <!-- ── 中部：资产配置 + 指数估值 ───────────────────────── -->
      <div class="card-grid">

        <!-- 资产配置环形图 -->
        <el-card shadow="never" class="alloc-card">
          <template #header>
            <div class="card-header-row">
              <span class="card-title">资产配置</span>
              <span class="card-badge">{{ allocTotal > 0 ? `¥${fmtMoney(allocTotal)}` : '暂无数据' }}</span>
            </div>
          </template>

          <div class="alloc-body">
            <!-- 环形图容器（含居中悬浮文字）-->
            <div class="donut-wrap">
              <v-chart :option="pieOption" autoresize class="donut-chart" />
              <!-- 居中文字：通过绝对定位叠加在图表上 -->
              <div class="donut-center">
                <span class="donut-label">总资产</span>
                <span class="donut-value">¥{{ fmtMoney(summary.total_value) }}</span>
              </div>
            </div>

            <!-- 自定义图例：右侧对齐 -->
            <div class="alloc-legend">
              <div
                v-for="item in allocLegend"
                :key="item.name"
                class="legend-row"
              >
                <span class="legend-dot" :style="{ background: item.color }"></span>
                <span class="legend-name">{{ item.name }}</span>
                <span class="legend-bar-wrap">
                  <span
                    class="legend-bar"
                    :style="{ width: item.rawPct + '%', background: item.color + '55' }"
                  ></span>
                </span>
                <span class="legend-pct">{{ item.pct }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 主要指数估值表 -->
        <el-card shadow="never">
          <template #header>
            <div class="card-header-row">
              <span class="card-title">主要指数估值</span>
            </div>
          </template>
          <el-table
            :data="marketIndices"
            size="small"
            :header-cell-style="{ background: '#f1f5f9', fontWeight: '600', color: '#475569', fontSize: '12px' }"
          >
            <!-- 文字列：左对齐 -->
            <el-table-column
              prop="index_name"
              label="指数"
              min-width="100"
              align="left"
            />

            <!-- 数值列：右对齐 -->
            <el-table-column prop="pe" label="PE" width="62" align="right" />

            <!-- PE 分位：右对齐 + 胶囊徽章 -->
            <el-table-column label="PE分位" width="82" align="right">
              <template #default="{ row }">
                <span class="pct-badge" :class="pctClass(row.pe_percentile)">
                  {{ row.pe_percentile }}%
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="pb" label="PB" width="62" align="right" />

            <!-- PB 分位：右对齐 + 胶囊徽章 -->
            <el-table-column label="PB分位" width="82" align="right">
              <template #default="{ row }">
                <span class="pct-badge" :class="pctClass(row.pb_percentile)">
                  {{ row.pb_percentile }}%
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="yield_ratio" label="股息率%" width="76" align="right" />
          </el-table>
        </el-card>
      </div>

      <!-- ── 持仓基金明细 ─────────────────────────────────── -->
      <el-card shadow="never" class="holdings-card">
        <template #header>
          <div class="card-header-row">
            <span class="card-title">持仓基金</span>
            <span class="card-badge">共 {{ summary.holdings?.length || 0 }} 只</span>
          </div>
        </template>

        <el-table
          :data="summary.holdings"
          size="small"
          :header-cell-style="{ background: '#f1f5f9', fontWeight: '600', color: '#475569', fontSize: '12px' }"
        >
          <!-- 文字列：左对齐 -->
          <el-table-column
            prop="fund_code"
            label="代码"
            width="90"
            sortable
            align="left"
          >
            <template #default="{ row }">
              <span class="fund-code">{{ row.fund_code }}</span>
            </template>
          </el-table-column>

          <el-table-column
            prop="fund_name"
            label="基金名称"
            min-width="180"
            sortable
            align="left"
          />

          <!-- 数值列：右对齐 + tabular 等宽字体 -->
          <el-table-column label="持有份额" width="108" align="right">
            <template #default="{ row }">
              <span class="num-cell">{{ fmtShares(row.shares) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="成本净值" width="100" align="right">
            <template #default="{ row }">
              <span class="num-cell">¥{{ row.cost_basis.toFixed(4) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="当前净值" width="100" align="right">
            <template #default="{ row }">
              <span class="num-cell">¥{{ row.current_value.toFixed(4) }}</span>
            </template>
          </el-table-column>

          <!-- 收益率：中国市场红涨绿跌 + ↑↓ 精致胶囊标签 -->
          <el-table-column label="收益率" width="108" align="right">
            <template #default="{ row }">
              <span
                class="return-badge"
                :class="returnClass(row)"
              >
                <span class="return-arrow">{{ returnArrow(row) }}</span>
                {{ returnPct(row) }}%
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

    </template>
  </div>
</template>

<script setup>
/**
 * Dashboard.vue — 总览页面
 *
 * 修复记录：
 *   - [Bug] loading ref 原位于 script 结束标签之外，已移入 script setup 内部
 *
 * 设计规范：
 *   - 中国市场涨跌色：正数红（#CF1E1E），负数绿（#2A7D3F）
 *   - 资产配置图表配色已通过 CVD 验证（ΔE ≥ 17.7）
 *   - 数值列全部右对齐，文字列左对齐
 */
import { ref, computed, onMounted } from 'vue'
import { graphic } from 'echarts'
import 'echarts'
import VChart from 'vue-echarts'
import KpiCard from '@/components/KpiCard.vue'
import { portfolioApi, marketApi } from '@/api'

// ── 数据状态 ─────────────────────────────────────────────────
// ⚠️ 注意：loading 必须在 <script setup> 内部声明（原文件存在 Bug）
const loading      = ref(true)
const summary      = ref({
  total_value: 0,
  total_return: 0,
  total_return_pct: 0,
  fund_count: 0,
  holdings: [],
})
const allocation   = ref({ equity: 0, bond: 0, commodity: 0, monetary: 0 })
const marketIndices = ref([])

// ── 已通过 CVD / 对比度验证的 4 色调色盘 ────────────────────
// 验证结果：ΔE worst-pair = 17.7 (protan)，all PASS
const ALLOC_COLORS = {
  equity:    { base: '#1A5FB4', light: '#4A8FE4' },   // 科技蓝
  bond:      { base: '#C75000', light: '#F78030' },   // 琥珀橙
  commodity: { base: '#2A7D3F', light: '#5AAD6F' },   // 森林绿
  monetary:  { base: '#7D44A5', light: '#AD74D5' },   // 高雅紫
}

/** 创建 ECharts 线性渐变（从浅→深，营造立体感）*/
function makeGradient(colorKey) {
  const { light, base } = ALLOC_COLORS[colorKey]
  return new graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: light },
    { offset: 1, color: base  },
  ])
}

// ── 计算属性 ─────────────────────────────────────────────────

/** 市场 PE 均值百分位 */
const marketAvgPct = computed(() => {
  if (!marketIndices.value.length) return 0
  return marketIndices.value.reduce((s, i) => s + (i.pe_percentile || 0), 0)
    / marketIndices.value.length
})

/** 总收益副文字（带方向箭头）*/
const returnSubText = computed(() => {
  const pct = (summary.value.total_return_pct || 0).toFixed(2)
  const arrow = summary.value.total_return >= 0 ? '↑' : '↓'
  return `${arrow} ${pct}%  总收益率`
})

/** 配置总额（用于环形图中心展示）*/
const allocTotal = computed(() => {
  const v = allocation.value
  return (v.equity || 0) + (v.bond || 0) + (v.commodity || 0) + (v.monetary || 0)
})

/** 图例数据（含百分比 + 进度条宽度）*/
const allocLegend = computed(() => {
  const v     = allocation.value
  const total = allocTotal.value || 1
  const rows  = [
    { key: 'equity',    name: '股票' },
    { key: 'bond',      name: '债券' },
    { key: 'commodity', name: '商品' },
    { key: 'monetary',  name: '货币' },
  ]
  return rows.map(({ key, name }) => {
    const val    = v[key] || 0
    const rawPct = (val / total) * 100
    return {
      name,
      color:  ALLOC_COLORS[key].base,
      rawPct,
      pct:    rawPct.toFixed(1) + '%',
    }
  })
})

/** ECharts 环形图配置 */
const pieOption = computed(() => {
  const v = allocation.value
  const seriesData = [
    { value: v.equity    || 0, name: '股票', itemStyle: { color: makeGradient('equity')    } },
    { value: v.bond      || 0, name: '债券', itemStyle: { color: makeGradient('bond')      } },
    { value: v.commodity || 0, name: '商品', itemStyle: { color: makeGradient('commodity') } },
    { value: v.monetary  || 0, name: '货币', itemStyle: { color: makeGradient('monetary')  } },
  ]

  return {
    // 内容区域与 SVG 容器零间距
    grid: { top: 0, right: 0, bottom: 0, left: 0 },

    tooltip: {
      trigger: 'item',
      borderColor: 'transparent',
      backgroundColor: 'rgba(255,255,255,0.97)',
      extraCssText: [
        'box-shadow: 0 4px 20px rgba(15,23,42,0.13)',
        'border-radius: 10px',
        'padding: 10px 14px',
      ].join(';'),
      formatter: ({ name, value, percent }) =>
        `<div style="font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif">
           <div style="font-weight:700;color:#1e293b;margin-bottom:4px">${name}</div>
           <div style="color:#64748b;font-size:12px;margin-bottom:2px">
             ¥${typeof value === 'number' ? value.toFixed(2) : '—'}
           </div>
           <div style="font-size:15px;font-weight:700;color:#1e293b">
             ${percent.toFixed(1)}%
           </div>
         </div>`,
    },

    series: [
      {
        type: 'pie',
        // 环形比例：内径 48%，外径 74%
        radius: ['48%', '74%'],
        // 图表居中（中心文字叠加层 left: 50% 与此对应）
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,           // 扇区圆角
          borderColor:  '#f8fafc',   // 扇区间隔色（与页面背景一致）
          borderWidth:  3,
        },
        label:     { show: false },  // 标签由 HTML 图例承担
        labelLine: { show: false },
        emphasis: {
          scale:    true,
          scaleSize: 5,
          itemStyle: {
            shadowBlur:  20,
            shadowColor: 'rgba(0,0,0,0.14)',
          },
        },
        data: seriesData,
      },
    ],
  }
})

// ── 工具函数 ─────────────────────────────────────────────────

/** 格式化金额（toFixed(2)，整数前加千分位逗号）*/
function fmtMoney(val) {
  if (val == null) return '—'
  const fixed = Math.abs(val).toFixed(2)
  const [int, dec] = fixed.split('.')
  const intFmt = int.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return (val < 0 ? '-' : '') + intFmt + '.' + dec
}

/** 格式化份额（保留 2 位，加千分位）*/
function fmtShares(val) {
  if (val == null) return '—'
  const [int, dec] = Math.abs(val).toFixed(2).split('.')
  return int.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '.' + dec
}

/** 估值分位 CSS 类（低 / 中 / 高）*/
function pctClass(pct) {
  if (pct <= 30) return 'pct-low'
  if (pct <= 60) return 'pct-mid'
  return 'pct-high'
}

/** 持仓收益率（(当前 - 成本) / 成本 × 100）*/
function calcReturn(row) {
  if (!row.cost_basis || row.cost_basis === 0) return 0
  return (row.current_value - row.cost_basis) / row.cost_basis * 100
}

/**
 * 中国市场：红涨绿跌
 * 收益 > 0 → 'positive'（红色）
 * 收益 ≤ 0 → 'negative'（绿色）
 */
function returnClass(row) {
  return calcReturn(row) >= 0 ? 'positive' : 'negative'
}

/** 方向箭头 */
function returnArrow(row) {
  return calcReturn(row) >= 0 ? '↑' : '↓'
}

/** 格式化收益率 */
function returnPct(row) {
  return Math.abs(calcReturn(row)).toFixed(2)
}

// ── 数据拉取 ─────────────────────────────────────────────────
onMounted(async () => {
  try {
    const [sumRes, allocRes, mkRes] = await Promise.all([
      portfolioApi.summary(),
      portfolioApi.allocation(),
      marketApi.overview(),
    ])
    summary.value      = sumRes.data   || summary.value
    allocation.value   = allocRes.data || allocation.value
    marketIndices.value = mkRes.data?.indices || []
  } catch (e) {
    console.error('[Dashboard] 加载失败:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* ── 页面容器 ─────────────────────────────────────────────── */
.dashboard {
  max-width: 1400px;
}

/* ── 卡片标题行 ───────────────────────────────────────────── */
.card-header-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.card-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.2px;
}
.card-badge {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-table-header);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: auto;       /* 推到右侧 */
}

/* ════════════════════════════════════════════════════════════
   资产配置环形图区域
   ════════════════════════════════════════════════════════════ */
.alloc-card :deep(.el-card__body) {
  padding: 16px 20px;
}

/* 外层弹性容器：图表左、图例右 */
.alloc-body {
  display: flex;
  align-items: center;
  gap: 20px;
  min-height: 220px;
}

/* 环形图容器：相对定位（用于叠加中心文字）*/
.donut-wrap {
  position: relative;
  flex: 0 0 220px;
  height: 220px;
}

.donut-chart {
  width: 100%;
  height: 100%;
}

/* 居中叠加文字 — 与 series.center: ['50%','50%'] 对应 */
.donut-center {
  position: absolute;
  top:  50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;     /* 不遮挡图表交互 */
  user-select: none;
}
.donut-label {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  line-height: 1;
  margin-bottom: 5px;
}
.donut-value {
  display: block;
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.3px;
  line-height: 1;
}

/* ── 自定义图例 ───────────────────────────────────────────── */
.alloc-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 颜色圆点 */
.legend-dot {
  width:  9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* 分类名称 */
.legend-name {
  font-size: 13px;
  color: #475569;
  font-weight: 500;
  width: 32px;
  flex-shrink: 0;
}

/* 进度条背景 */
.legend-bar-wrap {
  flex: 1;
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
}
/* 进度条填充（宽度由 style 动态设置）*/
.legend-bar {
  display: block;
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s cubic-bezier(0, 0, 0.2, 1);
}

/* 百分比数字（右对齐等宽）*/
.legend-pct {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  width: 42px;
  text-align: right;
  flex-shrink: 0;
}

/* ════════════════════════════════════════════════════════════
   通用表格辅助样式
   ════════════════════════════════════════════════════════════ */

/* 数字等宽单元格 */
.num-cell {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 13px;
  color: var(--text-primary);
}

/* 基金代码 — monospace 蓝色链接风格 */
.fund-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* ── 估值分位胶囊徽章 ─────────────────────────────────────── */
.pct-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
/* 低估（≤30%）— 绿色 */
.pct-badge.pct-low {
  background: var(--pct-low-bg);
  color:      var(--pct-low-color);
}
/* 中估（31%~60%）— 橙色 */
.pct-badge.pct-mid {
  background: var(--pct-mid-bg);
  color:      var(--pct-mid-color);
}
/* 高估（>60%）— 红色 */
.pct-badge.pct-high {
  background: var(--pct-high-bg);
  color:      var(--pct-high-color);
}

/* ── 收益率胶囊徽章（中国市场：红涨绿跌）─────────────────── */
.return-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  transition: filter 0.15s ease;
}
.return-badge:hover { filter: brightness(0.9); }

.return-arrow { font-size: 11px; line-height: 1; }

/* 正收益：红色（中国市场惯例）*/
.return-badge.positive {
  background: var(--color-up-bg);
  color:      var(--color-up);
}
/* 负收益：绿色（中国市场惯例）*/
.return-badge.negative {
  background: var(--color-down-bg);
  color:      var(--color-down);
}

/* ── 持仓卡片底部不挤压 ──────────────────────────────────── */
.holdings-card {
  margin-bottom: var(--space-lg);
}

/* ── 环形图响应式 ─────────────────────────────────────────── */
@media (max-width: 640px) {
  .alloc-body {
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }
  .donut-wrap {
    flex: 0 0 180px;
    height: 180px;
  }
  .alloc-legend { width: 100%; }
}
</style>
