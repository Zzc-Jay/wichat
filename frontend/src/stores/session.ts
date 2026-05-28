import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SessionMeta, SessionData, Message } from '../types'

export const useSessionStore = defineStore('session', () => {
  const currentSession = ref('')
  const sessions = ref<SessionMeta[]>([])
  const messages = ref<Message[]>([])
  const loading = ref(false)

  async function fetchSessions() {
    loading.value = true
    try {
      const res = await fetch('/api/sessions')
      sessions.value = await res.json()
    } finally {
      loading.value = false
    }
  }

  async function loadSession(id: string) {
    const res = await fetch(`/api/sessions/${id}`)
    if (!res.ok) throw new Error('Session not found')
    const data: SessionData = await res.json()
    currentSession.value = data.current_session
    messages.value = data.messages
  }

  async function createSession() {
    // If current session is already empty, do nothing
    if (messages.value.length === 0 && currentSession.value) return

    // If there's an existing empty session, switch to it instead of creating a new one
    const emptySession = sessions.value.find(s => s.count === 0)
    if (emptySession) {
      currentSession.value = emptySession.id
      messages.value = []
      return
    }

    const res = await fetch('/api/sessions', { method: 'POST' })
    const meta: SessionMeta = await res.json()
    currentSession.value = meta.id
    messages.value = []
    await fetchSessions()
  }

  async function deleteSession(id: string) {
    await fetch(`/api/sessions/${id}`, { method: 'DELETE' })
    if (id === currentSession.value) {
      currentSession.value = ''
      messages.value = []
    }
    await fetchSessions()
  }

  function addMessage(msg: Message) {
    messages.value.push(msg)
  }

  return {
    currentSession, sessions, messages, loading,
    fetchSessions, loadSession, createSession, deleteSession,
    addMessage,
  }
})
