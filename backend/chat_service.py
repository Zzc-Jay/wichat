import os
import json
import base64
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import (
    MODEL_NAME, REQUEST_TIMEOUT, MAX_RETRIES,
    SYSTEM_PROMPT_TEMPLATE, DEFAULT_NICK_NAME, DEFAULT_CHARACTER,
    provider_for,
)
from i18n import t

# 缓存：key=model_id → ChatOpenAI 实例
_llm_cache: dict[str, ChatOpenAI] = {}


def get_llm(model_name: str = "") -> ChatOpenAI:
    """获取指定模型的 ChatOpenAI 实例，自动使用对应供应商的 API 端点和密钥。"""
    model = model_name or MODEL_NAME
    if model not in _llm_cache:
        p = provider_for(model)
        api_key = os.environ.get(p["api_key_env"])
        if not api_key:
            raise EnvironmentError(
                t("config_error", p["api_key_env"])
            )
        _llm_cache[model] = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=p["base_url"],
            streaming=True,
            timeout=REQUEST_TIMEOUT,
            max_retries=MAX_RETRIES,
        )
    return _llm_cache[model]


def build_lc_messages(messages: list[dict], nick_name: str = "", character: str = "") -> list:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        nick_name=nick_name or DEFAULT_NICK_NAME,
        character=character or DEFAULT_CHARACTER,
    )
    msgs = [SystemMessage(content=system_prompt)]
    for msg in messages:
        content = msg["content"]
        if msg["role"] == "user":
            msgs.append(HumanMessage(content=content))
        else:
            if isinstance(content, list):
                text = " ".join(
                    item["text"] for item in content if item.get("type") == "text"
                )
                msgs.append(AIMessage(content=text))
            else:
                msgs.append(AIMessage(content=content))
    return msgs


def resolve_images(content: str, image_ids: list[str], upload_dir: Path) -> list | str:
    """将 image_ids 解析为 base64 data URI，构建多模态消息内容。"""
    if not image_ids:
        return content

    parts = []
    for fid in image_ids:
        file_path = upload_dir / fid
        if file_path.exists():
            b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })
    parts.append({"type": "text", "text": content})
    return parts


def stream_chat_sync(messages: list, model_name: str = ""):
    """同步生成器，yield 文本 delta。"""
    llm = get_llm(model_name)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content


# ========================================
#  文生图：按供应商分发
# ========================================

def _image_gen_dashscope(prompt: str, model: str) -> dict:
    """阿里 DashScope 文生图 — 原生 REST API。

    POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
    文档：https://help.aliyun.com/zh/model-studio/wanxiang-image-generation
    """
    import urllib.request
    import urllib.error

    p = provider_for(model)
    api_key = os.environ.get(p["api_key_env"])
    if not api_key:
        return {"error": f"环境变量 {p['api_key_env']} 未设置"}
    endpoint = p["image_gen_url"]

    body = json.dumps({
        "model": model,
        "input": {
            "messages": [{"role": "user", "content": [{"text": prompt}]}]
        },
        "parameters": {"size": "2K", "n": 1, "watermark": False},
    }).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # 返回格式：{"output": {"choices": [{"message": {"content": [{"image": {"url": "..."}}]}}]}}
        choices = data.get("output", {}).get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", [])
            for item in content:
                if item.get("image") and item["image"].get("url"):
                    return {"image_url": item["image"]["url"]}
        return {"error": data.get("message", "DashScope image generation failed")}
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode("utf-8"))
            return {"error": msg.get("message", f"HTTP {e.code}")}
        except Exception:
            return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _image_gen_volcengine(prompt: str, model: str) -> dict:
    """字节火山引擎文生图 — OpenAI 兼容 images API。

    POST https://ark.cn-beijing.volces.com/api/v3/images/generations
    文档：https://www.volcengine.com/docs/6791/1397048
    """
    import urllib.request
    import urllib.error

    p = provider_for(model)
    api_key = os.environ.get(p["api_key_env"])
    if not api_key:
        return {"error": f"环境变量 {p['api_key_env']} 未设置"}
    endpoint = p["image_gen_url"]

    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "size": "2K",
        "output_format": "png",
        "watermark": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # OpenAI 兼容格式：{"data": [{"url": "..."}]}
        if data.get("data") and data["data"][0].get("url"):
            return {"image_url": data["data"][0]["url"]}
        return {"error": data.get("message", "Volcengine image generation failed")}
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode("utf-8"))
            return {"error": msg.get("message", f"HTTP {e.code}")}
        except Exception:
            return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


# 供应商 → 文生图函数
_IMAGE_GEN_DISPATCH = {
    "dashscope": _image_gen_dashscope,
    "volcengine": _image_gen_volcengine,
}


def generate_image_sync(prompt: str, model_name: str) -> dict:
    """文生图统一入口：根据模型的 provider 分发到对应的 API。"""
    from config import model_caps

    caps = model_caps(model_name)
    provider = caps.get("provider", "dashscope")
    handler = _IMAGE_GEN_DISPATCH.get(provider)
    if handler is None:
        return {"error": f"供应商 {provider} 不支持文生图"}
    return handler(prompt, model_name)
