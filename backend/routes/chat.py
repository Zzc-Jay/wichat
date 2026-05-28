import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from models import ChatRequest
from chat_service import resolve_images, stream_chat_sync, generate_image_sync
from session_store import SessionStore
from config import UPLOAD_DIR, model_caps

router = APIRouter(prefix="/chat", tags=["chat"])


def _now_display() -> str:
    return datetime.now().strftime("%m-%d %H:%M")


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _auto_title(messages: list) -> str:
    for msg in messages:
        if msg["role"] != "user":
            continue
        content = msg["content"]
        if isinstance(content, str) and content.strip():
            return content.strip()[:30]
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "text" and item["text"].strip():
                    return item["text"].strip()[:30]
    return ""


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request):
    caps = model_caps(body.model)

    # ——— embedding 模型不支持聊天 ———
    if caps["type"] == "embedding":
        return StreamingResponse(
            iter([_sse_event("error", {
                "error": "Embedding 模型（text-embedding-v4）用于文本向量化，不支持对话。请切换到 chat 或 vision 模型。"
            })]),
            media_type="text/event-stream",
        )

    # 校验：非视觉模型不能传图片
    if body.image_ids and not caps["vision"]:
        return StreamingResponse(
            iter([_sse_event("error", {
                "error": f"模型 {body.model} 不支持图片识别，请切换为 vision 类模型或移除图片"
            })]),
            media_type="text/event-stream",
        )

    session_store: SessionStore = request.app.state.session_store
    data = session_store.load(body.session_id) or {
        "current_session": body.session_id,
        "nick_name": "",
        "character": "",
        "session_title": "",
        "messages": [],
    }
    messages = list(data.get("messages", []))

    if body.regenerate and messages and messages[-1]["role"] == "assistant":
        messages.pop()

    # ——— 文生图分支 ——————————————————————————————————————————————
    if caps["image_output"] and not body.regenerate:
        prompt = body.message.strip()
        user_msg = {"role": "user", "content": prompt, "timestamp": _now_display()}
        messages.append(user_msg)

        async def generate_image():
            try:
                yield _sse_event("generating", {"message": "正在生成图片..."})

                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, generate_image_sync, prompt, body.model
                )

                if "error" in result:
                    messages.pop()
                    yield _sse_event("error", {"error": result["error"]})
                    return

                image_url = result["image_url"]
                ts = _now_display()

                assistant_msg = {
                    "role": "assistant",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": f"已为你生成图片：{prompt}"},
                    ],
                    "timestamp": ts,
                }
                messages.append(assistant_msg)

                if not data.get("session_title"):
                    data["session_title"] = prompt[:30]

                data["messages"] = messages
                session_store.save(body.session_id, data)

                yield _sse_event("image", {"image_url": image_url})
                yield _sse_event("done", {"message": assistant_msg})
            except Exception as e:
                yield _sse_event("error", {"error": str(e)})

        return StreamingResponse(generate_image(), media_type="text/event-stream")

    # ——— 文本 / 视觉对话分支 ——————————————————————————————————————
    if not body.regenerate:
        content = resolve_images(body.message, body.image_ids, UPLOAD_DIR)
        user_msg = {"role": "user", "content": content, "timestamp": _now_display()}
        messages.append(user_msg)

    nick_name = data.get("nick_name", "")
    character = data.get("character", "")

    async def generate_text():
        try:
            loop = asyncio.get_event_loop()
            q: asyncio.Queue = asyncio.Queue()

            def _run():
                try:
                    for msg in stream_chat_sync(messages, body.model, nick_name, character,
                                               thinking_enabled=body.thinking):
                        loop.call_soon_threadsafe(q.put_nowait, msg)
                except Exception as e:
                    loop.call_soon_threadsafe(q.put_nowait, e)
                loop.call_soon_threadsafe(q.put_nowait, None)

            loop.run_in_executor(None, _run)

            resp_text = ""
            thinking_text = ""
            while True:
                item = await q.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    yield _sse_event("error", {"error": str(item)})
                    return
                if isinstance(item, tuple):
                    msg_type, text = item
                    if msg_type == "thinking":
                        thinking_text += text
                        yield _sse_event("thinking", {"delta": text})
                        continue
                    elif msg_type == "content":
                        resp_text += text
                        yield _sse_event("chunk", {"delta": text})
                        continue

            ts = _now_display()
            assistant_msg = {
                "role": "assistant",
                "content": resp_text,
                "reasoning": thinking_text or None,
                "timestamp": ts,
            }
            messages.append(assistant_msg)

            if not data.get("session_title"):
                data["session_title"] = _auto_title(messages)

            data["messages"] = messages
            session_store.save(body.session_id, data)

            yield _sse_event("done", {"message": assistant_msg})
        except Exception as e:
            yield _sse_event("error", {"error": str(e)})

    return StreamingResponse(generate_text(), media_type="text/event-stream")
