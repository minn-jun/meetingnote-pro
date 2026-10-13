"""DB 행을 응답 모델로 바꾸는 공통 함수"""
from app.models import Meeting, Todo
from app.schemas import MeetingDetail, MeetingListItem, TodoOut


def decision_lines(decisions: str) -> list[str]:
    return [line.strip() for line in (decisions or "").splitlines() if line.strip()]


def todo_out(t: Todo) -> TodoOut:
    return TodoOut(id=t.id, what=t.what, assignee_id=t.assignee_id,
                   assignee_name=t.assignee.name if t.assignee else None,
                   due_text=t.due_text, status=t.status,
                   meeting_id=t.meeting_id, meeting_title=t.meeting.title)


def _list_fields(m: Meeting) -> dict:
    return dict(id=m.id, title=m.title, met_at=m.met_at, attendees=m.attendees or "",
                summary=m.summary or "", created_at=m.created_at,
                todo_done_count=sum(1 for t in m.todos if t.status == "DONE"),
                todo_total_count=len(m.todos),
                decision_count=len(decision_lines(m.decisions)))


def meeting_item(m: Meeting) -> MeetingListItem:
    return MeetingListItem(**_list_fields(m))


def meeting_detail(m: Meeting) -> MeetingDetail:
    return MeetingDetail(**_list_fields(m), body=m.body, decisions=m.decisions or "",
                         author_id=m.author_id, todos=[todo_out(t) for t in m.todos])
