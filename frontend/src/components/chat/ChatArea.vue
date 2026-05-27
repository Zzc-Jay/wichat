<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import css from 'highlight.js/lib/languages/css'
import xml from 'highlight.js/lib/languages/xml'
import sql from 'highlight.js/lib/languages/sql'
import markdown from 'highlight.js/lib/languages/markdown'

import { useSessionStore } from '../../stores/session'
import { useChatStore } from '../../stores/chat'
import { useSSE } from '../../composables/useSSE'
import { useI18n } from '../../composables/useI18n'

hljs.registerLanguage('python', python)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('css', css)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('markdown', markdown)

marked.setOptions({ gfm:true, breaks:true })

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const { stream } = useSSE()
const { t } = useI18n()

const container = ref<HTMLElement | null>(null)
const liked = ref<Record<number, boolean>>({})
const disliked = ref<Record<number, boolean>>({})
const copyToast = ref(false)

const suggestions = () => chatStore.lang === 'zh'
  ? ['介绍一下你自己', '帮我写一段 Python 代码', '解释一下量子计算', '推荐几本好书']
  : ['Tell me about yourself', 'Write a Python function', 'Explain machine learning', 'Recommend some books']

const userAvatar = () => chatStore.config?.user_avatar || '👤'
const aiAvatar = () => chatStore.config?.assistant_avatar || '🤖'

function scrollToBottom() {
  nextTick(() => { if (container.value) container.value.scrollTop = container.value.scrollHeight })
}
watch(() => sessionStore.messages.length, scrollToBottom)
watch(() => chatStore.streamingText, scrollToBottom)

function renderMarkdown(text: string): string {
  try { return marked.parse(text) as string } catch { return text }
}

function getContentText(msg: any): string {
  if (typeof msg.content === 'string') return msg.content
  if (Array.isArray(msg.content)) return msg.content.filter((i:any) => i.type==='text').map((i:any) => i.text).join(' ')
  return ''
}
function getContentImages(msg: any): any[] {
  return Array.isArray(msg.content) ? msg.content.filter((i:any) => i.type==='image_url') : []
}

async function copyMessage(msgIndex: number) {
  const text = getContentText(sessionStore.messages[msgIndex])
  try {
    await navigator.clipboard.writeText(text)
    copyToast.value = true
    setTimeout(() => { copyToast.value = false }, 1800)
  } catch { /* noop */ }
}

function toggleLike(msgIndex: number) {
  disliked.value[msgIndex] = false
  liked.value[msgIndex] = !liked.value[msgIndex]
}
function toggleDislike(msgIndex: number) {
  liked.value[msgIndex] = false
  disliked.value[msgIndex] = !disliked.value[msgIndex]
}

async function retry(msgIndex: number) {
  if (chatStore.isStreaming) return
  // Find the user message before this AI message
  const msgs = sessionStore.messages
  if (msgIndex <= 0 || msgs[msgIndex - 1].role !== 'user') return
  const userMsg = msgs[msgIndex - 1]

  // Remove from this AI message onward
  msgs.splice(msgIndex)

  const text = getContentText(userMsg)
  chatStore.setStreaming(true)
  chatStore.setError(null)

  stream(
    { session_id: sessionStore.currentSession, message: text, image_ids: [], regenerate: true },
    {
      onChunk(d) { chatStore.appendStreamingText(d) },
      onDone(m) { sessionStore.addMessage(m); chatStore.setStreaming(false); chatStore.setError(null); sessionStore.fetchSessions() },
      onError(e) { chatStore.setError(e); chatStore.setStreaming(false) },
    }
  )
}

async function sendSuggestion(text: string) {
  if (chatStore.isStreaming) return
  chatStore.setStreaming(true)
  chatStore.setError(null)
  sessionStore.addMessage({ role: 'user', content: text, timestamp: now() })
  stream(
    { session_id: sessionStore.currentSession, message: text, image_ids: [], regenerate: false },
    {
      onChunk(d) { chatStore.appendStreamingText(d) },
      onDone(m) { sessionStore.addMessage(m); chatStore.setStreaming(false); chatStore.setError(null); sessionStore.fetchSessions() },
      onError(e) { chatStore.setError(e); chatStore.setStreaming(false) },
    }
  )
}

function now() {
  return new Date().toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).replace(/\//g,'-')
}
</script>

<template>
  <div ref="container" class="flex-1 overflow-y-auto chat-container">
    <!-- Day header -->
    <div v-if="sessionStore.messages.length > 0" class="text-center mb-5" style="color:var(--text-faint);font-size:var(--text-xs);font-weight:var(--weight-normal)">
      {{ t('今天', 'Today') }}
    </div>

    <!-- Empty state -->
    <div v-if="sessionStore.messages.length===0 && !chatStore.isStreaming" class="flex justify-center" style="margin-top:10vh">
      <div class="text-center" style="max-width:480px">
        <div class="text-5xl mb-5">{{ aiAvatar() }}</div>
        <p class="text-lg font-semibold mb-2" style="color:var(--text-primary)">
          {{ t('有什么可以帮你？', 'What can I help with?') }}
        </p>
        <p class="text-sm mb-6" style="color:var(--text-tertiary)">
          {{ t('我是你的 AI 助手，可以回答问题、编写代码、翻译文本等', 'Your AI assistant — ask questions, write code, translate text, and more') }}
        </p>
        <div class="suggested-wrap">
          <button
            v-for="(s, i) in suggestions()" :key="i"
            class="suggested-chip"
            @click="sendSuggestion(s)"
          >{{ s }}</button>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <template v-for="(msg, idx) in sessionStore.messages" :key="idx">
      <div class="msg-row" :class="msg.role">
        <!-- Avatar -->
        <div class="msg-avatar" :class="msg.role">
          {{ msg.role === 'assistant' ? aiAvatar() : userAvatar() }}
        </div>

        <!-- Bubble + actions -->
        <div :style="{ maxWidth: '650px' }">
          <div class="chat-bubble" :class="msg.role">
            <!-- Images -->
            <div v-for="(img,i) in getContentImages(msg)" :key="'img'+i" class="mb-2">
              <img :src="img.image_url.url" class="rounded-lg" style="max-width:300px;max-height:300px;object-fit:cover" />
            </div>
            <!-- Text -->
            <div v-if="getContentText(msg)" v-html="renderMarkdown(getContentText(msg))" />
            <!-- Time -->
            <div class="chat-time">{{ msg.timestamp }}</div>
          </div>

          <!-- AI action buttons -->
          <div v-if="msg.role==='assistant' && !chatStore.isStreaming" class="msg-actions">
            <button :title="t('复制','Copy')" @click="copyMessage(idx)">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            <button :title="t('重试','Retry')" @click="retry(idx)">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button :title="t('点赞','Like')" :class="{ liked: liked[idx] }" @click="toggleLike(idx)">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
            </button>
            <button :title="t('点踩','Dislike')" :class="{ disliked: disliked[idx] }" @click="toggleDislike(idx)">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Streaming message -->
    <div v-if="chatStore.isStreaming && chatStore.streamingText" class="msg-row assistant">
      <div class="msg-avatar assistant">{{ aiAvatar() }}</div>
      <div style="max-width:650px">
        <div class="chat-bubble assistant">
          <div v-html="renderMarkdown(chatStore.streamingText) + '<span class=streaming-cursor />'" />
        </div>
      </div>
    </div>

    <!-- Copy toast -->
    <div v-if="copyToast" class="copy-toast">{{ t('已复制', 'Copied!') }}</div>
  </div>
</template>
