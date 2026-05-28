import os
import json
import base64
from pathlib import Path
from config import (
    MODEL_NAME, REQUEST_TIMEOUT,
    SYSTEM_PROMPT_TEMPLATE, DEFAULT_NICK_NAME, DEFAULT_CHARACTER,
    provider_for, model_caps, THINKING_PARAMS,
)
from i18n import t


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


def stream_chat_sync(messages: list[dict], model_name: str = "",
                     nick_name: str = "", character: str = "",
                     thinking_enabled: bool = True):
    """直接调用 DashScope 兼容 API 的流式接口，提取 reasoning_content。

    thinking_enabled=False 时根据供应商不同传入对应参数关闭深度思考：
      - dashscope: enable_thinking=False
      - deepseek: thinking={"type": "disabled"}
      - volcengine: reasoning_effort="minimal"

    Yields (type, text) 元组：type="thinking"（深度思考）或 "content"（回答）。
    """
    import json
    import urllib.request
    import urllib.error
    import io

    model = model_name or MODEL_NAME
    p = provider_for(model)
    api_key = os.environ.get(p["api_key_env"])
    if not api_key:
        raise EnvironmentError(t("config_error", p["api_key_env"]))

    # 构建 API 消息列表（dict 格式，无需 LangChain）
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        nick_name=nick_name or DEFAULT_NICK_NAME,
        character=character or DEFAULT_CHARACTER,
    )
    api_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    request_payload: dict = {
        "model": model,
        "messages": api_messages,
        "stream": True,
    }
    if not thinking_enabled:
        caps = model_caps(model)
        provider_name = caps["provider"]
        params = THINKING_PARAMS.get(provider_name)
        if params:
            param_name, param_value = params
            request_payload[param_name] = param_value
    body = json.dumps(request_payload).encode("utf-8")

    req = urllib.request.Request(
        f"{p['base_url']}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API HTTP {e.code}: {err_body}")

    # 用 TextIOWrapper 逐行读取，自动处理 UTF-8 分片
    for raw_line in io.TextIOWrapper(resp, encoding="utf-8"):
        line = raw_line.strip()
        if not line or not line.startswith("data: "):
            continue
        data_str = line[6:]
        if data_str == "[DONE]":
            return
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            continue
        choices = data.get("choices", [])
        if not choices:
            continue
        delta = choices[0].get("delta", {})
        reasoning = delta.get("reasoning_content", "") or ""
        content = delta.get("content", "") or ""
        if reasoning:
            yield ("thinking", reasoning)
        if content:
            yield ("content", content)


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
