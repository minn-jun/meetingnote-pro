"""받아쓰기 · 3항목 구분 공급자 (결정사항 D2). 테스트는 가짜 공급자로 바꿔 끼운다"""
import json
from datetime import datetime
from typing import Protocol

from app.config import settings
from app.errors import ApiError


class AIProvider(Protocol):
    def transcribe(self, data: bytes, filename: str) -> str: ...

    def split(self, body: str, met_at: datetime, member_names: list[str]) -> dict:
        """{summary: str, decisions: [str], todos: [{what, assignee_name, due_text}]}"""
        ...


SPLIT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "decisions", "todos"],
    "properties": {
        "summary": {"type": "string"},
        "decisions": {"type": "array", "items": {"type": "string"}},
        "todos": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["what", "assignee_name", "due_text"],
                "properties": {
                    "what": {"type": "string"},
                    "assignee_name": {"type": ["string", "null"]},
                    "due_text": {"type": "string"},
                },
            },
        },
    },
}

SPLIT_PROMPT = """너는 한국어 회의 받아쓰기를 세 항목으로 나누는 도구다. 지어내지 않는다.
- summary: 회의 내용을 3~5줄로 요약. 줄바꿈으로 구분
- decisions: 합의가 끝난 결정만 한 줄씩. 논의만 하고 정하지 않은 것은 넣지 않는다. 없으면 빈 배열
- todos: 누가 무엇을 언제까지 하기로 한 일. 없으면 빈 배열
  - assignee_name: 아래 팀 멤버 이름 중 하나와 정확히 같을 때만 그 이름. 아니면 null
  - due_text: 기한을 회의 시각 기준 날짜 YYYY-MM-DD 로. 날짜를 정할 수 없으면 원래 표현 그대로. 기한이 없으면 "미정"
회의 시각: {met_at}
팀 멤버: {members}"""


INLINE_LIMIT = 12 * 1024 * 1024  # 인라인 요청은 통째로 20MB 까지라, 큰 파일은 Files API 로 올린다

TRANSCRIBE_PROMPT = (
    "이 회의 녹음을 한국어로 받아쓴다. 들린 말만 적고 요약 · 해설 · 시간 표시를 붙이지 않는다. "
    "화자를 구분하지 않고 문장마다 줄을 바꾼다."
)


class GeminiProvider:
    """Gemini 한 모델이 받아쓰기와 3항목 구분을 모두 한다 (결정사항 D2)"""

    @property
    def client(self):
        # 호출할 때 만든다. 키가 없어 실패해도 upstream() 이 502 로 바꾼다
        from google import genai
        return genai.Client(api_key=settings.stt_api_key or None)

    def transcribe(self, data: bytes, filename: str) -> str:
        from google.genai import types
        mime = "audio/wav" if data[:4] == b"RIFF" else "audio/mp3"
        if len(data) > INLINE_LIMIT:
            import io
            audio = self.client.files.upload(file=io.BytesIO(data), config={"mime_type": mime})
        else:
            audio = types.Part.from_bytes(data=data, mime_type=mime)
        r = self.client.models.generate_content(model=settings.stt_model, contents=[TRANSCRIBE_PROMPT, audio])
        return (r.text or "").strip()

    def split(self, body: str, met_at: datetime, member_names: list[str]) -> dict:
        r = self.client.models.generate_content(
            model=settings.summary_model,
            contents=body,
            config={
                "system_instruction": SPLIT_PROMPT.format(
                    met_at=met_at.isoformat(), members=", ".join(member_names) or "(없음)"),
                "response_mime_type": "application/json",
                "response_json_schema": SPLIT_SCHEMA,
            },
        )
        return json.loads(r.text)


def get_ai() -> AIProvider:
    return GeminiProvider()


def upstream(fn, *args):
    """공급자 실패는 502 UPSTREAM_ERROR (결정사항 D12)"""
    try:
        return fn(*args)
    except ApiError:
        raise
    except Exception as e:  # 공급자 SDK 예외 종류를 가리지 않는다
        raise ApiError(502, "UPSTREAM_ERROR", "받아쓰기 · 정리 서비스가 응답하지 않습니다. 잠시 후 다시 시도해 주세요") from e
