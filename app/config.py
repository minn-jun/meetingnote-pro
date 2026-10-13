"""환경변수 읽기. 비밀 값은 .env 또는 배포 환경변수로만 받는다"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _bool(v: str | None, default: bool) -> bool:
    if v is None or v == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-secret-change-me"))
    stt_api_key: str = field(default_factory=lambda: os.getenv("STT_API_KEY", ""))
    stt_model: str = field(default_factory=lambda: os.getenv("STT_MODEL", "gemini-3.8-flash"))
    summary_model: str = field(default_factory=lambda: os.getenv("SUMMARY_MODEL", "gemini-3.8-flash"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    max_upload_mb: float = field(default_factory=lambda: float(os.getenv("MAX_UPLOAD_MB", "25")))
    cors_origins: list[str] = field(default_factory=lambda: [
        o.strip() for o in os.getenv(
            "CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",") if o.strip()
    ])
    docs_enabled: bool = field(default_factory=lambda: _bool(os.getenv("DOCS_ENABLED"), True))
    on_vercel: bool = field(default_factory=lambda: bool(os.getenv("VERCEL")))


settings = Settings()
