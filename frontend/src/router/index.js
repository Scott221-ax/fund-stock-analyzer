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
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('@/views/Backtest.vue'),
    meta: { title: '交易回测', icon: 'DataBoard' },
  },
  {
    path: '/factor-mining',
    name: 'FactorMining',
    component: () => import('@/views/FactorMining.vue'),
    meta: { title: '因子发掘', icon: 'MagicStick' },
  },
  {
    path: '/fund-penetration',
    name: 'FundPenetration',
    component: () => import('@/views/FundPenetration.vue'),
    meta: { title: '盘中估值', icon: 'Odometer' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
