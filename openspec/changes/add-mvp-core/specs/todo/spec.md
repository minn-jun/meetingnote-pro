# Spec Delta

## Purpose

회의록에서 뽑힌 할 일을 대기 · 진행 · 완료 칸반으로 추적하고, 담당자와 기한을 바꾸며 완료까지 따라가는 기능을 정한다.

## ADDED Requirements

### Requirement: 할 일 목록
<!-- 근거: 스토리보드 E-01 · E-02 · J-01 / publish/todos.html (mine · all), publish/profile.html (내 할 일) -->
`GET /api/teams/{id}/todos` 는 팀의 모든 할 일을, `GET /api/me/todos` 는 내가 담당인 할 일만 돌려주어야 한다(SHALL). 항목은 `id · what · assignee_id · assignee_name · due_text · status · meeting_id · meeting_title` 이다. 정렬은 상태(`OPEN` · `DOING` · `DONE` 순) 다음 `due_text` 오름차순이다. 결과가 없으면 `200` 과 빈 배열이다. 담당자가 미정이면 `assignee_id` · `assignee_name` 은 `null` 이다.

#### Scenario: 팀 전체에는 회의록 제목이 함께
- **WHEN** 팀 할 일 목록을 부른다
- **THEN** 각 항목에 `meeting_title` 이 있고 `OPEN` 항목이 `DOING` · `DONE` 보다 앞에 온다

#### Scenario: 내 할 일
- **WHEN** 김대리가 `GET /api/me/todos` 를 부른다
- **THEN** 담당자가 김대리인 할 일만 돌아온다

### Requirement: 할 일 변경
<!-- 근거: 스토리보드 D-03 · D-04 · E-04 · E-05 · E-06 / publish/todos.html (moved · pick · assign), publish/detail.html (assign · progress) -->
`PUT /api/todos/{id}` 는 `status` · `assignee_id` · `due_text` 중 보낸 것만 바꾸고 `200` 과 바뀐 항목을 돌려주어야 한다(SHALL). 같은 팀 멤버라면 누구나 바꿀 수 있다. `status` 는 `OPEN` · `DOING` · `DONE` 셋뿐이고 되돌리기(`DONE` → `OPEN`)도 허용한다. 그 밖의 값이면 `400 VALIDATION_ERROR`, `assignee_id` 가 팀 멤버가 아니면 `400 VALIDATION_ERROR`, 없는 할 일이면 `404 NOT_FOUND`, 다른 팀 할 일이면 `403 FORBIDDEN` 이다. 담당자가 사람으로 바뀌면 `todo_assign`, 상태가 `DONE` 으로 바뀌면 `todo_done` 활동을 남겨야 한다(SHALL).

#### Scenario: 완료로 이동
- **WHEN** `DOING` 인 할 일을 `DONE` 으로 바꾼다
- **THEN** `200` 이 돌아오고 팀 활동 기록에 `todo_done` 이 생긴다

#### Scenario: 담당자 배정
- **WHEN** 미정인 할 일의 `assignee_id` 를 최선임으로 바꾼다
- **THEN** `200` 과 `assignee_name` 최선임이 돌아오고 `todo_assign` 활동이 생긴다

#### Scenario: 없는 상태 값
- **WHEN** `status` 를 `CLOSED` 로 보낸다
- **THEN** `400 VALIDATION_ERROR` 가 돌아온다

### Requirement: 할 일 삭제는 owner 만
<!-- 근거: 스토리보드 E-11 · F-08 / publish/todos.html (del) -->
`DELETE /api/todos/{id}` 는 owner 만 부를 수 있고 `204` 를 돌려주어야 한다(SHALL). owner 가 아니면 `403 OWNER_ONLY` 를 돌려주어야 한다(MUST). 화면은 owner 에게만 삭제 배지를 보인다.

#### Scenario: member 의 삭제
- **WHEN** member 가 할 일을 지운다
- **THEN** `403 OWNER_ONLY` 가 돌아오고 할 일은 남는다

### Requirement: 기한 지남 표시
<!-- 근거: 스토리보드 E-08 · 정의서 7-2 / publish/todos.html (late) -->
서버는 기한을 비교하지 않는다. 화면은 `due_text` 가 `YYYY-MM-DD` 로 시작하고 그 날짜가 오늘(현지 날짜)보다 앞이며 상태가 `DONE` 이 아닐 때만 카드에 붉은 띠와 붉은 기한 글자를 보여야 한다(SHALL) (D4). 그 밖의 글자(「미정」 · 「이번 주 안」 등)는 기한 지남으로 보지 않는다.

#### Scenario: 지난 날짜
- **WHEN** 오늘이 2026-10-06 이고 `due_text` 가 `2026-10-05` 인 `OPEN` 할 일이 있다
- **THEN** 그 카드에 붉은 띠가 보인다

#### Scenario: 완료는 제외
- **WHEN** 같은 날짜의 할 일이 `DONE` 이다
- **THEN** 붉은 띠가 없다

### Requirement: 칸반 화면 동작
<!-- 근거: 스토리보드 E-01 ~ E-12 · N-01 / publish/todos.html -->
todos.html 은 「내 할 일」 · 「전체」 탭, 담당자 필터, 대기(orange) · 진행(blue) · 완료(green) 3열을 보여야 한다(SHALL). 카드는 할 일 · 회의록 제목 · 담당자 배지 · 기한 배지를 보인다.

- 끌어서 옮기기는 포인터 이벤트로 만든다. HTML5 네이티브 드래그(draggable)는 쓰지 않는다(MUST NOT). 끄는 동안 반투명 사본이 따라오고 놓을 칸이 점선 테두리와 「여기에 놓기」로 바뀐다. 놓기 전에는 서버를 부르지 않고, 놓는 순간 `PUT` 을 한 번만 부른다. 실패하면 카드를 원래 칸으로 되돌리고 붉은 띠 알림을 보인다
- 카드를 끌지 않고 누르면 카드 아래에 대기 · 진행 · 완료 버튼이 뜨고, 눌러서 칸을 옮긴다. 좁은 화면(칸이 세로로 쌓일 때)에서는 이것이 옮기는 길이다
- 담당자 배지를 누르면 팀 멤버(미정 포함) 순으로 다음 사람으로 바뀐다. 담당자 선택지는 `GET /api/teams/{id}/members` 로 받는다 (D8 예외)
- 기한 배지를 누르면 미정 → 오늘 → 내일 → 이번 주 금요일 → 다음 주 금요일 → 미정 순으로 바뀌고, 미정 외에는 `YYYY-MM-DD` 로 저장한다
- 담당자 필터는 화면에서만 거르고 서버를 다시 부르지 않는다
- 할 일이 없으면 「배정된 할 일이 없음」 빈 상태를 보인다

#### Scenario: 놓는 순간 한 번 호출
- **WHEN** 대기 칸의 카드를 끌어 진행 칸에 놓는다
- **THEN** `PUT /api/todos/{id}` 가 `status: DOING` 으로 한 번만 불리고 카드는 진행 칸에 남는다

#### Scenario: 이동 실패는 되돌림
- **WHEN** 카드를 옮겼는데 `PUT` 이 실패한다
- **THEN** 카드는 원래 칸으로 돌아가고 붉은 띠 알림이 보인다

#### Scenario: 좁은 화면에서 눌러서 옮기기
- **WHEN** 360px 화면에서 카드를 누른다
- **THEN** 카드 아래에 대기 · 진행 · 완료 버튼이 뜨고, 현재 칸 버튼은 비활성이다

#### Scenario: 필터는 서버를 부르지 않음
- **WHEN** 담당자 필터에서 박과장을 고른다
- **THEN** 박과장 카드만 남고 추가 API 호출은 없다

### Requirement: 회의록 상세의 할 일 칸
<!-- 근거: 스토리보드 D-03 · D-04 · D-06 / publish/detail.html (assign · progress · no-todo) -->
detail.html 의 할 일 칸은 항목마다 담당자 select(미정 포함 팀 멤버) · 기한 · 상태 배지를 보여야 한다(SHALL). select 를 바꾸면 `PUT /api/todos/{id}` 로 담당자를 저장한다. 담당자 선택지는 `GET /api/teams/{id}/members` 로 받는다 (D8 예외).

#### Scenario: 상세에서 담당자 배정
- **WHEN** 상세 화면에서 미정 할 일의 담당자를 최선임으로 고른다
- **THEN** `PUT /api/todos/{id}` 가 불리고 칸반에서도 최선임 담당으로 보인다
