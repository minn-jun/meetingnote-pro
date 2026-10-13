from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import activity
from app.db import get_db
from app.deps import get_current_user, require_member
from app.errors import ApiError, forbidden, not_found, validation
from app.models import Comment, Meeting, Membership, User
from app.schemas import CommentIn, CommentOut

router = APIRouter(tags=["Comment"])

MAX_LEN = 500


def comment_out(c: Comment, user: User, membership: Membership) -> CommentOut:
    return CommentOut(id=c.id, user_id=c.user_id, user_name=c.user.name, content=c.content,
                      created_at=c.created_at,
                      can_delete=c.user_id == user.id or membership.role == "owner")


def meeting_for(db: Session, id: int, user: User) -> tuple[Meeting, Membership]:
    m = db.get(Meeting, id)
    if not m:
        raise ApiError(404, "MEETING_NOT_FOUND", "회의록을 찾을 수 없습니다")
    _, membership = require_member(db, m.team_id, user)
    return m, membership


@router.post("/api/meetings/{id}/comments", status_code=201, response_model=CommentOut, summary="댓글 달기")
def add_comment(id: int, data: CommentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m, membership = meeting_for(db, id, user)
    content = data.content.strip()
    if not content or len(content) > MAX_LEN:
        raise validation("댓글은 1자 이상 500자 이내로 입력해 주세요")
    c = Comment(meeting_id=m.id, user_id=user.id, content=content)
    db.add(c)
    activity.record(db, m.team_id, user.id, "comment_add", title=m.title)
    db.commit()
    db.refresh(c)
    return comment_out(c, user, membership)


@router.get("/api/meetings/{id}/comments", response_model=list[CommentOut], summary="댓글 목록")
def list_comments(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m, membership = meeting_for(db, id, user)
    rows = db.scalars(select(Comment).where(Comment.meeting_id == m.id).options(selectinload(Comment.user))
                      .order_by(Comment.created_at, Comment.id)).all()
    return [comment_out(c, user, membership) for c in rows]


@router.delete("/api/comments/{id}", status_code=204, summary="댓글 삭제 (쓴 사람 · owner)")
def delete_comment(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(Comment, id)
    if not c:
        raise not_found("댓글을 찾을 수 없습니다")
    m = db.get(Meeting, c.meeting_id)
    _, membership = require_member(db, m.team_id, user)
    if c.user_id != user.id and membership.role != "owner":
        raise forbidden("쓴 사람과 owner 만 지울 수 있습니다")
    db.delete(c)
    db.commit()
    return Response(status_code=204)
