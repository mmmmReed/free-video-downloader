"""Douyin-specific video parser and downloader.

Bypasses yt-dlp's cookie requirement by using Douyin's public share page API
and iesdouyin.com endpoints directly.

Reference: rathodpratham-dev/douyin_video_downloader (MIT License)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import uuid
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

logger = logging.getLogger("douyin")

_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)

_DOUYIN_HOSTS = {
    "www.douyin.com",
    "v.douyin.com",
    "m.douyin.com",
    "www.iesdouyin.com",
}

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.douyin.com/",
}

_MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
        "Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.douyin.com/",
}

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")


def is_douyin_url(url: str) -> bool:
    """Check whether a URL belongs to Douyin (含无协议、短链、子域名等情况)。"""
    if not url or not isinstance(url, str):
        return False
    low = url.strip().lower()
    if "douyin.com" in low or "douyin.cn" in low or "iesdouyin.com" in low:
        return True
    try:
        host = (urlparse(low).hostname or "").lower()
        return host in _DOUYIN_HOSTS or "douyin.com" in host
    except Exception:
        return False


def _extract_video_id(url: str) -> str:
    """Extract Douyin video ID from a resolved URL."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    for key in ("modal_id", "item_ids", "group_id", "aweme_id"):
        values = qs.get(key)
        if values:
            m = re.search(r"(\d{8,24})", values[0])
            if m:
                return m.group(1)

    for pattern in (r"/video/(\d{8,24})", r"/note/(\d{8,24})", r"/(\d{8,24})(?:/|$)"):
        m = re.search(pattern, parsed.path)
        if m:
            return m.group(1)

    raise ValueError(f"无法从链接中提取抖音视频 ID: {url}")


def _resolve_share_url(session: requests.Session, url: str) -> str:
    """Follow redirects on short share links to get the final URL."""
    resp = session.get(url, timeout=10, allow_redirects=True, headers=_DEFAULT_HEADERS)
    resp.raise_for_status()
    return resp.url


def _decode_urlsafe_b64(value: str) -> bytes:
    normalized = value.replace("-", "+").replace("_", "/")
    normalized += "=" * (-len(normalized) % 4)
    return base64.b64decode(normalized)


def _solve_waf_challenge(html: str) -> tuple[str, str] | None:
    """Solve Douyin's WAF SHA-256 challenge, returning (cookie_name, cookie_value)."""
    m = re.search(r'wci="([^"]+)"\s*,\s*cs="([^"]+)"', html)
    if not m:
        return None

    cookie_name, challenge_blob = m.groups()
    try:
        challenge_data = json.loads(_decode_urlsafe_b64(challenge_blob).decode("utf-8"))
        prefix = _decode_urlsafe_b64(challenge_data["v"]["a"])
        expected = _decode_urlsafe_b64(challenge_data["v"]["c"]).hex()
    except (KeyError, ValueError, TypeError):
        return None

    for candidate in range(1_000_001):
        if sha256(prefix + str(candidate).encode()).hexdigest() == expected:
            challenge_data["d"] = base64.b64encode(str(candidate).encode()).decode()
            cookie_value = base64.b64encode(
                json.dumps(challenge_data, separators=(",", ":")).encode()
            ).decode()
            return cookie_name, cookie_value

    return None


def _fetch_from_share_page(session: requests.Session, video_id: str) -> dict:
    """Fetch video metadata by parsing the iesdouyin.com share page HTML."""
    share_url = f"https://www.iesdouyin.com/share/video/{video_id}/"
    resp = session.get(share_url, headers=_MOBILE_HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    if "Please wait..." in html and "wci=" in html:
        solved = _solve_waf_challenge(html)
        if solved:
            domain = urlparse(share_url).hostname or "www.iesdouyin.com"
            session.cookies.set(solved[0], solved[1], domain=domain, path="/")
            resp = session.get(share_url, headers=_MOBILE_HEADERS, timeout=15)
            resp.raise_for_status()
            html = resp.text

    # Extract _ROUTER_DATA JSON
    marker = "window._ROUTER_DATA = "
    start = html.find(marker)
    if start < 0:
        raise ValueError("抖音分享页面结构异常，无法提取视频数据")

    idx = start + len(marker)
    while idx < len(html) and html[idx].isspace():
        idx += 1

    depth = 0
    in_str = False
    escaped = False
    for cursor in range(idx, len(html)):
        ch = html[cursor]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    router_data = json.loads(html[idx: cursor + 1])
                except json.JSONDecodeError:
                    raise ValueError("抖音页面数据解析失败")
                break
    else:
        raise ValueError("抖音页面数据结构不完整")

    loader = router_data.get("loaderData", {})
    for node in loader.values():
        if not isinstance(node, dict):
            continue
        vinfo = node.get("videoInfoRes", {})
        items = vinfo.get("item_list", [])
        if items and isinstance(items[0], dict):
            return items[0]

    raise ValueError("抖音页面中未找到视频信息")


def _fetch_item_info(session: requests.Session, video_id: str) -> dict:
    """Try the public API first, then fall back to share page parsing."""
    try:
        resp = session.get(
            "https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/",
            params={"item_ids": video_id},
            headers=_DEFAULT_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("item_list", [])
        if items:
            return items[0]
    except Exception as e:
        logger.info("Public API unavailable, falling back to share page: %s", e)

    return _fetch_from_share_page(session, video_id)


def _coerce_non_negative_int(v) -> int | None:
    """将接口里的播放量/点赞等字段转为非负整数；无法解析则返回 None。"""
    if v is None or v is False:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if v >= 0 else None
    if isinstance(v, float):
        if v != v or v < 0:
            return None
        return int(v)
    if isinstance(v, str):
        s = v.strip().replace(",", "").replace(" ", "")
        if not s:
            return None
        try:
            x = float(s)
            if x < 0:
                return None
            return int(x)
        except ValueError:
            return None
    return None


def _stats_dict(item: dict) -> dict | None:
    st = item.get("statistics") or item.get("Statistics")
    if isinstance(st, dict):
        return st
    return None


def _douyin_stat_pick_positive(stats: dict | None, *keys: str) -> int | None:
    if not stats:
        return None
    for k in keys:
        n = _coerce_non_negative_int(stats.get(k))
        if n is not None and n > 0:
            return n
    return None


def _douyin_view_count(item: dict) -> int | None:
    """从 statistics（及备用嵌套）读取播放量；公开接口常省略或为 0，此时交由点赞兜底展示。"""
    for stats in (_stats_dict(item),):
        n = _douyin_stat_pick_positive(
            stats,
            "play_count",
            "playCount",
            "aweme_play_count",
            "awemePlayCount",
            "read_count",
            "readCount",
        )
        if n is not None:
            return n

    video = item.get("video")
    if isinstance(video, dict):
        st2 = video.get("statistics") or video.get("Statistics")
        if isinstance(st2, dict):
            n = _douyin_stat_pick_positive(
                st2, "play_count", "playCount", "aweme_play_count", "awemePlayCount"
            )
            if n is not None:
                return n

    return None


def _douyin_like_count(item: dict) -> int | None:
    """点赞数；在播放量缺失或为 0 时供前端展示互动量。"""
    for stats in (_stats_dict(item),):
        n = _douyin_stat_pick_positive(
            stats,
            "digg_count",
            "diggCount",
            "admire_count",
            "admireCount",
        )
        if n is not None:
            return n
    return None


def _probe_stream_content_length(url: str, session: requests.Session) -> int | None:
    """对直链做 HEAD 或 Range 探测长度（抖音 CDN 有时 HEAD 无长度）。"""
    try:
        r = session.head(url, headers=_MOBILE_HEADERS, timeout=15, allow_redirects=True)
        if r.status_code in (200, 206):
            cl = r.headers.get("Content-Length")
            if cl and str(cl).isdigit():
                return int(cl)
    except Exception:
        pass
    try:
        r = session.get(
            url,
            headers={**_MOBILE_HEADERS, "Range": "bytes=0-0"},
            timeout=15,
            allow_redirects=True,
            stream=True,
        )
        try:
            if r.status_code == 206:
                cr = r.headers.get("Content-Range") or ""
                if "/" in cr:
                    tail = cr.split("/")[-1].strip()
                    if tail.isdigit():
                        return int(tail)
            cl = r.headers.get("Content-Length")
            if cl and str(cl).isdigit():
                return int(cl)
        finally:
            r.close()
    except Exception:
        pass
    return None


def _douyin_estimate_size_from_bitrate(video: dict, duration_sec: int) -> int | None:
    """接口未返回文件大小时，用 bit_rate 列表中的峰值码率 × 时长估算体积（约值）。"""
    if duration_sec <= 0:
        return None
    rates: list[int] = []
    for br in video.get("bit_rate") or []:
        if not isinstance(br, dict):
            continue
        n = br.get("bit_rate") or br.get("Bitrate")
        if isinstance(n, (int, float)) and n > 0:
            rates.append(int(n))
    if not rates:
        return None
    bps = max(rates)
    return int(bps * duration_sec / 8)


def parse_douyin_video(url: str) -> dict:
    """Parse a Douyin URL and return video info in the same format as yt-dlp."""
    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)

    try:
        resolved = _resolve_share_url(session, url)
        video_id = _extract_video_id(resolved)
        item = _fetch_item_info(session, video_id)

        title = item.get("desc", "") or f"douyin_{video_id}"
        author = item.get("author", {}).get("nickname", "")
        video = item.get("video", {})

        play_urls = video.get("play_addr", {}).get("url_list", [])
        if not play_urls:
            raise ValueError("无法获取抖音视频播放地址")

        no_watermark_url = play_urls[0].replace("playwm", "play")

        cover_urls = video.get("cover", {}).get("url_list", [])
        thumbnail = cover_urls[0] if cover_urls else ""

        duration_ms = video.get("duration", 0)
        duration = duration_ms // 1000 if duration_ms > 1000 else duration_ms

        height = video.get("height", 0)
        width = video.get("width", 0)
        quality = f"{height}p" if height else "720p"

        view_count = _douyin_view_count(item)
        like_count = _douyin_like_count(item)

        dur_int = int(duration) if duration else 0
        filesize = _probe_stream_content_length(no_watermark_url, session)
        size_approx = False
        if not filesize and dur_int > 0:
            est = _douyin_estimate_size_from_bitrate(video, dur_int)
            if est:
                filesize = est
                size_approx = True

        formats = [{
            "format_id": "douyin_nowm",
            "ext": "mp4",
            "resolution": f"{width}x{height}" if width and height else "unknown",
            "quality": quality,
            "filesize": filesize,
            "filesize_approx": size_approx,
            "has_video": True,
            "has_audio": True,
            "vcodec": "h264",
            "acodec": "aac",
            "tbr": None,
            "url": no_watermark_url,
        }]

        return {
            "title": title,
            "thumbnail": thumbnail,
            "duration": duration,
            "uploader": author,
            "webpage_url": f"https://www.douyin.com/video/{video_id}",
            "formats": formats,
            "view_count": view_count,
            "like_count": like_count,
            "_douyin": True,
        }
    finally:
        session.close()


def download_douyin_video(url: str, task_id: str, tasks: dict) -> None:
    """Download a Douyin video directly (no yt-dlp) and update task state."""
    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)

    try:
        resolved = _resolve_share_url(session, url)
        video_id = _extract_video_id(resolved)
        item = _fetch_item_info(session, video_id)

        title = item.get("desc", "") or f"douyin_{video_id}"
        play_urls = item.get("video", {}).get("play_addr", {}).get("url_list", [])
        if not play_urls:
            raise ValueError("无法获取抖音视频播放地址")

        video_url = play_urls[0].replace("playwm", "play")

        safe_title = re.sub(r'[<>:"/\\|?*]', "", title)[:50]
        filepath = os.path.join(DOWNLOADS_DIR, f"{task_id}_{safe_title}.mp4")

        tasks[task_id].update({"status": "downloading", "percentage": 0})

        resp = session.get(
            video_url,
            stream=True,
            timeout=(10, 60),
            allow_redirects=True,
            headers=_MOBILE_HEADERS,
        )
        resp.raise_for_status()

        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        temp_path = filepath + ".part"

        with open(temp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = round(downloaded / total * 100, 1)
                    speed = 0
                    tasks[task_id].update({
                        "status": "downloading",
                        "percentage": pct,
                        "speed": f"{downloaded / 1024 / 1024:.1f}MB" if downloaded else "N/A",
                        "eta": 0,
                    })

        os.replace(temp_path, filepath)
        tasks[task_id].update({
            "status": "finished",
            "percentage": 100,
            "filename": filepath,
        })

    except Exception as e:
        tasks[task_id].update({"status": "error", "error": str(e)})
    finally:
        session.close()
