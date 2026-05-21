from contextlib import asynccontextmanager
from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.video import router as video_router
from routers.summary import router as summary_router
from routers.billing import router as billing_router, setup_billing_db
from routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_billing_db()
    auth_paths = sorted(
        {
            getattr(r, "path", "")
            for r in app.routes
            if getattr(r, "path", "").startswith("/api/auth")
        }
    )
    # 便于排查「文档里没有 auth」：若此处为空而代码已 include_router，多半是连到了别的进程/旧实例
    print(f"[boot] main.py: {Path(__file__).resolve()}", flush=True)
    print(f"[boot] /api/auth routes: {auth_paths}", flush=True)
    yield


app = FastAPI(
    title="Free Video Downloader API",
    description="A universal video downloader API powered by yt-dlp",
    version="1.0.0",
    lifespan=lifespan,
)

_cors = os.getenv("CORS_ORIGINS", "").strip()
if _cors == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
elif _cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[x.strip() for x in _cors.split(",") if x.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 开发：前端直连 127.0.0.1:8001 与页面 localhost:3000 不同源，须显式允许 Origin（比 regex 更稳）。
    # 线上请在 .env 设置 CORS_ORIGINS=https://你的域名
    _default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_default_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(video_router)
app.include_router(summary_router)
app.include_router(auth_router)
app.include_router(billing_router)


@app.get("/")
async def root():
    return {"message": "Free Video Downloader API is running", "docs": "/docs"}
