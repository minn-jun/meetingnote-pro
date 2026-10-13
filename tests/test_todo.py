"""specs/todo"""


def todos_of(client, user, team):
    return client.get(f"/api/teams/{team['id']}/todos", headers=user["h"]).json()


def kinds(client, user, team):
    return [a["kind"] for a in client.get(f"/api/teams/{team['id']}/activities", headers=user["h"]).json()]


def test_team_todos_sorted_with_meeting_title(client, h):
    owner, _, team, m = h.setup_team()
    rows = todos_of(client, owner, team)
    assert all(r["meeting_title"] == "2차 스프린트 계획 회의" and r["meeting_id"] == m["id"] for r in rows)
    # 같은 상태 안에서는 due_text 오름차순
    assert [r["due_text"] for r in rows] == sorted(r["due_text"] for r in rows)
    client.put(f"/api/todos/{rows[0]['id']}", json={"status": "DONE"}, headers=owner["h"])
    client.put(f"/api/todos/{rows[1]['id']}", json={"status": "DOING"}, headers=owner["h"])
    assert [r["status"] for r in todos_of(client, owner, team)] == ["OPEN", "DOING", "DONE"]


def test_my_todos_only_mine(client, h):
    owner, member, _, _ = h.setup_team()
    mine = client.get("/api/me/todos", headers=owner["h"]).json()
    assert [t["what"] for t in mine] == ["목록 화면 및 검색 구현"]
    assert all(t["assignee_name"] == "김대리" for t in mine)
    r = client.get("/api/me/todos", headers=member["h"])
    assert r.status_code == 200 and r.json() == []


def test_move_to_done_records_todo_done(client, h):
    owner, member, team, m = h.setup_team()
    t = m["todos"][0]
    client.put(f"/api/todos/{t['id']}", json={"status": "DOING"}, headers=member["h"])
    assert "todo_done" not in kinds(client, owner, team)
    r = client.put(f"/api/todos/{t['id']}", json={"status": "DONE"}, headers=member["h"])
    assert r.status_code == 200 and r.json()["status"] == "DONE"
    assert kinds(client, owner, team)[0] == "todo_done"
    # 되돌리기도 허용. 되돌리기는 기록하지 않는다
    n = len(kinds(client, owner, team))
    r = client.put(f"/api/todos/{t['id']}", json={"status": "OPEN"}, headers=member["h"])
    assert r.status_code == 200 and r.json()["status"] == "OPEN"
    assert len(kinds(client, owner, team)) == n


def test_assign_records_todo_assign(client, h):
    owner, member, team, m = h.setup_team()
    unassigned = next(t for t in m["todos"] if t["assignee_id"] is None)
    member_id = h.me(member)["id"]
    r = client.put(f"/api/todos/{unassigned['id']}", json={"assignee_id": member_id}, headers=owner["h"])
    assert r.status_code == 200
    assert (r.json()["assignee_id"], r.json()["assignee_name"]) == (member_id, "박과장")
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert acts[0]["kind"] == "todo_assign"
    assert "박과장에게 배정" in acts[0]["text"]
    # 미정으로 되돌리기 - 기록 없음
    n = len(acts)
    r = client.put(f"/api/todos/{unassigned['id']}", json={"assignee_id": None}, headers=owner["h"])
    assert r.status_code == 200 and r.json()["assignee_id"] is None
    assert len(kinds(client, owner, team)) == n


def test_update_only_sent_fields(client, h):
    owner, _, _, m = h.setup_team()
    t = next(x for x in m["todos"] if x["assignee_id"] is not None)
    r = client.put(f"/api/todos/{t['id']}", json={"due_text": "2026-10-20"}, headers=owner["h"])
    d = r.json()
    assert (d["due_text"], d["status"], d["assignee_id"]) == ("2026-10-20", t["status"], t["assignee_id"])
    r = client.put(f"/api/todos/{t['id']}", json={"due_text": ""}, headers=owner["h"])
    assert r.json()["due_text"] == "미정"


def test_invalid_status_and_assignee(client, h):
    owner, _, _, m = h.setup_team()
    tid = m["todos"][0]["id"]
    r = client.put(f"/api/todos/{tid}", json={"status": "CLOSED"}, headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")
    outsider = h.signup("외부인")
    r = client.put(f"/api/todos/{tid}", json={"assignee_id": h.me(outsider)["id"]}, headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")
    r = client.put(f"/api/todos/{tid}", json={"assignee_id": 9999}, headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")


def test_other_team_forbidden_and_missing_not_found(client, h):
    owner, _, _, m = h.setup_team()
    outsider = h.signup()
    h.team(outsider, "다른팀")
    r = client.put(f"/api/todos/{m['todos'][0]['id']}", json={"status": "DONE"}, headers=outsider["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
    r = client.put("/api/todos/9999", json={"status": "DONE"}, headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (404, "NOT_FOUND")
    r = client.get(f"/api/teams/{h.me(owner) and 1}/todos", headers=outsider["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")


def test_delete_owner_only(client, h):
    owner, member, team, m = h.setup_team()
    tid = m["todos"][0]["id"]
    r = client.delete(f"/api/todos/{tid}", headers=member["h"])
    assert (r.status_code, r.json()["code"]) == (403, "OWNER_ONLY")
    assert len(todos_of(client, owner, team)) == 3
    assert client.delete(f"/api/todos/{tid}", headers=owner["h"]).status_code == 204
    assert len(todos_of(client, owner, team)) == 2
    assert client.delete(f"/api/todos/{tid}", headers=owner["h"]).status_code == 404


def test_empty_todos(client, h):
    owner = h.signup()
    team = h.team(owner)
    assert todos_of(client, owner, team) == []
