<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, CandlestickChart, LineChart } from 'echarts/charts'
import { DataZoomComponent, GridComponent, TooltipComponent } from 'echarts/components'
import type { EChartsOption } from 'echarts'
import { getApiError, tokenApi } from '@/api/client'
import type { TokenAISummary, TokenChartResponse, TokenInfo } from '@/types/api'
import { assetUrl, compactNumber, formatDate, percent } from '@/utils'

use([CanvasRenderer, CandlestickChart, LineChart, BarChart, GridComponent, TooltipComponent, DataZoomComponent])

const route = useRoute()
const router = useRouter()
const symbol = computed(() => String(route.params.symbol || '').toUpperCase())
const info = ref<TokenInfo | null>(null)
const chart = ref<TokenChartResponse | null>(null)
const summary = ref<TokenAISummary | null>(null)
const chartRange = ref('7d')
const chartInterval = ref('1h')
const loading = ref(false)
const summaryLoading = ref(false)
const error = ref('')

const klineRows = computed(() => {
  return (chart.value?.klines ?? []).map((item, index) => {
    const time = item.close_time ?? item.open_time ?? index
    const close = Number(item.close ?? item.price ?? item.end_price ?? 0)
    const open = Number(item.open ?? close)
    const high = Number(item.high ?? Math.max(open, close))
    const low = Number(item.low ?? Math.min(open, close))
    const volume = Number(item.volume ?? item.quote_asset_volume ?? item.quote_volume ?? 0)

    return {
      time: formatDate(time as string | number),
      open,
      close,
      low,
      high,
      volume,
    }
  }).filter((item) => [item.open, item.close, item.low, item.high].every(Number.isFinite))
})

const sharedTooltip = {
  trigger: 'axis' as const,
  backgroundColor: '#102033',
  borderColor: '#274761',
  textStyle: { color: '#eef7ff' },
}

const candlestickOption = computed<EChartsOption>(() => {
  const rows = klineRows.value

  return {
    grid: { left: 58, right: 24, top: 32, bottom: 46 },
    tooltip: sharedTooltip,
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 8, borderColor: 'transparent' }],
    xAxis: { type: 'category', data: rows.map((item) => item.time), boundaryGap: true },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: 'rgba(110, 141, 170, .18)' } } },
    series: [
      {
        name: `${symbol.value} K线`,
        type: 'candlestick',
        data: rows.map((item) => [item.open, item.close, item.low, item.high]),
        itemStyle: {
          color: '#21d0a2',
          color0: '#e05664',
          borderColor: '#0c9f7f',
          borderColor0: '#c85050',
        },
      },
    ],
  }
})

const priceTrendOption = computed<EChartsOption>(() => {
  const rows = klineRows.value

  return {
    grid: { left: 48, right: 18, top: 28, bottom: 46 },
    tooltip: sharedTooltip,
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 8, borderColor: 'transparent' }],
    xAxis: { type: 'category', boundaryGap: false, data: rows.map((item) => item.time) },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: 'rgba(110, 141, 170, .16)' } } },
    series: [
      {
        name: '收盘价',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: rows.map((item) => item.close),
        lineStyle: { width: 3, color: '#21d0a2' },
        areaStyle: { color: 'rgba(33, 208, 162, .14)' },
      },
    ],
  }
})

const volumeTrendOption = computed<EChartsOption>(() => {
  const rows = klineRows.value

  return {
    grid: { left: 58, right: 18, top: 28, bottom: 46 },
    tooltip: sharedTooltip,
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 8, borderColor: 'transparent' }],
    xAxis: { type: 'category', data: rows.map((item) => item.time) },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(110, 141, 170, .16)' } } },
    series: [
      {
        name: '交易量',
        type: 'bar',
        data: rows.map((item) => item.volume),
        itemStyle: { color: '#e59f3a', borderRadius: [6, 6, 0, 0] },
      },
    ],
  }
})

async function loadDetail() {
  loading.value = true
  error.value = ''
  summary.value = null
  try {
    const res = await tokenApi.detail({
      symbol: symbol.value,
      include_chart: true,
      chart_range: chartRange.value,
      chart_interval: chartInterval.value,
      chart_source: 'binance',
    })
    info.value = res.info
    chart.value = res.chart ?? null
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}

async function loadSummary() {
  summaryLoading.value = true
  try {
    const res = await tokenApi.aiSummary({ symbol: symbol.value, chart_summary: chart.value?.summary ?? null })
    summary.value = res.summary
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    summaryLoading.value = false
  }
}

onMounted(loadDetail)
watch(() => route.params.symbol, loadDetail)
</script>

<template>
  <main class="page-stack">
    <section class="detail-header panel reveal">
      <button class="ghost compact" @click="router.push('/tokens')">返回总览</button>
      <div class="token-title">
        <img v-if="info?.logo" :src="assetUrl(info.logo)" :alt="symbol" />
        <div class="token-fallback" v-else>{{ symbol.slice(0, 1) }}</div>
        <div>
          <p class="eyebrow bilingual-label"><span>Token Detail</span><span>代币详情</span></p>
          <h1>{{ info?.display_name || symbol }}</h1>
          <span>{{ info?.primary_chain || '--' }} · {{ info?.category || '--' }}</span>
        </div>
      </div>
      <div class="inline-controls">
        <select v-model="chartRange" @change="loadDetail"><option value="1d">1d</option><option value="7d">7d</option><option value="1m">1m</option><option value="3m">3m</option><option value="1y">1y</option></select>
        <select v-model="chartInterval" @change="loadDetail"><option value="15m">15m</option><option value="1h">1h</option><option value="4h">4h</option><option value="1d">1d</option><option value="1w">1w</option></select>
      </div>
    </section>

    <p v-if="error" class="form-error">{{ error }}</p>

    <section class="grid detail-grid">
      <article class="panel reveal delay-1">
        <div class="market-strip">
          <div><span>Price</span><strong>{{ info?.price_display || '--' }}</strong></div>
          <div><span>24h</span><strong :class="(info?.price_change_24h ?? 0) >= 0 ? 'up' : 'down'">{{ percent(info?.price_change_24h) }}</strong></div>
          <div><span>High</span><strong>{{ compactNumber(info?.high_24h) }}</strong></div>
          <div><span>Low</span><strong>{{ compactNumber(info?.low_24h) }}</strong></div>
          <div><span>Volume</span><strong>{{ compactNumber(info?.volume_24h) }}</strong></div>
        </div>
        <div v-if="klineRows.length" class="chart-suite">
          <div class="chart-card kline-chart-card">
            <div class="mini-heading">
              <div>
                <p class="eyebrow">Candlestick</p>
                <h3>标准 K 线图</h3>
              </div>
              <span>{{ chart?.interval || chartInterval }}</span>
            </div>
            <div class="chart-box kline-chart-box">
              <VChart :option="candlestickOption" autoresize />
            </div>
          </div>

          <div class="chart-pair">
            <div class="chart-card">
              <div class="mini-heading">
                <div>
                  <p class="eyebrow">Price Trend</p>
                  <h3>价格趋势图</h3>
                </div>
              </div>
              <div class="chart-box trend-chart-box">
                <VChart :option="priceTrendOption" autoresize />
              </div>
            </div>

            <div class="chart-card">
              <div class="mini-heading">
                <div>
                  <p class="eyebrow">Volume Trend</p>
                  <h3>交易量趋势图</h3>
                </div>
              </div>
              <div class="chart-box trend-chart-box">
                <VChart :option="volumeTrendOption" autoresize />
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">{{ loading ? '正在加载图表...' : '暂无图表数据' }}</div>
      </article>

      <article class="panel reveal delay-2">
        <div class="section-heading">
          <div><p class="eyebrow">AI Summary</p><h2>智能摘要</h2></div>
          <button class="ghost compact" :disabled="summaryLoading" @click="loadSummary">生成摘要</button>
        </div>
        <div v-if="summary" class="summary-box">
          <h3>{{ summary.title }}</h3>
          <p>{{ summary.summary }}</p>
          <h4>关键观点</h4>
          <ul><li v-for="point in summary.key_points" :key="point">{{ point }}</li></ul>
          <h4>风险提示</h4>
          <ul><li v-for="risk in summary.risk_notes" :key="risk">{{ risk }}</li></ul>
          <small>{{ summary.generated_by }} · {{ formatDate(summary.generated_at) }}</small>
        </div>
        <div v-else class="empty-state">点击生成摘要，查看该代币的智能分析。</div>
      </article>
    </section>
  </main>
</template>
