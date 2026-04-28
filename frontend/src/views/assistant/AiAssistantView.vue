<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { aiApi, getApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import type { ChatMessage, ChatMode, ChatSessionSummary } from '@/types/api'
import { formatDate } from '@/utils'

const auth = useAuthStore()
const sessions = ref<ChatSessionSummary[]>([])
const activeSessionId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
const input = ref('')
const mode = ref<ChatMode>('auto')
const loading = ref(false)
const loadingSessions = ref(false)
const error = ref('')
const faqOpen = ref(false)
const activeFaqCategory = ref('token')
const faqPickerRef = ref<HTMLElement | null>(null)
const editingSessionId = ref<string | null>(null)
const editingTitle = ref('')

const faqGroups = [
  {
    key: 'token',
    title: '代币类',
    mode: 'token' as ChatMode,
    questions: [
      '请分析 BTC 最近 7 天的价格走势和成交量变化。',
      'ETH 当前价格表现如何？有哪些主要风险？',
      '请比较 BTC 和 ETH 的近期走势差异。',
      '当前平台支持哪些 Token？请按类别总结。',
      '帮我生成 SOL 的市场摘要，并列出关键观察点。',
      '请比较 ARB 和 OP 两个 Layer2 代币的近期表现。',
      'UNI 和 AAVE 在 DeFi 治理中的定位有什么不同？',
    ],
  },
  {
    key: 'dao',
    title: 'DAO 类',
    mode: 'dao' as ChatMode,
    questions: [
      '当前平台支持哪些 DAO？',
      '请总结 Aave DAO 最近同步的治理情况。',
      '哪个 DAO 的提案数量最多？可能说明什么？',
      '请解释 DAO 治理中的 active、closed、pending 状态含义。',
      '帮我从治理参与角度分析这些 DAO 的活跃度。',
    ],
  },
  {
    key: 'proposal',
    title: '提案类',
    mode: 'proposal' as ChatMode,
    questions: [
      '请帮我总结最近的 active proposal 重点。',
      '某个 Proposal 的主要内容、投票选择和风险是什么？',
      '请找出与当前 Proposal 相似的提案，并说明相似原因。',
      '一个 closed proposal 通常应该重点关注哪些信息？',
      '请从关键词角度总结这些 Proposal 的主题分布。',
    ],
  },
  {
    key: 'platform',
    title: '平台使用类',
    mode: 'auto' as ChatMode,
    questions: [
      '请介绍 ChainPilot 的核心功能。',
      '我应该如何使用代币、治理和 AI 助手三个模块？',
      '如果我要做 DAO Proposal 分析，推荐的操作流程是什么？',
      '请给我一个适合答辩展示的系统功能讲解顺序。',
      '请总结当前平台的数据来源和接口能力。',
    ],
  },
]

function fillQuestion(question: string, nextMode: ChatMode) {
  input.value = question
  mode.value = nextMode
  faqOpen.value = false
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderInlineMarkdown(value: string) {
  return value
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
}

function renderMarkdown(value?: string) {
  const source = escapeHtml(value || '')
  const codeBlocks: string[] = []
  const withoutCode = source.replace(/```([\s\S]*?)```/g, (_, code: string) => {
    const key = `@@CODE_BLOCK_${codeBlocks.length}@@`
    codeBlocks.push(`<pre><code>${code.trim()}</code></pre>`)
    return key
  })

  const lines = withoutCode.split(/\r?\n/)
  const html: string[] = []
  let listOpen = false
  let tableBuffer: string[] = []

  const closeList = () => {
    if (listOpen) {
      html.push('</ul>')
      listOpen = false
    }
  }

  const flushTable = () => {
    if (tableBuffer.length < 2) {
      tableBuffer.forEach((line) => html.push(`<p>${renderInlineMarkdown(line)}</p>`))
      tableBuffer = []
      return
    }

    const rows = tableBuffer
      .filter((line) => !/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line))
      .map((line) => line.replace(/^\||\|$/g, '').split('|').map((cell) => renderInlineMarkdown(cell.trim())))

    if (!rows.length) {
      tableBuffer = []
      return
    }

    const [head = [], ...body] = rows
    html.push('<table><thead><tr>')
    head.forEach((cell) => html.push(`<th>${cell}</th>`))
    html.push('</tr></thead><tbody>')
    body.forEach((row) => {
      html.push('<tr>')
      row.forEach((cell) => html.push(`<td>${cell}</td>`))
      html.push('</tr>')
    })
    html.push('</tbody></table>')
    tableBuffer = []
  }

  for (const line of lines) {
    if (line.startsWith('@@CODE_BLOCK_')) {
      closeList()
      flushTable()
      html.push(line)
      continue
    }

    if (line.includes('|') && line.trim().startsWith('|')) {
      closeList()
      tableBuffer.push(line)
      continue
    }

    flushTable()

    if (!line.trim()) {
      closeList()
      continue
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/)
    if (heading) {
      closeList()
      const level = (heading[1] || '').length + 2
      html.push(`<h${level}>${renderInlineMarkdown(heading[2] || '')}</h${level}>`)
      continue
    }

    const listItem = line.match(/^\s*[-*]\s+(.+)$/)
    if (listItem) {
      if (!listOpen) {
        html.push('<ul>')
        listOpen = true
      }
      html.push(`<li>${renderInlineMarkdown(listItem[1] || '')}</li>`)
      continue
    }

    closeList()
    html.push(`<p>${renderInlineMarkdown(line)}</p>`)
  }

  closeList()
  flushTable()

  return html.join('').replace(/@@CODE_BLOCK_(\d+)@@/g, (_, index: string) => codeBlocks[Number(index)] || '')
}

function handleDocumentClick(event: MouseEvent) {
  if (!faqOpen.value) return
  const target = event.target
  if (target instanceof Node && faqPickerRef.value?.contains(target)) return
  faqOpen.value = false
}

function startEditSessionTitle(session: ChatSessionSummary) {
  editingSessionId.value = session.session_id
  editingTitle.value = session.title || '未命名会话'
}

async function saveSessionTitle() {
  const sessionId = editingSessionId.value
  if (!sessionId) return

  const nextTitle = editingTitle.value.trim() || '未命名会话'
  const session = sessions.value.find((item) => item.session_id === sessionId)
  if (!session) {
    editingSessionId.value = null
    editingTitle.value = ''
    return
  }

  editingSessionId.value = null
  editingTitle.value = ''

  if (session.title === nextTitle) return

  const previousTitle = session.title
  session.title = nextTitle

  try {
    const updated = await aiApi.updateSession(sessionId, { title: nextTitle })
    session.title = updated.title || nextTitle
    session.updated_at = updated.updated_at || session.updated_at
  } catch (err) {
    session.title = previousTitle
    error.value = getApiError(err)
  }
}

function handleSessionTitleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    saveSessionTitle()
  }
}

async function loadSessions() {
  loadingSessions.value = true
  try {
    const res = await aiApi.sessions({ page: 1, page_size: 30, status: 'active', user_id: auth.user?.user_id ?? undefined })
    sessions.value = res.sessions
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loadingSessions.value = false
  }
}

async function createSession() {
  error.value = ''
  try {
    const doc = await aiApi.createSession({ title: '新的链上会话', mode: mode.value, user_id: auth.user?.user_id ?? null, client: 'web' })
    activeSessionId.value = doc.session_id
    messages.value = doc.messages ?? []
    sessions.value = [{ ...doc, message_count: doc.message_count ?? 0, last_message: doc.last_message ?? '' }, ...sessions.value]
  } catch (err) {
    error.value = getApiError(err)
  }
}

async function selectSession(sessionId: string) {
  activeSessionId.value = sessionId
  error.value = ''
  try {
    const doc = await aiApi.session(sessionId)
    mode.value = doc.mode || 'auto'
    messages.value = doc.messages ?? []
  } catch (err) {
    error.value = getApiError(err)
  }
}

async function deleteSession(sessionId: string) {
  try {
    await aiApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter((session) => session.session_id !== sessionId)
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = null
      messages.value = []
    }
  } catch (err) {
    error.value = getApiError(err)
  }
}

async function sendMessage(text = input.value) {
  const content = text.trim()
  if (!content) return

  input.value = ''
  error.value = ''
  messages.value.push({ role: 'user', content })
  loading.value = true

  try {
    const res = await aiApi.chat({
      session_id: activeSessionId.value,
      message: content,
      mode: mode.value,
      history: [],
      user_id: auth.user?.user_id ?? null,
      client: 'web',
    })
    activeSessionId.value = res.session_id
    messages.value.push({ role: 'assistant', content: res.answer || res.error_message || '暂未生成回答。' })
    await loadSessions()
  } catch (err) {
    messages.value.push({ role: 'assistant', content: `请求失败：${getApiError(err)}` })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const draft = sessionStorage.getItem('chainpilot_ai_draft')
  if (draft) {
    input.value = draft
    mode.value = 'auto'
    sessionStorage.removeItem('chainpilot_ai_draft')
  }
  document.addEventListener('click', handleDocumentClick)
  await loadSessions()
  if (sessions.value[0]) await selectSession(sessions.value[0].session_id)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <main class="assistant-page panel reveal">
    <aside class="session-sidebar">
      <div class="section-heading compact-heading">
        <div><p class="eyebrow">AI Assistant</p><h2>会话</h2></div>
      </div>
      <button class="primary wide" @click="createSession">新建会话</button>
      <div class="session-list">
        <button v-for="session in sessions" :key="session.session_id" class="session-item" :class="{ active: activeSessionId === session.session_id }" @click="selectSession(session.session_id)">
          <input
            v-if="editingSessionId === session.session_id"
            v-model="editingTitle"
            class="session-title-input"
            maxlength="60"
            autofocus
            @click.stop
            @dblclick.stop
            @blur="saveSessionTitle"
            @keydown="handleSessionTitleKeydown"
          />
          <strong v-else class="session-title" title="双击修改会话标题" @dblclick.stop="startEditSessionTitle(session)">
            {{ session.title || '未命名会话' }}
          </strong>
          <span>{{ session.last_message || `${session.mode} · ${session.message_count} 条消息` }}</span>
          <small>{{ formatDate(session.updated_at) }}</small>
          <em @click.stop="deleteSession(session.session_id)">删除</em>
        </button>
        <div v-if="loadingSessions" class="empty-state small-empty">加载会话中...</div>
        <div v-if="!loadingSessions && !sessions.length" class="empty-state small-empty">暂无会话，先新建或直接发送消息。</div>
      </div>
    </aside>

    <section class="chat-panel">
      <div class="chat-header">
        <div>
          <p class="eyebrow">MCP Tool Chat</p>
          <h1>智能问答</h1>
        </div>
        <select v-model="mode">
          <option value="auto">auto</option>
          <option value="token">token</option>
          <option value="dao">dao</option>
          <option value="proposal">proposal</option>
        </select>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>
      <div class="chat-window assistant-chat-window">
        <div v-if="!messages.length" class="chat-bubble assistant">你好，我是链上数据智能助手。可以向我询问 Token 行情、DAO 治理或 Proposal 内容。</div>
        <div v-for="(message, index) in messages" :key="index" class="chat-bubble" :class="message.role || 'assistant'">
          <div v-if="message.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(message.content || message.message)" />
          <template v-else>{{ message.content || message.message }}</template>
        </div>
        <div v-if="loading" class="chat-bubble assistant">AI 正在分析上下文并调用工具...</div>
      </div>

      <form class="chat-input" @submit.prevent="sendMessage()">
        <div ref="faqPickerRef" class="faq-picker">
          <button class="ghost compact" type="button" @click="faqOpen = !faqOpen">
            常见问题
          </button>
          <div v-if="faqOpen" class="faq-menu">
            <div class="faq-categories">
              <button
                v-for="group in faqGroups"
                :key="group.key"
                type="button"
                :class="{ active: activeFaqCategory === group.key }"
                @click="activeFaqCategory = group.key"
              >
                {{ group.title }}
              </button>
            </div>
            <div class="faq-questions">
              <button
                v-for="question in faqGroups.find((group) => group.key === activeFaqCategory)?.questions"
                :key="question"
                type="button"
                @click="fillQuestion(question, faqGroups.find((group) => group.key === activeFaqCategory)?.mode || 'auto')"
              >
                {{ question }}
              </button>
            </div>
          </div>
        </div>
        <input v-model="input" maxlength="500" placeholder="输入问题，例如：帮我分析 BTC 最近走势" />
        <button class="primary" :disabled="loading">发送</button>
      </form>
    </section>
  </main>
</template>
