<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { daoApi, getApiError } from '@/api/client'
import type { ProposalDetail, ProposalListItem } from '@/types/api'
import { formatDate } from '@/utils'

const route = useRoute()
const router = useRouter()
const proposalId = computed(() => String(route.params.proposalId || ''))
const proposal = ref<ProposalDetail | null>(null)
const similar = ref<ProposalListItem[]>([])
const loading = ref(false)
const updatingStatus = ref(false)
const error = ref('')
const statusMessage = ref('')

const canUpdateStatus = computed(() => {
  const state = (proposal.value?.state || '').trim().toLowerCase()
  return ['active', 'pending', '进行中', '待开始'].includes(state)
})

const wordCloud = computed(() => {
  const counts = new Map<string, number>()
  const stopWords = new Set([
    'this',
    'that',
    'with',
    'from',
    'will',
    'have',
    'proposal',
    'snapshot',
    'https',
    'http',
    'the',
    'and',
    'for',
    'are',
    'about',
  ])

  for (const keyword of proposal.value?.keywords ?? []) {
    const normalized = keyword.trim()
    if (normalized) counts.set(normalized, (counts.get(normalized) || 0) + 5)
  }

  const body = proposal.value?.body || ''
  const words = body.match(/[A-Za-z][A-Za-z0-9_-]{3,}|[\u4e00-\u9fa5]{2,}/g) ?? []
  for (const word of words) {
    const normalized = /^[A-Za-z]/.test(word) ? word.toLowerCase() : word
    if (stopWords.has(normalized)) continue
    counts.set(normalized, (counts.get(normalized) || 0) + 1)
  }

  const ranked = Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 28)

  const max = ranked[0]?.[1] || 1
  return ranked.map(([text, count], index) => ({
    text,
    count,
    size: 0.78 + (count / max) * 1.15,
    weight: count > max * 0.55 ? 950 : count > max * 0.28 ? 850 : 700,
    rotate: index % 7 === 0 ? -5 : index % 5 === 0 ? 4 : 0,
    tone: count > max * 0.55 ? 'strong' : count > max * 0.28 ? 'medium' : 'soft',
  }))
})

function wordStyle(word: { size: number; weight: number; rotate: number }) {
  return {
    fontSize: `${word.size}rem`,
    fontWeight: word.weight,
    transform: `rotate(${word.rotate}deg)`,
  }
}

function stateText(state?: string | null) {
  const stateMap: Record<string, string> = {
    active: '进行中',
    closed: '已关闭',
    pending: '待开始',
  }
  return state ? stateMap[state] || state : '--'
}

function choiceText(choice: string) {
  const choiceMap: Record<string, string> = {
    for: 'for | 支持',
    against: 'against | 反对',
    abstain: 'abstain | 弃权',
  }
  return choiceMap[choice.trim().toLowerCase()] || choice
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
  const source = escapeHtml(value || '该 Proposal 暂无正文。')
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

    const [head = [], ...body] = rows
    if (!head.length) {
      tableBuffer = []
      return
    }

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

async function loadDetail() {
  loading.value = true
  error.value = ''
  statusMessage.value = ''
  try {
    const res = await daoApi.proposalDetail(proposalId.value, 3)
    proposal.value = res.proposal
    similar.value = res.similar_proposals.similar_proposals
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

async function updateProposalStatus() {
  if (!proposal.value || updatingStatus.value) return
  updatingStatus.value = true
  error.value = ''
  statusMessage.value = ''
  try {
    const res = await daoApi.updateProposalStatus({
      proposal_id: proposal.value.proposal_id,
      space_id: proposal.value.space_id,
    })
    proposal.value = {
      ...proposal.value,
      state: res.state || proposal.value.state,
      end: res.end,
      choices: res.choices,
      scores: res.scores,
      scores_total: res.scores_total ?? proposal.value.scores_total,
      scores_updated: res.scores_updated ?? proposal.value.scores_updated,
    }
    statusMessage.value = 'Proposal 状态已更新。'
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    updatingStatus.value = false
  }
}

onMounted(loadDetail)
watch(() => route.params.proposalId, loadDetail)
</script>

<template>
  <main class="page-stack">
    <section class="detail-header panel reveal">
      <button class="ghost compact" @click="router.push(proposal ? `/governance/${proposal.space_id}/proposals` : '/governance')">返回列表</button>
      <div>
        <p class="eyebrow bilingual-label"><span>Proposal Detail</span><span>提案详情</span></p>
        <h1>{{ proposal?.title || 'Proposal 详情' }}</h1>
        <span class="muted">{{ proposal?.space_id || '--' }} · {{ proposal?.author || '--' }}</span>
      </div>
    </section>

    <p v-if="error" class="form-error">{{ error }}</p>
    <div v-if="loading" class="empty-state">正在加载 Proposal 详情...</div>

    <section v-else class="grid proposal-detail-grid">
      <article class="panel reveal delay-1">
        <div class="proposal-detail-card-header">
          <span class="status-pill online">{{ stateText(proposal?.state) }}</span>
          <button
            v-if="canUpdateStatus"
            class="primary compact"
            :disabled="updatingStatus"
            @click="updateProposalStatus"
          >
            {{ updatingStatus ? '更新中...' : '更新状态' }}
          </button>
        </div>
        <p v-if="statusMessage" class="status-message">{{ statusMessage }}</p>
        <h2>{{ proposal?.title }}</h2>
        <div class="proposal-copy markdown-body proposal-markdown" v-html="renderMarkdown(proposal?.body)" />
        <div class="choice-grid" v-if="proposal?.choices?.length">
          <div v-for="(choice, index) in proposal.choices" :key="choice">
            <span>{{ choiceText(choice) }}</span>
            <strong>{{ proposal.scores?.[index] ?? 0 }}</strong>
          </div>
        </div>
        <a v-if="proposal?.link" :href="proposal.link" target="_blank" rel="noreferrer">查看 Snapshot 原文</a>
        <small v-if="proposal?.created">创建时间：{{ formatDate(proposal.created) }}</small>
      </article>

      <aside class="panel reveal delay-2">
        <div class="section-heading">
          <div><p class="eyebrow">Keyword Cloud</p><h2>提案词云</h2></div>
        </div>
        <div v-if="wordCloud.length" class="proposal-word-cloud">
          <span
            v-for="word in wordCloud"
            :key="word.text"
            class="word-cloud-item"
            :class="word.tone"
            :style="wordStyle(word)"
          >
            {{ word.text }}
          </span>
        </div>
        <div v-else class="empty-state small-empty">暂无可生成词云的关键词。</div>

        <div class="section-heading"><div><p class="eyebrow">Similar</p><h2>相似提案</h2></div></div>
        <div class="similar-list">
          <button v-for="item in similar" :key="item.proposal_id" class="similar-card" @click="router.push(`/governance/proposal/${item.proposal_id}`)">
            <strong>{{ item.title }}</strong>
            <span>{{ item.space_id }} · {{ stateText(item.state) }}</span>
          </button>
          <div v-if="!similar.length" class="empty-state">暂无相似提案。</div>
        </div>
      </aside>
    </section>
  </main>
</template>
