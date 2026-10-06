# Design

## Context

- 저장소에는 코드가 없다. 입력은 docs PDF 3종(정의서 · 스토리보드 · 디자인 시스템), publish 폴더(확정 디자인 9개 파일), `docs/결정사항.md`(D1~D13)다. 동기와 범위는 proposal.md, 동작 계약은 specs/ 7묶음을 본다
- 기술 스택은 정의서 9장에서 정해져 있다: FastAPI + SQLAlchemy, 로컬 SQLite · 배포 Neon Postgres, Vanilla JS + Tailwind CDN, Vercel 배포
- 개발 PC 는 Windows, Python 3.12.6 · pip 가 있다. uv 는 없다
- publish 화면은 상태를 눈으로 확인하려고 만든 정적 시안이라 가짜 데이터와 STATE 바를 품고 있고, `window.UI` 를 쓰지 않는 등 디자인 규칙과 어긋나는 곳이 있다 (D1)

## Goals / Non-Goals

**Goals:**

- 코드 한 벌로 로컬(uvicorn + SQLite)과 배포(Vercel + Neon)가 모두 돈다
- API 26개 · 화면 6종 · 오류 코드 15종 · 활동 kind 5종이 spec 과 1:1 로 맞는다
- 받아쓰기 · 3항목 구분 공급자를 갈아 끼울 수 있어 테스트가 키 없이 돈다
- publish 의 화면을 다시 디자인하지 않고 옮겨 와 실제 API 에 붙인다

**Non-Goals:**

- 빌드 도구(번들러 · npm)를 들이지 않는다. 프론트엔드는 정적 파일 그대로다
- DB 마이그레이션 도구(Alembic)를 쓰지 않는다. 1회차는 시작할 때 테이블을 만든다
- 프론트엔드 자동 테스트(브라우저 E2E)는 하지 않는다. 화면은 마지막 수락 항목에서 사람이 확인한다

## Decisions

### 1. 폴더 구조 - 백엔드 · 프론트엔드 · 테스트를 나눈다

```
app/                 FastAPI 백엔드
  main.py            앱 생성 · 라우터 · 오류 처리기 · 정적 파일 · /docs
  config.py          환경변수 읽기 (.env)
  db.py              엔진 · 세션 (DATABASE_URL 유무로 분기)
  models.py          테이블 7개
  schemas.py         요청 · 응답 모델 (Swagger 스키마의 원본)
  errors.py          ApiError(code, status, msg) 와 오류 코드 15종
  deps.py            현재 사용자 · 팀 멤버 확인 · owner 확인
  activity.py        활동 기록 남기기와 문장 만들기
  ai.py              받아쓰기 · 3항목 구분 공급자 (교체 가능)
  routers/           auth · teams · meetings · todos · comments · activities
frontend/            화면 6종 + theme.js + app.js (StaticFiles 로 제공)
tests/               pytest
pyproject.toml       의존성 · Vercel entrypoint
```

- 대안: 한 파일 `main.py` 에 전부 → 26개 API 와 권한 규칙이 섞여 읽기 어렵다. 라우터를 기능 6묶음(spec 과 같은 이름)으로 나눈다
- publish 폴더는 손대지 않는다. frontend/ 로 옮겨 와 고친다. 둘을 비교할 수 있게 남긴다

### 2. 오류는 한 가지 예외와 처리기로 통일한다

- `ApiError(status, code, msg)` 를 던지면 처리기가 `{code, msg}` 로 바꾼다
- FastAPI 의 요청 검증 오류(기본 422)는 처리기에서 `400 VALIDATION_ERROR` 로 바꾼다
- 인증 의존성은 토큰이 없거나 위조 · 만료된 경우 모두 `401 TOKEN_EXPIRED` 를 돌려준다. 15종 안에서 고르면 이것이 맞고, 화면도 셋을 똑같이 처리(토큰 지우고 로그인으로)한다. 로그인 실패만 `INVALID_CREDENTIALS` 다 (D12)
- 대안: 라우터마다 `HTTPException(detail=...)` → 본문 형식이 `{detail}` 이 되어 spec 을 어긴다

### 3. 인증 - PyJWT + bcrypt, 토큰은 localStorage

- 비밀번호는 `bcrypt` 패키지로 직접 해시한다 (passlib 은 bcrypt 4.x 와 경고 · 호환 문제가 있어 쓰지 않는다)
- JWT 는 PyJWT, HS256, `sub`=user id, `exp`=발급 + 24h. 비밀키는 `JWT_SECRET`
- Swagger 연동을 위해 `HTTPBearer` 보안 스키마를 쓴다. OAuth2 password flow 는 폼 로그인을 요구해 JSON 로그인 API 와 어긋나므로 쓰지 않는다
- 가입 · 로그인 응답은 `{token, team_id}` (auth spec). 로그인 화면이 매핑표상 `auth/me` 를 부르지 않으므로 이동할 화면을 이 값으로 정한다

### 4. 데이터 모델 - 정의서 6장 7테이블 그대로

- `users` · `teams` · `memberships` · `meetings` · `todos` · `comments` · `activities`
- `memberships.user_id` 에 UNIQUE 를 걸어 사람당 팀 하나(D5)를 DB 가 지킨다
- `todos.status` 는 `OPEN|DOING|DONE` 문자열, `activities.kind` 는 5종 문자열. 둘 다 앱에서 검증한다 (DB enum 은 SQLite · Postgres 차이가 있어 쓰지 않는다)
- `activities.target` 에는 대상 제목 · 이름을 넣고, `text` 문장은 조회할 때 kind · actor · target 으로 만든다
- 회의록 삭제는 할 일 · 댓글을 함께 지운다 (ORM cascade)
- 시각 컬럼은 timezone 포함 UTC 로 저장하고 응답에서 `Z` 를 붙인 ISO 문자열로 내보낸다
- 배포 DB 전환: `DATABASE_URL` 이 있으면 그 값(`postgres://` 는 `postgresql+psycopg://` 로 바꿈), 없으면 `sqlite:///./meetingnote.db`. 시작할 때 `create_all`

### 5. 받아쓰기와 3항목 구분 - 공급자 인터페이스 하나

- `ai.py` 에 `transcribe(bytes, filename) -> str`, `split(body, met_at, member_names) -> {summary, decisions[], todos[{what, assignee_name, due_text}]}` 두 함수를 가진 공급자를 둔다
- 기본 공급자는 OpenAI SDK. 받아쓰기는 `STT_MODEL`(기본 `gpt-4o-transcribe`), 구분은 `SUMMARY_MODEL` 에 JSON 스키마 구조화 출력으로 받는다. 기본값은 구현 때 OpenAI 문서에서 확인한다 (D2)
- 프롬프트에 「지어내지 않는다 · 결정사항은 합의된 것만 · 담당자는 주어진 멤버 이름 중에서만 · 기한은 met_at 기준 YYYY-MM-DD 로」를 넣는다. 서버는 받은 담당자 이름을 멤버 이름과 다시 대조한다 (모델 출력을 믿지 않는다)
- 앱은 의존성 주입으로 공급자를 받는다. 테스트는 고정 결과를 돌려주는 가짜 공급자로 바꿔 끼운다
- 공급자 예외는 `502 UPSTREAM_ERROR` 로 바꾼다 (D12)
- 대안: 받아쓰기와 구분을 업로드 한 번에 → 스토리보드가 「받아쓰기 완료(본문만) → 정리하기」 두 단계라 나눈다

### 6. 업로드 판정 - 내용으로 형식을 본다

- 앞 바이트로 판정한다: wav 는 `RIFF....WAVE`, mp3 는 `ID3` 또는 MPEG 프레임 동기(`0xFFE` 상위 11비트). 그 밖은 415
- 크기는 읽으면서 `MAX_UPLOAD_MB` 를 넘는 순간 413. 기본 25, 배포 환경변수 4 (D3)

### 7. 프론트엔드 - publish 를 옮기고 공통 모듈 하나를 더한다

- `frontend/theme.js` 는 publish 것을 복사한 뒤, 화면에서 반복되는 조합을 이름으로 등록한다 (D1): 헤더 · nav 항목 · 탭 · 카드 안 작은 배지(`tag`) · 작은 select · 칸 고르기 버튼 · 빨간 글자 고스트 버튼 등. `stateBar` 는 지운다
- `frontend/app.js` 를 새로 둔다: 토큰 저장 · `api(method, path, body)` (Bearer 붙이기 · `{code,msg}` 해석 · `TOKEN_EXPIRED` 면 토큰 지우고 `/login.html?expired=1`) · 로그인 확인 · 현재 팀 구하기 · 공통 헤더 그리기 · 시각 표시 · 기한 지남 판정 · 기한 배지 순환
- 화면마다 publish 의 마크업을 옮기고, 가짜 데이터 · STATES · note 줄을 API 호출로 바꾼다. 화면이 부르는 API 는 매핑표(D8)를 따른다
- 칸반 끌기는 publish 의 포인터 이벤트 구현을 그대로 쓰고, 놓을 때 `PUT` 실패하면 되돌린다
- 메시지는 스토리보드 존댓말 문장을 한곳(`app.js` 의 코드 → 문장 표)에 모은다
- 대안: 프레임워크(React 등) → 정의서가 Vanilla JS 로 고정했다

### 8. 정적 파일과 Swagger 순서

- 라우터를 모두 붙인 뒤 맨 끝에 `StaticFiles(directory="frontend", html=True)` 를 `/` 에 마운트한다. `/` 요청은 `/login.html` 로 보내는 라우트를 먼저 둔다
- FastAPI 기본 `/docs` · `/openapi.json` 을 쓰고, `DOCS_ENABLED=false` 면 끈다 (D9). 라우터마다 tags 를 단다

### 9. 배포 - Vercel Python 런타임

- `pyproject.toml` 의 `[tool.vercel]` entrypoint 를 `app.main:app` 으로 둔다 (스토리보드 H-01). 정적 화면은 FastAPI StaticFiles 로 함께 낸다
- 환경변수: `DATABASE_URL`(Neon 연결 시 자동) · `JWT_SECRET` · `STT_API_KEY` · `MAX_UPLOAD_MB=4` · `CORS_ORIGINS`
- 정확한 Vercel 설정 형식은 배포 작업 때 Vercel 문서로 확인한다

### 10. 테스트 - pytest + TestClient

- 테스트마다 임시 SQLite 파일 DB 를 쓰고(`tmp_path`), 앱의 DB 세션 · 공급자 의존성을 바꿔 끼운다
- 기능 묶음마다 테스트 파일 하나: `test_auth.py` · `test_team.py` · `test_meeting.py` · `test_todo.py` · `test_comment.py` · `test_activity.py` · `test_platform.py`
- spec 의 Scenario 가 곧 테스트 케이스다. 26개 API 가 모두 한 번 이상 불리는지 OpenAPI 경로 목록과 대조하는 테스트를 둔다
- 업로드 테스트용 mp3 · wav · mp4 앞부분 바이트는 테스트 안에서 만든다 (파일을 저장소에 넣지 않는다)

## Risks / Trade-offs

- [25MB 녹취의 받아쓰기가 60초를 넘을 수 있다] → 1회차는 재기만 한다. 넘으면 다음 회차에 비동기 처리나 길이 제한을 검토한다
- [Vercel 요청 본문 4.5MB 제한] → 배포는 `MAX_UPLOAD_MB=4` (D3). 25MB 가 필요하면 Blob 직접 업로드를 다음 회차에 한다
- [모델이 담당자 · 기한을 지어낼 수 있다] → 프롬프트로 막고, 서버가 멤버 이름과 대조해 아니면 미정으로 둔다
- [기한 판정이 `YYYY-MM-DD` 에만 맞는다] → 날짜로 바꿀 수 없는 글자는 기한 지남으로 보이지 않는다. 사람이 기한 배지로 날짜를 다시 고를 수 있다
- [Vercel 함수 파일시스템은 쓰기 불가] → 배포에서는 반드시 `DATABASE_URL` 이 있어야 한다. 없으면 시작할 때 오류를 내서 SQLite 로 조용히 떨어지지 않게 한다 (`VERCEL` 환경변수로 판별)
- [Tailwind CDN 은 운영용이 아니다] → 정의서가 정한 스택이라 그대로 쓴다. 성능 문제는 범위 밖이다

## Migration Plan

- 새 프로젝트라 옮길 데이터가 없다
- 배포: Vercel 프로젝트 연결 → Neon 연결(Vercel Storage) → 환경변수 등록 → 배포 → `/docs` 와 `/login.html` 확인
- 되돌리기: Vercel 의 이전 배포로 되돌린다 (첫 배포는 프로젝트를 내린다)

## Open Questions

- 기본 `SUMMARY_MODEL` 이름 - 구현 때 OpenAI 문서에서 고른다. spec · 작업 분해에는 영향이 없다
