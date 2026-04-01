from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_ip_hash
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.schemas import (
    AuthMessageResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth import (
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    create_access_token,
    create_auth_session,
    create_email_verification_code,
    create_password_reset_code,
    create_refresh_token,
    decode_token,
    ensure_utc,
    get_auth_session,
    revoke_all_user_sessions,
    revoke_auth_session,
    rotate_auth_session,
    set_auth_cookies,
    seconds_until_password_reset_code_can_be_resent,
    seconds_until_verification_code_can_be_resent,
    validate_email_verification_code,
    validate_password_reset_code,
    verify_password,
)
from app.services.mail import send_password_reset_code_email, send_verification_code_email
from app.services.users import (
    accept_terms,
    create_user,
    get_user_by_email,
    get_user_by_id,
    mark_email_verified,
    serialize_user,
    update_last_login,
    update_user_password,
)


router = APIRouter(tags=["auth"])
settings = Settings()


@router.post("/api/auth/register", response_model=AuthMessageResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db_session: AsyncSession = Depends(get_db_session)) -> AuthMessageResponse:
    if not settings.feature_registration_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="registration is disabled")

    user = await get_user_by_email(db_session, payload.email)
    if user is not None and user.email_verified_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")
    if user is None:
        user = await create_user(
            db_session,
            email=str(payload.email),
            password=payload.password,
            accepted_terms=True,
        )
    else:
        cooldown_remaining = await seconds_until_verification_code_can_be_resent(
            db_session,
            user_id=user.id,
            settings=settings,
        )
        if cooldown_remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"verification code can be resent in {cooldown_remaining} seconds",
            )
        await update_user_password(db_session, user, payload.password)
        await accept_terms(db_session, user)

    code = await create_email_verification_code(db_session, user_id=user.id, settings=settings)
    await send_verification_code_email(recipient=user.email, code=code, settings=settings)
    return AuthMessageResponse(message="verification code sent")


@router.post("/api/auth/verify-email", response_model=AuthMessageResponse)
async def verify_email(payload: VerifyEmailRequest, db_session: AsyncSession = Depends(get_db_session)) -> AuthMessageResponse:
    user = await get_user_by_email(db_session, payload.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    is_valid = await validate_email_verification_code(
        db_session,
        user_id=user.id,
        code=payload.code,
        settings=settings,
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid verification code")
    await mark_email_verified(
        db_session,
        user,
        make_admin=user.email in settings.bootstrap_admin_emails(),
    )
    return AuthMessageResponse(message="email verified")


@router.post("/api/auth/resend-verification-code", response_model=AuthMessageResponse)
async def resend_verification_code(
    payload: ForgotPasswordRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    user = await get_user_by_email(db_session, payload.email)
    if user is None or user.email_verified_at is not None:
        return AuthMessageResponse(message="verification code sent")
    cooldown_remaining = await seconds_until_verification_code_can_be_resent(
        db_session,
        user_id=user.id,
        settings=settings,
    )
    if cooldown_remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"verification code can be resent in {cooldown_remaining} seconds",
        )
    code = await create_email_verification_code(db_session, user_id=user.id, settings=settings)
    await send_verification_code_email(recipient=user.email, code=code, settings=settings)
    return AuthMessageResponse(message="verification code sent")


@router.post("/api/auth/login", response_model=AuthMessageResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    user = await get_user_by_email(db_session, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if user.email_verified_at is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="email is not verified")
    if user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user is blocked")

    auth_session = await create_auth_session(
        db_session,
        user_id=user.id,
        user_agent=request.headers.get("user-agent"),
        ip_hash=get_request_ip_hash(request),
        settings=settings,
    )
    await update_last_login(db_session, user)
    response = JSONResponse(AuthMessageResponse(message="logged in").model_dump())
    set_auth_cookies(
        response,
        access_token=create_access_token(user=user, session_id=auth_session.id, settings=settings),
        refresh_token=create_refresh_token(
            user=user,
            session_id=auth_session.id,
            refresh_jti=auth_session.refresh_jti,
            settings=settings,
        ),
        settings=settings,
    )
    return response


@router.post("/api/auth/refresh", response_model=AuthMessageResponse)
async def refresh(
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token missing")
    try:
        payload = decode_token(refresh_token, settings, expected_type="refresh")
    except jwt.InvalidTokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token") from error

    auth_session = await get_auth_session(db_session, payload["session_id"])
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or auth_session.refresh_jti != payload.get("jti")
        or ensure_utc(auth_session.expires_at) < datetime.now(UTC)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh session is invalid")

    user = await get_user_by_id(db_session, payload["sub"])
    if user is None or user.is_blocked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not available")

    auth_session = await rotate_auth_session(db_session, auth_session=auth_session, settings=settings)
    response = JSONResponse(AuthMessageResponse(message="refreshed").model_dump())
    set_auth_cookies(
        response,
        access_token=create_access_token(user=user, session_id=auth_session.id, settings=settings),
        refresh_token=create_refresh_token(
            user=user,
            session_id=auth_session.id,
            refresh_jti=auth_session.refresh_jti,
            settings=settings,
        ),
        settings=settings,
    )
    return response


@router.post("/api/auth/logout", response_model=AuthMessageResponse)
async def logout(
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    if refresh_token:
        try:
            payload = decode_token(refresh_token, settings, expected_type="refresh")
            auth_session = await get_auth_session(db_session, payload["session_id"])
            if auth_session is not None and auth_session.revoked_at is None:
                await revoke_auth_session(db_session, auth_session)
        except jwt.InvalidTokenError:
            pass

    response = JSONResponse(AuthMessageResponse(message="logged out").model_dump())
    clear_auth_cookies(response, settings)
    return response


@router.get("/api/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)) -> UserResponse:
    return serialize_user(current_user)


@router.post("/api/auth/forgot-password", response_model=AuthMessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    user = await get_user_by_email(db_session, payload.email)
    if user is None or user.email_verified_at is None or user.is_blocked:
        return AuthMessageResponse(message="password reset code sent")
    cooldown_remaining = await seconds_until_password_reset_code_can_be_resent(
        db_session,
        user_id=user.id,
        settings=settings,
    )
    if cooldown_remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"password reset code can be resent in {cooldown_remaining} seconds",
        )
    code = await create_password_reset_code(db_session, user_id=user.id, settings=settings)
    await send_password_reset_code_email(recipient=user.email, code=code, settings=settings)
    return AuthMessageResponse(message="password reset code sent")


@router.post("/api/auth/reset-password", response_model=AuthMessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> AuthMessageResponse:
    user = await get_user_by_email(db_session, payload.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    is_valid = await validate_password_reset_code(
        db_session,
        user_id=user.id,
        code=payload.code,
        settings=settings,
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid reset code")
    await update_user_password(db_session, user, payload.password)
    await revoke_all_user_sessions(db_session, user.id)
    return AuthMessageResponse(message="password updated")
