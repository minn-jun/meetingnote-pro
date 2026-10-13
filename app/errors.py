"""오류 코드 15종 - 본문은 언제나 {code, msg}"""


class ApiError(Exception):
    def __init__(self, status: int, code: str, msg: str):
        self.status = status
        self.code = code
        self.msg = msg


# 화면 10종 + 공통 4종 + 외부 공급자 실패 1종 (결정사항 D12)
CODES = {
    "EMAIL_INVALID", "PASSWORD_TOO_WEAK", "TOKEN_EXPIRED", "INVITE_NOT_FOUND",
    "MEETING_NOT_FOUND", "EMAIL_DUPLICATED", "TEAM_FULL", "PAYLOAD_TOO_LARGE",
    "UNSUPPORTED_MEDIA_TYPE", "INVALID_CREDENTIALS",
    "FORBIDDEN", "OWNER_ONLY", "VALIDATION_ERROR", "NOT_FOUND",
    "UPSTREAM_ERROR",
}


def validation(msg: str = "입력값을 확인해 주세요") -> ApiError:
    return ApiError(400, "VALIDATION_ERROR", msg)


def forbidden(msg: str = "권한이 없습니다") -> ApiError:
    return ApiError(403, "FORBIDDEN", msg)


def owner_only() -> ApiError:
    return ApiError(403, "OWNER_ONLY", "팀 owner 만 할 수 있습니다")


def not_found(msg: str = "찾을 수 없습니다") -> ApiError:
    return ApiError(404, "NOT_FOUND", msg)
