import axios, { type AxiosInstance, type AxiosError } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const detail = error.response?.data as any
      // Don't redirect if it's a login error or TOTP error - let the login page handle it
      const detailStr = String(detail?.detail || '')
      const isLoginError = detailStr.includes('用户名') || detailStr.includes('密码') || detailStr.includes('credential')
      const isTotpError = detailStr.includes('TOTP') || detailStr.includes('验证码') || detailStr.includes('totp')
      if (!isLoginError && !isTotpError) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
