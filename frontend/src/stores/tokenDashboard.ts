import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getApiError, tokenApi } from '@/api/client'
import type { TokenOverviewResponse } from '@/types/api'

export const useTokenDashboardStore = defineStore('tokenDashboard', () => {
  const overview = ref<TokenOverviewResponse | null>(null)
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref('')
  const lastLoadedAt = ref<string | null>(null)

  const totalOnline = computed(
    () => overview.value?.groups.flatMap((group) => group.cards).filter((token) => token.status === 'online').length ?? 0,
  )

  async function loadOverview(force = false) {
    if (loading.value) return overview.value
    if (loaded.value && !force) return overview.value

    loading.value = true
    error.value = ''
    try {
      overview.value = force ? await tokenApi.refreshAll() : await tokenApi.overview()
      loaded.value = true
      lastLoadedAt.value = new Date().toISOString()
      return overview.value
    } catch (err) {
      error.value = getApiError(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearCache() {
    overview.value = null
    loaded.value = false
    error.value = ''
    lastLoadedAt.value = null
  }

  return { overview, loading, loaded, error, lastLoadedAt, totalOnline, loadOverview, clearCache }
})
