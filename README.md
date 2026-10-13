# MeetingNote Pro

로그인한 팀이 함께 쓰는 회의록. 녹취를 올리면 받아써서 요약 · 결정사항 · 할 일 세 항목으로 나누고, 할 일은 칸반으로 추적하며, 댓글과 활동 기록이 남는다.

- 백엔드: FastAPI + SQLAlchemy (로컬 SQLite · 배포 Neon Postgres)
- 화면: Vanilla JS + Tailwind CDN. `frontend/` 의 화면 6종을 FastAPI 가 함께 낸다
- 받아쓰기 · 3항목 구분: Google Gemini (`gemini-3.8-flash`)
- 설계 문서: `docs/` (정의서 · 스토리보드 · 디자인 시스템 · 결정사항), `openspec/changes/add-mvp-core/`
- 확정 디자인 시안: `publish/` (참고용. 구현 화면은 `frontend/`)

## 로컬 실행

Python 3.12 이상이 필요하다.

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS · Linux 는 source .venv/bin/activate
pip install -e ".[dev]"
copy .env.example .env            # macOS · Linux 는 cp
```

`.env` 를 열어 두 값을 채운다.

| 값 | 내용 |
|---|---|
| `JWT_SECRET` | 긴 임의 문자열 |
| `STT_API_KEY` | Gemini API 키 (Google AI Studio 에서 발급). 없으면 녹취 업로드와 회의록 정리가 `502 UPSTREAM_ERROR` 로 실패하고, 나머지 기능은 그대로 쓸 수 있다 |

```bash
uvicorn app.main:app --reload
```

- 화면: http://127.0.0.1:8000 (로그인 화면으로 이동)
- API 문서: http://127.0.0.1:8000/docs
- DB: 처음 요청 때 `meetingnote.db` (SQLite) 가 만들어진다. 지우면 처음 상태로 돌아간다

## Swagger UI 에서 API 시험하기

1. http://127.0.0.1:8000/docs 를 연다
2. **Auth > POST /api/auth/signup** (또는 login) 을 실행하고 응답의 `token` 을 복사한다
3. 오른쪽 위 **Authorize** 를 눌러 token 을 붙여넣는다 (`Bearer` 는 붙이지 않는다)
4. 이제 나머지 API 를 바로 실행할 수 있다. `POST /api/upload` 는 파일 선택 칸에서 mp3 · wav 를 고른다

오류 응답은 언제나 `{"code": "...", "msg": "..."}` 형식이다.

## 테스트

```bash
pytest
```

임시 SQLite 와 가짜 받아쓰기 공급자로 돌기 때문에 API 키 없이 돈다. 기능 묶음마다 파일이 하나씩 있다 (`tests/test_auth.py` · `test_team.py` · `test_meeting.py` · `test_todo.py` · `test_comment.py` · `test_activity.py` · `test_platform.py` · `test_integration.py`).

## 환경변수

| 이름 | 기본값 | 내용 |
|---|---|---|
| `JWT_SECRET` | (개발용 값) | JWT 서명 키. 배포에서는 꼭 바꾼다 |
| `STT_API_KEY` | 없음 | Gemini API 키 |
| `STT_MODEL` · `SUMMARY_MODEL` | `gemini-3.8-flash` | 받아쓰기 · 3항목 구분 모델 |
| `DATABASE_URL` | 없음 | 있으면 Postgres, 없으면 로컬 SQLite |
| `MAX_UPLOAD_MB` | `25` | 녹취 업로드 상한. Vercel 배포는 `4` |
| `CORS_ORIGINS` | 로컬 주소 | 허용 출처. 쉼표로 구분 |
| `DOCS_ENABLED` | `true` | `false` 면 `/docs` 를 끈다 |

## Vercel 배포

코드는 로컬과 같은 한 벌이다. `pyproject.toml` 의 `[tool.vercel] entrypoint = "app.main:app"` 로 FastAPI 앱 하나가 Vercel Function 하나가 된다.

1. Vercel 에 이 저장소를 프로젝트로 연결한다
2. Storage 에서 Neon Postgres 를 만들어 프로젝트에 연결한다 (`DATABASE_URL` 이 자동으로 들어간다)
3. 환경변수를 등록한다: `JWT_SECRET` · `STT_API_KEY` · `MAX_UPLOAD_MB=4` · `CORS_ORIGINS=https://<프로젝트>.vercel.app`
4. 배포한 뒤 `https://<프로젝트>.vercel.app/login.html` 과 `/docs` 를 확인한다

알아 둘 것:

- **업로드는 4MB 까지다.** Vercel Function 은 요청 본문을 4.5MB 까지만 받는다. 그래서 배포에서는 `MAX_UPLOAD_MB=4` 로 둔다 (`docs/결정사항.md` D3)
- **`DATABASE_URL` 이 없으면 배포 환경에서는 시작하지 않는다.** Vercel Function 은 SQLite 파일을 쓸 수 없다
- 되돌리려면 Vercel 의 이전 배포로 되돌린다

## 폴더

```
app/         FastAPI 백엔드 (routers/ 는 기능 6묶음)
frontend/    화면 6종 + theme.js (색 · 클래스 규칙) + app.js (공통)
tests/       pytest
docs/        설계 PDF 3종 · 결정사항.md
publish/     확정 디자인 시안 (손대지 않는다)
openspec/    OpenSpec 변경안
```
