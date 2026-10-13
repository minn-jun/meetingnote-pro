# Tasks

## 1. 뼈대와 공통 기반

- [x] 1.1 `pyproject.toml` 에 의존성(fastapi · uvicorn · sqlalchemy · psycopg · pyjwt · bcrypt · python-multipart · python-dotenv · google-genai · pytest · httpx)과 Vercel entrypoint 를 적고, `pip install -e .[dev]` 가 성공하는지 확인한다
- [x] 1.2 `.gitignore` 에 `.env` · `meetingnote.db` · `__pycache__` · `.pytest_cache` 를 더하고 `.env.example`(JWT_SECRET · STT_API_KEY · STT_MODEL · SUMMARY_MODEL · DATABASE_URL · MAX_UPLOAD_MB · CORS_ORIGINS · DOCS_ENABLED)을 만든다. `git status` 에 `.env` 가 보이지 않는지 확인한다
- [x] 1.3 `app/config.py` · `app/db.py` 를 만든다. `DATABASE_URL` 유무로 Postgres / SQLite 를 고르고, Vercel 환경에서 `DATABASE_URL` 이 없으면 시작 오류를 낸다. 단위 테스트로 두 분기와 `postgres://` 변환을 확인한다
- [x] 1.4 `app/models.py` 에 테이블 7개를 정의(memberships.user_id UNIQUE, meetings 삭제 시 todos · comments cascade)하고, 빈 SQLite 에 `create_all` 뒤 테이블 7개가 생기는지 테스트로 확인한다
- [x] 1.5 `app/errors.py`(오류 코드 15종 · ApiError)와 `app/main.py` 의 처리기(ApiError → `{code,msg}`, 요청 검증 오류 → `400 VALIDATION_ERROR`)를 만들고, `test_platform.py` 에서 필드 누락 요청이 `400 VALIDATION_ERROR` 본문으로 오는지 확인한다
- [x] 1.6 시각을 UTC 로 저장하고 `Z` 로 끝나는 ISO 문자열로 내보내는 공통 직렬화를 만들고 테스트로 형식을 확인한다
- [x] 1.7 CORS(`CORS_ORIGINS`)와 Swagger(`/docs` · `/openapi.json` · HTTPBearer 보안 스키마 · `DOCS_ENABLED`)를 설정하고, 테스트로 `/docs` 200 과 허용하지 않은 출처의 CORS 헤더 부재를 확인한다
- [x] 1.8 pytest 공통 fixture(`tests/conftest.py`: 임시 SQLite · TestClient · 가짜 AI 공급자 · 가입 / 팀 생성 도우미)를 만들고 `pytest` 가 0건 실패로 도는지 확인한다

## 2. 인증 (specs/auth)

- [x] 2.1 bcrypt 해시 · JWT 발급(24h) · 검증 의존성(없음 · 위조 · 만료 → `401 TOKEN_EXPIRED`)을 만들고 단위 테스트로 만료 토큰을 확인한다
- [x] 2.2 `POST /api/auth/signup` · `POST /api/auth/login` (응답 `{token, team_id}`, 오류 EMAIL_INVALID · PASSWORD_TOO_WEAK · EMAIL_DUPLICATED · INVALID_CREDENTIALS)을 만들고 `test_auth.py` 로 spec 시나리오(가입 성공 · 형식 오류 · 약한 비밀번호 · 중복 · 로그인 성공 · 없는 이메일과 틀린 비밀번호 같은 응답 · 해시 저장)를 확인한다
- [x] 2.3 `GET /api/auth/me` · `PUT /api/auth/me` · `POST /api/auth/logout` 을 만들고 테스트로 role(팀 없음 `null`) · 이름만 변경 · 약한 새 비밀번호 · 로그아웃 200 · 계정 변경이 활동에 없음을 확인한다
- [x] 2.4 모든 auth API 에 Auth 태그와 요청 · 응답 스키마를 달고 `/openapi.json` 에 5개가 Auth 태그로 있는지 테스트로 확인한다

## 3. 팀 (specs/team)

- [x] 3.1 팀 멤버 확인 · owner 확인 의존성(`403 FORBIDDEN` · `403 OWNER_ONLY` · `404 NOT_FOUND`)과 초대코드 생성기(`MN-` + 대문자 · 숫자 4자리, 유일)를 만들고 단위 테스트로 형식과 중복 회피를 확인한다
- [x] 3.2 `POST /api/teams` · `GET /api/teams` · `POST /api/teams/join` 을 만들고 `test_team.py` 로 생성(owner) · 두 번째 팀 금지 · 빈 배열 · 합류 성공(member_join 생김) · 없는 코드 404 · 정원 초과 409 · 이미 팀 있음 400 을 확인한다
- [x] 3.3 `GET /api/teams/{id}/members`(todo_count 포함) · `PUT /api/teams/{id}/code` · `PUT /api/teams/{id}` 를 만들고 테스트로 다른 팀 403 · 재발급 뒤 옛 코드 404 · member 의 이름 변경 403 OWNER_ONLY 를 확인한다

## 4. 회의록 (specs/meeting)

- [x] 4.1 `app/ai.py` 공급자 인터페이스(transcribe · split)와 Gemini 구현을 만든다. 기본 모델 이름을 Gemini 문서로 확인해 `.env.example` 에 적고, 공급자 예외가 `502 UPSTREAM_ERROR` 로 바뀌는지 가짜 공급자 테스트로 확인한다
- [x] 4.2 업로드 형식 판정(wav · mp3 앞 바이트)과 크기 상한(`MAX_UPLOAD_MB`)을 만들고 `POST /api/upload` 를 붙인다. 테스트로 wav · mp3 통과, 확장자만 mp3 인 mp4 → 415, 상한 초과 → 413 을 확인한다
- [x] 4.3 `POST /api/teams/{id}/meetings` 를 만든다(필수 검증 · split 결과 저장 · 담당자 이름 대조 · 할 일 OPEN · meeting_add 기록 · 구분 실패 시 저장 안 함). 테스트로 저장과 구분 · 멤버가 아닌 담당자 null · 필수 누락 400 · 구분 실패 502 와 회의록 0건을 확인한다
- [x] 4.4 `GET /api/teams/{id}/meetings` 를 만든다(집계 3종 · met_at 내림차순 · body 없음 · `q` 는 제목 · 참석자만 · `from` / `to`). 테스트로 본문 낱말 검색 0건 · 참석자 검색 · body 부재 · 기간 필터 · decision_count 빈 줄 제외를 확인한다
- [x] 4.5 `GET` · `PUT` · `DELETE /api/meetings/{id}` 를 만든다(단건에 body · todos, 수정은 재구분 안 함, 수정 · 삭제는 쓴 사람과 owner, cascade, MEETING_NOT_FOUND). 테스트로 시나리오 4개(단건 내용 · 딸린 것까지 삭제 · 다른 member 403 · 없는 회의록 404)를 확인한다

## 5. 할 일 (specs/todo)

- [x] 5.1 `GET /api/teams/{id}/todos` · `GET /api/me/todos` 를 만들고(meeting_title 포함, 상태 순 다음 due_text 정렬) `test_todo.py` 로 정렬 · 내 할 일 거르기 · 빈 배열을 확인한다
- [x] 5.2 `PUT /api/todos/{id}` 를 만든다(보낸 필드만, 상태 3값 · 되돌리기 허용, 담당자 멤버 검증, todo_assign · todo_done 기록). 테스트로 완료 이동과 todo_done · 담당자 배정과 todo_assign · CLOSED 400 · 멤버 아닌 담당자 400 · 다른 팀 403 · 없는 할 일 404 를 확인한다
- [x] 5.3 `DELETE /api/todos/{id}` 를 owner 전용으로 만들고 테스트로 owner 204 · member 403 OWNER_ONLY 를 확인한다

## 6. 댓글 (specs/comment)

- [x] 6.1 `POST` · `GET /api/meetings/{id}/comments` · `DELETE /api/comments/{id}` 를 만든다(1~500자, created_at 오름차순, can_delete 서버 판정, comment_add 기록). `test_comment.py` 로 등록과 comment_add · 501자 400 · can_delete(member · owner 관점) · 남의 댓글 삭제 403 · 없는 댓글 404 · 다른 팀 회의록 403 을 확인한다

## 7. 활동 기록 (specs/activity)

- [x] 7.1 `app/activity.py`(kind 5종 외 거부 · target 저장 · 조회 시 완성 문장 만들기)와 `GET /api/teams/{id}/activities` · `GET /api/me/activities`(최근 순 50건)를 만들고, `test_activity.py` 로 정해진 kind 만 생김 · 60건 중 최근 50건 · 문장에 회의록 제목 포함 · 내 활동은 내가 행위자인 것만을 확인한다

## 8. 화면 공통 (specs/platform)

- [x] 8.1 `frontend/theme.js` 를 publish 에서 옮기고 D1 대로 정리한다: 반복 조합을 이름으로 등록(헤더 · nav · 탭 · 카드 안 배지 `tag` · 작은 select · 칸 고르기 버튼 · 빨간 글자 고스트 버튼 등), `stateBar` 삭제. `publish/` 는 그대로인지 `git diff --stat publish` 로 확인한다
- [x] 8.2 `frontend/app.js` 를 만든다: 토큰 저장 · `api()`(Bearer · `{code,msg}` 해석 · TOKEN_EXPIRED 처리) · 로그인 확인 · 현재 팀 · 공통 헤더 · 시각 현지 표시 · 기한 지남 판정 · 기한 배지 순환 · 오류 코드 → 존댓말 문장 표. 기한 판정과 배지 순환은 브라우저 콘솔에서 날짜 몇 개로 결과를 확인한다
- [x] 8.3 StaticFiles 마운트(`/` → `/login.html` 리다이렉트, API · `/docs` 를 가리지 않음)를 붙이고 테스트로 `/` 리다이렉트 · `/login.html` 200 · `/docs` 200 을 확인한다
- [x] 8.4 화면 규칙 검사 테스트를 만든다: frontend 의 HTML · JS 에 `!important` · 마크업 `style="` · `h-9` · `h-10` · `stateBar` · 「퍼블리싱 확인용」이 없는지 grep 으로 확인한다

## 9. 화면 6종 (매핑표 I-01 대로 API 연결)

- [x] 9.1 `login.html`: publish 마크업을 옮기고 signup · login · teams/join 만 부른다. 로그인 / 가입 모드 · 화면 선검증 · 처리 중 잠금 · 초대코드 실패 처리 · `?expired=1` 세션 만료 알림 · team_id 로 이동 분기를 서버를 띄워 브라우저에서 확인한다
- [x] 9.2 `meetings.html`: auth/me · teams/{id}/meetings(GET · POST) · upload 를 부른다. 카드 띠 순환 · 빈 상태 · 검색 0건 · 업로드 진행 · 415 · 413 알림 · 정리 중 잠금 · 저장 뒤 비움을 브라우저에서 확인한다
- [x] 9.3 `detail.html`: meetings/{id}(GET · PUT · DELETE) · todos/{id}(PUT) · 댓글 3개 + 담당자 선택지용 members(D8 예외)를 부른다. 3단 · 결정사항 번호 · 빈 칸 문구 · 본문 접힘 · 삭제 확인 · 404 이동 · can_delete 에 따른 삭제 버튼을 브라우저에서 확인한다
- [x] 9.4 `todos.html`: teams/{id}/todos · me/todos · todos/{id}(PUT · DELETE) + members(D8 예외)를 부른다. 탭 · 필터(서버 재호출 없음) · 포인터 끌기와 실패 되돌림 · 눌러서 칸 고르기 · 담당자 · 기한 배지 · owner 만 삭제 배지 · 기한 지남 붉은 띠 · 빈 상태를 브라우저에서 확인한다
- [x] 9.5 `team.html`: teams(POST · GET) · teams/{id}(PUT) · teams/join · members · code · activities 를 부른다. 소속 팀 없음 화면 · 합류 오류 · 복사 · 재발급 · 정원 초과 · member 읽기 전용 · kind 별 띠 색을 브라우저에서 확인한다
- [x] 9.6 `profile.html`: auth/me(GET · PUT) · me/todos · me/activities + logout(D8 예외)을 부른다. 이름 변경 · 비밀번호 불일치(서버 호출 없음) · 약한 비밀번호 · 저장 중 잠금 · 활동 없음 · 로그아웃 이동을 브라우저에서 확인한다
- [x] 9.7 화면 6종을 360px 너비로 열어 가로 스크롤이 없고 카드 · 3단 · 칸반이 세로로 쌓이는지, 라이트 / 다크 전환이 되는지 브라우저에서 확인한다

## 10. 배포

- [x] 10.1 Vercel 설정(entrypoint · 환경변수 목록 · `MAX_UPLOAD_MB=4`)을 Vercel 문서로 확인해 적고, `README.md` 에 로컬 실행(`uvicorn app.main:app --reload` → http://127.0.0.1:8000) · `/docs` 사용법 · 배포 절차를 쓴다. README 의 로컬 실행 명령이 그대로 도는지 확인한다

## 11. 통합 확인

- [x] 11.1 OpenAPI 경로 목록이 정의서의 26개와 정확히 같고 각 경로가 테스트에서 한 번 이상 불리는지 대조하는 테스트를 돌려 통과를 확인한다
- [x] 11.2 응답 성능 테스트(회의록 30건 · 할 일 100건에서 목록 API 100ms 안, 가입 · 로그인 250ms 안)를 돌려 통과를 확인한다
- [x] 11.3 전체 `pytest -v` 를 돌려 통과 · 실패 수와 실패 내용을 그대로 사용자에게 보고한다
- [x] 11.4 【사람 확인 · 수락】 로컬 서버를 띄워 브라우저에서 사용자 여정(스토리보드 A-01: 가입 → 팀 생성 · 다른 계정 초대코드 합류 → 녹취 업로드 → 3항목 확인 → 담당자 배정 → 칸반 이동)을 따라가고, `/docs` 에서 Authorize 후 API 를 직접 불러 본다. 화면이 publish 와 같게 보이고 여정이 막힘없이 끝나면 사용자가 이 항목을 체크한다 (Claude 는 체크하지 않는다)
