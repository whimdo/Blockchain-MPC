<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { aiApi, getApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import type { ChatMessage, ChatMode, ChatSessionSummary } from '@/types/api'
import { formatDate } from '@/utils'

const auth = useAuthStore()
const sessions = ref<ChatSessionSummary[]>([])
const activeSessionId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
const suggestions = ref<string[]>([])
const input = ref('当前平台支持哪些 DAO？')
const mode = ref<ChatMode>('auto')
const loading = ref(false)
const loadingSessions = ref(false)
const error = ref('')

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
    suggestions.value = doc.suggested_questions ?? []
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
    suggestions.value = res.suggested_questions ?? []
    messages.value.push({ role: 'assistant', content: res.answer || res.error_message || '暂未生成回答。' })
    await loadSessions()
  } catch (err) {
    messages.value.push({ role: 'assistant', content: `请求失败：${getApiError(err)}` })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadSessions()
  if (sessions.value[0]) await selectSession(sessions.value[0].session_id)
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
          <strong>{{ session.title || '未命名会话' }}</strong>
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
          {{ message.content || message.message }}
        </div>
        <div v-if="loading" class="chat-bubble assistant">AI 正在分析上下文并调用工具...</div>
      </div>

      <div class="suggestions" v-if="suggestions.length">
        <button v-for="item in suggestions" :key="item" @click="sendMessage(item)">{{ item }}</button>
      </div>

      <form class="chat-input" @submit.prevent="sendMessage()">
        <input v-model="input" maxlength="500" placeholder="输入问题，例如：帮我分析 BTC 最近走势" />
        <button class="primary" :disabled="loading">发送</button>
      </form>
    </section>
  </main>
</template>
