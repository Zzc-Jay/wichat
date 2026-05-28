from pathlib import Path

# ========================================
#  模型列表
# ========================================
# type: embedding | text | vision | image_gen
# provider → PROVIDER_CONFIG 决定 API 端点和密钥
#
# vision      = type == "vision"      （前端据此显示图片上传）
# image_output = type == "image_gen"  （前端据此切换文生图流程）
AVAILABLE_MODELS = [
    {"id": "text-embedding-v4",         "name": "Text Embedding V4",      "type": "embedding",  "provider": "dashscope"},
    {"id": "deepseek-v4-flash",         "name": "DeepSeek V4 Flash",      "type": "text",       "provider": "deepseek"},
    {"id": "qwen3.6-plus",              "name": "Qwen 3.6 Plus",         "type": "vision",     "provider": "dashscope"},
    {"id": "doubao-seed-2-0-lite-260215","name": "豆包 Seed 2.0 Lite",    "type": "vision",     "provider": "volcengine"},
    {"id": "mimo-v2.5",                 "name": "小米 MiMo V2.5",         "type": "vision",     "provider": "mimo"},
    {"id": "wan2.7-image-pro",          "name": "通义万相 2.7 Pro",      "type": "image_gen",  "provider": "dashscope"},
    {"id": "doubao-seedream-5-0-260128", "name": "豆包 Seedream 5.0",     "type": "image_gen",  "provider": "volcengine"},
]
DEFAULT_MODEL = "qwen3.6-plus"
MODEL_NAME = DEFAULT_MODEL  # 向后兼容

# 供应商 → API 端点 + 环境变量名
# 对话 base_url 均为 OpenAI 兼容模式（/v1/chat/completions）
# 文生图 image_gen_url 为各自原生 API
PROVIDER_CONFIG = {
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        # 文生图原生 API（非 OpenAI 兼容）
        "image_gen_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "ARK_API_KEY",
        # 文生图 OpenAI 兼容格式（/v3/images/generations）
        "image_gen_url": "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    },
    "mimo": {
        "base_url": "https://api.xiaomimimo.com/v1",
        "api_key_env": "MIMO_API_KEY",
    },
}

# 向后兼容（供未迁移的旧代码使用）
API_KEY_ENV = PROVIDER_CONFIG["dashscope"]["api_key_env"]
BASE_URL = PROVIDER_CONFIG["dashscope"]["base_url"]

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
    return {"vision": False, "image_output": False, "type": "text", "provider": "dashscope"}


def provider_for(model_id: str) -> dict:
    """返回模型对应的供应商配置。"""
    caps = model_caps(model_id)
    return PROVIDER_CONFIG.get(caps["provider"], PROVIDER_CONFIG["dashscope"])

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
