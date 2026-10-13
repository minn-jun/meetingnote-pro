# Proposal

## Why

기초편 MeetingNote 는 혼자 쓰는 회의록 정리기라서, 팀 리더 · 팀원 · 신규 합류자가 같은 회의록과 할 일을 함께 보고 추적할 수 없다. 개발 전에 정의서 · 스토리보드 · 디자인 시스템 · 퍼블리싱이 모두 준비되었으므로, 이를 그대로 입력으로 삼아 1회차에 「로그인한 팀이 함께 쓰는 회의록」의 MVP 를 한 번에 만든다.

## What Changes

- 이메일 · 비밀번호 회원가입과 로그인을 만든다. 비밀번호는 bcrypt 로 해시하고, 로그인하면 24시간짜리 JWT 를 발급한다. 내 정보 조회 · 수정 · 로그아웃을 포함한다 (API 5)
- 팀을 만든다. 팀 생성 · 조회 · 초대코드 발급과 재발급 · 합류 · 멤버 목록 · 팀 이름 변경을 넣고, 권한은 owner / member 둘만 둔다. 한 사람은 팀 하나에만 속하고, 팀은 6명까지다 (API 6)
- 회의록을 만든다. mp3 · wav 녹취를 올려 받아쓰고, 저장할 때 요약 · 결정사항 · 할 일 3항목으로 나눈다. 회의록 CRUD 와 제목 · 참석자 검색, 기간 필터를 넣는다 (API 6)
- 할 일 칸반을 만든다. 대기 · 진행 · 완료 3열 사이를 끌거나 눌러서 옮기고, 담당자 · 기한을 바꾸고, owner 가 삭제한다 (API 4)
- 회의록에 댓글을 달고 지운다. 지우기는 쓴 사람과 owner 만 할 수 있다 (API 3)
- 팀 활동과 내 활동을 기록하고 보여 준다. kind 는 5종으로 고정한다 (API 2)
- 공통 기반을 만든다. 오류 본문을 `{code, msg}` 로 통일하고, Swagger UI(`/docs`)에서 API 를 직접 불러 볼 수 있게 한다. 화면 6종은 publish 폴더의 확정 디자인과 theme.js 규칙대로 제공하고, 로컬은 SQLite · 배포는 Vercel + Neon Postgres 로 같은 코드를 쓴다
- 화면과 API 의 연결은 스토리보드 매핑표(I-01)를 따른다
- 자세한 잠정 결정은 `docs/결정사항.md` D1~D11 에 있다

### Out of Scope

정의서 4장에서 「안 만들기로 한 것」이다. 없어서 못 만든 것이 아니다.

- 브라우저 실시간 녹음 (파일 업로드만 받는다)
- 화자 자동 구분 (본문은 단일 블록이다)
- 캘린더 연동 · 메일 발송 같은 외부 연동
- owner / member 외의 권한 등급
- 25MB 를 넘는 파일의 분할 업로드
- 푸시 알림 (활동 기록 화면 표시까지만 한다)
- 사람당 여러 팀 소속 (D5)
- Vercel Blob 직접 업로드 (배포 환경 업로드 상한은 D3 대로 4MB)

## Capabilities

### New Capabilities

- `auth`: 회원가입 · 로그인 · JWT 발급과 만료 · 내 정보 조회와 수정 · 로그아웃, 그리고 login.html · profile.html 의 계정 부분 화면 동작
- `team`: 팀 생성 · 조회 · 초대코드 발급과 재발급 · 합류 · 정원 6명 · 멤버 목록 · 팀 이름 변경 · owner 권한, 그리고 team.html 화면 동작
- `meeting`: 녹취 업로드와 받아쓰기 · 3항목 구분 · 회의록 생성 · 조회 · 수정 · 삭제 · 검색과 기간 필터, 그리고 meetings.html · detail.html 의 회의록 부분 화면 동작
- `todo`: 할 일 목록(팀 · 나) · 상태 변경 · 담당자와 기한 변경 · 삭제 · 기한 지남 표시, 그리고 todos.html 칸반과 detail.html 할 일 칸 화면 동작
- `comment`: 회의록 댓글 등록 · 목록 · 삭제와 삭제 권한 판정, 그리고 detail.html 댓글 칸 화면 동작
- `activity`: 활동 기록 kind 5종 · 서버가 만드는 문장 · 팀 활동과 내 활동 조회, 그리고 team.html · profile.html 의 활동 칸 화면 동작
- `platform`: API 공통 규약(`/api/` 접두사 · `{code, msg}` 오류 본문 · 시각 형식) · Swagger UI · 화면 제공과 디자인 규칙 · DB 전환 · 배포

### Modified Capabilities

(없음. 기존 spec 이 없는 새 프로젝트다)

## Impact

- 새 코드: FastAPI 백엔드, Vanilla JS + Tailwind CDN 프론트엔드(화면 6종 + theme.js), pytest 테스트
- 새 의존성: FastAPI · uvicorn · SQLAlchemy · Postgres 드라이버 · bcrypt · JWT 라이브러리 · google-genai SDK · pytest 계열
- 외부 시스템: Google Gemini 받아쓰기 · 3항목 구분(`STT_API_KEY`), Vercel 배포, Neon Postgres(Vercel Storage)
- 환경변수: `JWT_SECRET` · `STT_API_KEY` · `STT_MODEL` · `SUMMARY_MODEL` · `DATABASE_URL` · `MAX_UPLOAD_MB` · `CORS_ORIGINS`
- publish 폴더는 그대로 두고 참조만 한다. 구현 화면은 별도 폴더에 만든다
