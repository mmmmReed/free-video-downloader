"""API routes for AI video summarization."""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from services.subtitle import extract_subtitle
from services.ai_summary import summarize_stream, chat_stream

router = APIRouter(prefix="/api", tags=["summary"])


class SubtitleRequest(BaseModel):
    url: str


class SummarizeRequest(BaseModel):
    url: str
    subtitle_text: str = ""
    video_title: str = ""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    subtitle_text: str
    video_title: str = ""
    history: list[ChatMessage] = []
    question: str


@router.post("/subtitle")
async def get_subtitle(req: SubtitleRequest):
    """Extract subtitles from a video URL."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, extract_subtitle, req.url)
        if result.get("error"):
            return {"success": False, "error": result["error"], "data": result}
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/summarize")
async def summarize_video(req: SummarizeRequest):
    """Generate AI summary of video content via SSE streaming."""
    subtitle_text = req.subtitle_text

    if not subtitle_text:
        try:
            loop = asyncio.get_event_loop()
            sub_result = await loop.run_in_executor(
                None, extract_subtitle, req.url
            )
            subtitle_text = sub_result.get("full_text", "")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"字幕提取失败: {str(e)}"
            )

    if not subtitle_text:
        raise HTTPException(status_code=400, detail="该视频没有可用的字幕，无法生成总结")

    async def event_generator():
        try:
            loop = asyncio.get_event_loop()
            gen = summarize_stream(subtitle_text, req.video_title)
            while True:
                try:
                    chunk = await loop.run_in_executor(None, next, gen)
                    yield {
                        "data": json.dumps(
                            {"content": chunk, "done": False},
                            ensure_ascii=False,
                        )
                    }
                except StopIteration:
                    break
            yield {
                "data": json.dumps(
                    {"content": "", "done": True},
                    ensure_ascii=False,
                )
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": str(e), "done": True},
                    ensure_ascii=False,
                ),
            }

    return EventSourceResponse(event_generator())


@router.post("/chat")
async def chat_with_video(req: ChatRequest):
    """AI Q&A about video content via SSE streaming."""
    if not req.subtitle_text:
        raise HTTPException(status_code=400, detail="缺少字幕内容")

    history = [{"role": m.role, "content": m.content} for m in req.history]

    async def event_generator():
        try:
            loop = asyncio.get_event_loop()
            gen = chat_stream(
                req.subtitle_text, req.video_title, history, req.question
            )
            while True:
                try:
                    chunk = await loop.run_in_executor(None, next, gen)
                    yield {
                        "data": json.dumps(
                            {"content": chunk, "done": False},
                            ensure_ascii=False,
                        )
                    }
                except StopIteration:
                    break
            yield {
                "data": json.dumps(
                    {"content": "", "done": True},
                    ensure_ascii=False,
                )
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": str(e), "done": True},
                    ensure_ascii=False,
                ),
            }

    return EventSourceResponse(event_generator())
