"""DB 엔진과 세션. DATABASE_URL 이 있으면 Postgres(Neon), 없으면 로컬 SQLite"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

SQLITE_URL = "sqlite:///./meetingnote.db"


class Base(DeclarativeBase):
    pass


def resolve_url(database_url: str, on_vercel: bool) -> str:
    """연결 문자열을 고른다. Vercel 에서 DATABASE_URL 이 없으면 SQLite 로 떨어지지 않고 멈춘다"""
    if not database_url:
        if on_vercel:
            raise RuntimeError("배포 환경에는 DATABASE_URL 이 있어야 합니다. Vercel 함수는 SQLite 파일을 쓸 수 없습니다")
        return SQLITE_URL
    for prefix in ("postgres://", "postgresql://"):
        if database_url.startswith(prefix):
            return "postgresql+psycopg://" + database_url[len(prefix):]
    return database_url


def make_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


engine = make_engine(resolve_url(settings.database_url, settings.on_vercel))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


_tables_ready = False


def init_db(bind=None) -> None:
    from app import models  # noqa: F401 - 테이블을 Base 에 등록
    Base.metadata.create_all(bind=bind or engine)


def get_db():
    # 첫 요청 때 테이블을 만든다. 서버리스(Vercel)에서도 시작 순서에 기대지 않는다
    global _tables_ready
    if not _tables_ready:
        init_db()
        _tables_ready = True
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
