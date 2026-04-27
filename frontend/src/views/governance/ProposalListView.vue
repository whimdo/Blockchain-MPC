<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { daoApi, getApiError } from '@/api/client'
import type { ProposalListItem } from '@/types/api'
import { formatDate } from '@/utils'

const route = useRoute()
const router = useRouter()
const spaceId = computed(() => String(route.params.spaceId || ''))
const daoName = ref('')
const proposals = ref<ProposalListItem[]>([])
const updatedAt = ref('')
const page = ref(1)
const pageInput = ref(1)
const pageSize = ref(12)
const total = ref(0)
const stateFilter = ref('all')
const syncLatestK = ref(10)
const loading = ref(false)
const syncing = ref(false)
const error = ref('')
const syncDialogOpen = ref(false)
const syncDialog = ref({
  fetched: 0,
  recentUpdated: 0,
})

const stateOptions = ['all', 'active', 'pending', 'closed']

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const pageStart = computed(() => total.value ? (page.value - 1) * pageSize.value + 1 : 0)
const pageEnd = computed(() => total.value ? Math.min(page.value * pageSize.value, total.value) : 0)

function stateText(state: string) {
  const stateMap: Record<string, string> = {
    all: '全部状态',
    active: '进行中',
    closed: '已关闭',
    pending: '待开始',
  }
  return stateMap[state] || state
}

function stateClass(state: string) {
  const normalized = (state || '').trim().toLowerCase()
  return {
    active: normalized === 'active' || normalized === '进行中',
    pending: normalized === 'pending' || normalized === '待开始',
    closed: normalized === 'closed' || normalized === '已关闭',
  }
}

async function loadProposals() {
  loading.value = true
  error.value = ''
  try {
    const res = await daoApi.proposals(
      spaceId.value,
      page.value,
      pageSize.value,
      stateFilter.value === 'all' ? null : stateFilter.value,
    )
    proposals.value = res.proposals
    daoName.value = res.dao_name
    updatedAt.value = res.page_updated_at
    total.value = res.total ?? res.proposals.length
    page.value = Math.min(res.page || page.value, totalPages.value)
    pageInput.value = page.value
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

async function dynamicSync() {
  syncing.value = true
  error.value = ''
  syncDialogOpen.value = false
  try {
    const res = await daoApi.dynamicSync({ space_id: spaceId.value, latest_k: syncLatestK.value })
    if (res.proposals.length) {
      proposals.value = res.proposals
      total.value = res.proposals.length
      return
    }

    syncDialog.value = {
      fetched: res.fetched_count,
      recentUpdated: res.recent_updated_count,
    }
    syncDialogOpen.value = true
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    syncing.value = false
  }
}

function changePage(nextPage: number) {
  const safePage = Math.min(Math.max(nextPage, 1), totalPages.value)
  pageInput.value = safePage
  if (safePage === page.value) return
  page.value = safePage
  loadProposals()
}

function changePageSize() {
  page.value = 1
  pageInput.value = 1
  loadProposals()
}

function changeState() {
  page.value = 1
  pageInput.value = 1
  loadProposals()
}

function resetFilters() {
  stateFilter.value = 'all'
  page.value = 1
  pageInput.value = 1
  loadProposals()
}

function submitPageInput() {
  changePage(Number(pageInput.value) || 1)
}

onMounted(loadProposals)
watch(() => route.params.spaceId, () => {
  page.value = 1
  pageInput.value = 1
  resetFilters()
})
</script>

<template>
  <main class="page-stack">
    <section class="detail-header panel reveal">
      <button class="ghost compact" @click="router.push('/governance')">返回治理总览</button>
      <div>
        <p class="eyebrow bilingual-label"><span>Proposal List</span><span>提案列表</span></p>
        <h1>{{ daoName || spaceId }}</h1>
        <span class="muted">{{ spaceId }} · 更新于 {{ formatDate(updatedAt) }}</span>
      </div>
      <div class="inline-controls">
        <input v-model.number="syncLatestK" class="tiny-input" type="number" min="1" max="50" />
        <button class="primary compact" :disabled="syncing" @click="dynamicSync">动态同步</button>
      </div>
    </section>

    <section class="panel reveal delay-1">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Proposals</p>
          <h2>提案列表</h2>
        </div>
        <span class="muted">第 {{ pageStart }}-{{ pageEnd }} 条 / 共 {{ total || proposals.length }} 条</span>
      </div>

      <div class="proposal-filter-bar">
        <label>
          <span>状态</span>
          <select v-model="stateFilter" @change="changeState">
            <option v-for="state in stateOptions" :key="state" :value="state">{{ stateText(state) }}</option>
          </select>
        </label>
        <label>
          <span>每页展示</span>
          <select v-model.number="pageSize" @change="changePageSize">
            <option :value="6">6 条</option>
            <option :value="12">12 条</option>
            <option :value="24">24 条</option>
            <option :value="48">48 条</option>
          </select>
        </label>
        <button class="ghost compact" @click="resetFilters">重置筛选</button>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>
      <div v-if="loading" class="empty-state">正在加载 Proposal...</div>
      <div v-else class="proposal-grid">
        <button v-for="proposal in proposals" :key="proposal.proposal_id" class="proposal-card" @click="router.push(`/governance/proposal/${proposal.proposal_id}`)">
          <span class="proposal-state" :class="stateClass(proposal.state)">{{ stateText(proposal.state) }}</span>
          <h3>{{ proposal.title }}</h3>
          <p>{{ proposal.author || 'unknown author' }}</p>
          <div class="tag-row">
            <small class="keyword-label">关键词</small>
            <small v-for="keyword in proposal.keywords" :key="keyword">{{ keyword }}</small>
            <small v-if="!proposal.keywords.length">暂无</small>
          </div>
        </button>
        <div v-if="!proposals.length" class="empty-state">当前页暂无 Proposal。</div>
      </div>

      <div class="pagination-bar" v-if="!loading">
        <button class="ghost compact" :disabled="page <= 1" @click="changePage(page - 1)">上一页</button>
        <label class="page-jump">
          <span>第</span>
          <input v-model.number="pageInput" type="number" min="1" :max="totalPages" @change="submitPageInput" @keyup.enter="submitPageInput" />
          <span>/ {{ totalPages }} 页</span>
        </label>
        <button class="ghost compact" :disabled="page >= totalPages" @click="changePage(page + 1)">下一页</button>
      </div>
    </section>

    <div v-if="syncDialogOpen" class="modal-backdrop" @click.self="syncDialogOpen = false">
      <section class="sync-dialog panel reveal">
        <p class="eyebrow">Dynamic Sync</p>
        <h2>暂无新的提案</h2>
        <p class="muted">
          本次动态同步抓取了 <strong>{{ syncDialog.fetched }}</strong> 个最近 Proposal，
          其中 <strong>{{ syncDialog.recentUpdated }}</strong> 个属于最近已同步/已存在的 Proposal。
        </p>
        <button class="primary compact" @click="syncDialogOpen = false">我知道了</button>
      </section>
    </div>
  </main>
</template>
