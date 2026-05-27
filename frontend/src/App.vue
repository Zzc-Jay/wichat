<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from './stores/session'
import { useChatStore } from './stores/chat'
import { useI18n } from './composables/useI18n'


import SidebarPanel from './components/sidebar/SidebarPanel.vue'
import ChatArea from './components/chat/ChatArea.vue'
import BottomInput from './components/input/BottomInput.vue'

import ConfigError from './components/ConfigError.vue'

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const { load: loadI18n, detectLang } = useI18n()

const configError = ref<string | null>(null)
const appReady = ref(false)
const showLangMenu = ref(false)
const t = (zh: string, en: string) => chatStore.lang === 'zh' ? zh : en

function switchLang(l: 'zh' | 'en') {
  showLangMenu.value = false
  loadI18n(l); chatStore.setLang(l)
}
function closeLangMenu(e: MouseEvent) {
  const tgt = e.target as HTMLElement
  if (!tgt.closest('.lang-dropdown')) showLangMenu.value = false
}

onMounted(async () => {
  chatStore.initTheme()
  try {
    const configRes = await fetch('/api/config')
    if (!configRes.ok) {
      const err = await configRes.json()
      configError.value = err.detail || 'Failed to load config'
      return
    }
    const cfg = await configRes.json()
    chatStore.setConfig({ user_avatar: cfg.user_avatar, assistant_avatar: cfg.assistant_avatar })

    await loadI18n(detectLang())

    await sessionStore.fetchSessions()
    if (sessionStore.sessions.length > 0) {
      await sessionStore.loadSession(sessionStore.sessions[0].id)
    } else {
      await sessionStore.createSession()
    }

    appReady.value = true
  } catch (e: any) {
    configError.value = `Cannot connect to backend: ${e.message || e}`
  }
})
</script>

<template>
  <ConfigError v-if="configError" :error="configError" />

  <!-- Loading -->
  <div v-else-if="!appReady" class="flex items-center justify-center h-screen" style="background:var(--bg-primary)">
    <div class="text-center" style="color:var(--text-tertiary)">
      <svg class="w-10 h-10 mx-auto mb-3 animate-spin" style="color:var(--accent)" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p class="text-sm">Loading...</p>
    </div>
  </div>

  <!-- Main App -->
  <div v-else class="flex h-screen overflow-hidden" style="background:var(--bg-primary)" @click="closeLangMenu">
    <SidebarPanel />

    <div class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <header class="header-toolbar shrink-0" style="background:var(--bg-primary)">
        <!-- Theme toggle -->
        <button
          class="btn-icon"
          :title="chatStore.theme === 'light' ? t('深色模式','Dark mode') : t('浅色模式','Light mode')"
          @click="chatStore.toggleTheme()"
        >
          <svg v-if="chatStore.theme === 'light'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
          <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </button>

        <!-- Language dropdown -->
        <div class="lang-dropdown">
          <button class="btn-ghost" :title="t('语言','Language')" @click="showLangMenu = !showLangMenu">
            <span class="text-xs font-semibold">{{ chatStore.lang === 'zh' ? '中' : 'EN' }}</span>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div v-if="showLangMenu" class="lang-dropdown-menu">
            <button class="lang-dropdown-item" :class="{ active: chatStore.lang === 'zh' }" @click="switchLang('zh')">中文</button>
            <button class="lang-dropdown-item" :class="{ active: chatStore.lang === 'en' }" @click="switchLang('en')">English</button>
          </div>
        </div>
      </header>

      <!-- Chat -->
      <ChatArea />
      <BottomInput />
    </div>

  </div>
</template>
