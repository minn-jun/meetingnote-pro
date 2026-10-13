from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app import activity
from app.ai import AIProvider, get_ai, upstream
from app.config import settings
from app.db import get_db
from app.deps import get_current_user, require_member
from app.errors import ApiError, forbidden
from app.models import Meeting, Membership, Todo, User
from app.schemas import MeetingCreate, MeetingDetail, MeetingListItem, MeetingUpdate, UploadOut, as_utc
from app.views import decision_lines, meeting_detail, meeting_item

router = APIRouter(tags=["Meeting"])

CHUNK = 1024 * 1024


def audio_kind(head: bytes) -> str | None:
    """확장자가 아니라 내용으로 판정. wav · mp3 만"""
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[:3] == b"ID3":
        return "mp3"
    if len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
        return "mp3"
    return None


@router.post("/api/upload", response_model=UploadOut, summary="녹취 업로드 · 받아쓰기 (저장하지 않음)")
def upload(file: UploadFile = File(..., description="mp3 또는 wav"),
           user: User = Depends(get_current_user), ai: AIProvider = Depends(get_ai)):
    limit = int(settings.max_upload_mb * 1024 * 1024)
    data = bytearray()
    while chunk := file.file.read(CHUNK):
        data.extend(chunk)
        if len(data) > limit:
            raise ApiError(413, "PAYLOAD_TOO_LARGE", f"{settings.max_upload_mb:g}MB 를 넘는 파일은 올릴 수 없습니다")
    kind = audio_kind(bytes(data[:16]))
    if not kind:
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "mp3 또는 wav 파일만 올릴 수 있습니다")
    body = upstream(ai.transcribe, bytes(data), file.filename or f"audio.{kind}")
    if not body.strip():
        # 말소리가 없는 녹취 - 빈 본문을 돌려주지 않고 알려 준다 (결정사항 D15)
        raise ApiError(400, "VALIDATION_ERROR", "녹취에서 말소리를 찾지 못했습니다. 파일을 확인해 주세요")
    return UploadOut(body=body)


def load_meeting(db: Session, id: int, user: User) -> tuple[Meeting, Membership]:
    m = db.scalar(select(Meeting).where(Meeting.id == id)
                  .options(selectinload(Meeting.todos).selectinload(Todo.assignee)))
    if not m:
        raise ApiError(404, "MEETING_NOT_FOUND", "회의록을 찾을 수 없습니다")
    _, membership = require_member(db, m.team_id, user)
    return m, membership


def can_edit(m: Meeting, membership: Membership, user: User) -> bool:
    return m.author_id == user.id or membership.role == "owner"


@router.post("/api/teams/{id}/meetings", status_code=201, response_model=MeetingDetail,
             summary="회의록 만들기 (3항목 구분 포함)")
def create_meeting(id: int, data: MeetingCreate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db), ai: AIProvider = Depends(get_ai)):
    require_member(db, id, user)
    title, body = data.title.strip(), data.body.strip()
    if not title or not body:
        raise ApiError(400, "VALIDATION_ERROR", "제목 · 회의 시각 · 본문은 꼭 입력해 주세요")
    members = {ms.user.name: ms.user.id for ms in
               db.scalars(select(Membership).where(Membership.team_id == id)).all()}
    met_at = as_utc(data.met_at)
    result = upstream(ai.split, body, met_at, list(members))

    m = Meeting(team_id=id, title=title, met_at=met_at, attendees=data.attendees.strip(), body=body,
                summary=str(result.get("summary", "")).strip(),
                decisions="\n".join(decision_lines("\n".join(result.get("decisions") or []))),
                author_id=user.id)
    for t in result.get("todos") or []:
        what = str(t.get("what", "")).strip()
        if not what:
            continue
        # 모델 출력을 믿지 않고 멤버 이름과 다시 대조한다
        assignee = members.get((t.get("assignee_name") or "").strip())
        due = str(t.get("due_text") or "").strip() or "미정"
        m.todos.append(Todo(what=what, assignee_id=assignee, due_text=due[:100], status="OPEN"))
    db.add(m)
    db.flush()
    activity.record(db, id, user.id, "meeting_add", title=title)
    db.commit()
    return meeting_detail(load_meeting(db, m.id, user)[0])


@router.get("/api/teams/{id}/meetings", response_model=list[MeetingListItem], summary="회의록 목록 · 검색 · 기간")
def list_meetings(id: int,
                  q: str | None = Query(None, description="제목 · 참석자 부분 일치 (본문은 대상 아님)"),
                  from_: date | None = Query(None, alias="from", description="시작 날짜 (포함)"),
                  to: date | None = Query(None, description="끝 날짜 (포함)"),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_member(db, id, user)
    stmt = (select(Meeting).where(Meeting.team_id == id)
            .options(selectinload(Meeting.todos))
            .order_by(Meeting.met_at.desc(), Meeting.id.desc()))
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Meeting.title.like(like), Meeting.attendees.like(like)))
    if from_:
        stmt = stmt.where(Meeting.met_at >= datetime.combine(from_, time.min, timezone.utc))
    if to:
        stmt = stmt.where(Meeting.met_at < datetime.combine(to + timedelta(days=1), time.min, timezone.utc))
    return [meeting_item(m) for m in db.scalars(stmt).all()]


@router.get("/api/meetings/{id}", response_model=MeetingDetail, summary="회의록 한 건 (body · todos 포함)")
def get_meeting(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return meeting_detail(load_meeting(db, id, user)[0])


@router.put("/api/meetings/{id}", response_model=MeetingDetail, summary="회의록 수정 (쓴 사람 · owner)")
def update_meeting(id: int, data: MeetingUpdate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    m, membership = load_meeting(db, id, user)
    if not can_edit(m, membership, user):
        raise forbidden("쓴 사람과 owner 만 고칠 수 있습니다")
    if data.title is not None:
        if not data.title.strip():
            raise ApiError(400, "VALIDATION_ERROR", "제목을 입력해 주세요")
        m.title = data.title.strip()
    if data.met_at is not None:
        m.met_at = as_utc(data.met_at)
    if data.attendees is not None:
        m.attendees = data.attendees.strip()
    if data.body is not None:
        if not data.body.strip():
            raise ApiError(400, "VALIDATION_ERROR", "본문을 입력해 주세요")
        m.body = data.body.strip()  # 3항목은 다시 구분하지 않는다
    db.commit()
    return meeting_detail(m)


@router.delete("/api/meetings/{id}", status_code=204, summary="회의록 삭제 (딸린 할 일 · 댓글 포함)")
def delete_meeting(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m, membership = load_meeting(db, id, user)
    if not can_edit(m, membership, user):
        raise forbidden("쓴 사람과 owner 만 지울 수 있습니다")
    db.delete(m)
    db.commit()
    return Response(status_code=204)
