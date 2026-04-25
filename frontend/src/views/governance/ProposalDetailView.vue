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
const error = ref('')

function stateText(state?: string | null) {
  const stateMap: Record<string, string> = {
    active: '进行中',
    closed: '已关闭',
    pending: '待开始',
  }
  return state ? stateMap[state] || state : '--'
}

async function loadDetail() {
  loading.value = true
  error.value = ''
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
        <span class="status-pill online">{{ stateText(proposal?.state) }}</span>
        <h2>{{ proposal?.title }}</h2>
        <p class="proposal-copy">{{ proposal?.body || '该 Proposal 暂无正文。' }}</p>
        <div class="choice-grid" v-if="proposal?.choices?.length">
          <div v-for="(choice, index) in proposal.choices" :key="choice">
            <span>{{ choice }}</span>
            <strong>{{ proposal.scores?.[index] ?? 0 }}</strong>
          </div>
        </div>
        <a v-if="proposal?.link" :href="proposal.link" target="_blank" rel="noreferrer">查看 Snapshot 原文</a>
        <small v-if="proposal?.created">创建时间：{{ formatDate(proposal.created) }}</small>
      </article>

      <aside class="panel reveal delay-2">
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
