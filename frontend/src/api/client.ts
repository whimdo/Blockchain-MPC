import axios, { AxiosError } from 'axios'
import type {
  AuthResponse,
  ChatMode,
  ChatResponse,
  ChatSessionDocument,
  ChatSessionsResponse,
  DaoOverviewResponse,
  DynamicSyncResponse,
  MeResponse,
  ProposalDetailResponse,
  ProposalListResponse,
  ProposalStatusUpdateResponse,
  TokenAISummaryResponse,
  TokenChartResponse,
  TokenChartSummary,
  TokenDetailResponse,
  TokenOverviewResponse,
  WalletChainOptionsResponse,
  WalletInsightResponse,
} from '@/types/api'

const TOKEN_KEY = 'bmpc_access_token'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getApiError(error: unknown) {
  const axiosError = error as AxiosError<{ code?: string; message?: string }>
  return axiosError.response?.data?.message || axiosError.response?.data?.code || axiosError.message || '请求失败'
}

export const authApi = {
  register: (payload: { username: string; password: string; email?: string; display_name?: string }) =>
    api.post<AuthResponse>('/auth/register', payload).then((res) => res.data),
  login: (payload: { username: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', payload).then((res) => res.data),
  me: () => api.get<MeResponse>('/auth/me').then((res) => res.data),
}

export const tokenApi = {
  overview: () => api.get<TokenOverviewResponse>('/dashboard/tokens/overview').then((res) => res.data),
  refreshAll: () => api.post<TokenOverviewResponse>('/dashboard/tokens/refresh/all').then((res) => res.data),
  refreshOne: (symbol: string) => api.post('/dashboard/tokens/refresh', { symbol }).then((res) => res.data),
  detail: (payload: {
    symbol: string
    include_chart?: boolean
    chart_range?: string
    chart_interval?: string | null
    chart_source?: string
  }) => api.post<TokenDetailResponse>('/dashboard/tokens/detail', payload).then((res) => res.data),
  chart: (payload: { symbol: string; range?: string; interval?: string | null; source?: string }) =>
    api.post<TokenChartResponse>('/dashboard/tokens/chart', payload).then((res) => res.data),
  aiSummary: (payload: { symbol: string; chart_summary?: TokenChartSummary | null }) =>
    api.post<TokenAISummaryResponse>('/dashboard/tokens/ai-summary', payload).then((res) => res.data),
}

export const daoApi = {
  overview: () => api.get<DaoOverviewResponse>('/dao/overview').then((res) => res.data),
  proposals: (spaceId: string, page = 1, pageSize = 20, state?: string | null) =>
    api.get<ProposalListResponse>(`/dao/${encodeURIComponent(spaceId)}/proposals`, {
      params: { page, page_size: pageSize, state: state || undefined },
    }).then((res) => res.data),
  proposalDetail: (proposalId: string, topK = 2) =>
    api.get<ProposalDetailResponse>(`/dao/proposal/${encodeURIComponent(proposalId)}`, {
      params: { top_k: topK },
    }).then((res) => res.data),
  dynamicSync: (payload: { space_id: string; latest_k: number }) =>
    api.post<DynamicSyncResponse>('/dao/proposals/dynamic-sync', payload).then((res) => res.data),
  updateProposalStatus: (payload: { proposal_id: string; space_id: string }) =>
    api.post<ProposalStatusUpdateResponse>('/dao/proposal/status-update', payload).then((res) => res.data),
}

export const walletApi = {
  chains: () => api.get<WalletChainOptionsResponse>('/wallet/chains').then((res) => res.data),
  analyze: (payload: { address: string; chains: string[] }) =>
    api.post<WalletInsightResponse>('/wallet/analyze', payload).then((res) => res.data),
}

export const aiApi = {
  chat: (payload: {
    session_id?: string | null
    message: string
    mode?: ChatMode
    history?: unknown[]
    user_id?: string | null
    client?: string | null
  }) => api.post<ChatResponse>('/ai/chat', payload).then((res) => res.data),
  createSession: (payload: { title: string; mode?: ChatMode; user_id?: string | null; client?: string | null }) =>
    api.post<ChatSessionDocument>('/ai/sessions', payload).then((res) => res.data),
  sessions: (params: { page?: number; page_size?: number; status?: string; user_id?: string | null }) =>
    api.get<ChatSessionsResponse>('/ai/sessions', { params }).then((res) => res.data),
  session: (sessionId: string) => api.get<ChatSessionDocument>(`/ai/sessions/${sessionId}`).then((res) => res.data),
  updateSession: (sessionId: string, payload: { title?: string; status?: string }) =>
    api.patch<ChatSessionDocument>(`/ai/sessions/${sessionId}`, payload).then((res) => res.data),
  deleteSession: (sessionId: string) =>
    api.delete<ChatSessionDocument>(`/ai/sessions/${sessionId}`).then((res) => res.data),
}
