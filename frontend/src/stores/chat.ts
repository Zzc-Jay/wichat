import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ModelInfo } from '../types'

export const useChatStore = defineStore('chat', () => {
  const isStreaming = ref(false)
  const streamingText = ref('')
  const thinkingText = ref('')
  const thinkingEnabled = ref(true)
  const error = ref<string | null>(null)
  const pendingImage = ref<File | null>(null)
  const pendingImageUrl = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)
  const config = ref<{ user_avatar: string; assistant_avatar: string } | null>(null)
  const theme = ref<'light' | 'dark'>(
    (localStorage.getItem('theme') as 'light' | 'dark') || 'light'
  )
  const lang = ref<'zh' | 'en'>(
    localStorage.getItem('lang') as 'zh' | 'en' || 'zh'
  )

  // 模型选择
  const models = ref<ModelInfo[]>([])
  const selectedModel = ref('')
  const currentModelVision = computed(() =>
    models.value.find(m => m.id === selectedModel.value)?.vision ?? true
  )
  const currentModelImageOutput = computed(() =>
    models.value.find(m => m.id === selectedModel.value)?.image_output ?? false
  )
  const currentModelThinking = computed(() => {
    const m = models.value.find(m => m.id === selectedModel.value)
    return (m?.thinking && !m?.image_output) ?? false
  })
  // 文生图专用：streamingText 用于文字流，streamingImage 用于图片生成中状态
  const streamingImage = ref(false)
  const streamingImageUrl = ref<string | null>(null)

  function setPendingImage(file: File) {
    pendingImage.value = file
    pendingImageUrl.value = URL.createObjectURL(file)
  }

  function clearPendingImage() {
    pendingImage.value = null
    if (pendingImageUrl.value) {
      URL.revokeObjectURL(pendingImageUrl.value)
      pendingImageUrl.value = null
    }
  }

  function setStreaming(v: boolean) {
    isStreaming.value = v
    if (!v) {
      streamingText.value = ''
      thinkingText.value = ''
    }
  }

  function appendStreamingText(delta: string) {
    streamingText.value += delta
  }

  function appendThinkingText(delta: string) {
    if (!thinkingEnabled.value) return
    thinkingText.value += delta
  }

  function toggleThinking() {
    thinkingEnabled.value = !thinkingEnabled.value
    if (!thinkingEnabled.value) thinkingText.value = ''
  }

  function setError(msg: string | null) {
    error.value = msg
  }

  function cancelStream() {
    abortController.value?.abort()
    isStreaming.value = false
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  function setLang(l: 'zh' | 'en') {
    lang.value = l
    localStorage.setItem('lang', l)
  }

  function initTheme() {
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  function setConfig(c: { user_avatar: string; assistant_avatar: string; models?: ModelInfo[]; default_model?: string }) {
    config.value = { user_avatar: c.user_avatar, assistant_avatar: c.assistant_avatar }
    if (c.models) models.value = c.models
    if (c.default_model) selectedModel.value = c.default_model
  }

  return {
    isStreaming, streamingText, thinkingText, thinkingEnabled, error, pendingImage, pendingImageUrl, abortController,
    config, theme, lang, models, selectedModel, currentModelVision, currentModelImageOutput,
    currentModelThinking,
    streamingImage, streamingImageUrl,
    setPendingImage, clearPendingImage, setStreaming, appendStreamingText,
    appendThinkingText, toggleThinking,
    setError, cancelStream,
    setConfig, toggleTheme, setLang, initTheme,
  }
})
