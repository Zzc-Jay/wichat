import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from config import UPLOAD_DIR
from models import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg"}


@router.post("", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only jpg/png files allowed")

    UPLOAD_DIR.mkdir(exist_ok=True)

    ext = Path(file.filename).suffix or ".jpg"
    file_id = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / file_id

    content = await file.read()
    file_path.write_bytes(content)

    return UploadResponse(file_id=file_id, filename=file.filename)


@router.get("/files/{file_id}")
async def get_file(file_id: str):
    file_path = UPLOAD_DIR / file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    ext = file_path.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)
