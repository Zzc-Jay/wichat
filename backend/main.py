from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 优先从 .env 文件加载（systemd 的 EnvironmentFile 优先级更高，不会被覆盖）
from dotenv import load_dotenv
load_dotenv()

from config import MESSAGE_DIR, UPLOAD_DIR, CORS_ORIGINS
from session_store import SessionStore
from routes import sessions, chat, config, upload

app = FastAPI(title="WiChat API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    MESSAGE_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    app.state.session_store = SessionStore(MESSAGE_DIR)


app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
