# MeetingNote Pro

로그인한 팀이 함께 쓰는 회의록. 녹취를 올리면 받아써서 요약 · 결정사항 · 할 일 세 항목으로 나누고, 할 일은 칸반으로 추적하며, 댓글과 활동 기록이 남는다.

- 백엔드: FastAPI + SQLAlchemy (로컬 SQLite · 배포 Neon Postgres)
- 화면: Vanilla JS + Tailwind CDN. `frontend/` 의 화면 6종을 FastAPI 가 함께 낸다
- 받아쓰기 · 3항목 구분: Google Gemini (기본 `gemini-3.8-flash`, `.env` 에서 바꿀 수 있음)
- 설계 문서: `docs/` (정의서 · 스토리보드 · 디자인 시스템 · 결정사항)
- 동작 명세: `openspec/specs/` 7묶음 (OpenSpec)
- 확정 디자인 시안: `publish/` (참고용. 구현 화면은 `frontend/`)

## 무엇을 할 수 있나

| 화면 | 주소 | 하는 일 |
|---|---|---|
| 로그인 · 회원가입 | `/login.html` | 이메일 · 비밀번호로 가입하고 로그인. 가입할 때 초대코드를 넣으면 바로 팀에 합류 |
| 회의록 목록 | `/meetings.html` | 제목 · 참석자 검색, 기간 필터. 녹취(mp3 · wav)를 올려 받아쓰고 「정리하기」로 저장 |
| 회의록 상세 | `/detail.html?id=` | 요약 · 결정사항 · 할 일 3단, 담당자 배정, 받아쓴 본문, 댓글 |
| 할 일 칸반 | `/todos.html` | 대기 · 진행 · 완료 3열. 카드를 끌거나 눌러서 옮기고, 담당자 · 기한을 바꿈 |
| 팀 설정 | `/team.html` | 팀 만들기 · 초대코드 합류, 초대코드 복사 · 재발급, 멤버, 활동 기록 |
| 내 정보 | `/profile.html` | 이름 · 비밀번호 변경, 내 할 일, 내 활동, 로그아웃 |

권한은 owner 와 member 둘이다. 팀 이름 변경 · 초대코드 재발급 · 할 일 삭제는 owner 만 하고, 회의록과 댓글은 쓴 사람과 owner 가 고치고 지운다. 한 사람은 팀 하나에 속하고 팀은 6명까지다.

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

106개가 있고, 임시 SQLite 와 가짜 받아쓰기 공급자로 돌기 때문에 API 키 없이 돈다. 기능 묶음마다 파일이 하나씩 있다 (`tests/test_auth.py` · `test_team.py` · `test_meeting.py` · `test_todo.py` · `test_comment.py` · `test_activity.py` · `test_platform.py` · `test_integration.py`).

## API

모든 경로는 `/api/` 로 시작하고 26개다. 가입 · 로그인을 뺀 나머지는 `Authorization: Bearer <token>` 이 필요하다. 요청 · 응답 형식은 `/docs` 에서 본다.

| 묶음 | 개수 | 경로 |
|---|---|---|
| Auth | 5 | `POST /auth/signup` · `POST /auth/login` · `GET /auth/me` · `PUT /auth/me` · `POST /auth/logout` |
| Team | 6 | `POST /teams` · `GET /teams` · `POST /teams/join` · `GET /teams/{id}/members` · `PUT /teams/{id}/code` · `PUT /teams/{id}` |
| Meeting | 6 | `POST /teams/{id}/meetings` · `GET /teams/{id}/meetings` · `GET /meetings/{id}` · `PUT /meetings/{id}` · `DELETE /meetings/{id}` · `POST /upload` |
| Todo | 4 | `GET /teams/{id}/todos` · `PUT /todos/{id}` · `GET /me/todos` · `DELETE /todos/{id}` |
| Comment | 3 | `POST /meetings/{id}/comments` · `GET /meetings/{id}/comments` · `DELETE /comments/{id}` |
| Activity | 2 | `GET /teams/{id}/activities` · `GET /me/activities` |

## 환경변수

| 이름 | 기본값 | 내용 |
|---|---|---|
| `JWT_SECRET` | (개발용 값) | JWT 서명 키. 배포에서는 꼭 바꾼다 |
| `STT_API_KEY` | 없음 | Gemini API 키 |
| `STT_MODEL` · `SUMMARY_MODEL` | `gemini-3.8-flash` | 받아쓰기 · 3항목 구분 모델. 오디오 입력과 구조화 출력(JSON)을 지원하는 Gemini 모델이어야 한다 (예: `gemini-3.1-flash-lite`) |
| `DATABASE_URL` | 없음 | 있으면 Postgres, 없으면 로컬 SQLite |
| `MAX_UPLOAD_MB` | `25` | 녹취 업로드 상한 (소수 가능). Vercel 배포는 `4.2` |
| `CORS_ORIGINS` | 로컬 주소 | 허용 출처. 쉼표로 구분 |
| `DOCS_ENABLED` | `true` | `false` 면 `/docs` 를 끈다 |

## Vercel 배포

지금 배포된 주소: https://meetingnote-pro-psi.vercel.app (API 문서는 `/docs`)

코드는 로컬과 같은 한 벌이다. `pyproject.toml` 의 `[tool.vercel] entrypoint = "app.main:app"` 로 FastAPI 앱 하나가 Vercel Function 하나가 된다.

처음부터 다시 배포할 때의 순서 (Vercel CLI):

```bash
vercel link --yes --project meetingnote-pro        # 프로젝트 만들고 연결
vercel integration add neon --name meetingnote-pro-db   # Neon Postgres 만들고 연결 (DATABASE_URL 자동 등록)
vercel env add JWT_SECRET production --sensitive   # 아래 환경변수를 하나씩 등록
vercel deploy --prod
```

- 환경변수: `JWT_SECRET` · `STT_API_KEY` · `STT_MODEL` · `SUMMARY_MODEL` · `MAX_UPLOAD_MB=4.2` · `CORS_ORIGINS=https://<배포 주소>`
- 테이블 만들기: 첫 요청 때 자동으로 만들어진다. 미리 만들려면 Neon 연결 문자열을 `DATABASE_URL` 로 주고 `python -m app.migrate` 를 돌린다 (이미 있는 테이블은 건드리지 않는다)
- 코드를 고친 뒤에는 `vercel deploy --prod` 로 다시 배포한다. GitHub 저장소가 비공개라 push 만으로는 자동 배포되지 않는다 (Vercel 에 저장소 접근을 허용한 뒤 `vercel git connect` 를 하면 자동 배포가 된다)

알아 둘 것:

- **업로드는 4.2MB 까지다.** Vercel Function 은 요청 본문을 4.5MB 까지만 받는다. 그래서 배포에서는 `MAX_UPLOAD_MB=4.2` 로 둔다 (`docs/결정사항.md` D3)
- **`DATABASE_URL` 이 없으면 배포 환경에서는 시작하지 않는다.** Vercel Function 은 SQLite 파일을 쓸 수 없다
- 되돌리려면 Vercel 의 이전 배포로 되돌린다

## 폴더

```
app/         FastAPI 백엔드 (routers/ 는 기능 6묶음)
frontend/    화면 6종 + theme.js (색 · 클래스 규칙) + app.js (공통)
tests/       pytest
docs/        설계 PDF 3종 · 결정사항.md
publish/     확정 디자인 시안 (손대지 않는다)
openspec/    OpenSpec 명세와 변경 기록
```

## 명세와 결정 기록

- `openspec/specs/` - 지금 시스템이 지켜야 하는 동작 명세 7묶음: `auth` · `team` · `meeting` · `todo` · `comment` · `activity` · `platform`. 요구사항마다 근거 스토리보드 번호와 퍼블리싱 파일이 적혀 있다
- `openspec/changes/archive/2026-10-13-add-mvp-core/` - 1회차 MVP 를 만든 변경안 (proposal · design · tasks). 구현이 끝나 보관했다
- `docs/결정사항.md` - 설계 문서에 없거나 서로 어긋나 따로 정한 것 (D1~D15). 모두 잠정 결정이라, 바꿀 때는 이 파일을 먼저 고친다
- 기능을 더하거나 바꿀 때는 `/opsx:propose <이름>` 으로 변경안을 만들고 `/opsx:apply` · `/opsx:archive` 순으로 진행한다

## 아직 확인하지 않은 것

- 25MB 에 가까운 긴 녹취의 받아쓰기 시간 (4MB 녹음은 배포 환경에서 9초쯤 걸렸다)
- 브라우저로 배포 주소에서 화면 6종을 눌러 보는 확인 (API 는 배포 주소에서 실제 녹음 파일로 확인했다)
