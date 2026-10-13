# Spec Delta

## Purpose

회의록에 의견을 남기고 읽으며, 쓴 사람과 owner 만 지울 수 있게 해 결정의 맥락을 팀이 함께 보존하는 기능을 정한다.

## ADDED Requirements

### Requirement: 댓글 등록
<!-- 근거: 스토리보드 D-09 · D-10 / publish/detail.html (comment · comment-added) -->
`POST /api/meetings/{id}/comments` 는 내용을 받아 댓글을 만들고 `201` 과 댓글을 돌려주어야 한다(SHALL). 내용은 비어 있으면 안 되고 500자 이하여야 하며, 어기면 `400 VALIDATION_ERROR` 를 돌려준다(MUST). 없는 회의록이면 `404 MEETING_NOT_FOUND`, 다른 팀 회의록이면 `403 FORBIDDEN` 이다. 등록하면 활동 기록 `comment_add` 를 남겨야 한다(SHALL).

#### Scenario: 댓글 등록
- **WHEN** 팀 멤버가 회의록에 「받아쓰기 실패는 세 칸을 비우기로 했습니다」 를 단다
- **THEN** `201` 이 돌아오고 팀 활동 기록에 `comment_add` 가 생긴다

#### Scenario: 501자 댓글
- **WHEN** 501자 내용을 보낸다
- **THEN** `400 VALIDATION_ERROR` 가 돌아온다

### Requirement: 댓글 목록과 삭제 권한 판정
<!-- 근거: 스토리보드 D-11 · D-12 / publish/detail.html (comment-none · comment-del) -->
`GET /api/meetings/{id}/comments` 는 `id · user_id · user_name · content · created_at · can_delete` 배열을 `created_at` 오름차순으로 돌려주어야 한다(SHALL). `can_delete` 는 부른 사람이 쓴 사람이거나 팀 owner 일 때 `true` 다. 댓글이 없으면 `200` 과 빈 배열이다.

#### Scenario: 삭제 가능 여부를 서버가 판정
- **WHEN** member A 가 A 의 댓글과 B 의 댓글이 있는 목록을 부른다
- **THEN** A 의 댓글은 `can_delete: true`, B 의 댓글은 `false` 다

#### Scenario: owner 는 모두 지울 수 있음
- **WHEN** owner 가 같은 목록을 부른다
- **THEN** 모든 댓글이 `can_delete: true` 다

### Requirement: 댓글 삭제
<!-- 근거: 스토리보드 D-12 / publish/detail.html (comment-del) -->
`DELETE /api/comments/{id}` 는 쓴 사람이나 owner 가 부르면 `204` 를 돌려주어야 한다(SHALL). 그 밖이면 `403 FORBIDDEN`, 없는 댓글이면 `404 NOT_FOUND` 다.

#### Scenario: 남의 댓글 삭제
- **WHEN** owner 가 아닌 member 가 다른 사람의 댓글을 지운다
- **THEN** `403 FORBIDDEN` 이 돌아오고 댓글은 남는다

### Requirement: 댓글 칸 화면 동작
<!-- 근거: 스토리보드 D-09 ~ D-12 / publish/detail.html (댓글 section) -->
detail.html 의 댓글 칸은 댓글 목록(이름 · 내용 · 시각)과 입력칸 · 등록 버튼을 보여야 한다(SHALL). 삭제 버튼은 `can_delete` 가 `true` 인 댓글에만 보인다. 등록이 `201` 로 끝나면 입력칸을 비우고 목록 맨 아래에 붙인다. 댓글이 없으면 「아직 댓글이 없음」 빈 상태를 보인다. 입력은 500자에서 막힌다.

#### Scenario: 등록 뒤 입력칸 비움
- **WHEN** 댓글 등록이 `201` 로 끝난다
- **THEN** 입력칸이 비워지고 새 댓글이 목록 맨 아래에 보인다

#### Scenario: 삭제 버튼은 권한 있는 댓글에만
- **WHEN** member 가 상세 화면을 연다
- **THEN** 자기 댓글에만 삭제 버튼이 보인다
