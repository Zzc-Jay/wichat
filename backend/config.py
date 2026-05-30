import os
from pathlib import Path

# ========================================
#  模型列表（通过 New API 统一网关）
# ========================================
# type: embedding | text | vision | image_gen
#
# vision      = type == "vision"      （前端据此显示图片上传）
# image_output = type == "image_gen"  （前端据此切换文生图流程）
AVAILABLE_MODELS = [
    {"id": "deepseek-v4-flash",         "name": "DeepSeek V4 Flash",      "type": "text",       "provider": "newapi"},
    {"id": "qwen3.6-plus",              "name": "Qwen 3.6 Plus",         "type": "vision",     "provider": "newapi"},
    {"id": "doubao-seed-2-0-lite-260215","name": "豆包 Seed 2.0 Lite",    "type": "vision",     "provider": "newapi"},
    {"id": "mimo-v2.5",                 "name": "小米 MiMo V2.5",         "type": "vision",     "provider": "newapi"},
    {"id": "wan2.7-image-pro",          "name": "通义万相 2.7 Pro",      "type": "image_gen",  "provider": "newapi"},
    {"id": "doubao-seedream-5-0-260128", "name": "豆包 Seedream 5.0",     "type": "image_gen",  "provider": "newapi"},
]
DEFAULT_MODEL = "qwen3.6-plus"
MODEL_NAME = DEFAULT_MODEL  # 向后兼容

# New API 统一网关配置
NEW_API_BASE_URL = os.environ.get("NEW_API_BASE_URL", "http://localhost:3000/v1")
NEW_API_KEY = os.environ.get("NEW_API_KEY", "")

# 向后兼容：所有模型共用 New API 配置
PROVIDER_CONFIG = {
    "newapi": {
        "base_url": NEW_API_BASE_URL,
        "api_key": NEW_API_KEY,
    },
}

# 模型级参数（extra_body 传递给 API）
MODEL_PARAMS: dict[str, dict] = {}

# 每个模型关闭深度思考的请求参数（通过 New API 透传）
# key = model id, value = (param_name, param_value)
THINKING_PARAMS: dict[str, tuple[str, object]] = {
    "qwen3.6-plus": ("enable_thinking", False),
    "deepseek-v4-flash": ("thinking", {"type": "disabled"}),
    "doubao-seed-2-0-lite-260215": ("reasoning_effort", "minimal"),
}

# 向后兼容
API_KEY_ENV = "NEW_API_KEY"
BASE_URL = NEW_API_BASE_URL

REQUEST_TIMEOUT = 60
MAX_RETRIES = 2

# ========================================
#  辅助：从 type 推导 vision / image_output
# ========================================
def model_caps(model_id: str) -> dict:
    """返回 {vision, image_output, type, provider}。"""
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            return {
                "vision": m["type"] == "vision",
                "image_output": m["type"] == "image_gen",
                "type": m["type"],
                "provider": m["provider"],
            }
    return {"vision": False, "image_output": False, "type": "text", "provider": "newapi"}


def provider_for(model_id: str) -> dict:
    """返回模型对应的 New API 网关配置。"""
    return PROVIDER_CONFIG["newapi"]

# ========================================
#  系统 Prompt & 默认角色
# ========================================
SYSTEM_PROMPT_TEMPLATE = (
    "你的名字是：{nick_name}，你需要以一个朋友的视角和我对话，"
    "尽量简洁，涉及代码相关的问题可以详细说明，你的性格是：{character}"
)

DEFAULT_NICK_NAME = "太阳之子"
DEFAULT_CHARACTER = "理性的编程大佬，带有一些幽默感"

USER_AVATAR = "🥷🏻"
ASSISTANT_AVATAR = "🤪"

IMAGE_WIDTH = 300

# ========================================
#  FastAPI 路径
# ========================================
BASE_DIR = Path(__file__).resolve().parent
MESSAGE_DIR = BASE_DIR / "message_list"
UPLOAD_DIR = BASE_DIR / "uploads"
CORS_ORIGINS = ["http://localhost:5173"]
