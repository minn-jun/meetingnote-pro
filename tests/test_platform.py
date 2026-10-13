"""specs/platform - 공통 규약 · Swagger · 화면 제공 · DB 전환 · 화면 규칙"""
import re
from pathlib import Path

import pytest
from sqlalchemy import inspect

from app.db import init_db, make_engine, resolve_url

ROOT = Path(__file__).resolve().parent.parent
ISO_Z = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def test_bad_request_is_400_validation_error(client):
    r = client.post("/api/auth/login", json={"email": "a@b.co"})
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert set(r.json()) == {"code", "msg"}


def test_time_is_iso_utc_z(client, h):
    owner, _, _, meeting = h.setup_team()
    r = client.get(f"/api/meetings/{meeting['id']}", headers=owner["h"])
    assert ISO_Z.match(r.json()["met_at"])
    assert ISO_Z.match(r.json()["created_at"])
    assert r.json()["met_at"] == "2026-09-24T05:00:00Z"


def test_docs_and_openapi(client):
    assert client.get("/docs").status_code == 200
    spec = client.get("/openapi.json").json()
    assert "HTTPBearer" in spec["components"]["securitySchemes"]
    tags = {t for p in spec["paths"].values() for op in p.values() for t in op.get("tags", [])}
    assert tags == {"Auth", "Team", "Meeting", "Todo", "Comment", "Activity"}
    upload = spec["paths"]["/api/upload"]["post"]["requestBody"]["content"]
    assert "multipart/form-data" in upload


def test_token_calls_protected_api(client, h):
    u = h.signup()
    assert client.get("/api/auth/me", headers=u["h"]).status_code == 200


def test_cors_only_allowed_origins(client):
    bad = client.get("/api/teams", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in bad.headers
    ok = client.get("/api/teams", headers={"Origin": "http://127.0.0.1:8000"})
    assert ok.headers.get("access-control-allow-origin") == "http://127.0.0.1:8000"


def test_root_redirects_to_login(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/login.html"


@pytest.mark.parametrize("page", ["login", "meetings", "detail", "todos", "team", "profile"])
def test_six_pages_served(client, page):
    r = client.get(f"/{page}.html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_config_js_follows_server_setting(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "max_upload_mb", 4)
    r = client.get("/config.js")
    assert r.status_code == 200 and "maxUploadMb: 4" in r.text
    assert "/config.js" not in client.get("/openapi.json").json()["paths"]


def test_unknown_api_is_not_found_body(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


def test_db_url_switch():
    assert resolve_url("", on_vercel=False).startswith("sqlite")
    assert resolve_url("postgres://u:p@h/db", False) == "postgresql+psycopg://u:p@h/db"
    assert resolve_url("postgresql://u:p@h/db", False) == "postgresql+psycopg://u:p@h/db"
    with pytest.raises(RuntimeError):
        resolve_url("", on_vercel=True)


def test_seven_tables(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'x.db'}")
    init_db(engine)
    assert set(inspect(engine).get_table_names()) == {
        "users", "teams", "memberships", "meetings", "todos", "comments", "activities"}


# ── 화면 규칙 (결정사항 D1) ────────────────────────────
FRONT_FILES = sorted((ROOT / "frontend").glob("*.html")) + sorted((ROOT / "frontend").glob("*.js"))


@pytest.mark.parametrize("path", FRONT_FILES, ids=lambda p: p.name)
def test_frontend_design_rules(path):
    text = path.read_text(encoding="utf-8")
    assert "!important" not in text
    assert 'style="' not in text
    # 버튼 높이는 h-11 하나. 정사각 아바타 · 로고(w-9 h-9)는 버튼이 아니라 제외
    assert not re.search(r"(?<!w-9 )\bh-(9|10)\b", text), "button height must be h-11"
    assert "stateBar" not in text
    assert "퍼블리싱 확인용" not in text


def test_publish_untouched():
    assert (ROOT / "publish" / "theme.js").read_text(encoding="utf-8").count("window.stateBar") == 1
