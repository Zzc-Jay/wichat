<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSessionStore } from '../../stores/session'
import { useChatStore } from '../../stores/chat'

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const collapsed = ref(false)

const t = (zh: string, en: string) => chatStore.lang === 'zh' ? zh : en

function handleSelect(id: string) {
  sessionStore.loadSession(id)
}
function handleDelete(id: string, e: Event) {
  e.stopPropagation()
  sessionStore.deleteSession(id)
}

function normalizeTitle(s: { id: string; title: string }): string {
  if (/^\d{8}_\d{6}$/.test(s.title)) return t('未命名对话', 'Untitled chat')
  return s.title
}

function getDateGroup(id: string): string {
  const y = id.slice(0, 4), m = id.slice(4, 6), d = id.slice(6, 8)
  const dStr = `${y}-${m}-${d}`
  const today = new Date().toISOString().slice(0, 10)
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  if (dStr === today) return 'today'
  if (dStr === yesterday) return 'yesterday'
  return 'earlier'
}

const groupedSessions = computed(() => {
  const groups: { key: string; label: string; items: typeof sessionStore.sessions }[] = [
    { key: 'today', label: t('今天', 'Today'), items: [] },
    { key: 'yesterday', label: t('昨天', 'Yesterday'), items: [] },
    { key: 'earlier', label: t('更早', 'Earlier'), items: [] },
  ]
  for (const s of sessionStore.sessions) {
    const g = getDateGroup(s.id)
    const target = groups.find(x => x.key === g)
    if (target) target.items.push(s)
  }
  return groups.filter(g => g.items.length > 0)
})
</script>

<template>
  <aside
    class="h-screen flex flex-col shrink-0 transition-all duration-200 border-r"
    :class="collapsed ? 'w-0 overflow-hidden border-0' : ''"
    :style="{background:'var(--bg-sidebar)', borderColor:'var(--border-primary)', width: collapsed ? '0' : '280px'}"
  >
    <!-- Brand -->
    <div class="flex items-center justify-between px-3 h-14 pb-4 shrink-0">
      <div class="flex items-center gap-2.5">
        <img src="/icon.png" alt="WiChat" class="w-8 h-8 rounded-lg flex-shrink-0" />
        <div class="leading-tight">
          <div style="font-size:var(--text-lg);font-weight:var(--weight-bold);color:var(--text-primary);letter-spacing:-0.02em">WiChat</div>
          <div style="font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--text-muted)">AI Workspace</div>
        </div>
      </div>
      <button
        class="btn-icon"
        style="color:var(--text-tertiary)"
        @click="collapsed = true"
      >
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </div>

    <!-- New Chat -->
    <div class="px-3 pb-3">
      <button
        class="btn-primary w-full"
        @click="sessionStore.createSession()"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        {{ t('新建聊天', 'New Chat') }}
      </button>
    </div>

    <!-- Session list -->
    <div class="flex-1 overflow-y-auto px-3 py-1">
      <!-- Empty state -->
      <div v-if="sessionStore.sessions.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
        <svg class="w-10 h-10 mb-3" style="color:var(--text-tertiary)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p class="text-xs text-center" style="color:var(--text-tertiary)">
          {{ t('暂无聊天记录', 'No conversations yet') }}
        </p>
      </div>

      <!-- Grouped sessions -->
      <template v-for="group in groupedSessions" :key="group.key">
        <p class="sidebar-group-label">
          {{ group.label }}
        </p>
        <div
          v-for="s in group.items"
          :key="s.id"
          class="sidebar-session-btn group"
          :class="{ active: s.id === sessionStore.currentSession }"
          @click="handleSelect(s.id)"
        >
          <div class="flex-1 min-w-0">
            <div class="sidebar-session-title" :title="normalizeTitle(s)">{{ normalizeTitle(s) }}</div>
            <div class="sidebar-session-meta">
              <span>{{ s.time }}</span>
              <span style="margin:0 5px;opacity:0.35">·</span>
              <span>{{ s.count }} {{ t('条', 'msgs') }}</span>
            </div>
          </div>
          <button
            class="sidebar-session-delete"
            @click="handleDelete(s.id, $event)"
            :title="t('删除', 'Delete')"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </template>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="sidebar-footer-label">{{ t('资源', 'Resources') }}</div>
      <div class="flex items-center gap-1.5 flex-wrap">
        <a href="https://zengzhichao.com/fantools" target="_blank" rel="noreferrer">FanTools</a>
        <span style="opacity:0.3">·</span>
        <a href="https://zengzhichao.com/damentang" target="_blank" rel="noreferrer">Damentang</a>
      </div>
    </div>
  </aside>

  <!-- Expand button -->
  <button
    v-if="collapsed"
    class="absolute top-3 left-3 z-10 w-8 h-8 flex items-center justify-center rounded-lg shadow-sm border transition-colors"
    style="background:var(--bg-secondary); border-color:var(--border-primary); color:var(--text-secondary)"
    @click="collapsed = false"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  </button>
</template>
