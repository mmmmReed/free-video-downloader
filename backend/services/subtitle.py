"""Subtitle extraction service using yt-dlp."""

import json
import re
import requests
from yt_dlp import YoutubeDL

from services.douyin import (
    _DEFAULT_HEADERS,
    _extract_video_id,
    _fetch_item_info,
    _resolve_share_url,
    is_douyin_url,
)


SUBTITLE_LANGS = ["zh-Hans", "zh", "zh-CN", "en", "ja", "ko"]

_BILIBILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

_BILIBILI_SUB_LANG_PRIORITY = ["ai-zh", "zh-Hans", "zh", "zh-CN", "ai-en", "en"]


def _normalize_media_url(url: str) -> str:
    """去掉 BOM/零宽字符；无协议时补全 https，便于 urlparse 识别主机名。"""
    u = (url or "").strip().replace("\ufeff", "").replace("\u200b", "")
    if not u:
        return u
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u.lstrip("/")
    return u


def _parse_json3(data: dict) -> list[dict]:
    """Parse json3 subtitle format into structured segments."""
    segments = []
    for event in data.get("events", []):
        start_ms = event.get("tStartMs", 0)
        duration_ms = event.get("dDurationMs", 0)
        segs = event.get("segs")
        if not segs:
            continue
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if not text or text == "\n":
            continue
        segments.append({
            "start": round(start_ms / 1000, 2),
            "end": round((start_ms + duration_ms) / 1000, 2),
            "text": text,
        })
    return segments


def _parse_vtt(content: str) -> list[dict]:
    """Parse VTT subtitle content into structured segments."""
    segments = []
    pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})"
    )

    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                start = _timestamp_to_seconds(match.group(1))
                end = _timestamp_to_seconds(match.group(2))
                text_lines = lines[i + 1:]
                text = " ".join(
                    re.sub(r"<[^>]+>", "", l) for l in text_lines
                ).strip()
                if text:
                    segments.append({"start": start, "end": end, "text": text})
                break
    return segments


def _parse_srt(content: str) -> list[dict]:
    """Parse SRT subtitle content into structured segments."""
    segments = []
    pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})"
    )

    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                start = _timestamp_to_seconds(match.group(1).replace(",", "."))
                end = _timestamp_to_seconds(match.group(2).replace(",", "."))
                text_lines = lines[i + 1:]
                text = " ".join(l.strip() for l in text_lines).strip()
                if text:
                    segments.append({"start": start, "end": end, "text": text})
                break
    return segments


def _timestamp_to_seconds(ts: str) -> float:
    """Convert HH:MM:SS.mmm to seconds."""
    parts = ts.split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return round(h * 3600 + m * 60 + s, 2)


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _deduplicate_segments(segments: list[dict]) -> list[dict]:
    """Remove duplicate/overlapping subtitle segments."""
    if not segments:
        return segments
    result = []
    prev_text = ""
    for seg in segments:
        text = seg["text"].strip()
        if text and text != prev_text:
            result.append(seg)
            prev_text = text
    return result


def _douyin_fetch_caption_json(url: str) -> dict | None:
    try:
        resp = requests.get(
            url,
            headers={**_DEFAULT_HEADERS, "Referer": "https://www.douyin.com/"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _douyin_segments_from_utterances(data: dict) -> tuple[list[dict], str]:
    lang = str(data.get("language") or "zh")
    utterances = data.get("utterances") or []
    segments: list[dict] = []
    for u in utterances:
        text = (u.get("text") or "").strip()
        if not text:
            continue
        st = float(u.get("start_time") or 0) / 1000.0
        et = float(u.get("end_time") or 0) / 1000.0
        segments.append({
            "start": round(st, 2),
            "end": round(et, 2),
            "text": text,
        })
    return segments, lang


def _try_douyin_caption_segments(aweme: dict) -> dict | None:
    """Parse Douyin auto-caption JSON / cla / subtitleInfos when present on item."""
    cap_headers = {**_DEFAULT_HEADERS, "Referer": "https://www.douyin.com/"}

    for sticker in aweme.get("interaction_stickers") or []:
        if not isinstance(sticker, dict):
            continue
        info = sticker.get("auto_video_caption_info") or {}
        for cap in info.get("auto_captions") or []:
            if not isinstance(cap, dict):
                continue
            url_obj = cap.get("url")
            urls: list[str] = []
            if isinstance(url_obj, dict):
                for u in url_obj.get("url_list") or []:
                    if isinstance(u, str) and u.startswith("http"):
                        urls.append(u)
            elif isinstance(url_obj, str) and url_obj.startswith("http"):
                urls.append(url_obj)
            for cap_url in urls:
                data = _douyin_fetch_caption_json(cap_url)
                if not data or "utterances" not in data:
                    continue
                segments, lang = _douyin_segments_from_utterances(data)
                segments = _deduplicate_segments(segments)
                if segments:
                    full_text = "\n".join(
                        f"[{_format_timestamp(s['start'])}] {s['text']}" for s in segments
                    )
                    return {
                        "segments": segments,
                        "full_text": full_text,
                        "language": lang,
                        "source": "auto",
                    }

    video = aweme.get("video") or {}
    cla = video.get("cla_info") or {}
    for cap in cla.get("caption_infos") or []:
        if not isinstance(cap, dict):
            continue
        cap_url = cap.get("url")
        if not cap_url:
            continue
        fmt = (cap.get("Format") or cap.get("format") or "").lower()
        try:
            resp = requests.get(cap_url, headers=cap_headers, timeout=30)
            resp.raise_for_status()
            content = resp.text
        except Exception:
            continue
        if fmt == "webvtt" or "WEBVTT" in content[:40]:
            segments = _parse_vtt(content)
        else:
            segments = _parse_srt(content)
        segments = _deduplicate_segments(segments)
        if segments:
            lang = cap.get("lang") or "zh"
            full_text = "\n".join(
                f"[{_format_timestamp(s['start'])}] {s['text']}" for s in segments
            )
            return {
                "segments": segments,
                "full_text": full_text,
                "language": lang,
                "source": "manual",
            }

    for cap in video.get("subtitleInfos") or []:
        if not isinstance(cap, dict):
            continue
        cap_url = cap.get("Url") or cap.get("url")
        if not cap_url:
            continue
        fmt = (cap.get("Format") or cap.get("format") or "").lower()
        try:
            resp = requests.get(cap_url, headers=cap_headers, timeout=30)
            resp.raise_for_status()
            content = resp.text
        except Exception:
            continue
        if fmt == "webvtt" or "WEBVTT" in content[:40]:
            segments = _parse_vtt(content)
        else:
            segments = _parse_srt(content)
        segments = _deduplicate_segments(segments)
        if segments:
            lang = cap.get("LanguageCodeName") or cap.get("lang") or "zh"
            full_text = "\n".join(
                f"[{_format_timestamp(s['start'])}] {s['text']}" for s in segments
            )
            return {
                "segments": segments,
                "full_text": full_text,
                "language": lang,
                "source": "manual",
            }

    return None


def _douyin_fallback_from_aweme(aweme: dict) -> dict | None:
    """When API returns no caption tracks, use description + music title for summarization."""
    desc = (aweme.get("desc") or "").strip()
    music = aweme.get("music") or {}
    music_title = (music.get("title") or "").strip()
    parts: list[str] = []
    if desc:
        parts.append(desc)
    if music_title and music_title not in desc:
        parts.append(f"[原声] {music_title}")
    text = "\n".join(parts).strip()
    if not text:
        return None

    video = aweme.get("video") or {}
    dur_raw = int(video.get("duration") or 0)
    if dur_raw > 1000:
        end = round(dur_raw / 1000.0, 2)
    else:
        end = round(float(dur_raw or 1), 2)
    if end < 1:
        end = 1.0

    segments = [{"start": 0.0, "end": end, "text": text}]
    full_text = "\n".join(
        f"[{_format_timestamp(s['start'])}] {s['text']}" for s in segments
    )
    return {
        "segments": segments,
        "full_text": full_text,
        "language": "zh",
        "source": "auto",
    }


def extract_douyin_subtitles(url: str) -> dict:
    """Douyin: iesdouyin 元数据 + 字幕轨道 URL；若无轨道则用简介/原声兜底供 AI 总结。"""
    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)
    try:
        resolved = _resolve_share_url(session, url)
        video_id = _extract_video_id(resolved)
        aweme = _fetch_item_info(session, video_id)
    except Exception as e:
        return {
            "segments": [],
            "full_text": "",
            "language": "",
            "source": "",
            "error": f"抖音字幕获取失败: {e}",
        }
    finally:
        session.close()

    rich = _try_douyin_caption_segments(aweme)
    if rich:
        return rich

    # 抖音 yt-dlp 通常需 Cookie，且对部分页面 URL（如精选页 modal_id）报 Unsupported；
    # 已有 iesdouyin 元数据后直接走文案兜底，不再调用 yt-dlp。
    fallback = _douyin_fallback_from_aweme(aweme)
    if fallback:
        return fallback

    return {
        "segments": [],
        "full_text": "",
        "language": "",
        "source": "",
        "error": "该视频没有可用的字幕",
    }


def _is_bilibili_url(url: str) -> bool:
    """Check if URL is a Bilibili video."""
    return "bilibili.com" in url or "b23.tv" in url


def _extract_bilibili_subtitle(url: str) -> dict | None:
    """Extract subtitles from Bilibili via their dedicated subtitle API.

    Bilibili serves AI-generated subtitles through a separate dm/view API,
    not through standard subtitle fields that yt-dlp reads.
    """
    try:
        # Step 1: Get bvid from URL
        bvid_match = re.search(r"(BV[\w]+)", url)
        if not bvid_match:
            # Resolve short URL (b23.tv) first
            resp = requests.get(url, headers=_BILIBILI_HEADERS, allow_redirects=True, timeout=10)
            bvid_match = re.search(r"(BV[\w]+)", resp.url)
        if not bvid_match:
            return None
        bvid = bvid_match.group(1)

        # Step 2: Get aid and cid via web-interface API
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        resp = requests.get(api_url, headers=_BILIBILI_HEADERS, timeout=10)
        data = resp.json()
        if data.get("code") != 0:
            return None

        aid = data["data"]["aid"]
        cid = data["data"]["cid"]

        # Step 3: Get subtitle list from dm/view API
        dm_url = f"https://api.bilibili.com/x/v2/dm/view?type=1&oid={cid}&pid={aid}"
        resp = requests.get(dm_url, headers=_BILIBILI_HEADERS, timeout=10)
        dm_data = resp.json()
        if dm_data.get("code") != 0:
            return None

        subtitle_list = dm_data.get("data", {}).get("subtitle", {}).get("subtitles", [])
        if not subtitle_list:
            return None

        # Step 4: Pick best subtitle by language priority
        chosen = None
        chosen_lang = ""
        for lang_pref in _BILIBILI_SUB_LANG_PRIORITY:
            for sub in subtitle_list:
                if sub.get("lan") == lang_pref:
                    chosen = sub
                    chosen_lang = lang_pref
                    break
            if chosen:
                break
        if not chosen:
            chosen = subtitle_list[0]
            chosen_lang = chosen.get("lan", "unknown")

        # Step 5: Fetch subtitle content
        sub_url = chosen.get("subtitle_url", "")
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url
        elif sub_url.startswith("http://"):
            sub_url = sub_url.replace("http://", "https://", 1)

        resp = requests.get(sub_url, headers=_BILIBILI_HEADERS, timeout=15)
        resp.raise_for_status()
        sub_content = resp.json()

        # Step 6: Parse Bilibili subtitle format (body: [{from, to, content}, ...])
        segments = []
        for item in sub_content.get("body", []):
            text = item.get("content", "").strip()
            if not text:
                continue
            segments.append({
                "start": round(item.get("from", 0), 2),
                "end": round(item.get("to", 0), 2),
                "text": text,
            })

        if not segments:
            return None

        source = "auto" if "ai-" in chosen_lang else "manual"
        display_lang = chosen.get("lan_doc", chosen_lang)

        full_text = "\n".join(
            f"[{_format_timestamp(s['start'])}] {s['text']}" for s in segments
        )

        return {
            "segments": segments,
            "full_text": full_text,
            "language": display_lang,
            "source": source,
        }

    except Exception:
        return None


def extract_subtitle(url: str) -> dict:
    """Extract subtitles from a video URL.

    Uses Bilibili-specific API for Bilibili videos, falls back to yt-dlp
    for all other platforms.

    Returns:
        {
            "segments": [{"start": float, "end": float, "text": str}, ...],
            "full_text": str,
            "language": str,
            "source": "manual" | "auto"
        }
    """
    url = _normalize_media_url(url)

    # Bilibili: use dedicated API (yt-dlp doesn't capture their AI subtitles)
    if _is_bilibili_url(url):
        result = _extract_bilibili_subtitle(url)
        if result:
            return result

    if is_douyin_url(url):
        return extract_douyin_subtitles(url)

    # 双保险：避免无协议 URL 等边界情况漏进 yt-dlp
    low = url.lower()
    if "douyin.com" in low or "iesdouyin.com" in low:
        return extract_douyin_subtitles(url)

    # Standard path: yt-dlp subtitles
    try:
        # Step 1: Try manual subtitles first
        info = _extract_sub_info(url, auto=False)
        subs = info.get("subtitles", {})
        req_subs = info.get("requested_subtitles") or {}
        lang, sub_data, source = _pick_best_subtitle(subs, req_subs, "manual")

        # Step 2: Fallback to auto-generated subtitles
        if not sub_data:
            info = _extract_sub_info(url, auto=True)
            auto_subs = info.get("automatic_captions", {})
            req_subs = info.get("requested_subtitles") or {}
            lang, sub_data, source = _pick_best_subtitle(auto_subs, req_subs, "auto")

        if not sub_data:
            return {
                "segments": [],
                "full_text": "",
                "language": "",
                "source": "",
                "error": "该视频没有可用的字幕",
            }

        # Step 3: Fetch and parse subtitle content
        segments = _fetch_and_parse(sub_data)
        segments = _deduplicate_segments(segments)

        full_text = "\n".join(
            f"[{_format_timestamp(s['start'])}] {s['text']}" for s in segments
        )

        return {
            "segments": segments,
            "full_text": full_text,
            "language": lang,
            "source": source,
        }
    except Exception as e:
        return {
            "segments": [],
            "full_text": "",
            "language": "",
            "source": "",
            "error": f"字幕提取失败: {e}",
        }


def _extract_sub_info(url: str, auto: bool) -> dict:
    """Run yt-dlp extract_info with subtitle options."""
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": auto,
        "subtitleslangs": SUBTITLE_LANGS,
        "subtitlesformat": "json3/vtt/srt/best",
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def _pick_best_subtitle(
    all_subs: dict, req_subs: dict, source_type: str
) -> tuple[str, dict | None, str]:
    """Pick the best subtitle from available options by language priority."""
    # First check requested_subtitles (yt-dlp's selection)
    for lang_pref in SUBTITLE_LANGS:
        if lang_pref in req_subs and req_subs[lang_pref]:
            return lang_pref, req_subs[lang_pref], source_type

    # Then check all available subtitles
    for lang_pref in SUBTITLE_LANGS:
        if lang_pref in all_subs and all_subs[lang_pref]:
            formats = all_subs[lang_pref]
            for fmt_pref in ["json3", "vtt", "srt"]:
                for fmt_entry in formats:
                    if fmt_entry.get("ext") == fmt_pref:
                        return lang_pref, fmt_entry, source_type
            if formats:
                return lang_pref, formats[0], source_type

    return "", None, ""


def _fetch_and_parse(sub_data: dict) -> list[dict]:
    """Fetch subtitle content from URL and parse it."""
    sub_url = sub_data.get("url", "")
    sub_ext = sub_data.get("ext", "")
    sub_data_content = sub_data.get("data")

    if sub_data_content:
        content = sub_data_content
    elif sub_url:
        resp = requests.get(sub_url, timeout=30)
        resp.raise_for_status()
        content = resp.text
    else:
        return []

    if sub_ext == "json3" or sub_url.endswith(".json3"):
        try:
            data = json.loads(content) if isinstance(content, str) else content
            return _parse_json3(data)
        except (json.JSONDecodeError, TypeError):
            pass

    if sub_ext == "vtt" or "WEBVTT" in (content[:20] if isinstance(content, str) else ""):
        return _parse_vtt(content)

    if sub_ext == "srt":
        return _parse_srt(content)

    # Best-effort: try all parsers
    if isinstance(content, str):
        if "WEBVTT" in content[:50]:
            return _parse_vtt(content)
        try:
            return _parse_json3(json.loads(content))
        except (json.JSONDecodeError, TypeError):
            pass
        return _parse_srt(content)

    return []
