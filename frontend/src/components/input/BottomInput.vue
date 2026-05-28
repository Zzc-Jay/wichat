<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useSessionStore } from '../../stores/session'
import { useSSE } from '../../composables/useSSE'

const chatStore = useChatStore()
const sessionStore = useSessionStore()
const { stream } = useSSE()

const text = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const t = (zh:string, en:string) => chatStore.lang === 'zh' ? zh : en
const recording = ref(false)

function autoResize() {
  nextTick(() => {
    const el = textareaRef.value
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  })
}
watch(text, autoResize)

function handleFileSelect(e: Event) {
  const tgt = e.target as HTMLInputElement
  if (tgt.files?.[0]) chatStore.setPendingImage(tgt.files[0])
}
function removeImage() { chatStore.clearPendingImage(); if (fileInput.value) fileInput.value.value = '' }

function now() {
  return new Date().toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).replace(/\//g,'-')
}

async function send() {
  const msg = text.value.trim()
  if (!msg || chatStore.isStreaming || !sessionStore.currentSession) return
  text.value = ''
  chatStore.setError(null)

  let imageIds: string[] = []
  if (chatStore.pendingImage) {
    const form = new FormData(); form.append('file', chatStore.pendingImage)
    try {
      const res = await fetch('/api/upload', { method:'POST', body:form })
      if (res.ok) { const d = await res.json(); imageIds = [d.file_id] }
    } catch { chatStore.setError(t('图片上传失败','Image upload failed')); return }
    chatStore.clearPendingImage()
    if (fileInput.value) fileInput.value.value = ''
  }

  chatStore.setStreaming(true)
  let uc: any = msg
  if (imageIds.length > 0) uc = [...imageIds.map(id=>({type:'image_url' as const, image_url:{url:`/api/upload/files/${id}`}})), {type:'text' as const, text:msg}]
  sessionStore.addMessage({ role:'user', content:uc, timestamp:now() })

  // 文生图模型：设置图片生成中状态
  if (isImageGen()) {
    chatStore.streamingImage = true
    chatStore.streamingImageUrl = null
  }

  stream(
    { session_id:sessionStore.currentSession, message:msg, model:chatStore.selectedModel, image_ids:imageIds, regenerate:false, thinking:chatStore.thinkingEnabled },
    {
      onChunk(d) { chatStore.appendStreamingText(d) },
      onThinking(d) { chatStore.appendThinkingText(d) },
      onGenerating() {
        // 文生图：后端开始生成，前端保持 loading 状态
      },
      onImage(imageUrl) {
        chatStore.streamingImageUrl = imageUrl
      },
      onDone(message) {
        sessionStore.addMessage(message)
        chatStore.setStreaming(false); chatStore.setError(null)
        chatStore.streamingImage = false; chatStore.streamingImageUrl = null
        sessionStore.fetchSessions()
      },
      onError(e) {
        chatStore.setError(e); chatStore.setStreaming(false)
        chatStore.streamingImage = false; chatStore.streamingImageUrl = null
      },
    }
  )
}

// 切换为不支持图片输入的模型时（纯文本或文生图），清除已选图片
watch(() => chatStore.currentModelVision, (supportsVision) => {
  if (!supportsVision && chatStore.pendingImage) {
    chatStore.clearPendingImage()
    if (fileInput.value) fileInput.value.value = ''
  }
})

// 文生图模型不适用"重新生成"逻辑（每次都是新生成）
const isImageGen = () => chatStore.currentModelImageOutput

// 模型下拉选项标签
function modelLabel(m: { name: string; type: string }) {
  const tags: Record<string, string> = { embedding: ' [向量]', vision: ' [多模态]', image_gen: ' [文生图]' }
  return m.name + (tags[m.type] || '')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); send() }
}

function toggleVoice() {
  recording.value = !recording.value
  if (recording.value) {
    setTimeout(() => { recording.value = false }, 2000)
  }
}
</script>

<template>
  <div class="chat-input-wrapper">
    <!-- Error -->
    <div v-if="chatStore.error" class="chat-input-error">
      <span>{{ chatStore.error }}</span>
      <button class="btn-icon" style="width:24px;height:24px" @click="chatStore.setError(null)">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Model selector + Image preview row -->
    <div style="max-width:860px;margin:0 auto 8px;display:flex;align-items:center;gap:8px">
      <select
        v-if="chatStore.models.length > 0"
        :value="chatStore.selectedModel"
        class="model-select"
        @change="chatStore.selectedModel = ($event.target as HTMLSelectElement).value"
      >
        <option v-for="m in chatStore.models" :key="m.id" :value="m.id">
          {{ modelLabel(m) }}
        </option>
      </select>
      <!-- 深度思考开关 -->
      <button
        v-if="chatStore.currentModelThinking"
        class="thinking-toggle"
        :class="{ active: chatStore.thinkingEnabled }"
        @click="chatStore.toggleThinking()"
        :title="t('开启后显示模型的深度思考/推理过程','Show the model\'s reasoning process')"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        {{ t('深度思考', 'Thinking') }}
      </button>
      <!-- Image preview chip (when image is selected) -->
      <div v-if="chatStore.pendingImageUrl" class="img-preview-chip" style="margin-left:auto">
        <img :src="chatStore.pendingImageUrl" class="h-6 w-6 object-cover rounded" />
        <span class="truncate max-w-[120px] text-xs">{{ chatStore.pendingImage?.name }}</span>
        <button class="btn-icon" style="width:22px;height:22px" @click="removeImage">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Input box — flexbox, no absolute positioning -->
    <div class="chat-input-box">
      <!-- Tool buttons: left -->
      <div class="chat-input-tools">
        <button v-if="chatStore.currentModelVision" class="btn-icon" :title="t('上传图片','Upload image')" @click="fileInput?.click()">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
        <button class="btn-icon" :class="{ recording }" :title="t('语音输入','Voice input')" @click="toggleVoice" :style="recording ? 'color:#dc2626;background:#fef2f2' : ''">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </button>
      </div>
      <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/jpg" hidden @change="handleFileSelect" />

      <!-- Textarea: center, flex-1 -->
      <textarea
        ref="textareaRef"
        v-model="text" rows="1"
        class="chat-input-textarea"
        :placeholder="isImageGen() ? t('描述你想生成的图片...','Describe the image you want to generate...') : t('给 WiChat 发送消息...','Message WiChat...')"
        :disabled="chatStore.isStreaming"
        @keydown="handleKeydown"
      />

      <!-- Send / Stop: right -->
      <button
        v-if="!chatStore.isStreaming"
        class="chat-input-send"
        :class="text.trim() ? 'active' : 'inactive'"
        :disabled="!text.trim()"
        @click="send"
      >
        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
      <button v-else class="chat-input-stop" @click="chatStore.cancelStream()">
        {{ t('停止','Stop') }}
      </button>
    </div>

    <div class="chat-input-hint">{{ t('Enter 发送，Shift+Enter 换行','Enter to send, Shift+Enter for new line') }}</div>
  </div>
</template>
