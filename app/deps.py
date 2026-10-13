"""현재 사용자 · 팀 멤버 확인 · owner 확인"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ApiError, forbidden, not_found, owner_only
from app.models import Membership, Team, User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False, description="로그인 · 가입 응답의 token")


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    # 없음 · 위조 · 만료를 모두 같은 코드로 (결정사항 D12)
    user_id = decode_token(cred.credentials) if cred else None
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise ApiError(401, "TOKEN_EXPIRED", "세션이 만료되었습니다. 다시 로그인해 주세요")
    return user


def membership_of(db: Session, user_id: int) -> Membership | None:
    return db.scalar(select(Membership).where(Membership.user_id == user_id))


def require_member(db: Session, team_id: int, user: User) -> tuple[Team, Membership]:
    """팀 자원은 그 팀 멤버만. 없는 팀 404, 남의 팀 403"""
    team = db.get(Team, team_id)
    if not team:
        raise not_found("팀을 찾을 수 없습니다")
    m = membership_of(db, user.id)
    if not m or m.team_id != team_id:
        raise forbidden("이 팀의 멤버가 아닙니다")
    return team, m


def require_owner(db: Session, team_id: int, user: User) -> tuple[Team, Membership]:
    team, m = require_member(db, team_id, user)
    if m.role != "owner":
        raise owner_only()
    return team, m
