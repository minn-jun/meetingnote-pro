# Spec Delta

## Purpose

녹취를 올려 받아쓰고, 저장할 때 요약 · 결정사항 · 할 일 3항목으로 나눈 회의록을 팀이 함께 만들고 찾고 고치는 기능을 정한다.

## ADDED Requirements

### Requirement: 녹취 업로드와 받아쓰기
<!-- 근거: 스토리보드 C-06 · C-07 · C-08 · C-09 / publish/meetings.html (upload · upload-done · err-type · err-size) -->
`POST /api/upload` 는 multipart 파일 하나를 받아 받아쓴 본문을 `{"body": "..."}` 로 돌려주어야 한다(SHALL). 저장은 하지 않는다. 형식은 확장자가 아니라 파일 내용으로 판정해 mp3 · wav 만 받고, 그 밖이면 `415 UNSUPPORTED_MEDIA_TYPE` 를 돌려주어야 한다(MUST). 크기가 상한(`MAX_UPLOAD_MB`, 로컬 25MB · 배포 4MB, D3)을 넘으면 `413 PAYLOAD_TOO_LARGE` 를 돌려주어야 한다. 받아쓰기 공급자 호출이 실패하면 `502 UPSTREAM_ERROR` 를 돌려주어야 한다 (D12).

#### Scenario: wav 받아쓰기
- **WHEN** 4MB 짜리 wav 파일을 올린다
- **THEN** `200` 과 받아쓴 본문 텍스트가 돌아오고 회의록은 아직 생기지 않는다

#### Scenario: 확장자만 바꾼 파일
- **WHEN** 내용이 mp4 인 파일을 이름만 `a.mp3` 로 바꿔 올린다
- **THEN** `415 UNSUPPORTED_MEDIA_TYPE` 가 돌아온다

#### Scenario: 용량 초과
- **WHEN** 상한보다 큰 파일을 올린다
- **THEN** `413 PAYLOAD_TOO_LARGE` 가 돌아온다

### Requirement: 회의록 생성과 3항목 구분
<!-- 근거: 스토리보드 C-05 · C-10 · C-11 / publish/meetings.html (new · saving · saved) -->
`POST /api/teams/{id}/meetings` 는 제목 · 회의 시각(`met_at`, ISO 8601 UTC) · 본문을 필수로, 참석자를 선택으로 받아야 한다(SHALL). 필수가 빠지면 `400 VALIDATION_ERROR` 를 돌려준다. 저장하면서 본문을 요약 · 결정사항 · 할 일 3항목으로 나누어 함께 저장하고 `201` 과 단건 응답을 돌려주어야 한다(SHALL).

- 요약은 3~5줄이다
- 결정사항은 합의가 끝난 것만 줄바꿈으로 구분해 한 칸에 저장한다. 없으면 비운다. 지어내지 않는다
- 할 일은 항목마다 `what` · 담당자 · 기한을 뽑는다. 담당자 이름이 팀 멤버 이름과 정확히 같을 때만 그 사람으로 배정하고, 아니면 미정(`null`)이다. 기한은 상대 표현을 `met_at` 기준 `YYYY-MM-DD` 로 바꾸고, 날짜를 정할 수 없으면 원래 글자, 기한이 없으면 「미정」이다 (D4). 새 할 일의 상태는 `OPEN` 이다
- 3항목 구분이 실패하면 회의록을 저장하지 않고 `502 UPSTREAM_ERROR` 를 돌려준다 (D12)
- 저장에 성공하면 활동 기록 `meeting_add` 를 남긴다

#### Scenario: 저장과 구분
- **WHEN** 제목 · 회의 시각 · 받아쓴 본문으로 회의록을 만든다
- **THEN** `201` 과 함께 `summary` · `decisions` · `todos` 가 채워진 회의록이 돌아오고 팀 활동 기록에 `meeting_add` 가 생긴다

#### Scenario: 멤버가 아닌 담당자
- **WHEN** 본문에서 뽑힌 할 일의 담당자 이름이 팀 멤버에 없다
- **THEN** 그 할 일의 `assignee_id` 는 `null` 이다

#### Scenario: 필수 값 누락
- **WHEN** 본문 없이 회의록을 만든다
- **THEN** `400 VALIDATION_ERROR` 가 돌아온다

### Requirement: 회의록 목록 · 검색 · 기간
<!-- 근거: 스토리보드 C-01 · C-02 · C-03 · C-04 / publish/meetings.html (list · empty · search · search-none) -->
`GET /api/teams/{id}/meetings` 는 `id · title · met_at · attendees · summary · created_at · todo_done_count · todo_total_count · decision_count` 배열을 `met_at` 내림차순으로 돌려주어야 한다(SHALL). `body` 는 싣지 않는다(MUST NOT). `?q=` 는 제목과 참석자에만 부분 일치하고 본문은 대상이 아니다. `?from=&to=` 는 ISO 날짜로 `met_at` 의 날짜 범위(양 끝 포함)를 거른다. 결과가 없으면 `404` 가 아니라 `200` 과 빈 배열이다. `decision_count` 는 `decisions` 에서 빈 줄을 뺀 줄 수다.

#### Scenario: 본문은 검색 대상이 아님
- **WHEN** 본문에만 있는 낱말로 `?q=` 검색한다
- **THEN** `200` 과 빈 배열이 돌아온다

#### Scenario: 참석자 검색
- **WHEN** `?q=최선임` 으로 검색한다
- **THEN** 참석자에 최선임이 있는 회의록만 `met_at` 내림차순으로 돌아온다

#### Scenario: 목록에 body 없음
- **WHEN** 목록을 부른다
- **THEN** 어느 항목에도 `body` 필드가 없다

### Requirement: 회의록 단건 · 수정 · 삭제
<!-- 근거: 스토리보드 D-01 · D-02 · D-08 · D-13 / publish/detail.html (view · edit · delete · not-found) -->
`GET /api/meetings/{id}` 는 목록 필드에 `body · decisions · author_id` 와 할 일 배열 `todos`(할 일 목록 응답 형식)를 더해 돌려주어야 한다(SHALL) (D6). `PUT /api/meetings/{id}` 는 제목 · 회의 시각 · 참석자 · 본문을 고친다. 본문을 고쳐도 3항목을 다시 구분하지 않는다. `DELETE /api/meetings/{id}` 는 딸린 할 일 · 댓글과 함께 지우고 `204` 를 돌려준다. 수정과 삭제는 쓴 사람과 owner 만 할 수 있고 그 밖이면 `403 FORBIDDEN` 이다. 없는 회의록이면 `404 MEETING_NOT_FOUND`, 다른 팀 회의록이면 `403 FORBIDDEN` 을 돌려주어야 한다(SHALL).

#### Scenario: 단건에는 body 와 todos
- **WHEN** 회의록 단건을 부른다
- **THEN** `body` 와 `todos` 배열이 함께 돌아온다

#### Scenario: 삭제는 딸린 것까지
- **WHEN** 할 일 3건 · 댓글 2건이 딸린 회의록을 쓴 사람이 지운다
- **THEN** `204` 가 돌아오고 그 할 일과 댓글도 더 조회되지 않는다

#### Scenario: 다른 member 의 삭제
- **WHEN** 쓴 사람도 owner 도 아닌 member 가 회의록을 지운다
- **THEN** `403 FORBIDDEN` 이 돌아온다

#### Scenario: 없는 회의록
- **WHEN** 없는 id 로 단건을 부른다
- **THEN** `404 MEETING_NOT_FOUND` 가 돌아오고, detail.html 은 붉은 띠 알림 뒤 meetings.html 로 보낸다

### Requirement: 회의록 목록 화면 동작
<!-- 근거: 스토리보드 C-01 ~ C-11 / publish/meetings.html -->
meetings.html 은 진입할 때 `GET /api/auth/me` 로 로그인과 팀을 확인하고, 검색 줄(검색어 · 시작일 · 종료일 · 새 회의록)과 카드 목록을 보여야 한다(SHALL). 카드 띠 색은 목록 순서대로 blue · green · orange · purple · red 를 돌려 쓴다. 카드는 제목 · 회의 시각 · 참석자 · 요약 2줄 · 「완료 할 일 수 / 전체 할 일 수」 · 결정 수 · 할 일 수를 보이고, 누르면 detail.html 로 간다. 목록이 비면 「아직 회의록이 없음」, 검색 결과가 없으면 「검색 결과 없음」 빈 상태를 보인다. 새 회의록 패널은 녹취 파일 끌어 놓기 · 진행률 · 본문 칸을 갖고, 받아쓰기가 끝나면 본문 칸을 채운다. 「정리하기」를 누르면 「정리 중...」 으로 잠그고, `201` 뒤 입력칸을 비우고 패널을 닫아 같은 회의록이 두 번 저장되지 않게 한다. 415 · 413 오류는 패널 안 붉은 띠 알림으로 보인다.

#### Scenario: 카드 띠 순환
- **WHEN** 회의록 6건이 목록에 있다
- **THEN** 띠 색은 차례로 blue · green · orange · purple · red · blue 다

#### Scenario: 저장 뒤 입력칸 비움
- **WHEN** 정리하기가 `201` 로 끝난다
- **THEN** 새 회의록 패널의 입력칸이 비워지고 패널이 닫히며 목록이 새로 그려진다

### Requirement: 회의록 상세 화면 동작
<!-- 근거: 스토리보드 D-01 ~ D-08 · D-13 / publish/detail.html -->
detail.html 은 머리(제목 · 시각 · 참석자 · 수정 · 삭제), 3단(요약 blue · 결정사항 green · 할 일 orange), 접힌 받아쓴 본문, 댓글 칸 순으로 보여야 한다(SHALL). 결정사항은 줄 단위로 끊어 번호를 붙인다. 결정사항이나 할 일이 없으면 그 칸에 「합의가 끝난 항목 없음」 · 「담당자와 기한이 드러난 항목 없음」을 보이고 억지로 채우지 않는다. 본문은 기본으로 접혀 있고 「펼치기」 / 「접기」로 바꾼다. 삭제를 누르면 「딸린 할 일 N건도 함께 사라짐. 되돌릴 수 없음」 확인 칸을 띄우고, 확인하면 지운 뒤 meetings.html 로 간다.

#### Scenario: 결정사항 없음
- **WHEN** `decisions` 가 비어 있는 회의록을 연다
- **THEN** 결정사항 칸에 빈 상태 문구가 보이고 번호 목록은 없다

#### Scenario: 본문은 접힌 채 시작
- **WHEN** detail.html 을 연다
- **THEN** 받아쓴 본문은 접혀 있고 3단이 먼저 보인다
