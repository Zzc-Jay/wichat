import os
from pathlib import Path

# ========================================
#  LLM 配置（复用自 wichat/config.py）
# ========================================
IMAGE_WIDTH = 300
MODEL_NAME = "qwen-vl-plus"
API_KEY_ENV = "DASHSCOPE_API_KEY"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
REQUEST_TIMEOUT = 60
MAX_RETRIES = 2

SYSTEM_PROMPT_TEMPLATE = (
    "你的名字是：{nick_name}，你需要以一个朋友的视角和我对话，"
    "尽量简洁，涉及代码相关的问题可以详细说明，你的性格是：{character}"
)

DEFAULT_NICK_NAME = "太阳之子"
DEFAULT_CHARACTER = "理性的编程大佬，带有一些幽默感"

USER_AVATAR = "🥷🏻"
ASSISTANT_AVATAR = "🤪"

# ========================================
#  FastAPI 路径设置
# ========================================
BASE_DIR = Path(__file__).resolve().parent
MESSAGE_DIR = BASE_DIR / "message_list"
UPLOAD_DIR = BASE_DIR / "uploads"
CORS_ORIGINS = ["http://localhost:5173"]
