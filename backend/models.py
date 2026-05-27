from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str = ""
    image_ids: list[str] = Field(default_factory=list)
    regenerate: bool = False


class SessionMeta(BaseModel):
    id: str
    title: str
    count: int
    time: str


class SessionData(BaseModel):
    current_session: str
    nick_name: str = ""
    character: str = ""
    session_title: str = ""
    messages: list[dict] = Field(default_factory=list)


class SessionUpdate(BaseModel):
    nick_name: str | None = None
    character: str | None = None
    session_title: str | None = None


class UploadResponse(BaseModel):
    file_id: str
    filename: str


class ConfigResponse(BaseModel):
    model_name: str
    image_width: int
    default_nick_name: str
    default_character: str
    user_avatar: str
    assistant_avatar: str


class I18nResponse(BaseModel):
    lang: str
    texts: dict[str, str]


class DeleteResponse(BaseModel):
    deleted: bool = True
