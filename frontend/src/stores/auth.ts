import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi, clearToken, getToken, saveToken } from '@/api/client'
import type { UserProfile } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserProfile | null>(null)
  const bootstrapped = ref(false)
  const token = ref<string | null>(getToken())

  const isAuthenticated = computed(() => Boolean(token.value))
  const displayName = computed(() => user.value?.display_name || user.value?.username || '未登录')

  async function bootstrap() {
    if (bootstrapped.value) return
    bootstrapped.value = true
    if (!token.value) return

    try {
      const res = await authApi.me()
      user.value = res.user
    } catch {
      signOut()
    }
  }

  async function login(payload: { username: string; password: string }) {
    const res = await authApi.login(payload)
    saveToken(res.access_token)
    token.value = res.access_token
    user.value = res.user
    return res.user
  }

  async function register(payload: { username: string; password: string; email?: string; display_name?: string }) {
    const res = await authApi.register(payload)
    saveToken(res.access_token)
    token.value = res.access_token
    user.value = res.user
    return res.user
  }

  function signOut() {
    clearToken()
    token.value = null
    user.value = null
  }

  return { user, token, bootstrapped, isAuthenticated, displayName, bootstrap, login, register, signOut }
})
