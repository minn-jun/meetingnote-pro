"""specs/team"""
import re

from app.routers.teams import new_code

CODE = re.compile(r"^MN-[A-Z0-9]{4}$")


def test_invite_code_format_and_unique(client):
    with client.Session() as db:
        codes = {new_code(db) for _ in range(200)}
    assert all(CODE.match(c) for c in codes)
    assert len(codes) > 190


def test_create_team_makes_owner(client, h):
    u = h.signup()
    team = h.team(u, "기획팀")
    assert team["name"] == "기획팀" and team["role"] == "owner" and team["member_count"] == 1
    assert CODE.match(team["invite_code"])


def test_second_team_not_allowed(client, h):
    u = h.signup()
    h.team(u)
    r = client.post("/api/teams", json={"name": "또다른팀"}, headers=u["h"])
    assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")
    assert len(client.get("/api/teams", headers=u["h"]).json()) == 1


def test_my_teams_empty_without_team(client, h):
    u = h.signup()
    r = client.get("/api/teams", headers=u["h"])
    assert r.status_code == 200 and r.json() == []


def test_join_success_records_member_join(client, h):
    owner = h.signup("김대리")
    team = h.team(owner)
    member = h.signup("박과장")
    joined = h.join(member, team["invite_code"].lower())  # 소문자로 넣어도 합류
    assert joined["role"] == "member" and joined["member_count"] == 2
    members = client.get(f"/api/teams/{team['id']}/members", headers=owner["h"]).json()
    assert [(m["name"], m["role"]) for m in members] == [("김대리", "owner"), ("박과장", "member")]
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert [a["kind"] for a in acts] == ["member_join"]
    assert acts[0]["actor_name"] == "박과장"


def test_join_invite_not_found_keeps_account(client, h):
    u = h.signup(email="user@example.com")
    r = client.post("/api/teams/join", json={"code": "MN-0000"}, headers=u["h"])
    assert (r.status_code, r.json()["code"]) == (404, "INVITE_NOT_FOUND")
    assert client.post("/api/auth/login",
                       json={"email": "user@example.com", "password": "mypassword"}).status_code == 200


def test_join_team_full(client, h):
    owner = h.signup()
    team = h.team(owner)
    for _ in range(5):
        h.join(h.signup(), team["invite_code"])
    seventh = h.signup()
    r = client.post("/api/teams/join", json={"code": team["invite_code"]}, headers=seventh["h"])
    assert (r.status_code, r.json()["code"]) == (409, "TEAM_FULL")


def test_join_when_already_in_team(client, h):
    a = h.signup()
    team_a = h.team(a)
    b = h.signup()
    h.team(b, "다른팀")
    r = client.post("/api/teams/join", json={"code": team_a["invite_code"]}, headers=b["h"])
    assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")


def test_members_have_todo_count(client, h):
    owner, member, team, _ = h.setup_team()
    members = client.get(f"/api/teams/{team['id']}/members", headers=member["h"]).json()
    assert len(members) == 2
    by = {m["name"]: m for m in members}
    assert set(by["김대리"]) == {"id", "name", "email", "role", "todo_count"}
    assert by["김대리"]["todo_count"] == 1  # 가짜 구분 결과에서 김대리 담당 1건
    assert by["박과장"]["todo_count"] == 0


def test_other_team_forbidden_and_missing_team_not_found(client, h):
    owner, _, team, _ = h.setup_team()
    outsider = h.signup()
    h.team(outsider, "다른팀")
    r = client.get(f"/api/teams/{team['id']}/members", headers=outsider["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
    r = client.get("/api/teams/9999/members", headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (404, "NOT_FOUND")


def test_recode_invalidates_old_code(client, h):
    owner = h.signup()
    team = h.team(owner)
    old = team["invite_code"]
    r = client.put(f"/api/teams/{team['id']}/code", headers=owner["h"])
    assert r.status_code == 200
    new = r.json()["invite_code"]
    assert new != old and CODE.match(new)
    late = h.signup()
    r = client.post("/api/teams/join", json={"code": old}, headers=late["h"])
    assert (r.status_code, r.json()["code"]) == (404, "INVITE_NOT_FOUND")
    assert client.post("/api/teams/join", json={"code": new}, headers=late["h"]).status_code == 200


def test_member_cannot_recode_or_rename(client, h):
    owner, member, team, _ = h.setup_team()
    r = client.put(f"/api/teams/{team['id']}/code", headers=member["h"])
    assert (r.status_code, r.json()["code"]) == (403, "OWNER_ONLY")
    r = client.put(f"/api/teams/{team['id']}", json={"name": "바꾼이름"}, headers=member["h"])
    assert (r.status_code, r.json()["code"]) == (403, "OWNER_ONLY")
    assert client.get("/api/teams", headers=owner["h"]).json()[0]["name"] == "기획팀"


def test_owner_renames_team(client, h):
    owner, _, team, _ = h.setup_team()
    r = client.put(f"/api/teams/{team['id']}", json={"name": "제품팀"}, headers=owner["h"])
    assert r.status_code == 200 and r.json()["name"] == "제품팀"
