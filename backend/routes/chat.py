import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from models import ChatRequest
from chat_service import build_lc_messages, resolve_images, stream_chat_sync
from session_store import SessionStore
from config import UPLOAD_DIR

router = APIRouter(prefix="/chat", tags=["chat"])


def _now_display() -> str:
    return datetime.now().strftime("%m-%d %H:%M")


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request):
    session_store: SessionStore = request.app.state.session_store
    data = session_store.load(body.session_id)
    if data is None:
        data = {
            "current_session": body.session_id,
            "nick_name": "",
            "character": "",
            "session_title": "",
            "messages": [],
        }

    messages = list(data.get("messages", []))

    if body.regenerate and messages and messages[-1]["role"] == "assistant":
        messages.pop()
    elif not body.regenerate:
        content = resolve_images(body.message, body.image_ids, UPLOAD_DIR)
        user_msg = {
            "role": "user",
            "content": content,
            "timestamp": _now_display(),
        }
        messages.append(user_msg)

    lc_msgs = build_lc_messages(messages)

    async def generate():
        try:
            loop = asyncio.get_event_loop()
            q: asyncio.Queue = asyncio.Queue()

            def _run():
                try:
                    for delta in stream_chat_sync(lc_msgs):
                        loop.call_soon_threadsafe(q.put_nowait, delta)
                except Exception as e:
                    loop.call_soon_threadsafe(q.put_nowait, e)
                loop.call_soon_threadsafe(q.put_nowait, None)

            loop.run_in_executor(None, _run)

            resp_text = ""
            while True:
                delta = await q.get()
                if delta is None:
                    break
                if isinstance(delta, Exception):
                    yield _sse_event("error", {"error": str(delta)})
                    return
                resp_text += delta
                yield _sse_event("chunk", {"delta": delta})

            ts = _now_display()
            assistant_msg = {
                "role": "assistant",
                "content": resp_text,
                "timestamp": ts,
            }
            messages.append(assistant_msg)

            # Auto-set title from first user message if empty
            if not data.get("session_title"):
                for msg in messages:
                    if msg["role"] == "user":
                        content = msg["content"]
                        if isinstance(content, str) and content.strip():
                            data["session_title"] = content.strip()[:30]
                        elif isinstance(content, list):
                            for item in content:
                                if item.get("type") == "text" and item["text"].strip():
                                    data["session_title"] = item["text"].strip()[:30]
                                    break
                        break

            data["messages"] = messages
            session_store.save(body.session_id, data)

            yield _sse_event("done", {"message": assistant_msg})
        except Exception as e:
            yield _sse_event("error", {"error": str(e)})

    return StreamingResponse(generate(), media_type="text/event-stream")
