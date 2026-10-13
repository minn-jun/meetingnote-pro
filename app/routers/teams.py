import secrets

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import activity
from app.db import get_db
from app.deps import get_current_user, membership_of, require_member, require_owner
from app.errors import ApiError, validation
from app.models import Meeting, Membership, Team, Todo, User
from app.schemas import MemberOut, TeamCreate, TeamJoin, TeamOut, TeamUpdate

router = APIRouter(prefix="/api/teams", tags=["Team"])

TEAM_LIMIT = 6
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_code(db: Session) -> str:
    while True:
        code = "MN-" + "".join(secrets.choice(CODE_CHARS) for _ in range(4))
        if not db.scalar(select(Team.id).where(Team.invite_code == code)):
            return code


def member_count(db: Session, team_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Membership).where(Membership.team_id == team_id))


def team_out(db: Session, team: Team, role: str) -> TeamOut:
    return TeamOut(id=team.id, name=team.name, invite_code=team.invite_code,
                   role=role, member_count=member_count(db, team.id))


def no_team_yet(db: Session, user: User) -> None:
    if membership_of(db, user.id):
        raise validation("이미 팀에 속해 있습니다. 팀은 하나만 가질 수 있습니다")


@router.post("", status_code=201, response_model=TeamOut, summary="팀 만들기")
def create_team(data: TeamCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    no_team_yet(db, user)
    name = data.name.strip()
    if not name:
        raise validation("팀 이름을 입력해 주세요")
    team = Team(name=name, invite_code=new_code(db), owner_id=user.id)
    db.add(team)
    db.flush()
    db.add(Membership(team_id=team.id, user_id=user.id, role="owner"))
    db.commit()
    return team_out(db, team, "owner")


@router.get("", response_model=list[TeamOut], summary="내 팀 (0건 또는 1건)")
def my_teams(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = membership_of(db, user.id)
    if not m:
        return []
    return [team_out(db, db.get(Team, m.team_id), m.role)]


@router.post("/join", response_model=TeamOut, summary="초대코드로 합류")
def join(data: TeamJoin, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    no_team_yet(db, user)
    team = db.scalar(select(Team).where(Team.invite_code == data.code.strip().upper()))
    if not team:
        raise ApiError(404, "INVITE_NOT_FOUND", "초대코드를 찾을 수 없습니다")
    if member_count(db, team.id) >= TEAM_LIMIT:
        raise ApiError(409, "TEAM_FULL", "팀 정원(6명)이 찼습니다")
    db.add(Membership(team_id=team.id, user_id=user.id, role="member"))
    activity.record(db, team.id, user.id, "member_join", team=team.name)
    db.commit()
    return team_out(db, team, "member")


@router.get("/{id}/members", response_model=list[MemberOut], summary="멤버 목록")
def members(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_member(db, id, user)
    rows = db.scalars(select(Membership).where(Membership.team_id == id)
                      .order_by((Membership.role != "owner"), Membership.joined_at, Membership.id)).all()
    counts = dict(db.execute(
        select(Todo.assignee_id, func.count()).join(Meeting, Todo.meeting_id == Meeting.id)
        .where(Meeting.team_id == id, Todo.assignee_id.is_not(None)).group_by(Todo.assignee_id)).all())
    return [MemberOut(id=m.user.id, name=m.user.name, email=m.user.email, role=m.role,
                      todo_count=counts.get(m.user.id, 0)) for m in rows]


@router.put("/{id}/code", response_model=TeamOut, summary="초대코드 재발급 (owner)")
def recode(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team, m = require_owner(db, id, user)
    team.invite_code = new_code(db)
    db.commit()
    return team_out(db, team, m.role)


@router.put("/{id}", response_model=TeamOut, summary="팀 이름 변경 (owner)")
def rename(id: int, data: TeamUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team, m = require_owner(db, id, user)
    name = data.name.strip()
    if not name:
        raise validation("팀 이름을 입력해 주세요")
    team.name = name
    db.commit()
    return team_out(db, team, m.role)
