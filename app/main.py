"""MeetingNote Pro - API 26개 + 화면 6종 + Swagger UI"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.errors import ApiError
from app.routers import activities, auth, comments, meetings, teams, todos
from app.schemas import ErrorOut

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

TAGS = [
    {"name": "Auth", "description": "회원가입 · 로그인 · 내 정보 · 로그아웃"},
    {"name": "Team", "description": "팀 · 초대코드 · 멤버"},
    {"name": "Meeting", "description": "녹취 업로드 · 회의록"},
    {"name": "Todo", "description": "할 일 칸반"},
    {"name": "Comment", "description": "회의록 댓글"},
    {"name": "Activity", "description": "활동 기록"},
]

ERROR_RESPONSES = {s: {"model": ErrorOut} for s in (400, 401, 403, 404)}

app = FastAPI(
    title="MeetingNote Pro API",
    version="0.1.0",
    description="로그인한 팀이 함께 쓰는 회의록. 오른쪽 위 **Authorize** 에 로그인 응답의 `token` 을 넣으면 보호된 API 를 바로 부를 수 있다.",
    openapi_tags=TAGS,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
def api_error(request: Request, e: ApiError):
    return JSONResponse(status_code=e.status, content={"code": e.code, "msg": e.msg})


@app.exception_handler(RequestValidationError)
def request_invalid(request: Request, e: RequestValidationError):
    # 프레임워크 기본 422 대신 400 VALIDATION_ERROR
    first = e.errors()[0] if e.errors() else {}
    where = ".".join(str(x) for x in first.get("loc", [])[1:])
    msg = f"입력값을 확인해 주세요 ({where})" if where else "입력값을 확인해 주세요"
    return JSONResponse(status_code=400, content={"code": "VALIDATION_ERROR", "msg": msg})


@app.exception_handler(StarletteHTTPException)
def http_error(request: Request, e: StarletteHTTPException):
    code = "NOT_FOUND" if e.status_code == 404 else "VALIDATION_ERROR"
    msg = "찾을 수 없습니다" if e.status_code == 404 else str(e.detail)
    return JSONResponse(status_code=e.status_code, content={"code": code, "msg": msg})


for r in (auth.router, teams.router, meetings.router, todos.router, comments.router, activities.router):
    app.include_router(r, responses=ERROR_RESPONSES)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/login.html")


@app.get("/config.js", include_in_schema=False)
def config_js():
    # 화면 안내 문구가 서버 설정값을 따르게 한다 (결정사항 D3 · D15). API 가 아니라 화면용 스크립트
    return Response(f"window.APP_CONFIG = {{ maxUploadMb: {settings.max_upload_mb} }};",
                    media_type="application/javascript")


# 화면은 맨 끝에 붙여 /api · /docs 를 가리지 않는다
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
