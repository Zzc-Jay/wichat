import { ref } from 'vue'
import type { ChatRequest } from '../types'

interface SSEHandlers {
  onChunk: (delta: string) => void
  onDone: (message: any) => void
  onError: (error: string) => void
}

export function useSSE() {
  const isStreaming = ref(false)
  let controller: AbortController | null = null

  async function stream(body: ChatRequest, handlers: SSEHandlers) {
    controller = new AbortController()
    isStreaming.value = true

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!res.ok) {
        const err = await res.json()
        handlers.onError(err.detail || 'Request failed')
        return
      }

      const reader = res.body?.getReader()
      if (!reader) {
        handlers.onError('No response body')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let eventType = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7)
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (eventType === 'chunk') {
                handlers.onChunk(data.delta)
              } else if (eventType === 'done') {
                handlers.onDone(data.message)
              } else if (eventType === 'error') {
                handlers.onError(data.error)
              }
            } catch {
              // skip unparseable lines
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        handlers.onError(e.message || String(e))
      }
    } finally {
      isStreaming.value = false
      controller = null
    }
  }

  function abort() {
    controller?.abort()
  }

  return { stream, abort, isStreaming }
}
