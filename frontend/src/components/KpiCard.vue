<template>
  <el-card shadow="never" class="kpi-card">
    <div class="kpi-inner">
      <div class="kpi-icon" :style="{ background: iconBg }">
        <el-icon :size="24" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </div>
      <div class="kpi-info">
        <span class="kpi-label">{{ label }}</span>
        <span class="kpi-value" :style="{ color: valueColor }">{{ value }}</span>
        <span v-if="sub" class="kpi-sub">{{ sub }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  value: { type: [String, Number], default: '' },
  sub: { type: String, default: '' },
  icon: { type: [String, Object], default: 'Coin' },
  iconBg: { type: String, default: '#e6f7ff' },
  iconColor: { type: String, default: '#1890ff' },
  valueColor: { type: String, default: '#1a1a2e' },
})
</script>

<style scoped>
.kpi-card {
  transition: all var(--duration-normal) var(--ease-spring);
  cursor: default;
}
.kpi-card:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: var(--shadow-lg) !important;
}
.kpi-card :deep(.el-card__body) { padding: var(--space-md); }
.kpi-inner {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}
.kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--border-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--duration-fast) var(--ease-spring);
}
.kpi-card:hover .kpi-icon {
  transform: scale(1.08) rotate(-3deg);
}
.kpi-info {
  display: flex;
  flex-direction: column;
}
.kpi-label {
  font-size: var(--font-size-small);
  color: var(--text-secondary);
  margin-bottom: 2px;
}
.kpi-value {
  font-size: var(--font-size-h1);
  font-weight: 700;
  line-height: 1.3;
}
.kpi-sub {
  font-size: var(--font-size-small);
  color: var(--text-muted);
  margin-top: 2px;
}
</style>
