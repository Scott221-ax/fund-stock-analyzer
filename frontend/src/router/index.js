import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '总览', icon: 'DataAnalysis' },
  },
  {
    path: '/portfolio',
    name: 'Portfolio',
    component: () => import('@/views/Portfolio.vue'),
    meta: { title: '持仓分析', icon: 'Coin' },
  },
  {
    path: '/funds',
    name: 'Funds',
    component: () => import('@/views/Funds.vue'),
    meta: { title: '基金池', icon: 'Search' },
  },
  {
    path: '/market',
    name: 'MarketScan',
    component: () => import('@/views/MarketScan.vue'),
    meta: { title: '市场扫描', icon: 'TrendCharts' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
