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
      </el-menu>
      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon :size="18">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
    </el-aside>

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
  background-color: #1a1a2e;
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
