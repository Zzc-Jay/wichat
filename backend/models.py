from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str = ""
    model: str = ""
    image_ids: list[str] = Field(default_factory=list)
    regenerate: bool = False
    thinking: bool = True


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


class ModelInfo(BaseModel):
    id: str
    name: str
    type: str          # "embedding" | "text" | "vision" | "image_gen"
    provider: str      # "dashscope" | "deepseek" | "volcengine"
    vision: bool       # 前端据此显隐图片上传按钮
    image_output: bool # 前端据此切换文生图流程
    thinking: bool = True  # 前端据此显隐深度思考开关


class ConfigResponse(BaseModel):
    models: list[ModelInfo]
    default_model: str
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
