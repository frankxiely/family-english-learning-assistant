from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlsplit

from fastapi import Body, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core import (
    WEB_PUBLIC_DIR,
    authenticate_local_account,
    debug_modules,
    export_learning_log,
    generate_lesson_draft_today,
    generate_lesson_draft_workspace,
    generate_lesson_asset_audio,
    generate_lesson_draft_audio,
    generate_weekly_lesson_draft_workspaces,
    generate_pending_lesson_drafts_audio,
    get_admin_dashboard,
    get_admin_user_directory,
    get_admin_user_workspace,
    get_learning_review,
    get_learning_overview,
    get_learning_route_map,
    get_today_lesson,
    get_user_state,
    get_weekly_summary,
    init_db,
    manually_update_lesson_draft,
    publish_lesson_draft_workspace,
    regenerate_lesson_draft_from_instruction,
    publish_lesson_asset,
    rollback_lesson_asset,
    save_admin_feedback,
    save_admin_note,
    submit_learning_progress,
    submit_sample_progress,
    today_iso,
    undo_lesson_draft,
    update_account_display_name,
    update_account_password,
    update_lesson_draft,
    update_lesson_draft_note,
    update_route_priority,
    update_user_profile,
    verify_admin_session,
)

DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
)


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def configured_cors_origins() -> list[str]:
    raw = os.environ.get("MOMO_CORS_ORIGINS", "").strip()
    if not raw:
        return list(DEFAULT_CORS_ORIGINS)
    origins = []
    for origin in raw.split(","):
        value = origin.strip().rstrip("/")
        if not value:
            continue
        parsed = urlsplit(value)
        if parsed.scheme and parsed.netloc:
            value = f"{parsed.scheme}://{parsed.netloc}"
        origins.append(value)
    return origins or list(DEFAULT_CORS_ORIGINS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db(seed_test_data=env_flag("MOMO_AUTO_SEED_TEST_DATA"))
    yield


app = FastAPI(title="家庭英语学习助手 API", version="1.1.0", lifespan=lifespan)

cors_origins = configured_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

generated_public_dir = WEB_PUBLIC_DIR / "generated"
generated_public_dir.mkdir(parents=True, exist_ok=True)
app.mount("/generated", StaticFiles(directory=generated_public_dir), name="generated")


def require_admin_session(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="admin authorization is required")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_admin_session(token)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="admin role is required") from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def get_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authorization is required")
    return authorization.removeprefix("Bearer ").strip()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.1.0"}


@app.get("/api/debug/modules")
def debug(_admin: dict[str, Any] = Depends(require_admin_session)) -> dict[str, Any]:
    return debug_modules()


@app.post("/api/auth/login")
def auth_login(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    login_account = str(payload.get("login_account") or payload.get("username") or "")
    password = str(payload.get("password") or "")
    remember = bool(payload.get("remember", True))
    if not login_account or not password:
        raise HTTPException(status_code=400, detail="login_account and password are required")
    try:
        return {"status": "ok", "session": authenticate_local_account(login_account, password, remember)}
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.put("/api/account/display-name")
def account_display_name(
    payload: dict[str, Any] = Body(default_factory=dict),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    display_name = str(payload.get("username") or payload.get("display_name") or "")
    try:
        return {"status": "ok", "session": update_account_display_name(get_bearer_token(authorization), display_name)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/account/password")
def account_password(
    payload: dict[str, Any] = Body(default_factory=dict),
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    current_password = str(payload.get("current_password") or "")
    new_password = str(payload.get("new_password") or "")
    try:
        return update_account_password(get_bearer_token(authorization), current_password, new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/learning/today")
def learning_today(user_id: str = "user_mom", date: str | None = None) -> dict[str, Any]:
    lesson = get_today_lesson(user_id, date or today_iso())
    return {"lesson_json": lesson}


@app.get("/api/learning/state")
def learning_state(user_id: str = "user_mom") -> dict[str, Any]:
    return get_user_state(user_id)


@app.get("/api/learning/route-map")
def learning_route_map(user_id: str = "user_mom") -> dict[str, Any]:
    return get_learning_route_map(user_id)


@app.post("/api/learning/complete")
def learning_complete(
    user_id: str = "user_mom",
    date: str | None = None,
    payload: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    try:
        if not payload:
            review_asset_id = submit_sample_progress(user_id, date or today_iso())
            return {"status": "ok", "review_asset_id": review_asset_id}
        return submit_learning_progress(user_id, payload, date or today_iso())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/learning/review")
def learning_review(user_id: str = "user_mom", date: str | None = None) -> dict[str, Any]:
    return {"review_json": get_learning_review(user_id, date or today_iso())}


@app.get("/api/learning/weekly-summary")
def learning_weekly_summary(user_id: str = "user_mom", end_date: str | None = None) -> dict[str, Any]:
    return {"weekly_summary": get_weekly_summary(user_id, end_date or today_iso())}


@app.get("/api/admin/dashboard")
def admin_dashboard(
    user_id: str = "user_mom",
    date: str | None = None,
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    return get_admin_dashboard(user_id, date or today_iso())


@app.get("/api/admin/users")
def admin_users(_admin: dict[str, Any] = Depends(require_admin_session)) -> dict[str, Any]:
    return get_admin_user_directory()


@app.get("/api/admin/users/{user_id}/workspace")
def admin_user_workspace(
    user_id: str,
    date: str | None = None,
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    return get_admin_user_workspace(user_id, date or today_iso())


@app.get("/api/admin/users/{user_id}/learning-overview")
def admin_learning_overview(
    user_id: str,
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    return {"learning_overview": get_learning_overview(user_id)}


@app.put("/api/admin/users/{user_id}/profile")
def admin_update_profile(
    user_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    return {"profile": update_user_profile(user_id, payload)}


@app.post("/api/admin/notes")
def admin_create_note(
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, str]:
    return save_admin_note(payload)


@app.post("/api/admin/generate/today")
def admin_generate_today(
    user_id: str = "user_mom",
    date: str | None = None,
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, str]:
    draft_id = generate_lesson_draft_today(user_id, date or today_iso())
    return {"status": "pending_publish", "draft_id": draft_id}


@app.post("/api/admin/drafts/generate")
def admin_generate_draft(
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, str]:
    draft_id = generate_lesson_draft_workspace(
        user_id=payload.get("user_id", "user_mom"),
        lesson_date=payload.get("lesson_date") or today_iso(),
        admin_instruction=payload.get("admin_instruction"),
        admin_note=payload.get("admin_note"),
        admin_id=str(_admin["login_account"]),
        action="admin_generate_draft",
    )
    return {"status": "pending_publish", "draft_id": draft_id}


@app.post("/api/admin/drafts/generate-week")
def admin_generate_weekly_drafts(
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        drafts = generate_weekly_lesson_draft_workspaces(
            user_id=payload.get("user_id", "user_mom"),
            start_date=payload.get("start_date") or payload.get("lesson_date") or today_iso(),
            days=int(payload.get("days") or 7),
            admin_instruction=payload.get("admin_instruction"),
            admin_note=payload.get("admin_note"),
            admin_id=str(_admin["login_account"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "pending_publish", "drafts": drafts}


@app.put("/api/admin/drafts/{draft_id}/note")
def admin_update_draft_note(
    draft_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return {"draft": update_lesson_draft_note(draft_id, payload.get("admin_note"), str(_admin["login_account"]))}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/admin/drafts/{draft_id}/ai-adjust")
def admin_ai_adjust_draft(
    draft_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    instruction = str(payload.get("admin_instruction") or "").strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="admin_instruction is required")
    try:
        return {"draft": regenerate_lesson_draft_from_instruction(draft_id, instruction, str(_admin["login_account"]))}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/admin/drafts/{draft_id}")
def admin_manual_update_draft(
    draft_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    lesson_json = payload.get("lesson_json") or payload
    if not isinstance(lesson_json, dict):
        raise HTTPException(status_code=400, detail="lesson_json must be an object")
    try:
        return {"draft": manually_update_lesson_draft(draft_id, lesson_json, str(_admin["login_account"]))}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/admin/drafts/{draft_id}/undo")
def admin_undo_draft(
    draft_id: str,
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return {"draft": undo_lesson_draft(draft_id, str(_admin["login_account"]))}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/admin/drafts/{draft_id}/audio")
def admin_generate_draft_audio(
    draft_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return generate_lesson_draft_audio(
            draft_id,
            str(_admin["login_account"]),
            force=bool(payload.get("force", False)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/admin/drafts/audio-batch")
def admin_generate_pending_drafts_audio(
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return generate_pending_lesson_drafts_audio(
            user_id=payload.get("user_id", "user_mom"),
            start_date=payload.get("start_date") or payload.get("lesson_date") or today_iso(),
            days=int(payload.get("days") or 7),
            admin_id=str(_admin["login_account"]),
            force=bool(payload.get("force", False)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/admin/drafts/{draft_id}/publish")
def admin_publish_draft(
    draft_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return publish_lesson_draft_workspace(
            draft_id,
            str(_admin["login_account"]),
            payload.get("reason", "admin_publish_draft"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/admin/lessons/{lesson_asset_id}/audio")
def admin_generate_lesson_audio(
    lesson_asset_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return generate_lesson_asset_audio(
            lesson_asset_id,
            str(_admin["login_account"]),
            force=bool(payload.get("force", False)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/admin/feedback")
def admin_feedback(
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, str]:
    try:
        return save_admin_feedback(payload, str(_admin["login_account"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/admin/lessons/{lesson_asset_id}/draft")
def admin_update_lesson_draft(
    lesson_asset_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return update_lesson_draft(lesson_asset_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/admin/lessons/{lesson_asset_id}/publish")
def admin_publish_lesson(
    lesson_asset_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    try:
        return publish_lesson_asset(lesson_asset_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/admin/lessons/{lesson_asset_id}/rollback")
def admin_rollback_lesson(
    lesson_asset_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    version_id = payload.get("version_id")
    if not version_id:
        raise HTTPException(status_code=400, detail="version_id is required")
    try:
        return rollback_lesson_asset(lesson_asset_id, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/admin/route/{route_item_id}")
def admin_update_route(
    route_item_id: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    if "recommended_order" not in payload:
        raise HTTPException(status_code=400, detail="recommended_order is required")
    return {"route_item": update_route_priority(route_item_id, payload)}


@app.get("/api/admin/exports/learning-log")
def admin_export_learning_log(
    user_id: str = "user_mom",
    date: str | None = None,
    format: str = "markdown",
    _admin: dict[str, Any] = Depends(require_admin_session),
) -> dict[str, Any]:
    if format not in {"markdown", "csv"}:
        raise HTTPException(status_code=400, detail="format must be markdown or csv")
    return export_learning_log(user_id, date or today_iso(), format)
