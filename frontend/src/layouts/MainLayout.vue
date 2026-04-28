<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.signOut()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/tokens">
        <span class="brand-mark">
          <img src="/chainpilot.svg" alt="ChainPilot" />
        </span>
        <span>
          <strong>ChainPilot</strong>
          <small>Onchain Intelligence</small>
        </span>
      </RouterLink>

      <nav class="main-nav">
        <RouterLink to="/tokens">代币</RouterLink>
        <RouterLink to="/wallet">地址分析</RouterLink>
        <RouterLink to="/governance">治理</RouterLink>
        <RouterLink to="/news">新闻</RouterLink>
        <RouterLink to="/assistant">AI助手</RouterLink>
      </nav>

      <div class="user-chip">
        <span>{{ auth.displayName }}</span>
        <button @click="logout">退出</button>
      </div>
    </header>

    <RouterView />
  </div>
</template>
