<template>
  <!--
    KpiCard — 金融级 KPI 卡片
    ─────────────────────────────────────────────────────────────
    Props:
      label      — 小标签文字，如"总资产"
      value      — 核心数字，如"¥128,500.00"
      sub        — 副文字，如"+2.34% 总收益率"
      icon       — Element Plus 图标名称
      iconBg     — 图标背景色 / 渐变字符串（如 "linear-gradient(...)"）
      iconColor  — 图标本身颜色
      valueColor — 核心数字颜色（盈亏状态）
      trend      — 'up' | 'down' | '' 控制角标箭头
    ─────────────────────────────────────────────────────────────
  -->
  <el-card shadow="never" class="kpi-card">
    <div class="kpi-inner">

      <!-- 图标 — 圆形渐变背景 + 微动效 -->
      <div class="kpi-icon-wrap" :style="{ background: iconBg }">
        <el-icon :size="22" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </div>

      <!-- 内容区 -->
      <div class="kpi-body">
        <!-- 小标签 -->
        <span class="kpi-label">{{ label }}</span>

        <!-- 核心数字 -->
        <span class="kpi-value" :style="valueColor ? { color: valueColor } : {}">
          {{ value }}
        </span>

        <!-- 副文字（可含涨跌箭头） -->
        <span v-if="sub" class="kpi-sub">{{ sub }}</span>
      </div>

    </div>
  </el-card>
</template>

<script setup>
defineProps({
  /** 标签文字 */
  label: {
    type: String,
    default: '',
  },
  /** 核心数字（已格式化的字符串或数字） */
  value: {
    type: [String, Number],
    default: '—',
  },
  /** 副文字 */
  sub: {
    type: String,
    default: '',
  },
  /** Element Plus 图标组件名 */
  icon: {
    type: [String, Object],
    default: 'Coin',
  },
  /** 图标容器背景（支持渐变字符串） */
  iconBg: {
    type: String,
    default: 'linear-gradient(135deg, #dbeafe, #93c5fd)',
  },
  /** 图标颜色 */
  iconColor: {
    type: String,
    default: '#1A5FB4',
  },
  /** 核心数字颜色，空则使用主色 */
  valueColor: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
/* ── 卡片容器 ─────────────────────────────────────────────── */
.kpi-card {
  cursor: default;
  /* 悬浮提升由 global.css 中 .el-card:hover 统一处理 */
}
/* 去掉 el-card__body 默认 padding，由内部控制 */
.kpi-card :deep(.el-card__body) {
  padding: 20px 22px;
}

/* ── 内部弹性布局 ─────────────────────────────────────────── */
.kpi-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* ── 图标容器 — 圆形 + 渐变背景 ──────────────────────────── */
.kpi-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 50%;               /* 圆形 */
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.22s ease;
}
/* 卡片 hover 时图标轻微放大旋转 */
.kpi-card:hover .kpi-icon-wrap {
  transform: scale(1.10) rotate(-6deg);
  box-shadow: 0 4px 12px rgba(0,0,0,0.10);
}

/* ── 文字区 ───────────────────────────────────────────────── */
.kpi-body {
  display: flex;
  flex-direction: column;
  min-width: 0;       /* 防止长数字撑破布局 */
}

/* 小标签 — 减淡，退到背景层 */
.kpi-label {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;       /* 比 text-secondary 再淡一级 */
  letter-spacing: 0.3px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 核心数字 — 大字、等宽、强视觉 */
.kpi-value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;   /* 等宽数字，上下对齐 */
  letter-spacing: -0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 副文字 — 趋势、描述 */
.kpi-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── 响应式：中小屏缩小字号 ─────────────────────────────── */
@media (max-width: 768px) {
  .kpi-value { font-size: 22px; }
  .kpi-icon-wrap { width: 44px; height: 44px; }
  .kpi-card :deep(.el-card__body) { padding: 14px 16px; }
}
</style>
