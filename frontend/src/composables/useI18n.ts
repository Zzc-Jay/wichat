import { reactive } from 'vue'
import { useChatStore } from '../stores/chat'

const texts = reactive<Record<string, string>>({})
let loaded = false

export function useI18n() {
  const chatStore = useChatStore()

  async function load(l: 'zh' | 'en' = 'zh') {
    const res = await fetch(`/api/config/i18n?lang=${l}`)
    if (res.ok) {
      const data = await res.json()
      Object.keys(texts).forEach(k => delete texts[k])
      Object.assign(texts, data.texts)
      chatStore.setLang(l)
      loaded = true
    }
  }

  function t(key: string, ...args: string[]): string {
    let text = texts[key] || key
    args.forEach(arg => {
      text = text.replace('{}', arg)
    })
    return text
  }

  function setLang(l: 'zh' | 'en') {
    load(l)
  }

  function detectLang(): 'zh' | 'en' {
    const saved = localStorage.getItem('lang') as 'zh' | 'en' | null
    if (saved) return saved
    return navigator.language.startsWith('zh') ? 'zh' : 'en'
  }

  return { load, t, setLang, detectLang, loaded }
}
