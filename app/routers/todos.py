from fastapi import APIRouter, Depends, Response
from sqlalchemy import case, select
from sqlalchemy.orm import Session, selectinload

from app import activity
from app.db import get_db
from app.deps import get_current_user, membership_of, require_member
from app.errors import not_found, owner_only, validation
from app.models import Meeting, Membership, Todo, User
from app.schemas import TodoOut, TodoUpdate
from app.views import todo_out

router = APIRouter(tags=["Todo"])

STATUSES = ("OPEN", "DOING", "DONE")
STATUS_ORDER = case({"OPEN": 0, "DOING": 1, "DONE": 2}, value=Todo.status, else_=3)


def todo_query():
    return (select(Todo).join(Meeting, Todo.meeting_id == Meeting.id)
            .options(selectinload(Todo.assignee), selectinload(Todo.meeting))
            .order_by(STATUS_ORDER, Todo.due_text, Todo.id))


@router.get("/api/teams/{id}/todos", response_model=list[TodoOut], summary="팀 할 일 전체")
def team_todos(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_member(db, id, user)
    return [todo_out(t) for t in db.scalars(todo_query().where(Meeting.team_id == id)).all()]


@router.get("/api/me/todos", response_model=list[TodoOut], summary="내가 담당인 할 일")
def my_todos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [todo_out(t) for t in db.scalars(todo_query().where(Todo.assignee_id == user.id)).all()]


def load_todo(db: Session, id: int, user: User) -> tuple[Todo, Membership]:
    t = db.scalar(select(Todo).where(Todo.id == id)
                  .options(selectinload(Todo.assignee), selectinload(Todo.meeting)))
    if not t:
        raise not_found("할 일을 찾을 수 없습니다")
    _, m = require_member(db, t.meeting.team_id, user)
    return t, m


@router.put("/api/todos/{id}", response_model=TodoOut, summary="할 일 변경 (상태 · 담당자 · 기한)")
def update_todo(id: int, data: TodoUpdate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    t, _ = load_todo(db, id, user)
    sent = data.model_fields_set
    team_id = t.meeting.team_id

    if "status" in sent:
        if data.status not in STATUSES:
            raise validation("상태는 OPEN · DOING · DONE 중 하나입니다")
        if data.status == "DONE" and t.status != "DONE":
            activity.record(db, team_id, user.id, "todo_done", what=t.what)
        t.status = data.status

    if "assignee_id" in sent:
        new = data.assignee_id
        if new is not None:
            target = membership_of(db, new)
            if not target or target.team_id != team_id:
                raise validation("담당자는 팀 멤버 중에서 골라 주세요")
            if new != t.assignee_id:
                activity.record(db, team_id, user.id, "todo_assign", what=t.what, assignee=target.user.name)
        t.assignee_id = new

    if "due_text" in sent:
        t.due_text = (data.due_text or "").strip() or "미정"

    db.commit()
    db.refresh(t)
    return todo_out(t)


@router.delete("/api/todos/{id}", status_code=204, summary="할 일 삭제 (owner)")
def delete_todo(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t, m = load_todo(db, id, user)
    if m.role != "owner":
        raise owner_only()
    db.delete(t)
    db.commit()
    return Response(status_code=204)
