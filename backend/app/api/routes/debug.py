from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_current_user, get_request_ip_hash
from app.db.dependencies import get_db_session
from app.schemas import AuthMessageResponse, DebugEventRequest
from app.services.debug_events import create_debug_event, generate_anonymous_id


router = APIRouter(tags=["debug"])


@router.post("/api/debug-events", response_model=AuthMessageResponse, status_code=202)
async def create_debug_event_route(
    payload: DebugEventRequest,
    request: Request,
    current_user=Depends(get_optional_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    anonymous_id = request.cookies.get("tabletki_anon_id") or generate_anonymous_id()
    await create_debug_event(
        db_session,
        event=payload,
        anonymous_id=anonymous_id,
        user_id=current_user.id if current_user is not None else None,
        request_id=request.headers.get("x-request-id") or getattr(request.state, "request_id", None),
        user_agent=request.headers.get("user-agent"),
        ip_hash=get_request_ip_hash(request),
    )
    response = JSONResponse(AuthMessageResponse(message="accepted").model_dump(), status_code=202)
    if "tabletki_anon_id" not in request.cookies:
        response.set_cookie("tabletki_anon_id", anonymous_id, max_age=60 * 60 * 24 * 365, path="/", samesite="lax")
    return response
