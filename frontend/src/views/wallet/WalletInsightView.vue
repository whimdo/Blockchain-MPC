<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { LegendComponent, TooltipComponent } from 'echarts/components'
import type { EChartsOption } from 'echarts'
import { getApiError, walletApi } from '@/api/client'
import type { WalletChainOption, WalletInsightResponse } from '@/types/api'
import { assetUrl, compactNumber, formatDate } from '@/utils'

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

const router = useRouter()
const address = ref('')
const chainOptions = ref<WalletChainOption[]>([])
const selectedChains = ref<string[]>([])
const result = ref<WalletInsightResponse | null>(null)
const loading = ref(false)
const loadingChains = ref(false)
const error = ref('')
const assetSupportFilter = ref<'all' | 'supported' | 'unsupported'>('all')
const assetChainFilter = ref('all')
const assetSort = ref<'default' | 'value'>('default')
const assetPage = ref(1)
const assetPageInput = ref(1)
const assetPageSize = 8
const supportedTokenSymbols = new Set([
  'BTC',
  'ETH',
  'USDT',
  'USDC',
  'BNB',
  'SOL',
  'ADA',
  'AVAX',
  'TON',
  'NEAR',
  'ARB',
  'OP',
  'XRP',
  'TRX',
  'DOGE',
  'LINK',
  'UNI',
  'AAVE',
  'FIL',
  'SHIB',
])

const riskClass = computed(() => `risk-${result.value?.risk_level || 'medium'}`)
const assetChainOptions = computed(() => {
  const chains = new Set((result.value?.assets ?? []).map((asset) => asset.blockchain || 'unknown'))
  return Array.from(chains)
})
const filteredAssets = computed(() => {
  const assets = [...(result.value?.assets ?? [])]
  const filtered = assets.filter((asset) => {
    const supported = isSupportedToken(asset.symbol)
    if (assetSupportFilter.value === 'supported' && !supported) return false
    if (assetSupportFilter.value === 'unsupported' && supported) return false
    if (assetChainFilter.value !== 'all' && (asset.blockchain || 'unknown') !== assetChainFilter.value) return false
    return true
  })

  if (assetSort.value === 'value') {
    filtered.sort((a, b) => b.value_usdt - a.value_usdt)
  }

  return filtered
})
const assetTotalPages = computed(() => Math.max(1, Math.ceil(filteredAssets.value.length / assetPageSize)))
const pagedAssets = computed(() => {
  const safePage = Math.min(assetPage.value, assetTotalPages.value)
  const start = (safePage - 1) * assetPageSize
  return filteredAssets.value.slice(start, start + assetPageSize)
})
const assetPageStart = computed(() => (filteredAssets.value.length ? (assetPage.value - 1) * assetPageSize + 1 : 0))
const assetPageEnd = computed(() => Math.min(assetPage.value * assetPageSize, filteredAssets.value.length))

const categoryOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: '#102033',
    borderColor: '#274761',
    textStyle: { color: '#eef7ff' },
    formatter: '{b}: {d}%',
  },
  legend: {
    bottom: 0,
    icon: 'circle',
    textStyle: { color: '#687889', fontWeight: 800 },
  },
  series: [
    {
      name: '资产分类',
      type: 'pie',
      radius: ['44%', '72%'],
      center: ['50%', '43%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: '#fffef7', borderWidth: 3 },
      label: { color: '#102033', fontWeight: 900, formatter: '{b}\n{d}%' },
      data: (result.value?.category_breakdown ?? []).map((item) => ({
        name: item.label,
        value: Number(item.value_usdt.toFixed(2)),
      })),
    },
  ],
}))

function toggleChain(key: string) {
  selectedChains.value = selectedChains.value.includes(key)
    ? selectedChains.value.filter((item) => item !== key)
    : [...selectedChains.value, key]
}

function ratio(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function shortAddress(value?: string | null) {
  if (!value) return '--'
  return value.length > 14 ? `${value.slice(0, 8)}...${value.slice(-6)}` : value
}

function isSupportedToken(symbol: string) {
  return supportedTokenSymbols.has((symbol || '').trim().toUpperCase())
}

function resetAssetPage() {
  assetPage.value = 1
  assetPageInput.value = 1
}

function changeAssetPage(nextPage: number) {
  const safePage = Math.min(Math.max(nextPage, 1), assetTotalPages.value)
  assetPage.value = safePage
  assetPageInput.value = safePage
}

function submitAssetPageInput() {
  changeAssetPage(Number(assetPageInput.value) || 1)
}

function openTokenDetail(symbol: string) {
  if (!isSupportedToken(symbol)) return
  router.push(`/tokens/${symbol}`)
}

async function loadChains() {
  loadingChains.value = true
  try {
    const res = await walletApi.chains()
    chainOptions.value = res.chains
    selectedChains.value = chainOptions.value.map((item) => item.key)
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loadingChains.value = false
  }
}

async function analyzeWallet() {
  loading.value = true
  error.value = ''
  try {
    result.value = await walletApi.analyze({ address: address.value, chains: selectedChains.value })
    assetSupportFilter.value = 'all'
    assetChainFilter.value = 'all'
    assetSort.value = 'default'
    resetAssetPage()
    if (result.value.chain_options.length && !chainOptions.value.length) {
      chainOptions.value = result.value.chain_options
    }
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

function askAi() {
  if (!result.value) return
  const prompt = [
    `请分析地址 ${result.value.address} 的链上资产画像。`,
    `总资产约 ${result.value.total_value_usdt.toFixed(2)} USDT。`,
    `稳定币占比 ${ratio(result.value.stablecoin_ratio)}，DeFi/治理占比 ${ratio(result.value.defi_ratio)}，Meme 占比 ${ratio(result.value.meme_ratio)}。`,
    `主要资产：${result.value.assets.slice(0, 5).map((item) => `${item.symbol} ${ratio(item.ratio)}`).join('、')}。`,
  ].join('\n')
  sessionStorage.setItem('chainpilot_ai_draft', prompt)
  router.push('/assistant')
}

onMounted(loadChains)
</script>

<template>
  <main class="page-stack">
    <section class="page-hero wallet-hero panel reveal">
      <div>
        <p class="eyebrow bilingual-label"><span>Wallet Insight</span><span>地址分析</span></p>
        <h1>链上地址资产画像</h1>
        <p>输入钱包地址后，系统会聚合多链资产、估算总资产、分析资产结构，并识别可能关联的 DAO 治理代币。</p>
      </div>
      <div class="hero-metrics small-metrics">
        <div class="metric-card"><span>Total Value</span><strong>{{ result ? compactNumber(result.total_value_usdt) : '--' }}</strong></div>
        <div class="metric-card"><span>Assets</span><strong>{{ result?.asset_count ?? '--' }}</strong></div>
        <div class="metric-card"><span>Risk</span><strong>{{ result?.risk_label ?? '--' }}</strong></div>
      </div>
    </section>

    <section class="panel reveal delay-1 wallet-query-panel">
      <div class="wallet-query-main">
        <label>
          <span>钱包地址</span>
          <input v-model="address" placeholder="例如：0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" @keyup.enter="analyzeWallet" />
        </label>
        <button class="primary" :disabled="loading || !address.trim()" @click="analyzeWallet">
          {{ loading ? '分析中...' : '开始分析' }}
        </button>
      </div>

      <div class="chain-picker">
        <span>{{ loadingChains ? '正在加载链配置...' : '选择链' }}</span>
        <button
          v-for="chain in chainOptions"
          :key="chain.key"
          class="chain-chip"
          :class="{ active: selectedChains.includes(chain.key) }"
          @click="toggleChain(chain.key)"
        >
          {{ chain.label }}
        </button>
      </div>
    </section>

    <p v-if="error" class="form-error">{{ error }}</p>

    <section v-if="result" class="grid wallet-grid">
      <article class="panel reveal delay-1 wallet-summary-card">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Portfolio</p>
            <h2>{{ shortAddress(result.address) }}</h2>
          </div>
          <span class="risk-pill" :class="riskClass">风险{{ result.risk_label }}</span>
        </div>

        <div class="wallet-value-row">
          <span>总资产估值</span>
          <strong>{{ compactNumber(result.total_value_usdt) }} USDT</strong>
          <small>更新于 {{ formatDate(result.page_updated_at) }}</small>
        </div>

        <div class="wallet-ratio-grid">
          <div><span>稳定币</span><strong>{{ ratio(result.stablecoin_ratio) }}</strong></div>
          <div><span>主流资产</span><strong>{{ ratio(result.mainstream_ratio) }}</strong></div>
          <div><span>DeFi/治理</span><strong>{{ ratio(result.defi_ratio) }}</strong></div>
          <div><span>Meme</span><strong>{{ ratio(result.meme_ratio) }}</strong></div>
        </div>

        <div class="insight-list">
          <p v-for="insight in result.insights" :key="insight">{{ insight }}</p>
        </div>
        <button class="ghost compact" @click="askAi">让 AI 继续分析</button>
      </article>

      <article class="panel reveal delay-2 wallet-chart-card">
        <div class="section-heading"><div><p class="eyebrow">Allocation</p><h2>资产结构</h2></div></div>
        <div v-if="result.category_breakdown.length" class="wallet-chart-box">
          <VChart :option="categoryOption" autoresize />
        </div>
        <div v-else class="empty-state">暂无可估值资产。</div>
      </article>
    </section>

    <section v-if="result" class="grid wallet-lower-grid">
      <article class="panel reveal delay-1">
        <div class="section-heading">
          <div><p class="eyebrow">Assets</p><h2>资产明细</h2></div>
          <span class="muted">第 {{ assetPageStart }}-{{ assetPageEnd }} 条 / 共 {{ filteredAssets.length }} 条</span>
        </div>

        <div class="wallet-table-filter">
          <label>
            <span>支持状态</span>
            <select v-model="assetSupportFilter" @change="resetAssetPage">
              <option value="all">默认</option>
              <option value="supported">平台支持</option>
              <option value="unsupported">平台不支持</option>
            </select>
          </label>
          <label>
            <span>链</span>
            <select v-model="assetChainFilter" @change="resetAssetPage">
              <option value="all">全部链</option>
              <option v-for="chain in assetChainOptions" :key="chain" :value="chain">{{ chain }}</option>
            </select>
          </label>
          <label>
            <span>排序方式</span>
            <select v-model="assetSort" @change="resetAssetPage">
              <option value="default">默认</option>
              <option value="value">按价值总额</option>
            </select>
          </label>
        </div>

        <div class="wallet-asset-table-wrap">
          <table v-if="pagedAssets.length" class="wallet-asset-table">
            <thead>
              <tr>
                <th>资产</th>
                <th>链</th>
                <th>支持状态</th>
                <th>余额</th>
                <th>估值</th>
                <th>占比</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="asset in pagedAssets"
                :key="`${asset.blockchain}-${asset.symbol}`"
                :class="{ clickable: isSupportedToken(asset.symbol), unsupported: !isSupportedToken(asset.symbol) }"
                @click="openTokenDetail(asset.symbol)"
              >
                <td>
                  <div class="wallet-table-token">
                    <img v-if="asset.logo" :src="assetUrl(asset.logo)" :alt="asset.symbol" />
                    <div class="token-fallback" v-else>{{ asset.symbol.slice(0, 1) }}</div>
                    <div>
                      <strong>{{ asset.symbol }}</strong>
                      <span>{{ asset.name || asset.symbol }}</span>
                    </div>
                  </div>
                </td>
                <td>{{ asset.blockchain || '--' }}</td>
                <td>
                  <small :class="isSupportedToken(asset.symbol) ? 'support-tag' : 'support-tag muted-tag'">
                    {{ isSupportedToken(asset.symbol) ? '平台支持' : '平台不支持' }}
                  </small>
                </td>
                <td>{{ asset.display_balance || compactNumber(asset.balance) }}</td>
                <td><strong>{{ compactNumber(asset.value_usdt) }} USDT</strong></td>
                <td>{{ ratio(asset.ratio) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">当前筛选条件下暂无资产。</div>
        </div>

        <div class="pagination-bar" v-if="filteredAssets.length">
          <button class="ghost compact" :disabled="assetPage <= 1" @click="changeAssetPage(assetPage - 1)">上一页</button>
          <label class="page-jump">
            <span>第</span>
            <input v-model.number="assetPageInput" type="number" min="1" :max="assetTotalPages" @change="submitAssetPageInput" @keyup.enter="submitAssetPageInput" />
            <span>/ {{ assetTotalPages }} 页</span>
          </label>
          <button class="ghost compact" :disabled="assetPage >= assetTotalPages" @click="changeAssetPage(assetPage + 1)">下一页</button>
        </div>
      </article>

      <aside class="panel reveal delay-2">
        <div class="section-heading"><div><p class="eyebrow">Governance</p><h2>治理关联</h2></div></div>
        <div class="governance-hint-list">
          <button
            v-for="hint in result.governance_hints"
            :key="hint.symbol"
            class="governance-hint-card"
            @click="router.push(`/governance/${hint.space_id}/proposals`)"
          >
            <span>{{ hint.symbol }}</span>
            <strong>{{ hint.dao_name }}</strong>
            <small>{{ compactNumber(hint.value_usdt) }} USDT · {{ ratio(hint.ratio) }}</small>
          </button>
          <div v-if="!result.governance_hints.length" class="empty-state">暂未识别到明显 DAO 治理代币。</div>
        </div>
      </aside>
    </section>

    <section v-if="!result && !loading" class="panel reveal delay-2 wallet-empty-guide">
      <p class="eyebrow">How it works</p>
      <h2>从地址到资产画像</h2>
      <div class="wallet-guide-grid">
        <div><strong>1</strong><span>选择链并抓取地址资产</span></div>
        <div><strong>2</strong><span>结合价格缓存估算资产价值</span></div>
        <div><strong>3</strong><span>根据分类和治理代币生成画像</span></div>
      </div>
    </section>
  </main>
</template>
