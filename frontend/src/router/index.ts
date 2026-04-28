import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/api/client'
import MainLayout from '@/layouts/MainLayout.vue'
import LoginView from '@/views/auth/LoginView.vue'
import AiAssistantView from '@/views/assistant/AiAssistantView.vue'
import GovernanceOverviewView from '@/views/governance/GovernanceOverviewView.vue'
import ProposalDetailView from '@/views/governance/ProposalDetailView.vue'
import ProposalListView from '@/views/governance/ProposalListView.vue'
import TokenDetailView from '@/views/tokens/TokenDetailView.vue'
import TokenOverviewView from '@/views/tokens/TokenOverviewView.vue'
import WalletInsightView from '@/views/wallet/WalletInsightView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/tokens' },
    { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        { path: 'tokens', name: 'tokens', component: TokenOverviewView },
        { path: 'tokens/:symbol', name: 'token-detail', component: TokenDetailView },
        { path: 'wallet', name: 'wallet', component: WalletInsightView },
        { path: 'governance', name: 'governance', component: GovernanceOverviewView },
        { path: 'governance/proposal/:proposalId', name: 'proposal-detail', component: ProposalDetailView },
        { path: 'governance/:spaceId/proposals', name: 'proposal-list', component: ProposalListView },
        { path: 'assistant', name: 'assistant', component: AiAssistantView },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/tokens' },
  ],
})

router.beforeEach((to) => {
  const hasToken = Boolean(getToken())
  if (to.meta.requiresAuth && !hasToken) return '/login'
  if (to.meta.guestOnly && hasToken) return '/tokens'
  return true
})

export default router
