"""specs/meeting"""
import pytest

from app.config import settings
from app.routers.meetings import audio_kind

WAV = b"RIFF" + (36).to_bytes(4, "little") + b"WAVEfmt " + b"\x00" * 64
MP3_ID3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64
MP3_FRAME = b"\xff\xfb\x90\x00" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


def upload(client, user, data, name="회의_녹음.wav"):
    return client.post("/api/upload", files={"file": (name, data, "application/octet-stream")}, headers=user["h"])


def test_audio_kind_by_content():
    assert audio_kind(WAV[:16]) == "wav"
    assert audio_kind(MP3_ID3[:16]) == "mp3"
    assert audio_kind(MP3_FRAME[:16]) == "mp3"
    assert audio_kind(MP4[:16]) is None
    assert audio_kind(b"") is None


@pytest.mark.parametrize("data", [WAV, MP3_ID3, MP3_FRAME], ids=["wav", "mp3-id3", "mp3-frame"])
def test_upload_transcribes_without_saving(client, h, fake_ai, data):
    owner, _, team, _ = h.setup_team()
    before = len(client.get(f"/api/teams/{team['id']}/meetings", headers=owner["h"]).json())
    r = upload(client, owner, data)
    assert r.status_code == 200
    assert r.json() == {"body": fake_ai.transcript}
    assert len(client.get(f"/api/teams/{team['id']}/meetings", headers=owner["h"]).json()) == before


def test_upload_mp4_renamed_to_mp3_is_415(client, h):
    u = h.signup()
    r = upload(client, u, MP4, name="a.mp3")
    assert (r.status_code, r.json()["code"]) == (415, "UNSUPPORTED_MEDIA_TYPE")


def test_upload_too_large_is_413(client, h, monkeypatch):
    u = h.signup()
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    r = upload(client, u, WAV + b"\x00" * (1024 * 1024 + 1))
    assert (r.status_code, r.json()["code"]) == (413, "PAYLOAD_TOO_LARGE")


def test_upload_provider_failure_is_502(client, h, fake_ai):
    u = h.signup()
    fake_ai.fail = True
    r = upload(client, u, WAV)
    assert (r.status_code, r.json()["code"]) == (502, "UPSTREAM_ERROR")


def test_upload_requires_login(client):
    assert client.post("/api/upload", files={"file": ("a.wav", WAV)}).status_code == 401


def test_create_meeting_splits_three_parts(client, h, fake_ai):
    owner, member, team, m = h.setup_team()
    assert m["title"] == "2차 스프린트 계획 회의"
    assert m["summary"].count("\n") == 2
    assert m["decisions"] == "목록 검색은 제목과 참석자 범위로 한정\n업로드 용량 상한은 25MB"
    assert m["decision_count"] == 2
    assert [t["status"] for t in m["todos"]] == ["OPEN"] * 3
    assert m["todo_total_count"] == 3 and m["todo_done_count"] == 0
    # 공급자에게 팀 멤버 이름을 넘긴다
    assert ("split", ["김대리", "박과장"]) in fake_ai.calls
    acts = client.get(f"/api/teams/{team['id']}/activities", headers=owner["h"]).json()
    assert acts[0]["kind"] == "meeting_add"


def test_assignee_matched_only_to_members(client, h):
    owner, _, _, m = h.setup_team()
    by = {t["what"]: t for t in m["todos"]}
    assert by["목록 화면 및 검색 구현"]["assignee_name"] == "김대리"
    assert by["목록 화면 및 검색 구현"]["due_text"] == "2026-10-02"
    assert by["받아쓰기 오류 처리"]["assignee_id"] is None       # 멤버가 아닌 이름
    assert by["받아쓰기 오류 처리"]["due_text"] == "이번 주 안"   # 날짜로 못 바꾼 글자는 그대로
    assert by["사용자 인터뷰"]["assignee_id"] is None
    assert by["사용자 인터뷰"]["due_text"] == "미정"


@pytest.mark.parametrize("payload", [
    {"title": "제목", "met_at": "2026-09-24T05:00:00Z"},                    # 본문 없음
    {"title": "", "met_at": "2026-09-24T05:00:00Z", "body": "본문"},        # 제목 빔
    {"title": "제목", "body": "본문"},                                       # 시각 없음
    {"title": "제목", "met_at": "2026-09-24T05:00:00Z", "body": "   "},     # 공백 본문
])
def test_create_meeting_missing_required(client, h, payload):
    owner = h.signup()
    team = h.team(owner)
    r = client.post(f"/api/teams/{team['id']}/meetings", json=payload, headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")


def test_split_failure_saves_nothing(client, h, fake_ai):
    owner = h.signup()
    team = h.team(owner)
    fake_ai.fail = True
    r = client.post(f"/api/teams/{team['id']}/meetings", headers=owner["h"],
                    json={"title": "제목", "met_at": "2026-09-24T05:00:00Z", "body": "본문"})
    assert (r.status_code, r.json()["code"]) == (502, "UPSTREAM_ERROR")
    assert client.get(f"/api/teams/{team['id']}/meetings", headers=owner["h"]).json() == []


def seed_three(h, owner, team):
    h.meeting(owner, team["id"], title="기획 킥오프", attendees="김대리, 박과장, 이주임, 최선임",
              met_at="2026-09-10T00:00:00Z", body="본문에만있는낱말 킥오프")
    h.meeting(owner, team["id"], title="배포 환경 점검", attendees="박과장, 최선임",
              met_at="2026-09-18T01:30:00Z")
    h.meeting(owner, team["id"], title="2차 스프린트 계획 회의", attendees="김대리, 박과장, 이주임",
              met_at="2026-09-24T05:00:00Z")


def test_list_sorted_desc_without_body(client, h):
    owner = h.signup()
    team = h.team(owner)
    seed_three(h, owner, team)
    rows = client.get(f"/api/teams/{team['id']}/meetings", headers=owner["h"]).json()
    assert [r["title"] for r in rows] == ["2차 스프린트 계획 회의", "배포 환경 점검", "기획 킥오프"]
    assert set(rows[0]) == {"id", "title", "met_at", "attendees", "summary", "created_at",
                            "todo_done_count", "todo_total_count", "decision_count"}
    assert all("body" not in r for r in rows)


def test_search_title_and_attendees_only(client, h):
    owner = h.signup()
    team = h.team(owner)
    seed_three(h, owner, team)
    url = f"/api/teams/{team['id']}/meetings"
    assert [r["title"] for r in client.get(url, params={"q": "배포"}, headers=owner["h"]).json()] == ["배포 환경 점검"]
    assert [r["title"] for r in client.get(url, params={"q": "최선임"}, headers=owner["h"]).json()] == [
        "배포 환경 점검", "기획 킥오프"]
    r = client.get(url, params={"q": "본문에만있는낱말"}, headers=owner["h"])
    assert r.status_code == 200 and r.json() == []


def test_date_range_inclusive(client, h):
    owner = h.signup()
    team = h.team(owner)
    seed_three(h, owner, team)
    url = f"/api/teams/{team['id']}/meetings"
    rows = client.get(url, params={"from": "2026-09-18", "to": "2026-09-24"}, headers=owner["h"]).json()
    assert [r["title"] for r in rows] == ["2차 스프린트 계획 회의", "배포 환경 점검"]
    rows = client.get(url, params={"to": "2026-09-10"}, headers=owner["h"]).json()
    assert [r["title"] for r in rows] == ["기획 킥오프"]


def test_detail_has_body_and_todos(client, h):
    owner, member, _, m = h.setup_team()
    r = client.get(f"/api/meetings/{m['id']}", headers=member["h"])
    assert r.status_code == 200
    d = r.json()
    assert d["body"] == "회의 본문" and len(d["todos"]) == 3 and d["author_id"] == h.me(owner)["id"]
    assert set(d["todos"][0]) == {"id", "what", "assignee_id", "assignee_name", "due_text", "status",
                                  "meeting_id", "meeting_title"}


def test_update_does_not_resplit(client, h, fake_ai):
    owner, _, _, m = h.setup_team()
    splits = sum(1 for c in fake_ai.calls if c[0] == "split")
    r = client.put(f"/api/meetings/{m['id']}", headers=owner["h"],
                   json={"title": "바꾼 제목", "met_at": "2026-09-25T05:00:00Z", "attendees": "김대리", "body": "고친 본문"})
    assert r.status_code == 200
    d = r.json()
    assert (d["title"], d["met_at"], d["attendees"], d["body"]) == (
        "바꾼 제목", "2026-09-25T05:00:00Z", "김대리", "고친 본문")
    assert d["summary"] == m["summary"] and len(d["todos"]) == 3
    assert sum(1 for c in fake_ai.calls if c[0] == "split") == splits


def test_edit_delete_only_author_or_owner(client, h):
    owner, member, team, _ = h.setup_team()
    third = h.signup("이주임")
    h.join(third, team["invite_code"])
    by_member = h.meeting(member, team["id"], title="member 가 쓴 회의록")
    r = client.put(f"/api/meetings/{by_member['id']}", json={"title": "x"}, headers=third["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
    r = client.delete(f"/api/meetings/{by_member['id']}", headers=third["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
    # 쓴 사람은 고치고, owner 는 지운다
    assert client.put(f"/api/meetings/{by_member['id']}", json={"title": "y"}, headers=member["h"]).status_code == 200
    assert client.delete(f"/api/meetings/{by_member['id']}", headers=owner["h"]).status_code == 204


def test_delete_cascades_todos_and_comments(client, h):
    owner, member, team, m = h.setup_team()
    for text in ("댓글 하나", "댓글 둘"):
        client.post(f"/api/meetings/{m['id']}/comments", json={"content": text}, headers=member["h"])
    assert len(client.get(f"/api/teams/{team['id']}/todos", headers=owner["h"]).json()) == 3
    r = client.delete(f"/api/meetings/{m['id']}", headers=owner["h"])
    assert r.status_code == 204 and r.content == b""
    assert client.get(f"/api/teams/{team['id']}/todos", headers=owner["h"]).json() == []
    r = client.get(f"/api/meetings/{m['id']}/comments", headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (404, "MEETING_NOT_FOUND")


def test_meeting_not_found_and_other_team(client, h):
    owner, _, _, m = h.setup_team()
    r = client.get("/api/meetings/9999", headers=owner["h"])
    assert (r.status_code, r.json()["code"]) == (404, "MEETING_NOT_FOUND")
    outsider = h.signup()
    h.team(outsider, "다른팀")
    r = client.get(f"/api/meetings/{m['id']}", headers=outsider["h"])
    assert (r.status_code, r.json()["code"]) == (403, "FORBIDDEN")
