"""요청 · 응답 모델 - Swagger 스키마의 원본"""
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer


def iso(dt: datetime | None) -> str | None:
    """UTC ISO 8601, Z 로 끝난다. SQLite 처럼 시간대가 빠진 값은 UTC 로 본다"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


UtcDT = Annotated[datetime, PlainSerializer(iso, return_type=str)]


class ErrorOut(BaseModel):
    code: str = Field(examples=["VALIDATION_ERROR"])
    msg: str = Field(examples=["입력값을 확인해 주세요"])


class OkOut(BaseModel):
    ok: bool = True


# ── Auth ────────────────────────────────────────────
class SignupIn(BaseModel):
    email: str = Field(examples=["user@example.com"])
    password: str = Field(examples=["mypassword"])
    name: str = Field(examples=["김대리"])


class LoginIn(BaseModel):
    email: str = Field(examples=["user@example.com"])
    password: str = Field(examples=["mypassword"])


class TokenOut(BaseModel):
    token: str
    team_id: int | None
    team_name: str | None


class MeOut(BaseModel):
    id: int
    name: str
    email: str
    role: str | None


class MeUpdate(BaseModel):
    name: str | None = Field(default=None, examples=["김수석"])
    password: str | None = Field(default=None, examples=["newpass1234"])


# ── Team ────────────────────────────────────────────
class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["기획팀"])


class TeamJoin(BaseModel):
    code: str = Field(min_length=1, examples=["MN-7K2D"])


class TeamUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["기획팀"])


class TeamOut(BaseModel):
    id: int
    name: str
    invite_code: str
    role: str
    member_count: int


class MemberOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    todo_count: int


# ── Meeting ─────────────────────────────────────────
class UploadOut(BaseModel):
    body: str


class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["2차 스프린트 계획 회의"])
    met_at: datetime = Field(examples=["2026-09-24T05:00:00Z"])
    attendees: str = Field(default="", examples=["김대리, 박과장, 이주임"])
    body: str = Field(min_length=1, examples=["김대리: 목록 화면 검색 범위를 제목과 참석자로 하겠습니다."])


class MeetingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    met_at: datetime | None = None
    attendees: str | None = None
    body: str | None = Field(default=None, min_length=1)


class TodoOut(BaseModel):
    id: int
    what: str
    assignee_id: int | None
    assignee_name: str | None
    due_text: str
    status: str
    meeting_id: int
    meeting_title: str


class MeetingListItem(BaseModel):
    id: int
    title: str
    met_at: UtcDT
    attendees: str
    summary: str
    created_at: UtcDT
    todo_done_count: int
    todo_total_count: int
    decision_count: int


class MeetingDetail(MeetingListItem):
    body: str
    decisions: str
    author_id: int
    todos: list[TodoOut]


# ── Todo ────────────────────────────────────────────
class TodoUpdate(BaseModel):
    status: str | None = Field(default=None, examples=["DOING"])
    assignee_id: int | None = Field(default=None, examples=[2])
    due_text: str | None = Field(default=None, max_length=100, examples=["2026-10-10"])


# ── Comment ─────────────────────────────────────────
class CommentIn(BaseModel):
    content: str = Field(examples=["받아쓰기 실패 시 표시는 어떻게 할까요?"])


class CommentOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    content: str
    created_at: UtcDT
    can_delete: bool


# ── Activity ────────────────────────────────────────
class ActivityOut(BaseModel):
    id: int
    kind: str
    actor_name: str
    text: str
    created_at: UtcDT
