"""bcrypt 해시와 JWT (24시간, 갱신 없음)"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

TOKEN_HOURS = 24
ALGORITHM = "HS256"


# 비용 10 (2^10 회). 기본값 12 는 개발 PC 에서 한 번에 250ms 쯤 걸려 가입 · 로그인 250ms 기준을 넘는다
BCRYPT_ROUNDS = 10


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:
        return False


def create_token(user_id: int, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=TOKEN_HOURS)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> int | None:
    """맞으면 user id, 없거나 위조 · 만료면 None"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
