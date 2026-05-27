from fastapi import APIRouter, HTTPException, Request
from session_store import SessionStore
from models import SessionMeta, SessionData, SessionUpdate, DeleteResponse
from config import MESSAGE_DIR

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_store(request: Request) -> SessionStore:
    return request.app.state.session_store


@router.get("", response_model=list[SessionMeta])
def list_sessions(request: Request):
    return _get_store(request).list_all()


@router.get("/{session_id}", response_model=SessionData)
def get_session(session_id: str, request: Request):
    data = _get_store(request).load(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return data


@router.post("", response_model=SessionMeta)
def create_session(request: Request):
    store = _get_store(request)
    sid = store.get_timestamp()
    store.save(sid, {
        "current_session": sid,
        "nick_name": "",
        "character": "",
        "session_title": "",
        "messages": [],
    })
    return {
        "id": sid,
        "title": sid,
        "count": 0,
        "time": store.format_display_time(sid),
    }


@router.put("/{session_id}", response_model=SessionData)
def update_session(session_id: str, update: SessionUpdate, request: Request):
    store = _get_store(request)
    data = store.load(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if update.nick_name is not None:
        data["nick_name"] = update.nick_name
    if update.character is not None:
        data["character"] = update.character
    if update.session_title is not None:
        data["session_title"] = update.session_title
    store.save(session_id, data)
    return data


@router.delete("/{session_id}", response_model=DeleteResponse)
def delete_session(session_id: str, request: Request):
    store = _get_store(request)
    if not store.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return DeleteResponse()
