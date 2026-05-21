"""SQLite：用户、订单、AI 用量与 Webhook 幂等。"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "billing.sqlite"


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS processed_webhook_events (
                event_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                vip_until INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stripe_checkout_session_id TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                currency TEXT,
                amount_minor INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                paid_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
            CREATE INDEX IF NOT EXISTS idx_orders_session ON orders(stripe_checkout_session_id);

            CREATE TABLE IF NOT EXISTS summary_daily_usage (
                user_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, day),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )


def try_claim_webhook_event(event_id: str) -> bool:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO processed_webhook_events (event_id) VALUES (?)",
                (event_id,),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def create_user(email: str, password_hash: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash),
        )
        return int(cur.lastrowid)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, vip_until, created_at FROM users WHERE email = ? COLLATE NOCASE",
            (email.strip().lower(),),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, vip_until, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def extend_user_vip(user_id: int, duration_seconds: int) -> int:
    """将 VIP 截止顺延 duration_seconds；已在期内则叠加上限从当前 vip_until 起算。"""
    import time

    now = int(time.time())
    with get_conn() as conn:
        row = conn.execute(
            "SELECT vip_until FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            raise ValueError("user not found")
        current = row["vip_until"] or 0
        base = max(now, int(current))
        new_until = base + duration_seconds
        conn.execute(
            "UPDATE users SET vip_until = ? WHERE id = ?", (new_until, user_id)
        )
        return new_until


def create_pending_order(user_id: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO orders (user_id, status) VALUES (?, 'pending')",
            (user_id,),
        )
        return int(cur.lastrowid)


def attach_session_to_order(order_id: int, stripe_session_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE orders SET stripe_checkout_session_id = ? WHERE id = ?",
            (stripe_session_id, order_id),
        )


def get_order_by_session_id(session_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, user_id, stripe_checkout_session_id, status, currency, amount_minor, created_at, paid_at FROM orders WHERE stripe_checkout_session_id = ?",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None


def get_order_by_id(order_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, user_id, stripe_checkout_session_id, status, currency, amount_minor, created_at, paid_at FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        return dict(row) if row else None


def mark_order_paid(order_id: int, currency: str | None, amount_minor: int | None) -> bool:
    """pending → paid；已 paid 返回 False（幂等）。"""
    import time

    paid_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE orders SET status = 'paid', paid_at = ?, currency = COALESCE(?, currency), amount_minor = COALESCE(?, amount_minor)
            WHERE id = ? AND status = 'pending'
            """,
            (paid_at, currency, amount_minor, order_id),
        )
        return cur.rowcount > 0


def mark_order_expired_by_session(session_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE orders SET status = 'expired' WHERE stripe_checkout_session_id = ? AND status = 'pending'",
            (session_id,),
        )


def consume_summary_quota(user_id: int, daily_limit: int, day_utc: str) -> bool:
    """非 VIP：原子占用一次当日额度。已满返回 False。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT count FROM summary_daily_usage WHERE user_id = ? AND day = ?",
            (user_id, day_utc),
        ).fetchone()
        c = int(row["count"]) if row else 0
        if c >= daily_limit:
            conn.rollback()
            return False
        conn.execute(
            """
            INSERT INTO summary_daily_usage (user_id, day, count) VALUES (?, ?, 1)
            ON CONFLICT(user_id, day) DO UPDATE SET count = count + 1
            """,
            (user_id, day_utc),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def user_is_vip(user: dict[str, Any]) -> bool:
    import time

    vu = user.get("vip_until")
    if vu is None:
        return False
    return int(vu) > int(time.time())
