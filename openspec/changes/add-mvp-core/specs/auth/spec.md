# Spec Delta

## Purpose

이메일과 비밀번호로 가입 · 로그인하고, 발급받은 토큰으로 내 정보를 보고 고치며 로그아웃하는 계정 기능을 정한다.

## ADDED Requirements

### Requirement: 회원가입
<!-- 근거: 스토리보드 B-05 · B-08 · B-09 · B-10 · B-11 / publish/login.html (signup · signup-err-*) -->
시스템은 `POST /api/auth/signup` 으로 이메일 · 비밀번호 · 이름을 받아 계정을 만들고 `201` 과 JWT 를 돌려주어야 한다(SHALL). 비밀번호는 bcrypt 해시로만 저장해야 한다(MUST). 이메일 형식이 틀리면 `400 EMAIL_INVALID`, 비밀번호가 8자 미만이면 `400 PASSWORD_TOO_WEAK`, 이미 있는 이메일이면 `409 EMAIL_DUPLICATED` 를 돌려주어야 한다(SHALL).

#### Scenario: 가입 성공
- **WHEN** 처음 쓰는 이메일 `user@example.com`, 비밀번호 `mypassword`, 이름 `김대리` 로 가입을 요청한다
- **THEN** `201` 과 함께 JWT 가 돌아오고, 저장된 비밀번호는 평문이 아닌 bcrypt 해시다

#### Scenario: 이메일 형식 오류
- **WHEN** 이메일을 `user@@example` 로 보낸다
- **THEN** `400` 과 본문 `{"code":"EMAIL_INVALID","msg":...}` 가 돌아온다

#### Scenario: 약한 비밀번호
- **WHEN** 비밀번호를 `1234` 로 보낸다
- **THEN** `400 PASSWORD_TOO_WEAK` 가 돌아온다

#### Scenario: 중복 이메일
- **WHEN** 이미 가입된 이메일로 다시 가입한다
- **THEN** `409 EMAIL_DUPLICATED` 가 돌아오고 계정은 새로 생기지 않는다

### Requirement: 로그인과 토큰
<!-- 근거: 스토리보드 B-01 · B-02 · B-04 / publish/login.html (login · login-fail · login-ok) -->
시스템은 `POST /api/auth/login` 에서 이메일과 비밀번호가 맞으면 `200` 과 24시간 뒤 만료되는 JWT 를 돌려주어야 한다(SHALL). 토큰 갱신은 없다. 가입 · 로그인 응답 본문은 `token` 과 소속 팀 id `team_id`(없으면 `null`)를 담아야 한다(SHALL). login.html 은 매핑표상 `auth/me` 를 부르지 않으므로 이 값으로 이동할 화면을 정한다. 이메일이 없거나 비밀번호가 틀리면 둘을 구분하지 않고 같은 `401 INVALID_CREDENTIALS` 를 돌려주어야 한다(MUST).

#### Scenario: 로그인 성공
- **WHEN** 가입한 이메일과 맞는 비밀번호로 로그인한다
- **THEN** `200` 과 JWT 가 돌아오고, 토큰의 만료 시각은 발급 시각에서 24시간 뒤다

#### Scenario: 없는 이메일과 틀린 비밀번호가 같은 응답
- **WHEN** 없는 이메일로 한 번, 있는 이메일에 틀린 비밀번호로 한 번 로그인한다
- **THEN** 두 번 모두 `401 INVALID_CREDENTIALS` 와 같은 메시지가 돌아온다

### Requirement: 보호된 API 와 토큰 만료
<!-- 근거: 스토리보드 B-03 · H-01 / publish/login.html (session-expired) -->
`/api/auth/signup` · `/api/auth/login` 을 뺀 모든 API 는 `Authorization: Bearer <JWT>` 가 있어야 한다(SHALL). 토큰이 없거나 위조 · 만료되었으면 모두 `401 TOKEN_EXPIRED` 를 돌려주어야 한다(SHALL). 오류 코드 15종 안에서 고른 값이다 (D12). 화면은 `401 TOKEN_EXPIRED` 를 받으면 저장한 토큰을 지우고 login.html 로 보내 「세션 만료」 알림을 띄워야 한다(SHALL).

#### Scenario: 만료 토큰
- **WHEN** 만료 시각이 지난 토큰으로 `GET /api/auth/me` 를 부른다
- **THEN** `401 TOKEN_EXPIRED` 가 돌아온다

#### Scenario: 화면의 세션 만료 처리
- **WHEN** 화면이 API 를 불렀다가 `401 TOKEN_EXPIRED` 를 받는다
- **THEN** localStorage 의 토큰이 지워지고 login.html 로 이동하며, 붉은 띠 알림 「세션 만료」가 보인다

### Requirement: 내 정보 조회와 수정
<!-- 근거: 스토리보드 J-01 · J-02 · J-03 · J-04 · J-05 · J-06 / publish/profile.html (view · edit-name · pw-mismatch · pw-weak · saving · saved) -->
`GET /api/auth/me` 는 `id · name · email · role` 을 돌려주어야 한다(SHALL). `role` 은 소속 팀에서의 역할(`owner` 또는 `member`)이고 팀이 없으면 `null` 이다. `PUT /api/auth/me` 는 이름과 비밀번호를 각각 선택적으로 받아 보낸 것만 바꾸어야 한다(SHALL). 이메일은 바꿀 수 없다. 새 비밀번호가 8자 미만이면 `400 PASSWORD_TOO_WEAK` 를 돌려주어야 한다. 계정 변경은 활동 기록에 남기지 않아야 한다(MUST NOT 기록).

#### Scenario: 이름만 변경
- **WHEN** `PUT /api/auth/me` 에 이름 `김수석` 만 보낸다
- **THEN** `200` 이 돌아오고 이름만 바뀌며 기존 비밀번호로 계속 로그인된다

#### Scenario: 비밀번호 확인 불일치는 화면에서 거른다
- **WHEN** profile.html 에서 새 비밀번호와 확인 칸을 다르게 입력하고 저장을 누른다
- **THEN** 서버를 부르지 않고 확인 칸 아래에 붉은 오류 글자가 나온다

#### Scenario: 저장 중 버튼 잠금
- **WHEN** 저장 요청이 진행 중이다
- **THEN** 저장 버튼은 비활성이고 「저장 중...」 으로 바뀌어 두 번 눌리지 않는다

#### Scenario: 계정 변경은 활동 기록에 없음
- **WHEN** 이름을 바꾼 뒤 `GET /api/me/activities` 를 부른다
- **THEN** 이름 변경에 해당하는 활동이 없다

### Requirement: 로그아웃
<!-- 근거: 스토리보드 B 엔드포인트 목록 · I-01 (meetings.html) / publish/profile.html 로그아웃 버튼 -->
`POST /api/auth/logout` 은 서버 쪽 블랙리스트 없이 `200` 만 돌려주어야 한다(SHALL). 화면은 이 응답 뒤 저장한 토큰을 지우고 login.html 로 보내야 한다(SHALL). 로그아웃은 profile.html 의 로그아웃 버튼에서 부른다 (D8).

#### Scenario: 로그아웃
- **WHEN** profile.html 에서 로그아웃을 누른다
- **THEN** `POST /api/auth/logout` 이 `200` 을 돌려주고, 토큰이 지워지며 login.html 로 이동한다

### Requirement: 로그인 · 가입 화면 동작
<!-- 근거: 스토리보드 B-01 ~ B-11 / publish/login.html -->
login.html 은 로그인과 회원가입 두 모드를 한 화면에서 바꾸어야 한다(SHALL). 이름 · 초대코드 칸은 회원가입 모드에서만 보인다. 제출 전에는 오류를 띄우지 않고, 이메일 형식과 비밀번호 8자는 화면에서 먼저 거른다. 요청 중에는 제출 버튼을 잠근다. 가입 때 초대코드를 넣었으면 가입 성공 뒤 `POST /api/teams/join` 을 부르고, 합류가 `404 INVITE_NOT_FOUND` 로 실패하면 계정은 유지한 채 초대코드 칸에 오류를 보이고 team.html 로 보낸다. 로그인 · 가입이 성공하면 토큰을 localStorage 에 저장하고, 소속 팀이 있으면 meetings.html, 없으면 team.html 로 보낸다.

#### Scenario: 회원가입 모드 전환
- **WHEN** 로그인 화면에서 「회원가입」 링크를 누른다
- **THEN** 제목이 「회원가입」 으로 바뀌고 이름 · 초대코드(선택) 칸이 나타나며 버튼이 「가입하기」 가 된다

#### Scenario: 처리 중 잠금
- **WHEN** 가입하기를 누르고 응답을 기다린다
- **THEN** 버튼은 「처리 중...」 이고 비활성이다

#### Scenario: 초대코드가 틀린 가입
- **WHEN** 초대코드 `MN-0000` 으로 가입한다
- **THEN** 계정은 만들어지고, 초대코드 칸에 「없는 초대코드」 오류가 나타난 뒤 team.html 의 소속 팀 없음 화면으로 간다

#### Scenario: 팀이 없는 사람의 로그인
- **WHEN** 소속 팀이 없는 계정으로 로그인한다
- **THEN** team.html 의 팀 만들기 / 합류 화면으로 간다
