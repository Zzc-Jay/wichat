import os
import base64
import uuid
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import (
    MODEL_NAME, API_KEY_ENV, BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES,
    SYSTEM_PROMPT_TEMPLATE, DEFAULT_NICK_NAME, DEFAULT_CHARACTER,
)
from i18n import t

_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise EnvironmentError(t("config_error", API_KEY_ENV))
        _llm = ChatOpenAI(
            model=MODEL_NAME,
            api_key=api_key,
            base_url=BASE_URL,
            streaming=True,
            timeout=REQUEST_TIMEOUT,
            max_retries=MAX_RETRIES,
        )
    return _llm


def validate_config() -> str | None:
    if not os.environ.get(API_KEY_ENV):
        return t("config_error", API_KEY_ENV)
    return None


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


def stream_chat_sync(messages: list):
    """同步生成器，yield 文本 delta。"""
    llm = get_llm()
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
