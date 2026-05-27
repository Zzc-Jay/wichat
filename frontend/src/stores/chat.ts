import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  const isStreaming = ref(false)
  const streamingText = ref('')
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
    if (!v) streamingText.value = ''
  }

  function appendStreamingText(delta: string) {
    streamingText.value += delta
  }

  function setError(msg: string | null) {
    error.value = msg
  }

  function setAbortController(ctrl: AbortController | null) {
    abortController.value = ctrl
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

  function setConfig(c: typeof config.value) {
    config.value = c
  }

  return {
    isStreaming, streamingText, error, pendingImage, pendingImageUrl, abortController,
    config, theme, lang,
    setPendingImage, clearPendingImage, setStreaming, appendStreamingText,
    setError, setAbortController, cancelStream,
    setConfig, toggleTheme, setLang, initTheme,
  }
})
