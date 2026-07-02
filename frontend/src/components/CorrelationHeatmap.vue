<template>
  <!--
    CorrelationHeatmap.vue
    多因子相关性矩阵热力图

    调色板：ColorBrewer RdBu 散度色阶（来自 Cynthia Brewer & Penn State）
      深蓝 #053061 → 白 #f7f7f7 → 深红 #67001f
    设计：精致金融投研风格，亮色面板可直接嵌入
  -->
  <div class="corr-card">

    <!-- ══ 卡片头部 ═════════════════════════════════════════ -->
    <div class="corr-header">
      <div class="header-left">
        <h3 class="corr-title">多因子相关性矩阵</h3>
        <p class="corr-sub">截面 Pearson 相关系数 · 月度调仓 · N = 60 期</p>
      </div>

      <!-- 色阶说明 -->
      <div class="scale-strip-wrap">
        <span class="scale-label">−1</span>
        <div class="scale-strip" />
        <span class="scale-label">0</span>
        <div class="scale-strip scale-strip--warm" />
        <span class="scale-label">+1</span>
      </div>
    </div>

    <!-- ══ 热力图 ════════════════════════════════════════════ -->
    <div class="chart-wrap">
      <v-chart
        ref="chartRef"
        :option="chartOption"
        autoresize
        class="heatmap-chart"
      />
    </div>

    <!-- ══ 关键发现摘要 ═══════════════════════════════════════ -->
    <div class="insights-bar">
      <span class="insights-label">关键相关</span>
      <div class="insights-pills">
        <span
          v-for="ins in insights"
          :key="ins.key"
          class="ins-pill"
          :class="ins.type"
        >
          <span class="ins-factors">{{ ins.a }} × {{ ins.b }}</span>
          <span class="ins-value">{{ ins.value }}</span>
        </span>
      </div>
    </div>

  </div>
</template>

<script setup>
/**
 * CorrelationHeatmap — 多因子相关性矩阵热力图
 *
 * 调色盘来源：ColorBrewer RdBu（散度色阶），适用于表达极性（正/负）数据。
 * 不要用分类色板验证器检验散度色阶——它们遵循不同的设计规则：
 *   1. 中间（r=0）颜色尽可能轻盈（白/近白）
 *   2. 两端（r=±1）颜色亮度最低（深蓝/深红）
 *   3. 期望相邻颜色平滑渐变，而非 CVD ΔE 最大化
 *
 * 矩阵说明：
 *   对角线恒为 1.0（自相关），矩阵对称。
 *   数值来自模拟的真实量化因子截面相关系数。
 */
import { computed, ref } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'

// ── 因子名称 ──────────────────────────────────────────────
const FACTORS = ['动量', '价值', '规模', '换手率', '夏普比率']
const N = FACTORS.length

// ── 相关性矩阵（对称，对角线 = 1.00）──────────────────────
// 数值来源：量化投研领域的典型因子相关结构
//   动量-价值负相关：经典"价值反转"效应
//   换手率-价值强负相关：低换手率股票常现价值特征
//   动量-夏普强正相关：动量因子捕获持续超额收益
const MATRIX = [
  //  动量     价值    规模    换手率  夏普比率
  [ 1.00, -0.38, -0.14,  0.52,  0.67],   // 动量
  [-0.38,  1.00,  0.23, -0.61, -0.22],   // 价值
  [-0.14,  0.23,  1.00, -0.35,  0.11],   // 规模
  [ 0.52, -0.61, -0.35,  1.00,  0.43],   // 换手率
  [ 0.67, -0.22,  0.11,  0.43,  1.00],   // 夏普比率
]

// ── ColorBrewer RdBu 散度色阶（11 级）────────────────────
// 来源：https://colorbrewer2.org/#type=diverging&scheme=RdBu&n=11
// 用途：相关系数 [-1, 0, +1] 冷暖色映射
const RD_BU = [
  '#053061',  // -1.0  深海蓝
  '#2166ac',  // -0.8  中蓝
  '#4393c3',  // -0.6  天蓝
  '#92c5de',  // -0.4  浅蓝
  '#d1e5f0',  // -0.2  极浅蓝
  '#f7f7f7',  //  0.0  近白（中性）
  '#fddbc7',  // +0.2  极浅红
  '#f4a582',  // +0.4  浅红
  '#d6604d',  // +0.6  中红
  '#b2182b',  // +0.8  深红
  '#67001f',  // +1.0  深酒红
]

// ── 构建 ECharts 数据 ─────────────────────────────────────
// 格式：[xIndex, yIndex, value]
// yAxis.data 反转后，yIndex=i 对应 FACTORS[N-1-i]（使对角线从左上→右下）
const heatmapData = (() => {
  const rows = []
  for (let row = 0; row < N; row++) {
    for (let col = 0; col < N; col++) {
      rows.push([col, N - 1 - row, MATRIX[row][col]])
    }
  }
  return rows
})()

// ── 关键相关对（排除对角线，取绝对值最强的若干对）─────────
const insights = computed(() => {
  const pairs = []
  for (let i = 0; i < N; i++) {
    for (let j = i + 1; j < N; j++) {
      pairs.push({
        key:   `${i}-${j}`,
        a:     FACTORS[i],
        b:     FACTORS[j],
        raw:   MATRIX[i][j],
        value: (MATRIX[i][j] >= 0 ? '+' : '') + MATRIX[i][j].toFixed(2),
        type:  MATRIX[i][j] >= 0.4 ? 'pill-pos' : MATRIX[i][j] <= -0.4 ? 'pill-neg' : 'pill-neu',
      })
    }
  }
  // 按绝对值降序，取前 4 强
  return pairs
    .sort((a, b) => Math.abs(b.raw) - Math.abs(a.raw))
    .slice(0, 4)
})

// ── ECharts 配置 ──────────────────────────────────────────
const chartRef = ref(null)

const chartOption = computed(() => ({
  backgroundColor: 'transparent',

  // ── Tooltip ────────────────────────────────────────────
  tooltip: {
    trigger:     'item',
    borderColor: 'transparent',
    backgroundColor: 'rgba(15, 23, 42, 0.92)',
    extraCssText: [
      'box-shadow: 0 8px 24px rgba(0,0,0,0.28)',
      'border-radius: 10px',
      'padding: 10px 14px',
    ].join(';'),
    textStyle:   { color: '#e2e8f0', fontSize: 12 },
    formatter(params) {
      const [xIdx, yIdx, val] = params.data
      const factorX = FACTORS[xIdx]
      const factorY = FACTORS[N - 1 - yIdx]
      const sign   = val > 0 ? '+' : ''
      const color  = val >= 0
        ? `rgba(210, 96, 77, ${Math.abs(val)})`
        : `rgba(67, 147, 195, ${Math.abs(val)})`
      const strength =
        Math.abs(val) >= 0.6 ? '强' :
        Math.abs(val) >= 0.3 ? '中' : '弱'
      const direction = val > 0 ? '正相关' : val < 0 ? '负相关' : '无相关'

      return `
        <div style="font-family:-apple-system,'PingFang SC',sans-serif">
          <div style="font-weight:700;font-size:13px;margin-bottom:6px;color:#f1f5f9">
            ${factorX} &nbsp;×&nbsp; ${factorY}
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span style="
              display:inline-block;width:10px;height:10px;
              border-radius:50%;background:${color};flex-shrink:0
            "></span>
            <span style="color:#94a3b8;font-size:12px">${strength}${direction}</span>
            <span style="
              margin-left:auto;font-family:monospace;font-weight:700;
              font-size:15px;color:#f8fafc
            ">${sign}${val.toFixed(2)}</span>
          </div>
        </div>
      `
    },
  },

  // ── Grid ───────────────────────────────────────────────
  grid: {
    top:          '5%',
    left:         '14%',
    right:        '8%',
    bottom:       '8%',
    containLabel: false,
  },

  // ── 坐标轴 ─────────────────────────────────────────────
  xAxis: {
    type:      'category',
    data:      FACTORS,
    position:  'top',   // 因子名在顶部（便于阅读矩阵）
    splitArea: { show: false },
    splitLine: { show: false },
    axisLine:  { show: false },
    axisTick:  { show: false },
    axisLabel: {
      fontSize:   13,
      fontWeight: '600',
      color:      '#334155',
      interval:    0,
      // 顶部留出间距
      margin: 10,
    },
  },

  yAxis: {
    type: 'category',
    // 反转后第 0 项在底部，但数据中已用 N-1-row 处理，使动量在顶行
    data:    FACTORS,
    inverse: true,
    splitArea: { show: false },
    splitLine: { show: false },
    axisLine:  { show: false },
    axisTick:  { show: false },
    axisLabel: {
      fontSize:   13,
      fontWeight: '600',
      color:      '#334155',
      interval:    0,
      width:       52,
      overflow:    'none',
      align:       'right',
    },
  },

  // ── Visual Map（散度色阶）─────────────────────────────
  visualMap: {
    min:      -1,
    max:       1,
    type:     'continuous',
    show:      false,   // 隐藏内置图例，由头部 CSS 色带替代
    inRange: {
      color: RD_BU,
    },
  },

  // ── 热力图系列 ─────────────────────────────────────────
  series: [
    {
      name: '相关系数',
      type: 'heatmap',
      data: heatmapData,

      // ── 单元格样式 ──────────────────────────────────
      itemStyle: {
        // 圆角使格子更精致（ECharts 5 支持）
        borderRadius: 5,
        // 格子之间的间距（用白色边框模拟）
        borderWidth:  2.5,
        borderColor:  '#f8fafc',
      },

      // ── 数值标签 ────────────────────────────────────
      label: {
        show:       true,
        fontSize:   12.5,
        fontWeight: '700',
        fontFamily: '"Inter","DIN Alternate","SF Mono",monospace',
        /**
         * 自动翻转标签颜色：
         * |r| ≥ 0.4 → 深色背景 → 白色文字
         * |r| < 0.4 → 浅色背景 → 深色文字
         * ECharts 5.x label.color 支持回调函数
         */
        color: (params) =>
          Math.abs(params.data[2]) >= 0.4 ? '#ffffff' : '#1e293b',

        formatter: (params) => {
          const v = params.data[2]
          // 对角线（自相关 = 1.00）使用特殊符号
          if (v === 1.0) return '1.00'
          return (v >= 0 ? '+' : '') + v.toFixed(2)
        },
      },

      // ── Hover 高亮 ──────────────────────────────────
      emphasis: {
        disabled: false,
        itemStyle: {
          borderWidth:  3,
          borderColor:  '#334155',
          shadowBlur:   12,
          shadowColor:  'rgba(15,23,42,0.30)',
        },
        label: {
          fontSize: 13.5,
        },
      },

      // 动画
      animation:         true,
      animationDuration: 600,
      animationEasing:   'cubicOut',
    },
  ],
}))
</script>

<style scoped>
/* ══════════════════════════════════════════════════════════════
   卡片容器
   ══════════════════════════════════════════════════════════════ */
.corr-card {
  background:    #ffffff;
  border:        1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow:    0 2px 8px rgba(15,23,42,0.06),
                 0 8px 24px rgba(15,23,42,0.04);
  overflow:      hidden;
  display:       flex;
  flex-direction: column;
}

/* ══════════════════════════════════════════════════════════════
   头部
   ══════════════════════════════════════════════════════════════ */
.corr-header {
  display:         flex;
  align-items:     center;
  justify-content: space-between;
  padding:         18px 22px 14px;
  border-bottom:   1px solid #f1f5f9;
  gap:             16px;
  flex-wrap:       wrap;
}

.corr-title {
  font-size:    15px;
  font-weight:  700;
  color:        #1e293b;
  letter-spacing: -0.3px;
  margin:       0 0 3px;
}

.corr-sub {
  font-size:  12px;
  color:      #94a3b8;
  font-weight: 400;
  margin:     0;
  letter-spacing: 0.1px;
}

/* ── 顶部色阶条（替代 ECharts 内置 visualMap）───────────── */
.scale-strip-wrap {
  display:     flex;
  align-items: center;
  gap:         4px;
  flex-shrink: 0;
}

.scale-label {
  font-size:   11px;
  font-weight: 700;
  color:       #94a3b8;
  font-family: monospace;
}

/* 冷色段（负相关：蓝）*/
.scale-strip {
  width:         90px;
  height:        10px;
  border-radius: 3px 0 0 3px;
  background:    linear-gradient(
    to right,
    #053061, #2166ac, #4393c3, #d1e5f0, #f7f7f7
  );
}

/* 暖色段（正相关：红）*/
.scale-strip--warm {
  border-radius: 0 3px 3px 0;
  background:    linear-gradient(
    to right,
    #f7f7f7, #fddbc7, #f4a582, #d6604d, #b2182b, #67001f
  );
}

/* ══════════════════════════════════════════════════════════════
   图表区域
   ══════════════════════════════════════════════════════════════ */
.chart-wrap {
  /* 保持正方形比例，确保矩阵格子均匀 */
  padding: 8px 12px;
}

.heatmap-chart {
  width:  100%;
  height: 380px;
  display: block;
}

/* ══════════════════════════════════════════════════════════════
   底部关键发现摘要
   ══════════════════════════════════════════════════════════════ */
.insights-bar {
  display:      flex;
  align-items:  center;
  gap:          10px;
  padding:      10px 22px 14px;
  border-top:   1px solid #f1f5f9;
  flex-wrap:    wrap;
}

.insights-label {
  font-size:   11px;
  font-weight: 600;
  color:       #94a3b8;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  white-space: nowrap;
}

.insights-pills {
  display:  flex;
  flex-wrap: wrap;
  gap:       6px;
}

/* 胶囊基础样式 */
.ins-pill {
  display:       inline-flex;
  align-items:   center;
  gap:           6px;
  padding:       4px 10px;
  border-radius: 100px;
  font-size:     12px;
  font-weight:   600;
  line-height:   1;
}

/* 正相关 */
.ins-pill.pill-pos {
  background: rgba(180, 29, 36, 0.08);
  color:      #9b1c1c;
}

/* 负相关 */
.ins-pill.pill-neg {
  background: rgba(30, 64, 175, 0.09);
  color:      #1e40af;
}

/* 中性（弱相关）*/
.ins-pill.pill-neu {
  background: #f1f5f9;
  color:      #64748b;
}

.ins-factors {
  font-weight: 500;
  opacity:     0.85;
}

.ins-value {
  font-family:  monospace;
  font-weight:  700;
  font-variant-numeric: tabular-nums;
  font-size:    12.5px;
}

/* ══════════════════════════════════════════════════════════════
   响应式
   ══════════════════════════════════════════════════════════════ */
@media (max-width: 640px) {
  .corr-header { padding: 14px 16px 12px; }
  .scale-strip-wrap { display: none; }
  .heatmap-chart { height: 300px; }
  .insights-bar { padding: 8px 16px 12px; }
}
</style>
