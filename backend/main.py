from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.video import router as video_router

app = FastAPI(
    title="Free Video Downloader API",
    description="A universal video downloader API powered by yt-dlp",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router)


@app.get("/")
async def root():
    return {"message": "Free Video Downloader API is running", "docs": "/docs"}
