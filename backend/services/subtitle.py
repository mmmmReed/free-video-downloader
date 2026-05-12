"""Subtitle extraction service using yt-dlp."""

import json
import re
import requests
from yt_dlp import YoutubeDL


SUBTITLE_LANGS = ["zh-Hans", "zh", "zh-CN", "en", "ja", "ko"]

_BILIBILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

_BILIBILI_SUB_LANG_PRIORITY = ["ai-zh", "zh-Hans", "zh", "zh-CN", "ai-en", "en"]


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
    # Bilibili: use dedicated API (yt-dlp doesn't capture their AI subtitles)
    if _is_bilibili_url(url):
        result = _extract_bilibili_subtitle(url)
        if result:
            return result

    # Standard path: yt-dlp subtitles
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
