# Spec Delta

## Purpose

모든 기능이 함께 따르는 API 규약 · Swagger UI · 화면 제공과 디자인 규칙 · 데이터베이스 전환 · 배포 조건을 한곳에 정한다.

## ADDED Requirements

### Requirement: API 공통 규약
<!-- 근거: 정의서 7 · 7-2 · 8-1 (Examples) / 스토리보드 I-01 -->
모든 API 경로는 `/api/` 로 시작해야 한다(MUST). 정의서의 26개 경로 밖의 API 는 만들지 않는다. 오류 응답 본문은 언제나 `{"code": "...", "msg": "..."}` 이고 `msg` 는 한국어다. 오류 코드는 `EMAIL_INVALID` · `PASSWORD_TOO_WEAK` · `TOKEN_EXPIRED` · `INVITE_NOT_FOUND` · `MEETING_NOT_FOUND` · `EMAIL_DUPLICATED` · `TEAM_FULL` · `PAYLOAD_TOO_LARGE` · `UNSUPPORTED_MEDIA_TYPE` · `INVALID_CREDENTIALS` · `FORBIDDEN` · `OWNER_ONLY` · `VALIDATION_ERROR` · `NOT_FOUND` 14종에 외부 공급자 실패용 `UPSTREAM_ERROR` 를 더한 15종만 쓴다 (D12). 요청 형식이 틀린 경우(필드 누락 · 형 오류)도 `400 VALIDATION_ERROR` 로 돌려준다. 시각은 ISO 8601 UTC 로 저장하고 주고받으며, 화면은 현지 시간으로 보인다.

#### Scenario: 요청 형식 오류도 같은 본문
- **WHEN** 필수 필드가 빠진 JSON 으로 아무 API 를 부른다
- **THEN** `400` 과 `{"code":"VALIDATION_ERROR","msg":...}` 가 돌아온다 (프레임워크 기본 422 형식이 아니다)

#### Scenario: 시각 형식
- **WHEN** 회의록 단건을 부른다
- **THEN** `met_at` · `created_at` 이 `Z` 로 끝나는 ISO 8601 문자열이다

### Requirement: Swagger UI 로 API 를 직접 시험
<!-- 근거: 사용자 지시 2026-10-06 (docs/결정사항.md D9) -->
서버는 `/docs` 에 Swagger UI 를, `/openapi.json` 에 OpenAPI 문서를 제공해야 한다(SHALL). 26개 API 는 모두 Auth · Team · Meeting · Todo · Comment · Activity 태그로 묶이고 요청 · 응답 스키마가 보여야 한다. Bearer 인증이 등록되어 Authorize 에 로그인 토큰을 넣으면 보호된 API 를 Swagger 에서 바로 부를 수 있어야 한다(SHALL). `POST /api/upload` 는 파일 선택 칸으로 보여야 한다. 환경변수로 끌 수 있지만 기본은 켜짐이다.

#### Scenario: 문서 화면
- **WHEN** 서버를 띄우고 `/docs` 를 연다
- **THEN** Swagger UI 가 열리고 6개 태그 아래 26개 API 가 보인다

#### Scenario: 토큰으로 보호된 API 호출
- **WHEN** Swagger 에서 로그인해 받은 토큰을 Authorize 에 넣고 `GET /api/auth/me` 를 실행한다
- **THEN** `200` 과 내 정보가 돌아온다

### Requirement: 화면 제공
<!-- 근거: 정의서 7-2 (정적 파일 경로) · 스토리보드 H-01 / publish/index.html -->
서버는 화면 6종을 `/login.html` · `/meetings.html` · `/detail.html` · `/todos.html` · `/team.html` · `/profile.html` 처럼 확장자를 붙인 경로로 제공해야 한다(SHALL). `/` 는 `/login.html` 로 보낸다. 화면 경로가 `/api/` · `/docs` · `/openapi.json` 을 가리면 안 된다(MUST NOT). 상세 화면은 `/detail.html?id=<회의록 id>` 로 연다. 로그인하지 않은 채 login.html 밖 화면을 열면 login.html 로 보낸다.

#### Scenario: 루트 진입
- **WHEN** `/` 를 연다
- **THEN** `/login.html` 로 이동한다

#### Scenario: 문서 경로는 가려지지 않음
- **WHEN** 화면 제공이 켜진 상태에서 `/docs` 를 연다
- **THEN** Swagger UI 가 열린다

### Requirement: 확정 디자인과 디자인 규칙
<!-- 근거: 디자인시스템 2 · 3 · 5 · 스토리보드 G-01 / publish/theme.js · publish/components.html (docs/결정사항.md D1) -->
화면은 publish 폴더의 구조 · 색 · 문구를 따르고, 화면을 새로 디자인하지 않아야 한다(MUST). 색 · 클래스는 theme.js 한 곳에서만 정의하고 화면은 `window.UI` · `STRIPE` · `LABEL` · `notice` 의 이름만 쓴다. 지켜야 할 규칙은 다음과 같다(MUST).

- 카드 배경은 무채색이다. 색은 좌측 6px 띠와 라벨 글자에만 둔다
- 버튼 높이는 44px(`h-11`) 하나다
- 모서리는 카드 `rounded-xl` · 패널 `rounded-2xl` 둘이다
- `!important` · 마크업 `style` 속성 · theme.js 에 없는 색 · 새 모서리 값 · 화면에서 만든 클래스 조합을 쓰지 않는다. 진행률 · 끌기 좌표처럼 실행 중에 바뀌는 값만 JS 로 `element.style` 을 설정할 수 있다
- 라이트 / 다크 테마 전환(theme.js `initTheme`)을 모든 화면에 둔다
- 퍼블리싱 확인용 STATE 바 · note 줄 · API 경로가 적힌 토스트는 구현 화면에 넣지 않는다
- 오류 · 알림 메시지는 스토리보드의 존댓말 문장을 쓴다

#### Scenario: 버튼 높이
- **WHEN** 구현된 화면 6종의 모든 버튼 요소를 잰다
- **THEN** 카드 안 배지형 버튼을 뺀 모든 버튼 높이가 44px 이다

#### Scenario: 확인용 요소 없음
- **WHEN** 구현된 화면을 연다
- **THEN** 보라색 STATE 바와 「퍼블리싱 확인용」 note 줄이 없다

### Requirement: 360px 반응형
<!-- 근거: 스토리보드 N-01 / publish/meetings.html · publish/detail.html · publish/todos.html -->
화면 6종은 너비 360px 에서 가로 스크롤 없이, 글자가 잘리지 않고 보여야 한다(SHALL). 회의록 카드는 한 열로, 상세의 3단은 세로로, 칸반의 3열은 세로로 쌓인다.

#### Scenario: 360px 칸반
- **WHEN** todos.html 을 360px 너비로 연다
- **THEN** 가로 스크롤이 없고 3열이 세로로 쌓인다

### Requirement: 데이터베이스 전환과 배포
<!-- 근거: 정의서 6 · 9 · 스토리보드 H-01 (docs/결정사항.md D3) -->
같은 코드가 환경변수 `DATABASE_URL` 이 있으면 Postgres(Neon), 없으면 로컬 SQLite 파일을 써야 한다(SHALL). 비밀 값(`JWT_SECRET` · `STT_API_KEY` · `DATABASE_URL`)은 `.env` 또는 배포 환경변수로만 읽고 코드와 저장소에 넣지 않는다(MUST NOT). 로컬 SQLite 파일과 `.env` 는 git 에서 뺀다. CORS 는 `CORS_ORIGINS` 에 적은 도메인만 허용한다. 배포는 Vercel 한 프로젝트로 화면과 API 를 함께 낸다.

#### Scenario: DB 전환
- **WHEN** `DATABASE_URL` 없이 서버를 띄운다
- **THEN** 로컬 SQLite 파일에 테이블 7개가 만들어진다

#### Scenario: 허용하지 않은 출처
- **WHEN** `CORS_ORIGINS` 에 없는 출처에서 API 를 부른다
- **THEN** 응답에 그 출처를 허용하는 CORS 헤더가 없다

### Requirement: 응답 성능
<!-- 근거: 정의서 8-1 (Metrics) · 9 (성능) -->
받아쓰기 · 3항목 구분 · 회원가입 · 로그인을 뺀 API 는 로컬에서 100ms 안에 응답해야 한다(SHALL). 회원가입 · 로그인은 bcrypt 비용 때문에 250ms 안이다.

#### Scenario: 목록 응답 시간
- **WHEN** 회의록 30건 · 할 일 100건이 있는 팀의 회의록 목록과 할 일 목록을 로컬에서 부른다
- **THEN** 각각 100ms 안에 응답한다
