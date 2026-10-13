import re

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, membership_of
from app.errors import ApiError, validation
from app.models import Team, User
from app.schemas import LoginIn, MeOut, MeUpdate, OkOut, SignupIn, TokenOut
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def check_password(pw: str) -> None:
    if len(pw) < 8:
        raise ApiError(400, "PASSWORD_TOO_WEAK", "비밀번호는 8자 이상 입력해 주세요")


def me_out(db: Session, user: User) -> MeOut:
    m = membership_of(db, user.id)
    return MeOut(id=user.id, name=user.name, email=user.email, role=m.role if m else None)


@router.post("/signup", status_code=201, response_model=TokenOut, summary="회원가입")
def signup(data: SignupIn, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ApiError(400, "EMAIL_INVALID", "올바른 이메일 형식이 아닙니다")
    check_password(data.password)
    name = data.name.strip()
    if not name:
        raise validation("이름을 입력해 주세요")
    if db.scalar(select(User).where(User.email == email)):
        raise ApiError(409, "EMAIL_DUPLICATED", "이미 가입된 이메일입니다")
    user = User(email=email, password_hash=hash_password(data.password), name=name)
    db.add(user)
    db.commit()
    return TokenOut(token=create_token(user.id), team_id=None, team_name=None)


@router.post("/login", response_model=TokenOut, summary="로그인")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.strip().lower()))
    # 이메일이 없는지 비밀번호가 틀렸는지 드러내지 않는다
    if not user or not verify_password(data.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다")
    m = membership_of(db, user.id)
    team = db.get(Team, m.team_id) if m else None
    return TokenOut(token=create_token(user.id), team_id=team.id if team else None,
                    team_name=team.name if team else None)


@router.get("/me", response_model=MeOut, summary="내 정보")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return me_out(db, user)


@router.put("/me", response_model=MeOut, summary="내 정보 수정 (이름 · 비밀번호)")
def update_me(data: MeUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise validation("이름을 입력해 주세요")
        user.name = name
    if data.password is not None:
        check_password(data.password)
        user.password_hash = hash_password(data.password)
    db.commit()
    return me_out(db, user)


@router.post("/logout", response_model=OkOut, summary="로그아웃 (서버는 상태를 두지 않음)")
def logout(user: User = Depends(get_current_user)):
    return OkOut()
