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

let _loginRedirect = '/admin/login'

// 处理 configureApi 业务流程。
export function configureApi(options: { loginRedirect?: string }) {
  if (options.loginRedirect) _loginRedirect = options.loginRedirect
}

// 处理 getToken 业务流程。
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

// 设置 Tokens 状态。
export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

// 清理 Tokens 状态。
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

// 处理 getRefreshToken 业务流程。
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

// 创建 Http 资源。
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
        window.location.href = _loginRedirect
      }
      return resp
    },
    (error) => {
      if (error.response?.status === 401) {
        clearTokens()
        window.location.href = _loginRedirect
      }
      const serverMessage: string =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        '请求失败'
      const serverCode: number = error.response?.data?.code ?? error.response?.status ?? 5000
      const fallback: ApiResult = { code: serverCode, message: serverMessage, data: null }
      return Promise.resolve({ data: fallback })
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

async function del<T = unknown>(url: string, data?: Record<string, unknown>): Promise<ApiResult<T>> {
  const resp = await http.delete<ApiResult<T>>(url, { data })
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

// ========== System ==========
export const adminSystemApi = {
  reset: (confirm: string) => post<{ reset: boolean; deleted_counts: Record<string, number>; message: string }>('/admin/system/reset', { confirm }),
}

// ========== Admin Coupons ==========
export const adminCouponApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/admin/coupons', params),
  create: (data: Record<string, unknown>) => post('/admin/coupons/create', data),
  update: (data: { template_id: number; status: string }) => post('/admin/coupons/update', data),
}

// ========== Admin Members ==========
export const adminMemberApi = {
  overview: () => get<{ levels: unknown[]; total_users: number }>('/admin/members/overview'),
}

// ========== AI ==========
export const aiApi = {
  reportSummary: (data: Record<string, unknown>) => post('/admin/ai/report-summary', data),
  reviewSummary: (data: Record<string, unknown>) => post('/admin/ai/review-summary', data),
  replySuggestion: (payload: number | { review_id: number }) =>
    post('/admin/ai/reply-suggestion', typeof payload === 'number' ? { review_id: payload } : payload),
  settings: () => get<{
    ai_enabled: boolean
    active_provider: string
    providers: { name: string; label: string; base_url: string; api_key_configured: boolean; chat_model: string; reasoning_model: string; timeout: number; is_active: boolean }[]
    builtin_providers: string[]
    current_provider: Record<string, unknown> | null
  }>('/admin/ai/settings'),
  updateSettings: (data: Record<string, unknown>) => post('/admin/ai/settings/update', data),
  addProvider: (data: { name: string; label?: string; base_url: string; api_key?: string; chat_model: string; reasoning_model?: string; timeout?: number }) =>
    post('/admin/ai/provider/add', data),
  switchProvider: (provider_name: string) => post('/admin/ai/provider/switch', { provider_name }),
  deleteProvider: (provider_name: string) => post('/admin/ai/provider/delete', { provider_name }),
}

// ========== Common ==========
export const commonApi = {
  cities: () => get<{ items: { label: string; value: string }[] }>('/common/cities'),
  dicts: (types: string) => get('/common/dicts', { types }),
  upload: (file: File, scene: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('scene', scene)
    return http.post<ApiResult<{ file_name: string; file_url: string; scene: string }>>('/common/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}

// ========== Public (User-Web) ==========
export const publicApi = {
  home: () => get<{
    banners: { id: number; image_url: string; link: string }[]
    hot_cities: string[]
    recommended_hotels: { id: number; name: string; city: string; star: number; image_url: string; min_price: number; rating: number; review_count: number; address: string; tags: string[] }[]
    promotions: { id: number; title: string; image_url: string; link: string }[]
  }>('/public/home'),
  hotels: (params?: Record<string, unknown>) => get<PaginatedData>('/public/hotels', params),
  searchSuggest: (keyword: string) => get<{ items: { label: string; type: string }[] }>('/public/hotels/search-suggest', { keyword }),
  hotelDetail: (hotel_id: number) => get('/public/hotels/detail', { hotel_id }),
  hotelReviews: (params: Record<string, unknown>) => get<PaginatedData>('/public/hotels/reviews', params),
  roomTypeCalendar: (params: { room_type_id: number; start_date: string; end_date: string }) =>
    get<{ room_type_id: number; calendar: { date: string; price: number; stock: number; status: string }[] }>('/public/room-types/calendar', params as Record<string, unknown>),
}

// ========== User Auth ==========
export const userAuthApi = {
  login: (data: { username: string; password: string }) =>
    post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number; user: { id: number; username: string; role: string; nickname?: string; member_level?: string } }>('/public/auth/login', data),
  register: (data: { username: string; password: string; confirm_password: string; mobile: string; email?: string }) =>
    post<{ user_id: number; username: string }>('/public/auth/register', data),
  me: () => get<{ id: number; username: string; nickname: string; mobile: string; email: string; role: string; status: string; member_level: string; avatar?: string; gender?: string; birthday?: string }>('/user/auth/me'),
  logout: (refresh_token: string) => post('/user/auth/logout', { refresh_token }),
}

// ========== User Profile ==========
export const userProfileApi = {
  get: () => get<{ id: number; username: string; nickname: string; mobile: string; email: string; gender: string; birthday: string; avatar: string; member_level: string; points: number }>('/user/profile'),
  update: (data: Record<string, unknown>) => post('/user/profile/update', data),
  uploadAvatar: (file: File) => {
    const fd = new FormData()
    fd.append('avatar', file)
    return http.post<ApiResult>('/user/profile/avatar', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
  },
  changePassword: (data: { old_password: string; new_password: string; confirm_password: string }) =>
    post('/user/profile/change-password', data),
}

// ========== User Orders ==========
export const userOrderApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/user/orders', params),
  guestHistory: (params?: { limit?: number }) => get<{ items: { guest_name: string; guest_mobile: string; masked_mobile: string }[] }>('/user/orders/guest-history', params as Record<string, unknown>),
  detail: (order_id: number) => get('/user/orders/detail', { order_id }),
  create: (data: Record<string, unknown>) => post('/user/orders/create', data),
  update: (data: Record<string, unknown>) => post('/user/orders/update', data),
  pay: (data: { order_id: number; payment_method: string }) => post('/user/orders/pay', data),
  cancel: (data: { order_id: number; reason: string }) => post('/user/orders/cancel', data),
}

// ========== User Reviews ==========
export const userReviewApi = {
  create: (data: { order_id: number; score: number; content: string }) => post('/user/reviews/create', data),
}

// ========== User Favorites ==========
export const userFavoriteApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/user/favorites', params),
  add: (hotel_id: number) => post('/user/favorites/add', { hotel_id }),
  remove: (hotel_id: number) => post('/user/favorites/remove', { hotel_id }),
}

// ========== User Coupons ==========
export const userCouponApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/user/coupons', params),
  available: () => get<{ items: unknown[] }>('/user/coupons/available'),
  claim: (template_id: number) => post('/user/coupons/claim', { template_id }),
  forOrder: (amount: number) => get<{ items: unknown[] }>('/user/orders/available-coupons', { amount }),
}

// ========== User Invoices ==========
export const userInvoiceApi = {
  list: () => get<PaginatedData>('/user/invoices'),
  createTitle: (data: { invoice_type: string; title: string; tax_no?: string; email: string }) =>
    post('/user/invoices/create', data),
  apply: (data: { order_id: number; invoice_title_id: number }) => post('/user/invoices/apply', data),
}

// ========== User Points ==========
export const userPointsApi = {
  logs: (params?: Record<string, unknown>) => get<PaginatedData>('/user/points/logs', params),
}

// ========== User Notices ==========
export const userNoticeApi = {
  list: (params?: Record<string, unknown>) => get<PaginatedData>('/user/notices', params),
  markRead: (ids?: number[]) => post<{ unread_count: number }>('/user/notices', ids ? { ids } : {}),
  unreadCount: () => get<{ unread_count: number }>('/user/notices/unread-count'),
  deleteNotices: (ids?: number[]) => del<{ deleted: number; unread_count: number }>('/user/notices', ids ? { ids } : {}),
}

// ========== User AI Chat ==========
export const userAiApi = {
  chat: (data: { scene: string; question: string; hotel_id?: number; order_id?: number; booking_context?: Record<string, unknown> }) =>
    post<{ answer: string; scene: string; booking_assistant?: Record<string, unknown> | null }>('/user/ai/chat', data),

  async *chatStream(
    data: { scene: string; question: string; hotel_id?: number; order_id?: number; booking_context?: Record<string, unknown> }
  ): AsyncGenerator<Record<string, unknown>> {
    const token = getToken()
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    let resp: Response
    try {
      resp = await fetch('/api/v1/user/ai/chat/stream', {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      })
    } catch {
      yield { content: '', done: true }
      return
    }

    if (!resp.ok || !resp.body) {
      yield { content: '', done: true }
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })

      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const eventBlock = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)

        for (const line of eventBlock.split('\n')) {
          if (!line.startsWith('data: ')) {
            continue
          }

          try {
            const event = JSON.parse(line.slice(6)) as Record<string, unknown>
            yield event
            if (event.done) {
              return
            }
          } catch {
            // ignore malformed events
          }
        }

        boundary = buffer.indexOf('\n\n')
      }
    }

    if (buffer.trim().startsWith('data: ')) {
      try {
        const event = JSON.parse(buffer.trim().slice(6)) as { content: string; done: boolean }
        yield event
      } catch {
        // ignore malformed tail event
      }
    }
  },
}
