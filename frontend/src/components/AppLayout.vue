<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <div class="logo-area">
        <el-icon :size="24" color="#409eff"><TrendCharts /></el-icon>
        <span v-show="!isCollapse" class="logo-text">基金智能分析</span>
      </div>
      <el-menu
        :default-active="activeRoute"
        :collapse="isCollapse"
        :router="true"
        background-color="#1a1a2e"
        text-color="#b0b0c0"
        active-text-color="#409eff"
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
          <el-icon><Coin /></el-icon>
          <template #title>交易回测</template>
        </el-menu-item>
      </el-menu>

    <!-- Mobile Bottom Nav -->
      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon :size="18">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
    </el-aside>
    <div class="mobile-bottom-nav">
      <router-link to="/dashboard" class="nav-item" :class="{ active: $route.path === '/dashboard' }">
        <el-icon :size="20"><DataAnalysis /></el-icon>
        <span>总览</span>
      </router-link>
      <router-link to="/portfolio" class="nav-item" :class="{ active: $route.path === '/portfolio' }">
        <el-icon :size="20"><Coin /></el-icon>
        <span>持仓</span>
      </router-link>
      <router-link to="/funds" class="nav-item" :class="{ active: $route.path === '/funds' }">
        <el-icon :size="20"><Search /></el-icon>
        <span>基金</span>
      </router-link>
        <router-link to="/market" class="nav-item" :class="{ active: $route.path === '/market' }">
          <el-icon :size="20"><TrendCharts /></el-icon>
          <span>市场</span>
        </router-link>
        <router-link to="/backtest" class="nav-item" :class="{ active: $route.path === '/backtest' }">
          <el-icon :size="20"><Coin /></el-icon>
          <span>回测</span>
        </router-link>
      </div>


    <!-- 主区域 -->
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tag type="success" effect="plain" size="small">数据更新: {{ lastUpdate }}</el-tag>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapse = ref(false)

const activeRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')
const lastUpdate = ref(new Date().toLocaleDateString('zh-CN'))
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.app-aside {
  background-color: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.app-aside .el-menu {
  border-right: none;
  flex: 1;
}

/* Mobile Bottom Nav */
.mobile-bottom-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  z-index: 1000;
  padding: 4px 0;
  justify-content: space-around;
  align-items: center;
  box-shadow: 0 -2px 8px rgba(44,62,80,0.08);
}
.mobile-bottom-nav .nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 10px;
  transition: color 150ms ease;
  padding: 4px 12px;
}
.mobile-bottom-nav .nav-item.active,
.mobile-bottom-nav .nav-item:hover {
  color: var(--color-primary);
}
.mobile-bottom-nav .nav-item span { line-height: 1; }

@media (max-width: 768px) {
  .app-aside { display: none !important; }
  .mobile-bottom-nav { display: flex !important; }
  .app-main { padding-bottom: 64px !important; }
}

.collapse-btn {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b0b0c0;
  cursor: pointer;
  border-top: 1px solid rgba(255,255,255,0.06);
  transition: color 0.2s;
}
.collapse-btn:hover { color: #fff; }

.app-header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  height: 60px;
}

.app-main {
  background: #f0f2f5;
  padding: 20px 24px;
  overflow-y: auto;
}
</style>
