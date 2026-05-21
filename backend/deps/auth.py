"""JWT 与登录用户依赖。"""

from __future__ import annotations

import os
import time
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException

from services import store

JWT_ALG = "HS256"


def jwt_secret() -> str:
    s = os.getenv("JWT_SECRET", "").strip()
    if not s:
        raise HTTPException(status_code=503, detail="服务未配置 JWT_SECRET")
    return s


def create_access_token(user_id: int, expires_seconds: int = 7 * 86400) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": str(user_id), "typ": "access", "iat": now, "exp": now + expires_seconds},
        jwt_secret(),
        algorithm=JWT_ALG,
    )


def decode_token(authorization: str | None) -> dict[str, Any] | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        return jwt.decode(token, jwt_secret(), algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None


def get_current_user_optional(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any] | None:
    payload = decode_token(authorization)
    if not payload or payload.get("typ") != "access":
        return None
    uid = int(payload["sub"])
    user = store.get_user_by_id(uid)
    return user


def get_current_user_required(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any]:
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def check_summary_quota(
    user: dict[str, Any] = Depends(get_current_user_required),
) -> dict[str, Any]:
    """VIP 无限次；否则占用每日免费额度（读库最新 vip_until）。"""
    import datetime

    fresh = store.get_user_by_id(user["id"])
    if not fresh:
        raise HTTPException(status_code=401, detail="用户不存在")

    if store.user_is_vip(fresh):
        return fresh

    limit = int(os.getenv("SUMMARY_FREE_DAILY_LIMIT", "1"))
    day = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    if not store.consume_summary_quota(fresh["id"], limit, day):
        raise HTTPException(
            status_code=402,
            detail=f"今日免费 AI 总结次数已用完（每日 {limit} 次），请登录后开通 VIP（¥9.9 起）",
        )
    return fresh
