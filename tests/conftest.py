"""공통 fixture - 임시 SQLite · TestClient · 가짜 AI 공급자 · 가입 / 팀 도우미"""
import os

os.environ["JWT_SECRET"] = "test-secret-" + "x" * 32
os.environ["DOCS_ENABLED"] = "true"
os.environ.pop("VERCEL", None)
os.environ.pop("DATABASE_URL", None)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import ai as ai_module
from app.db import get_db, init_db, make_engine
from app.main import app


class FakeAI:
    """고정 결과를 돌려주는 공급자. fail=True 면 공급자 장애를 흉내 낸다"""

    def __init__(self):
        self.fail = False
        self.transcript = "김대리: 목록과 검색은 제가 다음 주 금요일까지 하겠습니다."
        self.result = {
            "summary": "2차 스프린트 계획을 다루었다.\n검색 범위를 정했다.\n업로드 용량을 정했다.",
            "decisions": ["목록 검색은 제목과 참석자 범위로 한정", "", "업로드 용량 상한은 25MB"],
            "todos": [
                {"what": "목록 화면 및 검색 구현", "assignee_name": "김대리", "due_text": "2026-10-02"},
                {"what": "받아쓰기 오류 처리", "assignee_name": "없는사람", "due_text": "이번 주 안"},
                {"what": "사용자 인터뷰", "assignee_name": None, "due_text": ""},
            ],
        }
        self.calls = []

    def transcribe(self, data, filename):
        self.calls.append(("transcribe", filename))
        if self.fail:
            raise RuntimeError("공급자 장애")
        return self.transcript

    def split(self, body, met_at, member_names):
        self.calls.append(("split", member_names))
        if self.fail:
            raise RuntimeError("공급자 장애")
        return self.result


@pytest.fixture
def fake_ai():
    return FakeAI()


@pytest.fixture
def client(tmp_path, fake_ai):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[ai_module.get_ai] = lambda: fake_ai
    c = TestClient(app)
    c.Session = Session
    yield c
    app.dependency_overrides.clear()
    engine.dispose()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class Helper:
    def __init__(self, client):
        self.c = client
        self.n = 0

    def signup(self, name="김대리", email=None, password="mypassword"):
        self.n += 1
        email = email or f"user{self.n}@example.com"
        r = self.c.post("/api/auth/signup", json={"email": email, "password": password, "name": name})
        assert r.status_code == 201, r.text
        return {"token": r.json()["token"], "email": email, "name": name, "h": auth(r.json()["token"])}

    def me(self, user):
        return self.c.get("/api/auth/me", headers=user["h"]).json()

    def team(self, owner, name="기획팀"):
        r = self.c.post("/api/teams", json={"name": name}, headers=owner["h"])
        assert r.status_code == 201, r.text
        return r.json()

    def join(self, user, code):
        r = self.c.post("/api/teams/join", json={"code": code}, headers=user["h"])
        assert r.status_code == 200, r.text
        return r.json()

    def meeting(self, user, team_id, title="2차 스프린트 계획 회의", attendees="김대리, 박과장, 이주임",
                met_at="2026-09-24T05:00:00Z", body="회의 본문"):
        r = self.c.post(f"/api/teams/{team_id}/meetings", headers=user["h"],
                        json={"title": title, "met_at": met_at, "attendees": attendees, "body": body})
        assert r.status_code == 201, r.text
        return r.json()

    def setup_team(self):
        """owner 김대리 · member 박과장 으로 된 팀과 회의록 1건"""
        owner = self.signup("김대리")
        team = self.team(owner)
        member = self.signup("박과장")
        self.join(member, team["invite_code"])
        meeting = self.meeting(owner, team["id"])
        return owner, member, team, meeting


@pytest.fixture
def h(client):
    return Helper(client)
