import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getApiError, walletApi } from '@/api/client'
import type { WalletChainOption, WalletInsightResponse } from '@/types/api'

function normalizeChains(chains: string[]) {
  return [...chains].map((item) => item.trim()).filter(Boolean).sort()
}

function cacheKey(address: string, chains: string[]) {
  return `${address.trim().toLowerCase()}::${normalizeChains(chains).join(',')}`
}

export const useWalletInsightStore = defineStore('walletInsight', () => {
  const chainOptions = ref<WalletChainOption[]>([])
  const chainsLoaded = ref(false)
  const loadingChains = ref(false)
  const loading = ref(false)
  const error = ref('')
  const currentKey = ref('')
  const cache = ref<Record<string, WalletInsightResponse>>({})

  const result = computed(() => (currentKey.value ? cache.value[currentKey.value] || null : null))

  async function loadChains() {
    if (chainsLoaded.value || loadingChains.value) return chainOptions.value

    loadingChains.value = true
    error.value = ''
    try {
      const res = await walletApi.chains()
      chainOptions.value = res.chains
      chainsLoaded.value = true
      return chainOptions.value
    } catch (err) {
      error.value = getApiError(err)
      throw err
    } finally {
      loadingChains.value = false
    }
  }

  async function analyze(address: string, chains: string[], force = false) {
    const key = cacheKey(address, chains)
    if (!force && cache.value[key]) {
      currentKey.value = key
      return cache.value[key]
    }
    if (loading.value) return result.value

    loading.value = true
    error.value = ''
    try {
      const response = await walletApi.analyze({ address, chains })
      cache.value[key] = response
      currentKey.value = key
      if (response.chain_options.length && !chainOptions.value.length) {
        chainOptions.value = response.chain_options
        chainsLoaded.value = true
      }
      return response
    } catch (err) {
      error.value = getApiError(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearCache() {
    cache.value = {}
    currentKey.value = ''
    error.value = ''
  }

  return { chainOptions, chainsLoaded, loadingChains, loading, error, result, loadChains, analyze, clearCache }
})
