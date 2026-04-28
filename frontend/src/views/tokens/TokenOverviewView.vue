<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useTokenDashboardStore } from '@/stores/tokenDashboard'
import { assetUrl, formatDate } from '@/utils'

const router = useRouter()
const tokenDashboard = useTokenDashboardStore()
const { overview, loading, error, totalOnline } = storeToRefs(tokenDashboard)
const refreshDialogOpen = ref(false)

async function loadOverview(refresh = false) {
  await tokenDashboard.loadOverview(refresh)
  if (refresh) refreshDialogOpen.value = true
}

onMounted(() => loadOverview())
</script>

<template>
  <main class="page-stack">
    <section class="page-hero panel reveal">
      <div>
        <p class="eyebrow">Token Dashboard</p>
        <h1>代币总览</h1>
        <p>按后端配置分组展示主流币种卡片，点击任一代币进入独立详情页查看图表、行情指标和 AI 摘要。</p>
      </div>
      <div class="hero-metrics small-metrics">
        <div class="metric-card"><span>Total</span><strong>{{ overview?.total_tokens ?? '--' }}</strong></div>
        <div class="metric-card"><span>Groups</span><strong>{{ overview?.group_count ?? '--' }}</strong></div>
        <div class="metric-card"><span>Online</span><strong>{{ totalOnline }}</strong></div>
      </div>
    </section>

    <section class="panel reveal delay-1">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Overview</p>
          <h2>分组代币卡片</h2>
        </div>
        <div class="toolbar-actions">
          <span class="muted">更新于 {{ formatDate(overview?.page_updated_at) }}</span>
          <button class="ghost compact" :disabled="loading" @click="loadOverview(true)">刷新全部</button>
        </div>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>
      <div v-if="loading && !overview" class="empty-state">正在加载代币总览...</div>

      <div class="token-groups" v-else>
        <div v-for="group in overview?.groups" :key="group.group_key" class="token-group">
          <div class="group-title">{{ group.group_name }}</div>
          <div class="token-grid">
            <button v-for="token in group.cards" :key="token.symbol" class="token-card rich-card" @click="router.push(`/tokens/${token.symbol}`)">
              <img v-if="token.logo" :src="assetUrl(token.logo)" :alt="token.symbol" />
              <div class="token-fallback" v-else>{{ token.symbol.slice(0, 1) }}</div>
              <div>
                <strong>{{ token.symbol }}</strong>
                <span>{{ token.display_name || token.name }}</span>
                <small>{{ token.primary_chain }} · {{ token.category }}</small>
              </div>
              <p>{{ token.price_display || '--' }}</p>
              <em :class="token.status">{{ token.status }}</em>
            </button>
          </div>
        </div>
      </div>
    </section>

    <div v-if="refreshDialogOpen" class="modal-backdrop" @click.self="refreshDialogOpen = false">
      <section class="sync-dialog panel reveal">
        <p class="eyebrow">Refresh Complete</p>
        <h2>刷新成功</h2>
        <p class="muted">
          已完成全部代币行情刷新，共加载 <strong>{{ overview?.total_tokens ?? 0 }}</strong> 个代币，
          更新时间为 <strong>{{ formatDate(overview?.page_updated_at) }}</strong>。
        </p>
        <button class="primary compact" @click="refreshDialogOpen = false">我知道了</button>
      </section>
    </div>
  </main>
</template>



