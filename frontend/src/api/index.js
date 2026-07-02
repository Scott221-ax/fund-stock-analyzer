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

// 交易回测 API
export const backtestApi = {
  run: (data) => api.post('/backtest/run', data),
  presets: () => api.get('/backtest/presets'),
}

export default api
