<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useNewsStore } from '@/stores/news'
import { formatDate } from '@/utils'

const news = useNewsStore()
const { latest, loading, syncing, error, activeCategory, activeSymbol, articles, categories } = storeToRefs(news)
const syncDialogOpen = ref(false)
const symbolInput = ref('')
const page = ref(1)
const pageInput = ref(1)
const pageSize = 6

const categoryLabels: Record<string, string> = {
  all: '全部',
  market: '市场行情',
  dao: 'DAO治理',
  defi: 'DeFi',
  layer2: 'Layer2',
  security: '安全事件',
  regulation: '监管政策',
}

const hotSymbols = computed(() => {
  const counts = new Map<string, number>()
  for (const article of articles.value) {
    for (const symbol of article.related_symbols) counts.set(symbol, (counts.get(symbol) || 0) + 1)
  }
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 10)
})
const totalPages = computed(() => Math.max(1, Math.ceil(articles.value.length / pageSize)))
const pageStart = computed(() => (articles.value.length ? (page.value - 1) * pageSize + 1 : 0))
const pageEnd = computed(() => Math.min(page.value * pageSize, articles.value.length))
const pagedArticles = computed(() => {
  const safePage = Math.min(page.value, totalPages.value)
  const start = (safePage - 1) * pageSize
  return articles.value.slice(start, start + pageSize)
})

function categoryText(category: string) {
  return categoryLabels[category] || category
}

async function applyFilters(category = activeCategory.value, symbol = symbolInput.value) {
  news.setFilters(category, symbol)
  await news.loadLatest(true)
  resetPage()
}

async function syncNews() {
  await news.syncNews()
  resetPage()
  syncDialogOpen.value = true
}

function resetPage() {
  page.value = 1
  pageInput.value = 1
}

function changePage(nextPage: number) {
  const safePage = Math.min(Math.max(nextPage, 1), totalPages.value)
  page.value = safePage
  pageInput.value = safePage
}

function submitPageInput() {
  changePage(Number(pageInput.value) || 1)
}

function askAi(articleTitle: string, articleSummary?: string | null) {
  const prompt = `请解读这条 CoinDesk 新闻，并分析它可能影响哪些代币或链上风险：\n标题：${articleTitle}\n摘要：${articleSummary || '暂无摘要'}`
  sessionStorage.setItem('chainpilot_ai_draft', prompt)
  window.location.href = '/assistant'
}

onMounted(() => news.loadLatest())
</script>

<template>
  <main class="page-stack">
    <section class="page-hero news-hero panel reveal">
      <div>
        <p class="eyebrow bilingual-label"><span>News Intelligence</span><span>新闻资讯</span></p>
        <h1>CoinDesk 加密新闻</h1>
        <p>展示市场、DeFi、DAO、Layer2、安全与监管相关新闻，并自动识别相关代币。</p>
      </div>
      <div class="hero-metrics small-metrics">
        <div class="metric-card"><span>Articles</span><strong>{{ latest?.total ?? '--' }}</strong></div>
        <div class="metric-card"><span>Source</span><strong>CoinDesk</strong></div>
        <div class="metric-card"><span>Updated</span><strong>{{ formatDate(latest?.page_updated_at) }}</strong></div>
      </div>
    </section>

    <section class="panel reveal delay-1 news-filter-panel">
      <div class="section-heading">
        <div><p class="eyebrow">Filters</p><h2>新闻筛选</h2></div>
        <button class="primary compact" :disabled="syncing" @click="syncNews">{{ syncing ? '同步中...' : '同步 CoinDesk RSS' }}</button>
      </div>
      <div class="news-filter-bar">
        <label>
          <span>分类</span>
          <select v-model="activeCategory" @change="applyFilters(activeCategory, symbolInput)">
            <option value="all">全部</option>
            <option v-for="category in categories" :key="category" :value="category">{{ categoryText(category) }}</option>
          </select>
        </label>
        <label>
          <span>相关代币</span>
          <input v-model="symbolInput" placeholder="例如 BTC / ETH / AAVE" @keyup.enter="applyFilters(activeCategory, symbolInput)" />
        </label>
        <button class="ghost compact" @click="applyFilters(activeCategory, symbolInput)">应用筛选</button>
        <button class="ghost compact" @click="symbolInput = ''; applyFilters('all', '')">重置</button>
      </div>
      <p v-if="error" class="form-error">{{ error }}</p>
    </section>

    <section class="grid news-layout">
      <article class="panel reveal delay-1">
        <div class="section-heading">
          <div><p class="eyebrow">Latest</p><h2>最新新闻</h2></div>
          <span class="muted">第 {{ pageStart }}-{{ pageEnd }} 条 / 共 {{ articles.length }} 条</span>
        </div>

        <div v-if="loading && !articles.length" class="empty-state">正在加载新闻...</div>
        <div v-else class="news-card-list">
          <article v-for="article in pagedArticles" :key="article.article_id" class="news-card">
            <div class="news-card-head">
              <span>{{ article.category_label }}</span>
              <small>{{ article.source }} · {{ formatDate(article.published_at) }}</small>
            </div>
            <h3>{{ article.title }}</h3>
            <p>{{ article.summary || '暂无摘要。' }}</p>
            <div class="tag-row" v-if="article.related_symbols.length || article.related_keywords.length">
              <small v-for="symbol in article.related_symbols" :key="symbol" class="keyword-label">{{ symbol }}</small>
              <small v-for="keyword in article.related_keywords" :key="keyword">{{ keyword }}</small>
            </div>
            <div class="news-actions">
              <a :href="article.url" target="_blank" rel="noreferrer">查看原文</a>
              <button class="ghost compact" @click="askAi(article.title, article.summary)">AI 解读</button>
            </div>
          </article>
          <div v-if="!articles.length" class="empty-state">暂无新闻缓存，点击“同步 CoinDesk RSS”获取最新内容。</div>
        </div>

        <div class="pagination-bar" v-if="articles.length">
          <button class="ghost compact" :disabled="page <= 1" @click="changePage(page - 1)">上一页</button>
          <label class="page-jump">
            <span>第</span>
            <input v-model.number="pageInput" type="number" min="1" :max="totalPages" @change="submitPageInput" @keyup.enter="submitPageInput" />
            <span>/ {{ totalPages }} 页</span>
          </label>
          <button class="ghost compact" :disabled="page >= totalPages" @click="changePage(page + 1)">下一页</button>
        </div>
      </article>

      <aside class="panel reveal delay-2">
        <div class="section-heading"><div><p class="eyebrow">Signals</p><h2>热点代币</h2></div></div>
        <div class="news-signal-list">
          <button v-for="[symbol, count] in hotSymbols" :key="symbol" class="news-signal-card" @click="symbolInput = symbol; applyFilters('all', symbol)">
            <strong>{{ symbol }}</strong>
            <span>{{ count }} 篇相关新闻</span>
          </button>
          <div v-if="!hotSymbols.length" class="empty-state small-empty">暂无热点代币。</div>
        </div>
      </aside>
    </section>

    <div v-if="syncDialogOpen" class="modal-backdrop" @click.self="syncDialogOpen = false">
      <section class="sync-dialog panel reveal">
        <p class="eyebrow">News Sync</p>
        <h2>新闻同步完成</h2>
        <p class="muted">已从 CoinDesk RSS 同步新闻，当前列表共 <strong>{{ articles.length }}</strong> 篇。</p>
        <button class="primary compact" @click="syncDialogOpen = false">我知道了</button>
      </section>
    </div>
  </main>
</template>
