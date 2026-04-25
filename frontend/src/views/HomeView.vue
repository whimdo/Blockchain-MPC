<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent } from 'echarts/components'
import type { EChartsOption } from 'echarts'
import { aiApi, authApi, clearToken, daoApi, getApiError, getToken, saveToken, tokenApi } from '@/api/client'
import type {
  ChatMessage,
  ChatMode,
  DaoCard,
  ProposalDetail,
  ProposalListItem,
  TokenAISummary,
  TokenCard,
  TokenChartResponse,
  TokenOverviewResponse,
  TokenInfo,
  UserProfile,
} from '@/types/api'
import { assetUrl, compactNumber, formatDate, percent } from '@/utils'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, DataZoomComponent])

type NoticeTone = 'info' | 'success' | 'error'
type EndpointItem = [method: string, path: string, description: string]

const loading = ref({
  boot: true,
  auth: false,
  tokens: false,
  tokenDetail: false,
  aiSummary: false,
  daos: false,
  proposals: false,
  proposalDetail: false,
  sync: false,
  chat: false,
})

const notice = ref<{ tone: NoticeTone; text: string } | null>(null)
const user = ref<UserProfile | null>(null)
const authMode = ref<'login' | 'register'>('login')
const authForm = ref({ username: 'alice', password: 'password123', email: 'alice@example.com', display_name: 'Alice' })

const tokenOverview = ref<TokenOverviewResponse | null>(null)
const selectedToken = ref('BTC')
const chartRange = ref('7d')
const chartInterval = ref('1h')
const tokenDetail = ref<TokenInfo | null>(null)
const tokenChart = ref<TokenChartResponse | null>(null)
const tokenSummary = ref<TokenAISummary | null>(null)

const daos = ref<DaoCard[]>([])
const selectedDao = ref('')
const proposals = ref<ProposalListItem[]>([])
const selectedProposal = ref<ProposalDetail | null>(null)
const similarProposals = ref<ProposalListItem[]>([])
const syncLatestK = ref(10)

const chatMode = ref<ChatMode>('auto')
const chatInput = ref('当前平台支持哪些 DAO？')
const chatSessionId = ref<string | null>(null)
const chatMessages = ref<ChatMessage[]>([
  { role: 'assistant', content: '你好，我是链上数据智能助手。你可以问我 Token、DAO 或 Proposal 相关问题。' },
])
const chatSuggestions = ref<string[]>([])

const endpointGroups: Array<{ title: string; base: string; endpoints: EndpointItem[] }> = [
  {
    title: 'Auth 用户认证',
    base: '/api/auth',
    endpoints: [
      ['POST', '/register', '注册用户并返回 JWT access token'],
      ['POST', '/login', '用户名或邮箱登录'],
      ['GET', '/me', '通过 Bearer Token 获取当前用户'],
    ],
  },
  {
    title: 'AIChat 智能助手',
    base: '/api/ai',
    endpoints: [
      ['POST', '/chat', '发送聊天消息并获取工具增强回答'],
      ['POST', '/sessions', '创建聊天会话'],
      ['GET', '/sessions', '分页获取会话列表'],
      ['GET', '/sessions/{session_id}', '获取会话详情'],
      ['PATCH', '/sessions/{session_id}', '更新标题或状态'],
      ['DELETE', '/sessions/{session_id}', '软删除会话'],
    ],
  },
  {
    title: 'Dashboard Token',
    base: '/api/dashboard/tokens',
    endpoints: [
      ['GET', '/overview', '获取 Token 分组、卡片、价格和状态'],
      ['POST', '/refresh/all', '刷新全部 Token 卡片'],
      ['POST', '/refresh', '刷新单个 Token 卡片'],
      ['POST', '/detail', '获取 Token 详情和可选图表'],
      ['POST', '/chart', '获取 K 线图表数据'],
      ['POST', '/ai-summary', '生成 Token AI 摘要'],
    ],
  },
  {
    title: 'DAO 与 Proposal',
    base: '/api/dao',
    endpoints: [
      ['GET', '/overview', '获取 DAO 总览'],
      ['GET', '/{space_id}/proposals', '获取 DAO Proposal 列表'],
      ['GET', '/proposal/{proposal_id}', '获取 Proposal 详情和相似 Proposal'],
      ['POST', '/proposals/dynamic-sync', '动态同步 Snapshot 最新 Proposal'],
    ],
  },
]

const flatTokens = computed(() => tokenOverview.value?.groups.flatMap((group) => group.cards) ?? [])
const onlineTokens = computed(() => flatTokens.value.filter((token) => token.status === 'online').length)
const chartOption = computed<EChartsOption>(() => {
  const rows = tokenChart.value?.klines ?? []
  const points: Array<[string, number]> = rows.map((item, index) => {
    const time = item.close_time ?? item.open_time ?? index
    const close = Number(item.close ?? item.price ?? item.end_price ?? 0)
    return [formatDate(time as string | number), close] as [string, number]
  }).filter((point) => Number.isFinite(point[1]))

  const option: EChartsOption = {
    grid: { left: 36, right: 20, top: 24, bottom: 42 },
    tooltip: { trigger: 'axis', backgroundColor: '#102033', borderColor: '#274761', textStyle: { color: '#eef7ff' } },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 8, borderColor: 'transparent' }],
    xAxis: { type: 'category', boundaryGap: false, axisLine: { lineStyle: { color: '#7891a7' } }, data: points.map((point) => point[0]) },
    yAxis: { type: 'value', scale: true, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(110, 141, 170, .18)' } } },
    series: [
      {
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: points.map((point) => point[1]),
        lineStyle: { width: 3, color: '#21d0a2' },
        areaStyle: { color: 'rgba(33, 208, 162, .16)' },
      },
    ],
  }
  return option
})

function toast(text: string, tone: NoticeTone = 'info') {
  notice.value = { text, tone }
  window.setTimeout(() => {
    if (notice.value?.text === text) notice.value = null
  }, 3200)
}

async function loadMe() {
  if (!getToken()) return
  try {
    const res = await authApi.me()
    user.value = res.user
  } catch {
    clearToken()
    user.value = null
  }
}

async function submitAuth() {
  loading.value.auth = true
  try {
    const res = authMode.value === 'login'
      ? await authApi.login({ username: authForm.value.username, password: authForm.value.password })
      : await authApi.register(authForm.value)
    saveToken(res.access_token)
    user.value = res.user
    toast(`${authMode.value === 'login' ? '登录' : '注册'}成功，已接入当前用户`, 'success')
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.auth = false
  }
}

function logout() {
  clearToken()
  user.value = null
  toast('已退出当前账户')
}

async function loadTokens() {
  loading.value.tokens = true
  try {
    tokenOverview.value = await tokenApi.overview()
    if (!selectedToken.value && flatTokens.value[0]) selectedToken.value = flatTokens.value[0].symbol
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.tokens = false
  }
}

async function refreshAllTokens() {
  loading.value.tokens = true
  try {
    tokenOverview.value = await tokenApi.refreshAll()
    toast('Token 行情已刷新', 'success')
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.tokens = false
  }
}

async function loadTokenDetail(symbol = selectedToken.value) {
  if (!symbol) return
  selectedToken.value = symbol
  tokenSummary.value = null
  loading.value.tokenDetail = true
  try {
    const detail = await tokenApi.detail({
      symbol,
      include_chart: true,
      chart_range: chartRange.value,
      chart_interval: chartInterval.value,
      chart_source: 'binance',
    })
    tokenDetail.value = detail.info
    tokenChart.value = detail.chart ?? null
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.tokenDetail = false
  }
}

async function loadAiSummary() {
  if (!selectedToken.value) return
  loading.value.aiSummary = true
  try {
    const res = await tokenApi.aiSummary({ symbol: selectedToken.value, chart_summary: tokenChart.value?.summary ?? null })
    tokenSummary.value = res.summary
    toast('AI 摘要已生成', 'success')
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.aiSummary = false
  }
}

async function loadDaos() {
  loading.value.daos = true
  try {
    const res = await daoApi.overview()
    daos.value = res.daos
    if (!selectedDao.value && res.daos[0]) selectedDao.value = res.daos[0].space_id
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.daos = false
  }
}

async function loadProposals(spaceId = selectedDao.value) {
  if (!spaceId) return
  selectedDao.value = spaceId
  selectedProposal.value = null
  similarProposals.value = []
  loading.value.proposals = true
  try {
    const res = await daoApi.proposals(spaceId, 1, 12)
    proposals.value = res.proposals
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.proposals = false
  }
}

async function loadProposalDetail(proposalId: string) {
  loading.value.proposalDetail = true
  try {
    const res = await daoApi.proposalDetail(proposalId, 3)
    selectedProposal.value = res.proposal
    similarProposals.value = res.similar_proposals.similar_proposals
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.proposalDetail = false
  }
}

async function dynamicSync() {
  if (!selectedDao.value) return
  loading.value.sync = true
  try {
    const res = await daoApi.dynamicSync({ space_id: selectedDao.value, latest_k: syncLatestK.value })
    proposals.value = res.proposals.length ? res.proposals : proposals.value
    toast(`同步完成：抓取 ${res.fetched_count} 条，新增 ${res.new_count} 条`, 'success')
  } catch (error) {
    toast(getApiError(error), 'error')
  } finally {
    loading.value.sync = false
  }
}

async function sendChat(question = chatInput.value) {
  const message = question.trim()
  if (!message) return
  chatInput.value = ''
  chatMessages.value.push({ role: 'user', content: message })
  loading.value.chat = true
  try {
    const res = await aiApi.chat({
      session_id: chatSessionId.value,
      message,
      mode: chatMode.value,
      history: [],
      user_id: user.value?.user_id ?? null,
      client: 'web',
    })
    chatSessionId.value = res.session_id
    chatSuggestions.value = res.suggested_questions ?? []
    chatMessages.value.push({ role: 'assistant', content: res.answer || res.error_message || '暂未生成回答。' })
  } catch (error) {
    chatMessages.value.push({ role: 'assistant', content: `请求失败：${getApiError(error)}` })
  } finally {
    loading.value.chat = false
  }
}

onMounted(async () => {
  await Promise.all([loadMe(), loadTokens(), loadDaos()])
  await Promise.all([loadTokenDetail(selectedToken.value), loadProposals(selectedDao.value)])
  loading.value.boot = false
})
</script>

<template>
  <main class="dashboard-shell">
    <section class="hero panel reveal">
      <div>
        <p class="eyebrow">ChainPilot Onchain Intelligence</p>
        <h1>链上资产、DAO 治理与 AI 助手的一体化前端</h1>
        <p class="hero-copy">
          基于 API接口总说明.md 完整接入认证、Token Dashboard、Token 详情、DAO Proposal 和 AIChat，构建 ChainPilot 链上智能导航体验。
        </p>
        <div class="hero-actions">
          <button class="primary" :disabled="loading.tokens" @click="refreshAllTokens">刷新行情</button>
          <button class="ghost" @click="sendChat('帮我总结当前平台的核心能力')">询问 AI 助手</button>
        </div>
      </div>
      <div class="hero-metrics">
        <div class="metric-card">
          <span>Total Tokens</span>
          <strong>{{ tokenOverview?.total_tokens ?? '--' }}</strong>
        </div>
        <div class="metric-card">
          <span>Online</span>
          <strong>{{ onlineTokens }}</strong>
        </div>
        <div class="metric-card">
          <span>DAO Spaces</span>
          <strong>{{ daos.length || '--' }}</strong>
        </div>
        <div class="metric-card">
          <span>Current User</span>
          <strong>{{ user?.display_name || user?.username || 'Guest' }}</strong>
        </div>
      </div>
    </section>

    <div v-if="notice" class="notice" :class="notice.tone">{{ notice.text }}</div>

    <section class="grid two-columns">
      <article class="panel auth-card reveal delay-1">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Auth</p>
            <h2>用户认证</h2>
          </div>
          <span class="status-pill" :class="user ? 'online' : 'idle'">{{ user ? '已登录' : '未登录' }}</span>
        </div>

        <div v-if="user" class="profile-box">
          <div class="avatar">{{ (user.display_name || user.username).slice(0, 1).toUpperCase() }}</div>
          <div>
            <h3>{{ user.display_name || user.username }}</h3>
            <p>{{ user.email || '未绑定邮箱' }}</p>
            <small>User ID: {{ user.user_id }}</small>
          </div>
          <button class="ghost compact" @click="logout">退出</button>
        </div>

        <form class="form-stack" @submit.prevent="submitAuth">
          <div class="segmented">
            <button type="button" :class="{ active: authMode === 'login' }" @click="authMode = 'login'">登录</button>
            <button type="button" :class="{ active: authMode === 'register' }" @click="authMode = 'register'">注册</button>
          </div>
          <label>用户名或邮箱<input v-model="authForm.username" placeholder="alice" /></label>
          <label>密码<input v-model="authForm.password" type="password" placeholder="password123" /></label>
          <template v-if="authMode === 'register'">
            <label>邮箱<input v-model="authForm.email" placeholder="alice@example.com" /></label>
            <label>展示名<input v-model="authForm.display_name" placeholder="Alice" /></label>
          </template>
          <button class="primary wide" :disabled="loading.auth">{{ loading.auth ? '提交中...' : authMode === 'login' ? '登录账户' : '创建账户' }}</button>
        </form>
      </article>

      <article class="panel ai-card reveal delay-2">
        <div class="section-heading">
          <div>
            <p class="eyebrow">AI Chat</p>
            <h2>智能交互窗口</h2>
          </div>
          <select v-model="chatMode">
            <option value="auto">auto</option>
            <option value="token">token</option>
            <option value="dao">dao</option>
            <option value="proposal">proposal</option>
          </select>
        </div>
        <div class="chat-window">
          <div v-for="(message, index) in chatMessages" :key="index" class="chat-bubble" :class="message.role">
            {{ message.content || message.message }}
          </div>
          <div v-if="loading.chat" class="chat-bubble assistant">AI 正在调度工具和上下文...</div>
        </div>
        <div class="suggestions" v-if="chatSuggestions.length">
          <button v-for="item in chatSuggestions" :key="item" @click="sendChat(item)">{{ item }}</button>
        </div>
        <form class="chat-input" @submit.prevent="sendChat()">
          <input v-model="chatInput" maxlength="500" placeholder="问问 DAO、Token 或 Proposal..." />
          <button class="primary" :disabled="loading.chat">发送</button>
        </form>
      </article>
    </section>

    <section class="panel reveal delay-1">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Dashboard Tokens</p>
          <h2>主流币种链总览</h2>
        </div>
        <p class="muted">更新于 {{ formatDate(tokenOverview?.page_updated_at) }}</p>
      </div>
      <div class="token-groups">
        <div v-for="group in tokenOverview?.groups" :key="group.group_key" class="token-group">
          <div class="group-title">{{ group.group_name }}</div>
          <div class="token-grid">
            <button
              v-for="token in group.cards"
              :key="token.symbol"
              class="token-card"
              :class="{ selected: selectedToken === token.symbol }"
              @click="loadTokenDetail(token.symbol)"
            >
              <img v-if="token.logo" :src="assetUrl(token.logo)" :alt="token.symbol" />
              <div class="token-fallback" v-else>{{ token.symbol.slice(0, 1) }}</div>
              <div>
                <strong>{{ token.symbol }}</strong>
                <span>{{ token.display_name || token.name }}</span>
              </div>
              <p>{{ token.price_display || compactNumber(token.price) }}</p>
              <em :class="token.status">{{ token.status }}</em>
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="grid detail-grid">
      <article class="panel reveal delay-2">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Token Detail</p>
            <h2>{{ tokenDetail?.display_name || selectedToken }} 市场详情</h2>
          </div>
          <div class="inline-controls">
            <select v-model="chartRange" @change="loadTokenDetail()">
              <option value="1d">1d</option>
              <option value="7d">7d</option>
              <option value="1m">1m</option>
              <option value="3m">3m</option>
              <option value="1y">1y</option>
            </select>
            <select v-model="chartInterval" @change="loadTokenDetail()">
              <option value="15m">15m</option>
              <option value="1h">1h</option>
              <option value="4h">4h</option>
              <option value="1d">1d</option>
              <option value="1w">1w</option>
            </select>
          </div>
        </div>
        <div class="market-strip">
          <div><span>Price</span><strong>{{ tokenDetail?.price_display || '--' }}</strong></div>
          <div><span>24h</span><strong :class="(tokenDetail?.price_change_24h ?? 0) >= 0 ? 'up' : 'down'">{{ percent(tokenDetail?.price_change_24h) }}</strong></div>
          <div><span>High</span><strong>{{ compactNumber(tokenDetail?.high_24h) }}</strong></div>
          <div><span>Low</span><strong>{{ compactNumber(tokenDetail?.low_24h) }}</strong></div>
          <div><span>Volume</span><strong>{{ compactNumber(tokenDetail?.volume_24h) }}</strong></div>
        </div>
        <div class="chart-box">
          <VChart v-if="tokenChart?.klines?.length" :option="chartOption" autoresize />
          <div v-else class="empty-state">暂无图表数据，后端可返回 chart.klines 后自动绘制。</div>
        </div>
      </article>

      <article class="panel reveal delay-3">
        <div class="section-heading">
          <div>
            <p class="eyebrow">AI Summary</p>
            <h2>Token 智能摘要</h2>
          </div>
          <button class="ghost compact" :disabled="loading.aiSummary" @click="loadAiSummary">生成摘要</button>
        </div>
        <div v-if="tokenSummary" class="summary-box">
          <h3>{{ tokenSummary.title }}</h3>
          <p>{{ tokenSummary.summary }}</p>
          <h4>关键观点</h4>
          <ul><li v-for="point in tokenSummary.key_points" :key="point">{{ point }}</li></ul>
          <h4>风险提示</h4>
          <ul><li v-for="risk in tokenSummary.risk_notes" :key="risk">{{ risk }}</li></ul>
          <small>{{ tokenSummary.generated_by }} · {{ formatDate(tokenSummary.generated_at) }}</small>
        </div>
        <div v-else class="empty-state">选择 Token 后点击生成，可调用 /ai-summary 形成结构化摘要。</div>
      </article>
    </section>

    <section class="grid dao-grid">
      <article class="panel reveal delay-1">
        <div class="section-heading">
          <div>
            <p class="eyebrow">DAO Overview</p>
            <h2>治理空间</h2>
          </div>
          <button class="ghost compact" :disabled="loading.daos" @click="loadDaos">刷新 DAO</button>
        </div>
        <div class="dao-list">
          <button v-for="dao in daos" :key="dao.space_id" class="dao-card" :class="{ selected: selectedDao === dao.space_id }" @click="loadProposals(dao.space_id)">
            <img v-if="dao.logo" :src="assetUrl(dao.logo)" :alt="dao.name" />
            <div>
              <strong>{{ dao.name }}</strong>
              <span>{{ dao.space_id }}</span>
              <p>{{ dao.description || '暂无描述' }}</p>
            </div>
            <em>{{ dao.synchronized_proposals_count }} proposals</em>
          </button>
        </div>
      </article>

      <article class="panel reveal delay-2">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Proposal List</p>
            <h2>{{ selectedDao || '选择 DAO' }}</h2>
          </div>
          <div class="inline-controls">
            <input v-model.number="syncLatestK" class="tiny-input" type="number" min="1" max="50" />
            <button class="ghost compact" :disabled="loading.sync" @click="dynamicSync">动态同步</button>
          </div>
        </div>
        <div class="proposal-list">
          <button v-for="proposal in proposals" :key="proposal.proposal_id" class="proposal-row" @click="loadProposalDetail(proposal.proposal_id)">
            <span>{{ proposal.state }}</span>
            <strong>{{ proposal.title }}</strong>
            <small>{{ proposal.author }}</small>
          </button>
          <div v-if="!proposals.length" class="empty-state">暂无 Proposal 数据。</div>
        </div>
      </article>

      <article class="panel proposal-detail reveal delay-3">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Proposal Detail</p>
            <h2>详情与相似提案</h2>
          </div>
        </div>
        <div v-if="selectedProposal" class="proposal-body">
          <span class="status-pill online">{{ selectedProposal.state }}</span>
          <h3>{{ selectedProposal.title }}</h3>
          <p>{{ selectedProposal.body || '该 Proposal 暂无正文摘要。' }}</p>
          <a v-if="selectedProposal.link" :href="selectedProposal.link" target="_blank" rel="noreferrer">查看 Snapshot 原文</a>
          <div class="similar-list" v-if="similarProposals.length">
            <h4>相似 Proposal</h4>
            <p v-for="item in similarProposals" :key="item.proposal_id">{{ item.title }}</p>
          </div>
        </div>
        <div v-else class="empty-state">点击左侧 Proposal 查看详情。</div>
      </article>
    </section>

    <section class="panel docs-panel reveal delay-2">
      <div class="section-heading">
        <div>
          <p class="eyebrow">API Reference</p>
          <h2>接口参考速览</h2>
        </div>
        <p class="muted">API 返回格式均按 JSON 处理，错误响应读取 code/message。</p>
      </div>
      <div class="endpoint-grid">
        <div v-for="group in endpointGroups" :key="group.title" class="endpoint-card">
          <h3>{{ group.title }}</h3>
          <p>{{ group.base }}</p>
          <div v-for="endpoint in group.endpoints" :key="endpoint[0] + endpoint[1]" class="endpoint-row">
            <span>{{ endpoint[0] }}</span>
            <code>{{ group.base }}{{ endpoint[1] }}</code>
            <small>{{ endpoint[2] }}</small>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>



