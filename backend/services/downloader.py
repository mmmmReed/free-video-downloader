import asyncio
import glob
import os
import uuid
from typing import Callable

from yt_dlp import YoutubeDL

from services.douyin import is_douyin_url, parse_douyin_video, download_douyin_video

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def _find_ffmpeg() -> str | None:
    """Auto-detect ffmpeg location on Windows."""
    import shutil
    path = shutil.which("ffmpeg")
    if path:
        return os.path.dirname(path)

    search_patterns = [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\*ffmpeg*\*\bin"),
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        os.path.expanduser("~\\scoop\\shims"),
    ]
    for pattern in search_patterns:
        for match in glob.glob(pattern):
            if os.path.isfile(os.path.join(match, "ffmpeg.exe")):
                return match
    return None


FFMPEG_LOCATION = _find_ffmpeg()

# In-memory task store: task_id -> task state
tasks: dict[str, dict] = {}


def parse_video(url: str) -> dict:
    """Extract video metadata without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    cf = os.getenv("YTDLP_COOKIES_FILE", "").strip()
    if cf and os.path.isfile(cf):
        ydl_opts["cookiefile"] = cf
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        info = ydl.sanitize_info(info)

    formats = []
    seen = set()
    for f in info.get("formats", []):
        resolution = f.get("resolution", "audio only")
        height = f.get("height")
        ext = f.get("ext", "")
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")

        has_video = vcodec != "none"
        has_audio = acodec != "none"

        if has_video and height:
            quality = f"{height}p"
        elif not has_video and has_audio:
            quality = "audio"
        else:
            continue

        key = (f.get("format_id"), ext, quality)
        if key in seen:
            continue
        seen.add(key)

        formats.append({
            "format_id": f.get("format_id"),
            "ext": ext,
            "resolution": resolution,
            "quality": quality,
            "filesize": f.get("filesize") or f.get("filesize_approx"),
            "has_video": has_video,
            "has_audio": has_audio,
            "vcodec": vcodec,
            "acodec": acodec,
            "tbr": f.get("tbr"),
        })

    formats.sort(key=lambda x: x.get("tbr") or 0, reverse=True)

    vc = info.get("view_count")
    if vc is None:
        vc = info.get("concurrent_view_count")
    view_count = None
    if isinstance(vc, (int, float)) and vc >= 0:
        view_count = int(vc)

    return {
        "title": info.get("title", ""),
        "thumbnail": info.get("thumbnail", ""),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", ""),
        "webpage_url": info.get("webpage_url", ""),
        "formats": formats,
        "view_count": view_count,
    }


def _build_combined_formats(formats: list[dict]) -> list[dict]:
    """Build user-friendly combined format options (video+audio merged)."""
    video_formats = [f for f in formats if f["has_video"]]
    audio_formats = [f for f in formats if not f["has_video"] and f["has_audio"]]

    combined = []
    seen_qualities = set()

    for vf in video_formats:
        quality = vf["quality"]
        if quality in seen_qualities:
            continue
        seen_qualities.add(quality)

        if vf["has_audio"]:
            combined.append({
                "format_id": vf["format_id"],
                "ext": vf["ext"],
                "quality": quality,
                "resolution": vf["resolution"],
                "filesize": vf["filesize"],
                "label": f"{quality} ({vf['ext']})",
            })
        elif audio_formats:
            best_audio = audio_formats[0]
            combined.append({
                "format_id": f"{vf['format_id']}+{best_audio['format_id']}",
                "ext": "mp4",
                "quality": quality,
                "resolution": vf["resolution"],
                "filesize": (vf["filesize"] or 0) + (best_audio["filesize"] or 0) if vf["filesize"] and best_audio["filesize"] else None,
                "label": f"{quality} (mp4)",
            })

    for af in audio_formats[:1]:
        combined.append({
            "format_id": af["format_id"],
            "ext": af["ext"],
            "quality": "audio",
            "resolution": "audio only",
            "filesize": af["filesize"],
            "label": f"Audio only ({af['ext']})",
        })

    return combined


def get_download_options(url: str) -> dict:
    """Parse video and return user-friendly download options."""
    if is_douyin_url(url):
        raw = parse_douyin_video(url)
        combined = [{
            "format_id": f["format_id"],
            "ext": f["ext"],
            "quality": f["quality"],
            "resolution": f["resolution"],
            "filesize": f["filesize"],
            "filesize_approx": bool(f.get("filesize_approx")),
            "label": f"{f['quality']} ({f['ext']})",
        } for f in raw["formats"]]
        return {
            "title": raw["title"],
            "thumbnail": raw["thumbnail"],
            "duration": raw["duration"],
            "uploader": raw["uploader"],
            "webpage_url": raw["webpage_url"],
            "formats": combined,
            "view_count": raw.get("view_count"),
            "like_count": raw.get("like_count"),
            "_douyin": True,
        }

    raw = parse_video(url)
    combined = _build_combined_formats(raw["formats"])
    return {
        "title": raw["title"],
        "thumbnail": raw["thumbnail"],
        "duration": raw["duration"],
        "uploader": raw["uploader"],
        "webpage_url": raw["webpage_url"],
        "formats": combined,
        "view_count": raw.get("view_count"),
    }


def start_download(url: str, format_id: str) -> str:
    """Start a download task and return task_id."""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "percentage": 0,
        "speed": "",
        "eta": 0,
        "filename": "",
        "error": "",
    }

    if is_douyin_url(url):
        import threading
        thread = threading.Thread(
            target=download_douyin_video,
            args=(url, task_id, tasks),
            daemon=True,
        )
        thread.start()
        return task_id

    def progress_hook(d: dict):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            percentage = (downloaded / total * 100) if total else 0
            speed = d.get("speed", 0)
            eta = d.get("eta", 0)
            tasks[task_id].update({
                "status": "downloading",
                "percentage": round(percentage, 1),
                "speed": f"{speed / 1024 / 1024:.1f}MB/s" if speed else "N/A",
                "eta": eta or 0,
            })
        elif d["status"] == "finished":
            filepath = d.get("filename", "")
            tasks[task_id].update({
                "status": "merging",
                "percentage": 100,
                "filename": filepath,
            })

    def postprocessor_hook(d: dict):
        if d["status"] == "finished":
            filepath = d.get("info_dict", {}).get("filepath", "")
            if filepath:
                tasks[task_id]["filename"] = filepath
            tasks[task_id]["status"] = "finished"

    ydl_opts = {
        "format": format_id,
        "outtmpl": os.path.join(DOWNLOADS_DIR, f"{task_id}_%(title).50s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }
    if FFMPEG_LOCATION:
        ydl_opts["ffmpeg_location"] = FFMPEG_LOCATION

    import threading

    def _download():
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url)
                if tasks[task_id]["status"] != "finished":
                    filepath = ydl.prepare_filename(info)
                    mp4_path = os.path.splitext(filepath)[0] + ".mp4"
                    if os.path.exists(mp4_path):
                        filepath = mp4_path
                    tasks[task_id].update({
                        "status": "finished",
                        "percentage": 100,
                        "filename": filepath,
                    })
        except Exception as e:
            tasks[task_id].update({
                "status": "error",
                "error": str(e),
            })

    thread = threading.Thread(target=_download, daemon=True)
    thread.start()

    return task_id


def get_task(task_id: str) -> dict | None:
    return tasks.get(task_id)


def cleanup_task(task_id: str) -> bool:
    """Remove task and its downloaded file."""
    task = tasks.pop(task_id, None)
    if task and task.get("filename"):
        try:
            os.remove(task["filename"])
        except OSError:
            pass
        return True
    return False
