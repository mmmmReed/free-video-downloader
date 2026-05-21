"""邮箱 + 密码注册登录（JWT）。"""

from __future__ import annotations

import re
import time

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from deps.auth import create_access_token, get_current_user_required
from services import store

# 避免新版 bcrypt 与 passlib 1.7.x 不兼容导致注册 500（bcrypt 模块无 __about__ 等）
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(prefix="/api/auth", tags=["auth"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginBody(BaseModel):
    email: str
    password: str


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register")
async def register(body: RegisterBody):
    email = _normalize_email(body.email)
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    if store.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="该邮箱已注册")

    h = pwd_context.hash(body.password)
    uid = store.create_user(email, h)
    token = create_access_token(uid)
    return {"access_token": token, "token_type": "Bearer", "expires_in": 7 * 86400}


@router.post("/login")
async def login(body: LoginBody):
    email = _normalize_email(body.email)
    user = store.get_user_by_email(email)
    if not user or not pwd_context.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "Bearer", "expires_in": 7 * 86400}


@router.get("/me")
async def me(user: dict = Depends(get_current_user_required)):
    fresh = store.get_user_by_id(user["id"])
    if not fresh:
        raise HTTPException(status_code=401, detail="用户不存在")
    vu = fresh.get("vip_until")
    now_ts = int(time.time())
    is_vip = bool(vu and int(vu) > now_ts)
    return {
        "id": fresh["id"],
        "email": fresh["email"],
        "vip_until": vu,
        "is_vip": is_vip,
    }
