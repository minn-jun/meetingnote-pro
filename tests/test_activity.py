"""specs/activity"""
import pytest

from app import activity
from app.models import Activity

FIVE = {"meeting_add", "todo_assign", "todo_done", "comment_add", "member_join"}


def test_unknown_kind_rejected(client):
    with client.Session() as db:
        with pytest.raises(ValueError):
            activity.record(db, 1, 1, "team_create", team="x")


def test_only_five_kinds_are_recorded(client, h):
    owner, member, team, m = h.setup_team()           # 가입 · 팀 생성 · 합류 · 회의록 생성
    todo = next(t for t in m["todos"] if t["assignee_id"] is None)
    client.put(f"/api/todos/{todo['id']}", json={"assignee_id": h.me(member)["id"]}, headers=owner["h"])
    client.put(f"/api/todos/{todo['id']}", json={"status": "DONE"}, headers=member["h"])
    client.put(f"/api/todos/{todo['id']}", json={"status": "OPEN"}, headers=member["h"])   # 되돌리기
    client.post(f"/api/meetings/{m['id']}/comments", json={"content": "댓글"}, headers=member["h"])
    client.put("/api/auth/me", json={"name": "박차장"}, headers=member["h"])               # 계정 변경
    client.put(f"/api/teams/{team['id']}", json={"name": "제품팀"}, headers=owner["h"])    # 팀 이름
    client.put(f"/api/teams/{team['id']}/code", headers=owner["h"])                        # 재발급
    client.delete(f"/api/todos/{todo['id']}", headers=owner["h"])                          # 삭제
    client.delete(f"/api/meetings/{m['id']}", headers=owner["h"])
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert [a["kind"] for a in acts] == ["comment_add", "todo_done", "todo_assign", "meeting_add", "member_join"]
    assert {a["kind"] for a in acts} == FIVE
    assert set(acts[0]) == {"id", "kind", "actor_name", "text", "created_at"}


def test_sentences_built_by_server(client, h):
    owner, member, team, m = h.setup_team()
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert acts[0]["text"] == "회의록 「2차 스프린트 계획 회의」 등록"
    assert acts[0]["actor_name"] == "김대리"
    assert acts[1]["text"] == "기획팀에 합류"
    todo = m["todos"][0]
    client.put(f"/api/todos/{todo['id']}", json={"status": "DONE"}, headers=owner["h"])
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert acts[0]["text"] == f"할 일 「{todo['what']}」 완료"


def test_latest_50_descending(client, h):
    owner, _, team, _ = h.setup_team()
    owner_id = h.me(owner)["id"]
    with client.Session() as db:
        for i in range(60):
            db.add(Activity(team_id=team["id"], actor_id=owner_id, kind="meeting_add",
                            target=f'{{"title": "회의 {i:02d}"}}'))
        db.commit()
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert len(acts) == 50
    assert acts[0]["text"] == "회의록 「회의 59」 등록"
    assert acts[-1]["text"] == "회의록 「회의 10」 등록"
    assert [a["created_at"] for a in acts] == sorted((a["created_at"] for a in acts), reverse=True)


def test_my_activities_only_mine(client, h):
    owner, member, team, _ = h.setup_team()
    mine = client.get("/api/me/activities", headers=member["h"]).json()
    assert [a["kind"] for a in mine] == ["member_join"]
    assert [a["kind"] for a in client.get("/api/me/activities", headers=owner["h"]).json()] == ["meeting_add"]
    fresh = h.signup()
    r = client.get("/api/me/activities", headers=fresh["h"])
    assert r.status_code == 200 and r.json() == []


def test_other_team_activities_forbidden(client, h):
    _, _, team, _ = h.setup_team()
    outsider = h.signup()
    h.team(outsider, "다른팀")
    r = client.get(f"/api/teams/{team['id']}/activities", headers=outsider["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
