export interface TextContent {
  type: 'text'
  text: string
}

export interface ImageContent {
  type: 'image_url'
  image_url: { url: string }
}

export type MessageContent = string | (TextContent | ImageContent)[]

export interface Message {
  role: 'user' | 'assistant'
  content: MessageContent
  timestamp: string
}

export interface SessionMeta {
  id: string
  title: string
  count: number
  time: string
}

export interface SessionData {
  current_session: string
  nick_name: string
  character: string
  session_title: string
  messages: Message[]
}

export interface AppConfig {
  model_name: string
  image_width: number
  default_nick_name: string
  default_character: string
  user_avatar: string
  assistant_avatar: string
}

export interface SSEChunk {
  delta: string
}

export interface SSEDone {
  message: Message
}

export interface SSEError {
  error: string
}

export interface ChatRequest {
  session_id: string
  message: string
  image_ids: string[]
  regenerate: boolean
}
