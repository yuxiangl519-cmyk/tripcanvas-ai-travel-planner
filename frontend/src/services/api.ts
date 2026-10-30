import axios from 'axios'
import type { TripFormData, TripPlanResponse } from '@/types'

const API_BASE_URL = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || '')

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

/**
 * 生成旅行计划
 */
export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const { data: job } = await apiClient.post<{ id: string }>('/api/trip/plan/jobs', formData)
    const deadline = Date.now() + 600000
    let connectionFailures = 0
    while (Date.now() < deadline) {
      try {
        const { data } = await apiClient.get<{ status: 'pending' | 'completed'; result?: TripPlanResponse }>(`/api/trip/plan/jobs/${job.id}`)
        connectionFailures = 0
        if (data.status === 'completed') return data.result!
      } catch (error: any) {
        // Retry temporary tunnel/network failures, but surface backend validation and task errors.
        if (error.response?.data?.detail || ++connectionFailures >= 5) throw error
      }
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
    throw new Error('行程生成等待超时，请稍后重试')
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '生成旅行计划失败')
  }
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient

