import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getApiError, newsApi } from '@/api/client'
import type { NewsLatestResponse } from '@/types/api'

export const useNewsStore = defineStore('news', () => {
  const latest = ref<NewsLatestResponse | null>(null)
  const loaded = ref(false)
  const loading = ref(false)
  const syncing = ref(false)
  const error = ref('')
  const activeCategory = ref('all')
  const activeSymbol = ref('')

  const articles = computed(() => latest.value?.articles ?? [])
  const categories = computed(() => latest.value?.categories ?? [])

  async function loadLatest(force = false) {
    if (loading.value) return latest.value
    if (loaded.value && !force) return latest.value

    loading.value = true
    error.value = ''
    try {
      latest.value = await newsApi.latest({
        limit: 48,
        category: activeCategory.value === 'all' ? null : activeCategory.value,
        symbol: activeSymbol.value || null,
      })
      loaded.value = true
      return latest.value
    } catch (err) {
      error.value = getApiError(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function syncNews() {
    syncing.value = true
    error.value = ''
    try {
      await newsApi.sync(50)
      loaded.value = false
      return await loadLatest(true)
    } catch (err) {
      error.value = getApiError(err)
      throw err
    } finally {
      syncing.value = false
    }
  }

  function setFilters(category: string, symbol: string) {
    activeCategory.value = category
    activeSymbol.value = symbol.trim().toUpperCase()
    loaded.value = false
  }

  return { latest, loaded, loading, syncing, error, activeCategory, activeSymbol, articles, categories, loadLatest, syncNews, setFilters }
})
