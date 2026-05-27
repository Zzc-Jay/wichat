import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from config import MESSAGE_DIR


class SessionStore:
    def __init__(self, message_dir: Path = MESSAGE_DIR):
        self.message_dir = message_dir
        self._ensure_dir()

    # ---- helpers ----

    @staticmethod
    def get_timestamp() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def format_display_time(file_id: str) -> str:
        try:
            dt = datetime.strptime(file_id, "%Y%m%d_%H%M%S")
            return dt.strftime("%m-%d %H:%M")
        except ValueError:
            return file_id

    def _ensure_dir(self):
        self.message_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.message_dir / f"{session_id}.json"

    # ---- CRUD ----

    def save(self, session_id: str, data: dict):
        path = self._session_path(session_id)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp, path)

    def load(self, session_id: str) -> dict | None:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete(self, session_id: str) -> bool:
        path = self._session_path(session_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_all(self) -> list[dict]:
        if not self.message_dir.exists():
            return []
        sessions = []
        for fname in sorted(self.message_dir.glob("*.json"), reverse=True):
            file_id = fname.stem
            try:
                data = json.loads(fname.read_text(encoding="utf-8"))
                sessions.append({
                    "id": file_id,
                    "title": self._extract_title(data, file_id),
                    "count": len(data.get("messages", [])),
                    "time": self.format_display_time(file_id),
                })
            except (OSError, json.JSONDecodeError):
                sessions.append({"id": file_id, "title": file_id, "count": 0, "time": ""})
        return sessions

    @staticmethod
    def _extract_title(data: dict, file_id: str) -> str:
        custom = data.get("session_title", "")
        if custom:
            return custom[:30] + "…" if len(custom) > 30 else custom
        for msg in data.get("messages", []):
            if msg["role"] != "user":
                continue
            content = msg["content"]
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        t = item["text"].strip()
                        if t:
                            return t[:30] + "…" if len(t) > 30 else t
            elif isinstance(content, str):
                t = content.strip()
                if t:
                    return t[:30] + "…" if len(t) > 30 else t
        return file_id
