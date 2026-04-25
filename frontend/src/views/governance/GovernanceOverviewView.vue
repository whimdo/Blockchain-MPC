<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { daoApi, getApiError } from '@/api/client'
import type { DaoCard } from '@/types/api'
import { assetUrl, formatDate } from '@/utils'

const router = useRouter()
const daos = ref<DaoCard[]>([])
const updatedAt = ref('')
const loading = ref(false)
const error = ref('')

async function loadDaos() {
  loading.value = true
  error.value = ''
  try {
    const res = await daoApi.overview()
    daos.value = res.daos
    updatedAt.value = res.page_updated_at
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadDaos)
</script>

<template>
  <main class="page-stack">
    <section class="page-hero panel reveal governance-hero">
      <div>
        <p class="eyebrow">DAO Governance</p>
        <h1>治理总览</h1>
        <p>展示平台配置且可见的 DAO 空间。点击 DAO 卡片进入 Proposal 列表，再点击某个 Proposal 查看详情和相似提案。</p>
      </div>
      <div class="hero-metrics small-metrics">
        <div class="metric-card"><span>DAO Spaces</span><strong>{{ daos.length || '--' }}</strong></div>
        <div class="metric-card"><span>Updated</span><strong class="metric-small-text">{{ formatDate(updatedAt) }}</strong></div>
      </div>
    </section>

    <section class="panel reveal delay-1">
      <div class="section-heading">
        <div><p class="eyebrow">Spaces</p><h2>DAO 卡片</h2></div>
        <button class="ghost compact" :disabled="loading" @click="loadDaos">刷新 DAO</button>
      </div>
      <p v-if="error" class="form-error">{{ error }}</p>
      <div v-if="loading && !daos.length" class="empty-state">正在加载 DAO 总览...</div>
      <div v-else class="dao-card-grid">
        <button v-for="dao in daos" :key="dao.space_id" class="dao-card spacious" @click="router.push(`/governance/${dao.space_id}/proposals`)">
          <img v-if="dao.logo" :src="assetUrl(dao.logo)" :alt="dao.name" />
          <div class="token-fallback" v-else>{{ dao.name.slice(0, 1) }}</div>
          <div>
            <strong>{{ dao.name }}</strong>
            <span>{{ dao.space_id }}</span>
            <p>{{ dao.description || '暂无描述' }}</p>
            <small>同步 {{ dao.synchronized_proposals_count }} 个 Proposal · {{ formatDate(dao.latest_synchronization_time) }}</small>
          </div>
        </button>
      </div>
    </section>
  </main>
</template>
