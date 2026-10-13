from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.activity import to_out
from app.db import get_db
from app.deps import get_current_user, require_member
from app.models import Activity, User
from app.schemas import ActivityOut

router = APIRouter(tags=["Activity"])

LIMIT = 50


def recent():
    return (select(Activity).options(selectinload(Activity.actor))
            .order_by(Activity.created_at.desc(), Activity.id.desc()).limit(LIMIT))


@router.get("/api/teams/{id}/activities", response_model=list[ActivityOut], summary="팀 활동 (최근 50건)")
def team_activities(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_member(db, id, user)
    return [to_out(a) for a in db.scalars(recent().where(Activity.team_id == id)).all()]


@router.get("/api/me/activities", response_model=list[ActivityOut], summary="내 활동 (최근 50건)")
def my_activities(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [to_out(a) for a in db.scalars(recent().where(Activity.actor_id == user.id)).all()]
