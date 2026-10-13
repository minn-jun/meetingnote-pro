# activity Specification

## Purpose
팀에서 일어난 일을 행위자 · 시점 · 대상과 함께 남겨, 팀 활동과 내 활동을 최근 순으로 되짚어 볼 수 있게 하는 기능을 정한다.

## Requirements

### Requirement: 활동 종류는 5개로 고정
<!-- 근거: 정의서 6 (activities.kind 5종) / publish/profile.html (kind 표시), publish/team.html (ACTS) -->
활동 기록의 `kind` 는 `meeting_add` · `todo_assign` · `todo_done` · `comment_add` · `member_join` 다섯만 써야 한다(MUST). 그 밖의 값은 만들지 않는다. 남기는 때는 다음과 같다(SHALL).

| kind | 남기는 때 |
|---|---|
| `meeting_add` | 회의록 생성 성공 |
| `todo_assign` | 할 일 담당자가 사람으로 바뀜 |
| `todo_done` | 할 일 상태가 `DONE` 으로 바뀜 |
| `comment_add` | 댓글 등록 |
| `member_join` | 초대코드로 합류 |

팀 생성 · 계정 변경 · 삭제 · 상태 되돌리기는 남기지 않는다.

#### Scenario: 정해진 kind 만 생김
- **WHEN** 가입 · 팀 생성 · 합류 · 회의록 생성 · 담당자 배정 · 완료 · 댓글 · 이름 변경 · 회의록 삭제를 차례로 한다
- **THEN** 팀 활동 기록의 kind 는 `member_join` · `meeting_add` · `todo_assign` · `todo_done` · `comment_add` 다섯뿐이다

### Requirement: 활동 조회
<!-- 근거: 스토리보드 F-01 · J-01 · J-07 / publish/team.html (활동 기록), publish/profile.html (내 활동 · no-activity) -->
`GET /api/teams/{id}/activities` 는 팀 활동을, `GET /api/me/activities` 는 내가 행위자인 활동을 최근 순으로 최대 50건 돌려주어야 한다(SHALL). 항목은 `id · kind · actor_name · text · created_at` 이다. `text` 는 서버가 만든 완성 문장이고(예: 「할 일 「사용자 다섯 분 인터뷰」를 최선임에게 배정」), 화면은 그대로 그린다. 활동이 없으면 `200` 과 빈 배열이다.

#### Scenario: 최근 50건
- **WHEN** 활동이 60건 쌓인 팀의 활동을 부른다
- **THEN** 가장 최근 50건이 `created_at` 내림차순으로 돌아온다

#### Scenario: 서버가 만든 문장
- **WHEN** 회의록 「2차 스프린트 계획 회의」를 만든 뒤 팀 활동을 부른다
- **THEN** 맨 앞 항목의 `text` 가 회의록 제목을 담은 완성 문장이다

### Requirement: 활동 표시
<!-- 근거: 스토리보드 F-01 · J-01 · J-07 · 정의서 7-2 (활동 기록 띠 색) / publish/team.html · publish/profile.html -->
화면은 활동마다 좌측 띠 색을 kind 로 골라야 한다(SHALL). `meeting_add`=blue · `todo_assign`=orange · `todo_done`=green · `comment_add` 와 `member_join`=purple 이다. team.html 은 행위자 이름 · 문장 · 시각을, profile.html 은 문장 · 시각 · kind 를 보인다. 내 활동이 없으면 profile.html 에 「아직 활동이 없음」 빈 상태를 보인다.

#### Scenario: kind 별 띠 색
- **WHEN** `todo_done` 활동을 그린다
- **THEN** 그 항목의 좌측 띠는 green 이다

#### Scenario: 합류 직후
- **WHEN** 막 합류해 내 활동이 `member_join` 1건뿐이다
- **THEN** profile.html 내 활동에 그 1건이 purple 띠로 보인다
