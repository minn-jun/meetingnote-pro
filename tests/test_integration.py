"""통합 확인 - API 26개 대조 · 사용자 여정 · 응답 성능"""
import re
import time

from tests.test_meeting import WAV

# 정의서 7장의 26개
SPEC_APIS = {
    ("POST", "/api/auth/signup"), ("POST", "/api/auth/login"), ("GET", "/api/auth/me"),
    ("PUT", "/api/auth/me"), ("POST", "/api/auth/logout"),
    ("POST", "/api/teams"), ("GET", "/api/teams"), ("POST", "/api/teams/join"),
    ("GET", "/api/teams/{id}/members"), ("PUT", "/api/teams/{id}/code"), ("PUT", "/api/teams/{id}"),
    ("POST", "/api/teams/{id}/meetings"), ("GET", "/api/teams/{id}/meetings"), ("GET", "/api/meetings/{id}"),
    ("PUT", "/api/meetings/{id}"), ("DELETE", "/api/meetings/{id}"), ("POST", "/api/upload"),
    ("GET", "/api/teams/{id}/todos"), ("PUT", "/api/todos/{id}"), ("GET", "/api/me/todos"),
    ("DELETE", "/api/todos/{id}"),
    ("POST", "/api/meetings/{id}/comments"), ("GET", "/api/meetings/{id}/comments"),
    ("DELETE", "/api/comments/{id}"),
    ("GET", "/api/teams/{id}/activities"), ("GET", "/api/me/activities"),
}


def documented(client) -> set:
    spec = client.get("/openapi.json").json()
    return {(m.upper(), p) for p, ops in spec["paths"].items() for m in ops}


def test_openapi_is_exactly_the_26_apis(client):
    assert len(SPEC_APIS) == 26
    assert documented(client) == SPEC_APIS
    assert all(p.startswith("/api/") for _, p in documented(client))


def test_user_journey_calls_every_api(client, h):
    """스토리보드 A-01 여정을 따라가며 26개를 모두 한 번 이상 부른다"""
    called = set()
    patterns = [(m, p, re.compile("^" + re.sub(r"\{id\}", r"\\d+", p) + "$")) for m, p in SPEC_APIS]
    real = client.request

    def spy(method, url, *a, **kw):
        path = str(url).split("?")[0]
        for m, p, rx in patterns:
            if m == method.upper() and rx.match(path):
                called.add((m, p))
        return real(method, url, *a, **kw)

    client.request = spy

    # 1 가입 · 로그인
    leader = h.signup("김대리", email="kim@example.com")
    assert client.post("/api/auth/login", json={"email": "kim@example.com", "password": "mypassword"}).status_code == 200
    assert client.get("/api/auth/me", headers=leader["h"]).json()["role"] is None
    # 2 팀 생성 · 초대코드 재발급 · 합류
    team = h.team(leader)
    tid = team["id"]
    code = client.put(f"/api/teams/{tid}/code", headers=leader["h"]).json()["invite_code"]
    client.put(f"/api/teams/{tid}", json={"name": "제품팀"}, headers=leader["h"])
    newcomer = h.signup("박과장")
    h.join(newcomer, code)
    assert len(client.get("/api/teams", headers=newcomer["h"]).json()) == 1
    members = client.get(f"/api/teams/{tid}/members", headers=leader["h"]).json()
    assert len(members) == 2
    # 3 녹취 업로드 > 3항목 구분
    body = client.post("/api/upload", files={"file": ("회의.wav", WAV)}, headers=leader["h"]).json()["body"]
    m = h.meeting(leader, tid, body=body)
    assert client.get(f"/api/teams/{tid}/meetings", params={"q": "스프린트"}, headers=newcomer["h"]).json()
    # 4 3항목 확인 · 수정
    detail = client.get(f"/api/meetings/{m['id']}", headers=newcomer["h"]).json()
    assert detail["summary"] and detail["decisions"] and len(detail["todos"]) == 3
    client.put(f"/api/meetings/{m['id']}", json={"attendees": "김대리, 박과장"}, headers=leader["h"])
    # 5 담당자 배정
    todo = next(t for t in detail["todos"] if t["assignee_id"] is None)
    newcomer_id = next(x["id"] for x in members if x["name"] == "박과장")
    client.put(f"/api/todos/{todo['id']}", json={"assignee_id": newcomer_id}, headers=leader["h"])
    # 6 칸반 이동
    assert [t["id"] for t in client.get("/api/me/todos", headers=newcomer["h"]).json()] == [todo["id"]]
    client.put(f"/api/todos/{todo['id']}", json={"status": "DONE"}, headers=newcomer["h"])
    board = client.get(f"/api/teams/{tid}/todos", headers=leader["h"]).json()
    assert sum(1 for t in board if t["status"] == "DONE") == 1
    # 댓글 · 활동 기록
    c = client.post(f"/api/meetings/{m['id']}/comments", json={"content": "확인했습니다"}, headers=newcomer["h"]).json()
    assert len(client.get(f"/api/meetings/{m['id']}/comments", headers=leader["h"]).json()) == 1
    kinds = [a["kind"] for a in client.get(f"/api/teams/{tid}/activities", headers=leader["h"]).json()]
    assert kinds == ["comment_add", "todo_done", "todo_assign", "meeting_add", "member_join"]
    assert len(client.get("/api/me/activities", headers=newcomer["h"]).json()) == 3
    # 내 정보 수정 · 정리 · 로그아웃
    client.put("/api/auth/me", json={"name": "박차장"}, headers=newcomer["h"])
    assert client.delete(f"/api/comments/{c['id']}", headers=newcomer["h"]).status_code == 204
    assert client.delete(f"/api/todos/{todo['id']}", headers=leader["h"]).status_code == 204
    assert client.delete(f"/api/meetings/{m['id']}", headers=leader["h"]).status_code == 204
    assert client.post("/api/auth/logout", headers=leader["h"]).status_code == 200

    assert SPEC_APIS - called == set()


def best_ms(fn, n=5) -> float:
    """가장 빠른 한 번 (ms). 첫 호출의 준비 시간과 다른 프로세스의 방해를 뺀다"""
    best = float("inf")
    for _ in range(n):
        t = time.perf_counter()
        r = fn()
        best = min(best, (time.perf_counter() - t) * 1000)
        assert r.status_code < 300
    return best


def test_response_time(client, h, fake_ai):
    """정의서 Metrics - 목록 API 100ms 안, 가입 · 로그인 250ms 안 (로컬)"""
    owner = h.signup(email="perf@example.com")
    team = h.team(owner)
    tid = team["id"]
    fake_ai.result = {"summary": "요약", "decisions": ["결정 1", "결정 2"],
                      "todos": [{"what": f"할 일 {i}", "assignee_name": "김대리", "due_text": "2026-10-20"}
                                for i in range(4)]}
    for i in range(30):                      # 회의록 30건 · 할 일 120건
        h.meeting(owner, tid, title=f"회의 {i:02d}", met_at=f"2026-09-{i % 28 + 1:02d}T05:00:00Z")

    limits = {
        f"/api/teams/{tid}/meetings": 100, f"/api/teams/{tid}/todos": 100, "/api/me/todos": 100,
        f"/api/teams/{tid}/members": 100, f"/api/teams/{tid}/activities": 100, "/api/auth/me": 100,
    }
    for path, limit in limits.items():
        ms = best_ms(lambda: client.get(path, headers=owner["h"]))
        assert ms < limit, f"{path} {ms:.0f}ms"

    ms = best_ms(lambda: client.post("/api/auth/login",
                                     json={"email": "perf@example.com", "password": "mypassword"}), n=3)
    assert ms < 250, f"login {ms:.0f}ms"
    seq = iter(range(100))
    ms = best_ms(lambda: client.post("/api/auth/signup", json={
        "email": f"p{next(seq)}@example.com", "password": "mypassword", "name": "성능"}), n=3)
    assert ms < 250, f"signup {ms:.0f}ms"
