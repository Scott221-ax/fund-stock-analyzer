import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200 && res.code !== undefined) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    const msg = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// ─── 持仓分析 API ──────────────────────────────
export const portfolioApi = {
  summary: () => api.get('/portfolio/summary'),
  holdings: () => api.get('/portfolio/holdings'),
  saveHoldings: (data) => api.put('/portfolio/holdings', data),
  allocation: () => api.get('/portfolio/allocation'),
  sectors: () => api.get('/portfolio/sectors'),
  overlap: () => api.get('/portfolio/overlap'),
  risk: () => api.get('/portfolio/risk'),
}

// ─── 基金数据 API ──────────────────────────────
export const fundApi = {
  search: (keyword) => api.get('/funds/search', { params: { keyword } }),
  evaluate: (code) => api.get(`/funds/evaluate/${code}`),
  compare: (codes) => api.get('/funds/compare', { params: { codes: codes.join(',') } }),
  nav: (code) => api.get(`/funds/nav/${code}`),
  position: (code) => api.get(`/funds/position/${code}`),
}

// ─── 市场扫描 API ──────────────────────────────
export const marketApi = {
  overview: () => api.get('/market/overview'),
  sectors: () => api.get('/market/sectors'),
  undervalued: () => api.get('/market/undervalued'),
  northFlow: () => api.get('/market/north-flow'),
}

// ─── 交易回测 API ──────────────────────────────
export const backtestApi = {
  run:     (data) => api.post('/backtest/run', data),
  presets: ()     => api.get('/backtest/presets'),
}

// ─── 策略管理 API ──────────────────────────────
export const strategyApi = {
  /** 获取所有策略列表（按创建时间倒序）*/
  list:   ()         => api.get('/strategies'),
  /** 按 ID 获取单条策略 */
  get:    (id)       => api.get(`/strategies/${id}`),
  /** 新建策略 */
  create: (data)     => api.post('/strategies', data),
  /** 全量更新策略 */
  update: (id, data) => api.put(`/strategies/${id}`, data),
  /** 删除策略 */
  delete: (id)       => api.delete(`/strategies/${id}`),
}

// ─── 因子发掘 API ──────────────────────────────
export const factorApi = {
  /** 运行因子发掘，返回五分组净值曲线 + IC/IR 等指标 */
  mine: (data) => api.post('/factor/mine', data),
}

// ─── 基金穿透实时估值 API ──────────────────────
export const fundValuationApi = {
  /** 获取基金穿透实时估值（含持仓明细）*/
  get:      (code, refresh = false) =>
    api.get(`/fund-valuation/${code}`, { params: { refresh } }),
  /** 仅获取持仓快照（无实时行情，速度快）*/
  holdings: (code) => api.get(`/fund-valuation/${code}/holdings`),
}

export default api
