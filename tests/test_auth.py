"""specs/auth"""
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select

from app.config import settings
from app.models import User
from app.security import create_token, decode_token, hash_password, verify_password
from tests.conftest import auth


def test_signup_success_and_bcrypt_hash(client):
    r = client.post("/api/auth/signup",
                    json={"email": "user@example.com", "password": "mypassword", "name": "김대리"})
    assert r.status_code == 201
    assert r.json()["token"] and r.json()["team_id"] is None
    with client.Session() as db:
        u = db.scalar(select(User))
    assert u.password_hash != "mypassword"
    assert u.password_hash.startswith("$2")
    assert verify_password("mypassword", u.password_hash)


def test_signup_email_invalid(client):
    r = client.post("/api/auth/signup", json={"email": "user@@example", "password": "mypassword", "name": "김"})
    assert (r.status_code, r.json()["code"]) == (400, "EMAIL_INVALID")


def test_signup_password_too_weak(client):
    r = client.post("/api/auth/signup", json={"email": "a@example.com", "password": "1234", "name": "김"})
    assert (r.status_code, r.json()["code"]) == (400, "PASSWORD_TOO_WEAK")


def test_signup_email_duplicated(client, h):
    h.signup(email="dup@example.com")
    r = client.post("/api/auth/signup", json={"email": "dup@example.com", "password": "mypassword", "name": "김"})
    assert (r.status_code, r.json()["code"]) == (409, "EMAIL_DUPLICATED")
    with client.Session() as db:
        assert len(db.scalars(select(User)).all()) == 1


def test_signup_missing_name_is_validation_error(client):
    r = client.post("/api/auth/signup", json={"email": "a@example.com", "password": "mypassword", "name": "  "})
    assert (r.status_code, r.json()["code"]) == (400, "VALIDATION_ERROR")


def test_login_success_token_expires_in_24h(client, h):
    u = h.signup(email="user@example.com")
    r = client.post("/api/auth/login", json={"email": "user@example.com", "password": "mypassword"})
    assert r.status_code == 200
    payload = jwt.decode(r.json()["token"], settings.jwt_secret, algorithms=["HS256"])
    assert payload["exp"] - payload["iat"] == 24 * 3600
    assert r.json()["team_id"] is None


def test_login_response_has_team_id(client, h):
    u = h.signup(email="user@example.com")
    team = h.team(u)
    r = client.post("/api/auth/login", json={"email": "user@example.com", "password": "mypassword"})
    assert r.json()["team_id"] == team["id"]
    assert r.json()["team_name"] == "기획팀"


def test_login_unknown_email_and_wrong_password_same_response(client, h):
    h.signup(email="user@example.com")
    a = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "mypassword"})
    b = client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrongpass1"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()
    assert a.json()["code"] == "INVALID_CREDENTIALS"


def test_expired_token_is_401_token_expired(client, h):
    u = h.signup()
    me = h.me(u)
    old = create_token(me["id"], now=datetime.now(timezone.utc) - timedelta(hours=25))
    assert decode_token(old) is None
    r = client.get("/api/auth/me", headers=auth(old))
    assert (r.status_code, r.json()["code"]) == (401, "TOKEN_EXPIRED")


def test_missing_or_forged_token_is_401(client):
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/api/auth/me", headers=auth("not.a.token"))
    assert (r.status_code, r.json()["code"]) == (401, "TOKEN_EXPIRED")
    for path in ("/api/teams", "/api/me/todos", "/api/me/activities"):
        assert client.get(path).status_code == 401


def test_me_role_null_without_team_then_owner(client, h):
    u = h.signup("김대리", email="kim@example.com")
    assert h.me(u) == {"id": 1, "name": "김대리", "email": "kim@example.com", "role": None}
    h.team(u)
    assert h.me(u)["role"] == "owner"


def test_update_name_only_keeps_password(client, h):
    u = h.signup(email="user@example.com")
    r = client.put("/api/auth/me", json={"name": "김수석"}, headers=u["h"])
    assert r.status_code == 200 and r.json()["name"] == "김수석"
    assert r.json()["email"] == "user@example.com"
    ok = client.post("/api/auth/login", json={"email": "user@example.com", "password": "mypassword"})
    assert ok.status_code == 200


def test_update_password(client, h):
    u = h.signup(email="user@example.com")
    assert client.put("/api/auth/me", json={"password": "newpass1234"}, headers=u["h"]).status_code == 200
    assert client.post("/api/auth/login",
                       json={"email": "user@example.com", "password": "mypassword"}).status_code == 401
    assert client.post("/api/auth/login",
                       json={"email": "user@example.com", "password": "newpass1234"}).status_code == 200


def test_update_weak_password(client, h):
    u = h.signup()
    r = client.put("/api/auth/me", json={"password": "1234"}, headers=u["h"])
    assert (r.status_code, r.json()["code"]) == (400, "PASSWORD_TOO_WEAK")


def test_account_change_not_in_activities(client, h):
    owner, member, team, _ = h.setup_team()
    before = client.get("/api/me/activities", headers=member["h"]).json()
    client.put("/api/auth/me", json={"name": "박차장"}, headers=member["h"])
    after = client.get("/api/me/activities", headers=member["h"]).json()
    assert len(after) == len(before)


def test_logout_returns_200(client, h):
    u = h.signup()
    r = client.post("/api/auth/logout", headers=u["h"])
    assert r.status_code == 200


def test_hash_is_salted():
    assert hash_password("mypassword") != hash_password("mypassword")


def test_auth_tag_has_five_apis(client):
    spec = client.get("/openapi.json").json()
    ops = [(m, p) for p, v in spec["paths"].items() for m, op in v.items() if "Auth" in op.get("tags", [])]
    assert len(ops) == 5
