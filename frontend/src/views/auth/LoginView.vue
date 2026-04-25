<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')
const form = ref({
  username: 'alice',
  password: 'password123',
  email: 'alice@example.com',
  display_name: 'Alice',
})

const title = computed(() => mode.value === 'login' ? '欢迎回来' : '创建账户')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    if (mode.value === 'login') {
      await auth.login({ username: form.value.username, password: form.value.password })
    } else {
      await auth.register(form.value)
    }
    router.push('/tokens')
  } catch (err) {
    error.value = getApiError(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-hero panel reveal">
      <div class="auth-logo-lockup">
        <img src="/chainpilot.svg" alt="ChainPilot" />
        <p class="eyebrow">ChainPilot</p>
      </div>
      <h1>为链上资产、DAO 治理和 AI 交互导航。</h1>
      <p>
        ChainPilot 像一枚链上驾驶舱罗盘，登录后默认进入代币总览；再通过顶部导航切换治理空间和 AI 助手。
      </p>
      <div class="auth-orbit">
        <span>Token Overview</span>
        <span>DAO Governance</span>
        <span>AI Assistant</span>
      </div>
    </section>

    <section class="auth-card panel reveal delay-1">
      <div class="section-heading compact-heading">
        <div>
          <p class="eyebrow">Account</p>
          <h2>{{ title }}</h2>
        </div>
      </div>

      <div class="segmented">
        <button type="button" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button type="button" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <form class="form-stack" @submit.prevent="submit">
        <label>用户名或邮箱<input v-model="form.username" autocomplete="username" /></label>
        <label>密码<input v-model="form.password" type="password" autocomplete="current-password" /></label>
        <template v-if="mode === 'register'">
          <label>邮箱<input v-model="form.email" autocomplete="email" /></label>
          <label>展示名<input v-model="form.display_name" /></label>
        </template>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="primary wide" :disabled="loading">{{ loading ? '提交中...' : mode === 'login' ? '登录并进入主界面' : '注册并进入主界面' }}</button>
      </form>
    </section>
  </main>
</template>
