"""활동 기록 - kind 5종 고정, 문장은 조회할 때 만든다"""
import json

from sqlalchemy.orm import Session

from app.models import Activity
from app.schemas import ActivityOut

KINDS = ("meeting_add", "todo_assign", "todo_done", "comment_add", "member_join")


def record(db: Session, team_id: int, actor_id: int, kind: str, **target: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"정해지지 않은 활동 kind: {kind}")
    db.add(Activity(team_id=team_id, actor_id=actor_id, kind=kind,
                    target=json.dumps(target, ensure_ascii=False)))


def sentence(kind: str, t: dict) -> str:
    if kind == "meeting_add":
        return f"회의록 「{t.get('title', '')}」 등록"
    if kind == "todo_assign":
        return f"할 일 「{t.get('what', '')}」를 {t.get('assignee', '')}에게 배정"
    if kind == "todo_done":
        return f"할 일 「{t.get('what', '')}」 완료"
    if kind == "comment_add":
        return f"회의록 「{t.get('title', '')}」에 댓글 작성"
    return f"{t.get('team', '')}에 합류"


def to_out(a: Activity) -> ActivityOut:
    try:
        t = json.loads(a.target or "{}")
    except ValueError:
        t = {}
    return ActivityOut(id=a.id, kind=a.kind, actor_name=a.actor.name,
                       text=sentence(a.kind, t), created_at=a.created_at)
