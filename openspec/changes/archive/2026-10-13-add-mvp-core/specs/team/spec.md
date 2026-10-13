# Spec Delta

## Purpose

팀을 만들고 초대코드 하나로 멤버를 모으며, owner 와 member 두 권한으로 팀 설정을 관리하는 기능을 정한다.

## ADDED Requirements

### Requirement: 팀 생성
<!-- 근거: 스토리보드 F-02 / publish/team.html (onboard 팀 만들기) -->
`POST /api/teams` 는 팀 이름을 받아 팀을 만들고 `201` 과 팀(`id · name · invite_code · role`)을 돌려주어야 한다(SHALL). 만든 사람은 그 팀의 owner 가 된다. 초대코드는 `MN-` 뒤에 영문 대문자 · 숫자 4자리를 붙인 형식(예: `MN-7K2D`)이고 모든 팀에서 유일해야 한다(MUST). 이미 팀에 속한 사람이 팀을 만들면 `400 VALIDATION_ERROR` 를 돌려주어야 한다 (D5). 팀 생성은 활동 기록에 남기지 않는다 (D6).

#### Scenario: 팀 생성 성공
- **WHEN** 팀이 없는 사람이 이름 `기획팀` 으로 팀을 만든다
- **THEN** `201` 과 함께 `role` 이 `owner` 이고 `invite_code` 가 `MN-` 뒤에 영문 대문자 · 숫자 4자리가 붙은 형식인 팀이 돌아온다

#### Scenario: 두 번째 팀은 만들 수 없음
- **WHEN** 이미 팀이 있는 사람이 팀을 하나 더 만든다
- **THEN** `400 VALIDATION_ERROR` 가 돌아오고 팀은 생기지 않는다

### Requirement: 내 팀 조회
<!-- 근거: 스토리보드 F-01 · F-02 / publish/team.html (team · onboard) -->
`GET /api/teams` 는 내가 속한 팀을 배열로 돌려주어야 한다(SHALL). 한 사람은 팀 하나에만 속하므로 배열은 0건 또는 1건이다 (D5). 항목은 `id · name · invite_code · role · member_count` 를 담는다.

#### Scenario: 팀이 없는 사람
- **WHEN** 팀이 없는 사람이 `GET /api/teams` 를 부른다
- **THEN** `200` 과 빈 배열이 돌아온다

### Requirement: 초대코드로 합류
<!-- 근거: 스토리보드 F-03 · F-06 · B-11 / publish/team.html (join-err · full), publish/login.html (signup-err-invite) -->
`POST /api/teams/join` 은 초대코드를 받아 그 팀의 member 로 넣고 `200` 과 팀을 돌려주어야 한다(SHALL). 없는 코드(재발급으로 폐기된 코드 포함)면 `404 INVITE_NOT_FOUND`, 팀이 이미 6명이면 `409 TEAM_FULL`, 이미 팀이 있는 사람이면 `400 VALIDATION_ERROR` 를 돌려주어야 한다(SHALL). 합류에 성공하면 활동 기록 `member_join` 을 남겨야 한다(SHALL).

#### Scenario: 합류 성공
- **WHEN** 팀이 없는 사람이 `MN-7K2D` 로 합류한다
- **THEN** `200` 이 돌아오고 멤버 목록에 role `member` 로 나타나며 팀 활동 기록에 `member_join` 이 생긴다

#### Scenario: 없는 초대코드
- **WHEN** `MN-0000` 으로 합류한다
- **THEN** `404 INVITE_NOT_FOUND` 가 돌아오고 계정은 그대로 남는다

#### Scenario: 정원 초과
- **WHEN** 멤버가 6명인 팀의 코드로 7번째 사람이 합류한다
- **THEN** `409 TEAM_FULL` 이 돌아온다

### Requirement: 멤버 목록
<!-- 근거: 스토리보드 F-01 / publish/team.html (members) -->
`GET /api/teams/{id}/members` 는 `id · name · email · role · todo_count` 배열을 돌려주어야 한다(SHALL). `todo_count` 는 그 사람이 담당인 할 일 수다. 그 팀의 멤버가 아니면 `403 FORBIDDEN`, 없는 팀이면 `404 NOT_FOUND` 를 돌려주어야 한다. 이 규칙(팀 멤버만 팀 자원에 접근)은 `{id}` 가 팀인 모든 API 에 같이 적용된다.

#### Scenario: 멤버 목록 조회
- **WHEN** 멤버 4명인 팀의 멤버가 목록을 부른다
- **THEN** 4건이 돌아오고 각 항목에 `todo_count` 가 있다

#### Scenario: 다른 팀은 볼 수 없음
- **WHEN** 다른 팀의 멤버 목록을 부른다
- **THEN** `403 FORBIDDEN` 이 돌아온다

### Requirement: 초대코드 재발급과 팀 이름 변경은 owner 만
<!-- 근거: 스토리보드 F-05 · F-07 · F-08 / publish/team.html (recode · save-name · member-view) -->
`PUT /api/teams/{id}/code` 는 새 초대코드를 만들어 돌려주고 앞의 코드를 폐기해야 한다(SHALL). 이미 합류한 멤버는 그대로다. `PUT /api/teams/{id}` 는 팀 이름을 바꾼다. 두 API 모두 owner 가 아니면 `403 OWNER_ONLY` 를 돌려주어야 한다(MUST).

#### Scenario: 재발급 뒤 옛 코드는 무효
- **WHEN** owner 가 코드를 재발급한 뒤 누군가 옛 코드로 합류한다
- **THEN** `404 INVITE_NOT_FOUND` 가 돌아오고, 새 코드로는 합류된다

#### Scenario: member 의 팀 이름 변경
- **WHEN** member 가 `PUT /api/teams/{id}` 를 부른다
- **THEN** `403 OWNER_ONLY` 가 돌아오고 이름은 그대로다

### Requirement: 팀 설정 화면 동작
<!-- 근거: 스토리보드 F-01 ~ F-08 / publish/team.html -->
team.html 은 팀이 없으면 팀 만들기와 초대코드 합류 두 칸을 보이고, 팀이 있으면 팀 이름 · 초대코드(복사 · 재발급) · 멤버(현재 수 / 6) · 활동 기록을 보여야 한다(SHALL). 복사는 클립보드에 코드를 넣고 초록 띠 알림 「초대코드를 복사함」을 띄운다. 재발급은 주황 띠 알림으로 옛 코드가 무효임을 알린다. member 로 들어오면 팀 이름 칸 · 복사 · 재발급 · 이름 저장을 잠그고 읽기만 하게 한다. 소속 팀이 없는 사람은 다른 화면에 들어가면 team.html 로 보낸다.

#### Scenario: member 의 읽기 전용 화면
- **WHEN** member 가 team.html 을 연다
- **THEN** 팀 이름 칸은 읽기 전용이고 복사 · 재발급 · 이름 저장 버튼이 비활성이다

#### Scenario: 팀 없는 사람의 회의록 진입
- **WHEN** 팀이 없는 사람이 meetings.html 을 연다
- **THEN** team.html 의 「아직 소속 팀이 없음」 화면으로 이동한다
