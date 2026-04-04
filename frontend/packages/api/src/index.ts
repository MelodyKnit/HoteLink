import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

export interface ApiResult<T = unknown> {
  code: number
  message: string
  data: T
  request_id?: string
  timestamp?: string
}

export interface PaginatedData<T = unknown> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

const TOKEN_KEY = 'hotelink_access_token'
const REFRESH_KEY = 'hotelink_refresh_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

function createHttp(baseURL: string): AxiosInstance {
  const instance = axios.create({ baseURL, timeout: 30000 })

  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  instance.interceptors.response.use(
    (resp: AxiosResponse<ApiResult>) => {
      const body = resp.data
      if (body.code === 4011 || body.code === 4012) {
        clearTokens()
        window.location.href = '/admin/login'
      }
      return resp
    },
    (error) => {
      if (error.response?.status === 401) {
        clearTokens()
        window.location.href = '/admin/login'
      }
      return Promise.reject(error)
    }
  )

  return instance
}

const http = createHttp('/api/v1')

async function get<T = unknown>(url: string, params?: Record<string, unknown>): Promise<ApiResult<T>> {
  const resp = await http.get<ApiResult<T>>(url, { params })
  return resp.data
}

async function post<T = unknown>(url: string, data?: Record<string, unknown>): Promise<ApiResult<T>> {
  const resp = await http.post<ApiResult<T>>(url, data)
  return resp.data
}

// ========== System Init ==========
export const systemApi = {
  initCheck: () => get<{ initialized: boolean }>('/system/init-check'),
  initSetup: (data: { username: string; password: string; confirm_password: string }) =>
    post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number; user: { id: number; username: string; role: string } }>('/system/init-setup', data),
}

// ========== Auth ==========
export const authApi = {
  adminLogin: (data: { username: string; password: string }) =>
    post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number; user: { id: number; username: string; role: string } }>('/public/auth/admin-login', data),
  refresh: (refresh_token: string) =>
    post<{ access_token: string; token_type: string }>('/public/auth/refresh', { refresh_token }),
  logout: (refresh_token: string) =>
    post('/user/auth/logout', { refresh_token }),
  me: () =>
    get<{ id: number; username: string; nickname: string; mobile: string; email: string; role: string; status: string; member_level: string }>('/user/auth/me'),
}

// ========== Dashboard ==========
export const dashboardApi = {
  overview: () => get<{
    today_order_count: number; today_check_in_count: number; today_check_out_count: number
    today_revenue: number; month_revenue: number; occupancy_rate: number
    pending_review_count: number; pending_report_task_count: number
  }>('/admin/dashboard/overview'),
  charts: (params?: { start_date?: string; end_date?: string; date_type?: string }) =>
    get<{ items: { date: string; order_count: number; revenue: number }[] }>('/admin/dashboard/charts', params as Record<string, unknown>),
}

// ========== Hotels ==========
export const hotelApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/hotels', params),
  create: (data: Record<string, unknown>) => post('/admin/hotels/create', data),
  update: (data: Record<string, unknown>) => post('/admin/hotels/update', data),
  delete: (hotel_id: number) => post('/admin/hotels/delete', { hotel_id }),
}

// ========== Room Types ==========
export const roomTypeApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/room-types', params),
  create: (data: Record<string, unknown>) => post('/admin/room-types/create', data),
  update: (data: Record<string, unknown>) => post('/admin/room-types/update', data),
  delete: (room_type_id: number) => post('/admin/room-types/delete', { room_type_id }),
}

// ========== Inventory ==========
export const inventoryApi = {
  calendar: (params: Record<string, unknown>) => get<PaginatedData>('/admin/inventory/calendar', params),
  update: (data: Record<string, unknown>) => post('/admin/inventory/update', data),
}

// ========== Orders ==========
export const orderApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/orders', params),
  detail: (order_id: number) => get('/admin/orders/detail', { order_id }),
  changeStatus: (data: { order_id: number; target_status: string }) => post('/admin/orders/change-status', data),
  checkIn: (data: { order_id: number; room_no: string; operator_remark?: string }) => post('/admin/orders/check-in', data),
  checkOut: (data: { order_id: number; consume_amount?: number; operator_remark?: string }) => post('/admin/orders/check-out', data),
}

// ========== Reviews ==========
export const reviewApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/reviews', params),
  reply: (data: { review_id: number; content: string }) => post('/admin/reviews/reply', data),
}

// ========== Users ==========
export const userApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/users', params),
  changeStatus: (data: { user_id: number; status: string }) => post('/admin/users/change-status', data),
}

// ========== Employees ==========
export const employeeApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/employees', params),
  create: (data: Record<string, unknown>) => post('/admin/employees/create', data),
}

// ========== Reports ==========
export const reportApi = {
  tasks: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/reports/tasks', params),
  createTask: (data: Record<string, unknown>) => post('/admin/reports/tasks/create', data),
}

// ========== Settings ==========
export const settingsApi = {
  get: () => get('/admin/settings'),
  update: (data: Record<string, unknown>) => post('/admin/settings/update', data),
}

// ========== AI ==========
export const aiApi = {
  reportSummary: (data: Record<string, unknown>) => post('/admin/ai/report-summary', data),
  reviewSummary: (data: Record<string, unknown>) => post('/admin/ai/review-summary', data),
  replySuggestion: (review_id: number) => post('/admin/ai/reply-suggestion', { review_id }),
  settings: () => get('/admin/ai/settings'),
  updateSettings: (data: Record<string, unknown>) => post('/admin/ai/settings/update', data),
}

// ========== Common ==========
export const commonApi = {
  cities: () => get<{ items: { label: string; value: string }[] }>('/common/cities'),
  dicts: (types: string) => get('/common/dicts', { types }),
}
