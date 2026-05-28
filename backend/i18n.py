_TEXTS = {
    "page_title":          "太阳之子",
    "app_title":           "太阳之子",
    "new_session":         "新建会话",
    "session_history":     "会话历史",
    "expand_more":         "查看更多（共 {} 条）",
    "session_settings":    "会话设置",
    "session_title_ph":    "对话标题，留空自动生成",
    "ai_nickname_ph":      "AI 昵称",
    "ai_character_ph":     "AI 性格描述",
    "friend_links":        "友情链接",
    "regen":               "重新生成",
    "regen_help":          "重新生成最后一条回答",
    "confirm_delete":      "确认删除",
    "delete_warning":      "确定要删除会话「{}」吗？此操作不可撤销。",
    "cancel":              "取消",
    "confirm_yes":         "确定删除",
    "chat_placeholder":    "请输入您想问的问题",
    "config_error":        "环境变量 {} 未设置，请先配置 API Key",
    "config_solution":     "**解决方法：**",
    "config_get_key":      "获取 Key：[阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/apiKey)",
}

_EN_TEXTS = {
    "page_title":          "Sun Child",
    "app_title":           "Sun Child",
    "new_session":         "New Chat",
    "session_history":     "History",
    "expand_more":         "Show all ({} total)",
    "session_settings":    "Settings",
    "session_title_ph":    "Chat title, auto if empty",
    "ai_nickname_ph":      "AI nickname",
    "ai_character_ph":     "AI personality",
    "friend_links":        "Links",
    "regen":               "Regenerate",
    "regen_help":          "Regenerate last response",
    "confirm_delete":      "Confirm Delete",
    "delete_warning":      "Delete '{}'? This cannot be undone.",
    "cancel":              "Cancel",
    "confirm_yes":         "Delete",
    "chat_placeholder":    "Ask me anything...",
    "config_error":        "Environment variable {} not set. Please configure API Key.",
    "config_solution":     "**Solution:**",
    "config_get_key":      "Get Key: [Alibaba DashScope Console](https://dashscope.console.aliyun.com/apiKey)",
}


def t(key: str, *args, lang: str = "zh") -> str:
    d = _EN_TEXTS if lang == "en" else _TEXTS
    text = d.get(key, key)
    if args:
        text = text.format(*args)
    return text


def get_texts(lang: str = "zh") -> dict[str, str]:
    return _EN_TEXTS if lang == "en" else _TEXTS
