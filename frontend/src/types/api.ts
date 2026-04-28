export interface ApiErrorResponse {
  code: string
  message: string
}

export interface UserProfile {
  user_id: string
  username: string
  email?: string | null
  display_name?: string | null
  status: string
  created_at: string
  updated_at: string
  last_login_at?: string | null
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserProfile
}

export interface MeResponse {
  user: UserProfile
}

export interface TokenCard {
  symbol: string
  name: string
  display_name: string
  primary_chain: string
  category: string
  logo?: string | null
  price?: number | null
  price_display?: string | null
  updated_at?: string | null
  status: string
  tags: string[]
}

export interface TokenGroup {
  group_name: string
  group_key: string
  cards: TokenCard[]
}

export interface TokenOverviewResponse {
  page_updated_at: string
  total_tokens: number
  group_count: number
  groups: TokenGroup[]
}

export interface TokenInfo extends TokenCard {
  price_change_24h?: number | null
  high_24h?: number | null
  low_24h?: number | null
  volume_24h?: number | null
}

export interface TokenKline {
  open_time?: number | string
  close_time?: number | string
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
  quote_asset_volume?: number
  quote_volume?: number
  number_of_trades?: number
  trades?: number
  [key: string]: unknown
}

export interface TokenChartSummary {
  start_price?: number | null
  end_price?: number | null
  change?: number | null
  change_percent?: number | null
  high?: number | null
  low?: number | null
  total_quote_volume?: number | null
  total_trades?: number | null
}

export interface TokenChartResponse {
  symbol: string
  price_symbol: string
  range: string
  interval: string
  source: string
  klines: TokenKline[]
  summary?: TokenChartSummary | null
}

export interface TokenDetailResponse {
  info: TokenInfo
  chart?: TokenChartResponse | null
}

export interface TokenAISummary {
  symbol: string
  title: string
  summary: string
  key_points: string[]
  risk_notes: string[]
  generated_by: string
  generated_at: string
}

export interface TokenAISummaryResponse {
  symbol: string
  summary: TokenAISummary
}

export interface WalletChainOption {
  key: string
  label: string
  enabled: boolean
}

export interface WalletChainOptionsResponse {
  chains: WalletChainOption[]
}

export interface WalletAssetItem {
  symbol: string
  name?: string | null
  blockchain?: string | null
  token_type?: string | null
  contract_address?: string | null
  balance?: number | null
  display_balance?: string | null
  price_usdt?: number | null
  value_usdt: number
  ratio: number
  category: string
  logo?: string | null
  tags: string[]
}

export interface WalletCategoryBreakdown {
  category: string
  label: string
  value_usdt: number
  ratio: number
}

export interface WalletGovernanceHint {
  symbol: string
  dao_name: string
  space_id: string
  value_usdt: number
  ratio: number
}

export interface WalletInsightResponse {
  address: string
  chains: string[]
  chain_options: WalletChainOption[]
  asset_count: number
  priced_count: number
  total_value_usdt: number
  stablecoin_ratio: number
  mainstream_ratio: number
  defi_ratio: number
  meme_ratio: number
  governance_ratio: number
  concentration_ratio: number
  risk_level: string
  risk_label: string
  page_updated_at: string
  assets: WalletAssetItem[]
  category_breakdown: WalletCategoryBreakdown[]
  governance_hints: WalletGovernanceHint[]
  insights: string[]
}

export interface DaoCard {
  name: string
  space_id: string
  logo?: string | null
  description?: string | null
  tags: string[]
  enabled: boolean
  latest_synchronization_time?: string | null
  synchronized_proposals_count: number
}

export interface DaoOverviewResponse {
  page_updated_at: string
  dao_count: number
  daos: DaoCard[]
}

export interface ProposalListItem {
  proposal_id: string
  space_id: string
  author?: string | null
  title: string
  state: string
  keywords: string[]
}

export interface ProposalListResponse {
  page_updated_at: string
  space_id: string
  dao_name: string
  page: number
  page_size: number
  total?: number
  proposals: ProposalListItem[]
}

export interface ProposalDetail extends ProposalListItem {
  body?: string
  end?: number | null
  choices?: string[]
  scores?: number[]
  scores_total?: number | null
  scores_updated?: number | null
  created?: number
  link?: string
}

export interface SimilarProposalResponse {
  proposal_id: string
  space_id: string
  top_k: number
  similar_proposals: ProposalListItem[]
}

export interface ProposalDetailResponse {
  proposal: ProposalDetail
  similar_proposals: SimilarProposalResponse
}

export interface DynamicSyncResponse {
  fetched_count: number
  new_count: number
  recent_updated_count: number
  proposals: ProposalListItem[]
}

export interface ProposalStatusUpdateResponse {
  proposal_id: string
  space_id: string
  state?: string | null
  end?: number | null
  choices: string[]
  scores: number[]
  scores_total?: number | null
  scores_updated?: number | null
}

export type ChatMode = 'auto' | 'token' | 'dao' | 'proposal'

export interface ChatMessage {
  role?: 'user' | 'assistant' | 'system'
  content?: string
  message?: string
  created_at?: string
  [key: string]: unknown
}

export interface ChatResponse {
  session_id: string
  answer: string
  mode: ChatMode
  status: string
  used_tools: unknown[]
  result_cards: unknown[]
  error_message?: string | null
}

export interface ChatSessionSummary {
  session_id: string
  title: string
  mode: ChatMode
  status: string
  created_at: string
  updated_at: string
  message_count: number
  last_message?: string | null
}

export interface ChatSessionsResponse {
  page: number
  page_size: number
  total: number
  sessions: ChatSessionSummary[]
}

export interface ChatSessionDocument extends ChatSessionSummary {
  user_id?: string | null
  client?: string | null
  messages?: ChatMessage[]
  tool_calls?: unknown[]
}
