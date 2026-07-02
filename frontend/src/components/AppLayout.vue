<template>
  <el-container class="layout-container">

    <!-- ══ 侧边栏 ══════════════════════════════════════════════ -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">

      <!-- Logo 区 -->
      <div class="logo-area" :class="{ collapsed: isCollapse }">
        <div class="logo-icon-wrap">
          <el-icon :size="18" color="#60a5fa"><TrendCharts /></el-icon>
        </div>
        <transition name="logo-fade">
          <span v-show="!isCollapse" class="logo-text">基金智能分析</span>
        </transition>
      </div>

      <!-- 导航菜单：背景/文字/激活色通过 global.css 统一管理 -->
      <el-menu
        :default-active="activeRoute"
        :collapse="isCollapse"
        :router="true"
        background-color="#1e222b"
        text-color="#94a3b8"
        active-text-color="#60a5fa"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>总览</template>
        </el-menu-item>

        <el-menu-item index="/portfolio">
          <el-icon><Coin /></el-icon>
          <template #title>持仓分析</template>
        </el-menu-item>

        <el-menu-item index="/funds">
          <el-icon><Search /></el-icon>
          <template #title>基金池</template>
        </el-menu-item>

        <el-menu-item index="/market">
          <el-icon><TrendCharts /></el-icon>
          <template #title>市场扫描</template>
        </el-menu-item>

        <el-menu-item index="/backtest">
          <el-icon><DataBoard /></el-icon>
          <template #title>交易回测</template>
        </el-menu-item>

        <el-menu-item index="/factor-mining">
          <el-icon><MagicStick /></el-icon>
          <template #title>因子发掘</template>
        </el-menu-item>

        <el-menu-item index="/fund-penetration">
          <el-icon><Odometer /></el-icon>
          <template #title>盘中估值</template>
        </el-menu-item>
      </el-menu>

      <!-- 折叠/展开按钮 -->
      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon :size="16">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
        <transition name="logo-fade">
          <span v-show="!isCollapse" class="collapse-text">收起菜单</span>
        </transition>
      </div>
    </el-aside>

    <!-- ══ 主区域 ═══════════════════════════════════════════════ -->
    <el-container>

      <!-- 顶部 Header -->
      <el-header class="app-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <span class="update-tag">
            <span class="update-dot"></span>
            数据更新：{{ lastUpdate }}
          </span>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- ══ 移动端底部导航 ════════════════════════════════════════ -->
    <div class="mobile-bottom-nav">
      <router-link
        v-for="item in mobileNavItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: $route.path === item.path }"
      >
        <el-icon :size="20"><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </router-link>
    </div>

  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route     = useRoute()
const isCollapse = ref(false)

const activeRoute  = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')
const lastUpdate   = ref(new Date().toLocaleDateString('zh-CN'))

/** 移动端导航项配置 */
const mobileNavItems = [
  { path: '/dashboard',     icon: 'DataAnalysis', label: '总览'   },
  { path: '/portfolio',     icon: 'Coin',         label: '持仓'   },
  { path: '/funds',         icon: 'Search',       label: '基金'   },
  { path: '/market',        icon: 'TrendCharts',  label: '市场'   },
  { path: '/backtest',      icon: 'DataBoard',    label: '回测'   },
  { path: '/factor-mining',    icon: 'MagicStick',   label: '因子'   },
  { path: '/fund-penetration', icon: 'Odometer',     label: '估值'   },
]
</script>

<style scoped>
/* ── 整体布局 ────────────────────────────────────────────── */
.layout-container { height: 100vh; overflow: hidden; }

/* ── 侧边栏 ──────────────────────────────────────────────── */
.app-aside {
  background: #1e222b;
  display: flex;
  flex-direction: column;
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: 2px 0 12px rgba(0,0,0,0.18);
  z-index: 100;
}

/* Logo 区 */
.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.logo-area.collapsed { padding: 0; justify-content: center; }

.logo-icon-wrap {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, rgba(99,160,255,0.2), rgba(37,99,235,0.3));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(99,160,255,0.2);
}

.logo-text {
  color: #f1f5f9;
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: 0.3px;
}

/* 菜单 */
.sidebar-menu {
  flex: 1;
  border-right: none !important;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 0;
}
/* 隐藏菜单内部多余边框 */
.sidebar-menu :deep(.el-menu) { border-right: none !important; }

/* 折叠/展开按钮 */
.collapse-btn {
  height: 44px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 18px;
  color: #64748b;
  cursor: pointer;
  border-top: 1px solid rgba(255,255,255,0.05);
  transition: color 0.2s ease, background 0.2s ease;
  flex-shrink: 0;
  font-size: 12px;
}
.collapse-btn:hover { color: #94a3b8; background: rgba(255,255,255,0.04); }
.collapse-text { white-space: nowrap; }

/* ── 顶部 Header ──────────────────────────────────────────── */
.app-header {
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: 60px;
  border-bottom: 1px solid #e9eef5;
  box-shadow: 0 1px 6px rgba(15,23,42,0.05);
  flex-shrink: 0;
}

.header-left :deep(.el-breadcrumb__item .el-breadcrumb__inner) {
  color: var(--text-secondary);
  font-size: 13px;
  transition: color 0.15s;
}
.header-left :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--text-primary);
  font-weight: 600;
}

/* 数据更新标签 */
.update-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  font-size: 12px;
  font-weight: 500;
}
.update-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1;   transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.8); }
}

/* ── 主内容区 ─────────────────────────────────────────────── */
.app-main {
  background: var(--bg-body);
  padding: 24px 28px;
  overflow-y: auto;
}

/* ── Logo 文字过渡 ─────────────────────────────────────────── */
.logo-fade-enter-active, .logo-fade-leave-active {
  transition: opacity 0.2s ease, width 0.25s ease;
  overflow: hidden;
}
.logo-fade-enter-from, .logo-fade-leave-to { opacity: 0; width: 0; }
.logo-fade-enter-to,   .logo-fade-leave-from { opacity: 1; }

/* ── 移动端底部导航 ────────────────────────────────────────── */
.mobile-bottom-nav {
  display: none;
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 58px;
  background: #ffffff;
  border-top: 1px solid #e9eef5;
  box-shadow: 0 -4px 16px rgba(15,23,42,0.07);
  z-index: 1000;
  padding: 4px 0;
  justify-content: space-around;
  align-items: center;
}
.mobile-bottom-nav .nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 10px;
  padding: 4px 14px;
  border-radius: 10px;
  transition: color 0.15s ease, background 0.15s ease;
}
.mobile-bottom-nav .nav-item.active,
.mobile-bottom-nav .nav-item:hover {
  color: var(--color-primary);
}
.mobile-bottom-nav .nav-item.active {
  background: var(--color-primary-light);
}

@media (max-width: 768px) {
  .app-aside        { display: none !important; }
  .mobile-bottom-nav { display: flex !important; }
  .app-main         { padding: 16px 16px 72px; }
}
</style>
