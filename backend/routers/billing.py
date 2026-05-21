"""Stripe Checkout 单次付款（非订阅）+ Webhook；订单 pending→paid / expired。"""

from __future__ import annotations

import logging
import os
from typing import Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from deps.auth import get_current_user_required
from services import store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _stripe_metadata_as_dict(raw: Any) -> dict[str, Any]:
    """Checkout Session.metadata 为 StripeObject：无 .get() / .keys()，须用 to_dict()。"""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    to_dict = getattr(raw, "to_dict", None)
    if callable(to_dict):
        try:
            d = to_dict()
            if isinstance(d, dict):
                return {str(k): v for k, v in d.items()}
        except Exception as e:
            logger.warning("stripe metadata to_dict 失败: %s", e)
    return {}


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise HTTPException(status_code=503, detail=f"服务未配置 {name}")
    return v


def _stripe_user_message(exc: stripe.error.StripeError) -> str:
    raw = (exc.user_message or str(exc)).strip()
    lower = raw.lower()
    if "payment" in lower and "recurring" in lower:
        return (
            "Stripe 价格类型不匹配：本项目使用「单次付款」(mode=payment)。请在 Stripe 控制台为该商品新建「一次性」(One-time) 价格，"
            "将新的 price_xxx 写入环境变量 STRIPE_PRICE_ID；不要使用「按月/按年订阅」类 Price。"
        )
    if "idempotent" in lower and "same parameters" in lower:
        return (
            "Stripe 幂等键冲突：此前用同一密钥发起过参数不同的结账。"
            "后端已改为每笔订单独立密钥；请直接再点一次「立即开通」。若仍报错可等待约 1 小时后再试。"
        )
    return raw


def _stripe_secret() -> str:
    return _require_env("STRIPE_SECRET_KEY")


def _price_id() -> str:
    return _require_env("STRIPE_PRICE_ID")


def _frontend_base_url() -> str:
    return _require_env("FRONTEND_PUBLIC_URL").rstrip("/")


def _vip_duration_seconds() -> int:
    days = int(os.getenv("VIP_DURATION_DAYS", "30"))
    return max(1, days) * 86400


def fulfill_payment_session(session: stripe.checkout.Session) -> dict[str, Any]:
    """
    幂等履约：payment + paid → orders.paid + 延长 vip。
    不向 Stripe Webhook 抛 HTTP 业务错误（仅日志），避免误触发无限重试。
    """
    if session.mode != "payment":
        return {"fulfilled": False, "reason": "not_payment_mode"}
    if session.payment_status != "paid":
        return {"fulfilled": False, "reason": "not_paid"}

    meta = _stripe_metadata_as_dict(session.metadata)
    try:
        user_id = int(meta.get("user_id", "0"))
        order_id = int(meta.get("order_id", "0"))
    except (TypeError, ValueError):
        logger.warning("checkout session %s 缺少 user_id/order_id metadata", session.id)
        return {"fulfilled": False, "reason": "bad_metadata"}

    ord_row = store.get_order_by_id(order_id)
    if not ord_row or ord_row["user_id"] != user_id:
        logger.warning("订单不匹配 session=%s order=%s", session.id, order_id)
        return {"fulfilled": False, "reason": "order_mismatch"}
    if ord_row["stripe_checkout_session_id"] != session.id:
        logger.warning("会话 id 与订单不一致 session=%s", session.id)
        return {"fulfilled": False, "reason": "session_mismatch"}

    if ord_row["status"] == "paid":
        u = store.get_user_by_id(user_id)
        return {
            "fulfilled": True,
            "already_paid": True,
            "vip_until": u.get("vip_until") if u else None,
        }

    cur = getattr(session, "currency", None)
    amt = getattr(session, "amount_total", None)
    paid_ok = store.mark_order_paid(order_id, cur, amt)
    if paid_ok:
        new_until = store.extend_user_vip(user_id, _vip_duration_seconds())
        return {
            "fulfilled": True,
            "already_paid": False,
            "vip_until": new_until,
        }

    u = store.get_user_by_id(user_id)
    return {
        "fulfilled": True,
        "already_paid": True,
        "vip_until": u.get("vip_until") if u else None,
    }


class VerifySessionBody(BaseModel):
    session_id: str


@router.post("/checkout-session")
async def create_checkout_session(
    user: dict = Depends(get_current_user_required),
):
    """需登录；一次性收款 Checkout（Stripe Price 须为 one-time，例如 CNY ¥9.9）。"""
    stripe.api_key = _stripe_secret()
    price_id = _price_id()
    base = _frontend_base_url()

    order_id = store.create_pending_order(user["id"])
    # Stripe：同一 idempotency key 只能绑定同一组请求参数。原先「用户+UTC 小时」在换 Price /
    # 改 Checkout 参数后仍相同，会触发报错。每笔 pending 订单唯一，故按 order_id 生成。
    idempotency_key = f"checkout-order-{order_id}"

    params: dict[str, Any] = {
        "mode": "payment",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{base}/?stripe_session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{base}/#pricing",
        "metadata": {
            "user_id": str(user["id"]),
            "order_id": str(order_id),
        },
        "customer_email": user["email"],
    }

    try:
        session = stripe.checkout.Session.create(
            **params,
            idempotency_key=idempotency_key,
        )
    except stripe.error.StripeError as e:
        logger.warning("Stripe Checkout 创建失败: %s", e)
        raise HTTPException(status_code=400, detail=_stripe_user_message(e)) from e

    if not session.id or not session.url:
        raise HTTPException(status_code=500, detail="Stripe 未返回结账会话")

    store.attach_session_to_order(order_id, session.id)
    return {"url": session.url, "order_id": order_id}


@router.post("/verify-session")
async def verify_checkout_session(
    body: VerifySessionBody,
    user: dict = Depends(get_current_user_required),
):
    """前端回跳校验；幂等。"""
    stripe.api_key = _stripe_secret()
    sid = body.session_id.strip()
    if not sid.startswith("cs_"):
        raise HTTPException(status_code=400, detail="无效的 session_id")

    try:
        session = stripe.checkout.Session.retrieve(sid)
    except stripe.error.InvalidRequestError:
        raise HTTPException(status_code=404, detail="找不到该结账会话") from None
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message or e)) from e

    meta = _stripe_metadata_as_dict(session.metadata)
    try:
        meta_uid = int(meta.get("user_id", 0))
    except (TypeError, ValueError):
        meta_uid = 0
    if meta_uid != user["id"]:
        raise HTTPException(status_code=403, detail="该支付会话不属于当前登录账号")

    if session.payment_status != "paid":
        raise HTTPException(status_code=400, detail="订单尚未完成支付")

    res = fulfill_payment_session(session)
    if not res.get("fulfilled"):
        raise HTTPException(status_code=400, detail=f"履约未完成：{res.get('reason', 'unknown')}")

    fresh = store.get_user_by_id(user["id"])
    return {
        "ok": True,
        "vip_until": fresh.get("vip_until") if fresh else None,
        "is_vip": store.user_is_vip(fresh) if fresh else False,
    }


@router.post("/webhook")
async def stripe_webhook(request: Request):
    stripe.api_key = _stripe_secret()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="未配置 STRIPE_WEBHOOK_SECRET")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="缺少 Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效 payload: {e}") from e
    except stripe.error.SignatureVerificationError as e:
        logger.warning("Webhook 签名校验失败: %s", e)
        raise HTTPException(status_code=400, detail="签名校验失败") from e

    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="无效事件")

    if not store.try_claim_webhook_event(event_id):
        return {"received": True, "duplicate": True}

    etype = event["type"]
    data_object = event["data"]["object"]

    try:
        if etype == "checkout.session.completed":
            sid = data_object.get("id")
            if sid:
                sess = stripe.checkout.Session.retrieve(sid)
                fulfill_payment_session(sess)

        elif etype == "checkout.session.expired":
            sid = data_object.get("id")
            if sid:
                store.mark_order_expired_by_session(sid)
    except stripe.error.StripeError as e:
        logger.exception("Webhook 处理 Stripe 错误: %s", e)
        raise HTTPException(status_code=500, detail="Webhook 处理失败") from e

    return {"received": True}


def setup_billing_db() -> None:
    store.init_db()
