import asyncio
import json
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from services.downloader import (
    cleanup_task,
    get_download_options,
    get_task,
    start_download,
)

router = APIRouter(prefix="/api", tags=["video"])


class ParseRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: str


@router.post("/parse")
async def parse_video(req: ParseRequest):
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, get_download_options, req.url)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def download_video(req: DownloadRequest):
    try:
        task_id = start_download(req.url, req.format_id)
        return {"success": True, "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/progress/{task_id}")
async def progress(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        while True:
            task = get_task(task_id)
            if not task:
                yield {"event": "error", "data": json.dumps({"error": "Task not found"})}
                break

            yield {"data": json.dumps(task)}

            if task["status"] in ("finished", "error"):
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@router.get("/file/{task_id}")
async def get_file(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "finished":
        raise HTTPException(status_code=400, detail="Download not finished yet")

    filepath = task.get("filename", "")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    filename = os.path.basename(filepath)
    # Remove the task_id prefix from the filename for user-friendliness
    if filename.startswith(task_id + "_"):
        filename = filename[len(task_id) + 1:]

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.delete("/file/{task_id}")
async def delete_file(task_id: str):
    success = cleanup_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}
