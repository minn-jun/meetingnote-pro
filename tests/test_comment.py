"""specs/comment"""


def post(client, user, meeting_id, content):
    return client.post(f"/api/meetings/{meeting_id}/comments", json={"content": content}, headers=user["h"])


def test_add_comment_records_activity(client, h):
    owner, member, team, m = h.setup_team()
    r = post(client, member, m["id"], "받아쓰기 실패는 세 칸을 비우기로 했습니다")
    assert r.status_code == 201
    c = r.json()
    assert set(c) == {"id", "user_id", "user_name", "content", "created_at", "can_delete"}
    assert c["user_name"] == "박과장" and c["can_delete"] is True
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert acts[0]["kind"] == "comment_add" and "2차 스프린트 계획 회의" in acts[0]["text"]


def test_comment_length_limits(client, h):
    owner, _, _, m = h.setup_team()
    assert post(client, owner, m["id"], "가" * 500).status_code == 201
    for bad in ("가" * 501, "", "   "):
        r = post(client, owner, m["id"], bad)
        assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")


def test_list_ascending_and_can_delete(client, h):
    owner, member, team, m = h.setup_team()
    third = h.signup("이주임")
    h.join(third, team["invite_code"])
    post(client, member, m["id"], "첫째 (박과장)")
    post(client, third, m["id"], "둘째 (이주임)")
    as_member = client.get(f"/api/meetings/{m['id']}/comments", headers=member["h"]).json()
    assert [c["content"] for c in as_member] == ["첫째 (박과장)", "둘째 (이주임)"]
    assert [c["can_delete"] for c in as_member] == [True, False]
    as_owner = client.get(f"/api/meetings/{m['id']}/comments", headers=owner["h"]).json()
    assert [c["can_delete"] for c in as_owner] == [True, True]


def test_empty_comments(client, h):
    owner, _, _, m = h.setup_team()
    r = client.get(f"/api/meetings/{m['id']}/comments", headers=owner["h"])
    assert r.status_code == 200 and r.json() == []


def test_delete_rules(client, h):
    owner, member, team, m = h.setup_team()
    third = h.signup("이주임")
    h.join(third, team["invite_code"])
    a = post(client, member, m["id"], "박과장 댓글").json()
    b = post(client, third, m["id"], "이주임 댓글").json()
    r = client.delete(f"/api/comments/{b['id']}", headers=member["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
    assert client.delete(f"/api/comments/{a['id']}", headers=member["h"]).status_code == 204   # 쓴 사람
    assert client.delete(f"/api/comments/{b['id']}", headers=owner["h"]).status_code == 204    # owner
    r = client.delete(f"/api/comments/{b['id']}", headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (404, "NOT_FOUND")
    assert client.get(f"/api/meetings/{m['id']}/comments", headers=owner["h"]).json() == []


def test_missing_meeting_and_other_team(client, h):
    owner, _, _, m = h.setup_team()
    r = post(client, owner, 9999, "댓글")
    assert (r.status_code, r.json()["code"]) == (404, "MEETING_NOT_FOUND")
    outsider = h.signup()
    h.team(outsider, "다른팀")
    r = post(client, outsider, m["id"], "댓글")
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
    r = client.get(f"/api/meetings/{m['id']}/comments", headers=outsider["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
