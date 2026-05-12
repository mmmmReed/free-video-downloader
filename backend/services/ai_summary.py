"""AI video summarization service using DeepSeek API (OpenAI-compatible)."""

import os
from typing import Generator

from openai import OpenAI


DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def _get_client() -> OpenAI:
    if not DEEPSEEK_API_KEY:
        raise ValueError(
            "DEEPSEEK_API_KEY 环境变量未设置。"
            "请设置后重启服务：export DEEPSEEK_API_KEY=your_key"
        )
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


SUMMARY_SYSTEM_PROMPT = """\
你是一位专业的视频内容分析师，擅长从视频字幕中提取关键信息并生成结构化总结。

请根据提供的视频字幕内容，生成以下格式的 Markdown 总结：

## 视频概述
（2-3句话概括视频的核心主题和主要内容）

## 章节摘要
按照视频的逻辑结构，将内容分为若干章节。每个章节格式如下：
### [时间戳] 章节标题
- 该章节的要点1
- 该章节的要点2
- 该章节的要点3

## 核心知识点
以列表形式列出视频中最重要的3-8个知识点或结论：
1. 知识点1
2. 知识点2
3. 知识点3

要求：
- 时间戳使用 [MM:SS] 或 [HH:MM:SS] 格式
- 章节数量根据视频长度和内容密度灵活调整（通常3-8个）
- 语言与字幕语言保持一致
- 总结要精练，抓住重点，避免冗余
- 如果字幕内容较少或质量较差，做出合理推断"""


CHAT_SYSTEM_PROMPT = """\
你是一位视频内容助手。用户会给你一段视频的字幕内容，你需要基于字幕内容回答用户的问题。

要求：
- 回答要准确，基于字幕中的实际内容
- 如果字幕中没有相关信息，诚实告知
- 回答时可以引用相关的时间戳
- 语言与用户提问的语言保持一致
- 回答简洁有用"""


def summarize_stream(
    subtitle_text: str, video_title: str
) -> Generator[str, None, None]:
    """Stream AI summary of video content.

    Yields:
        Content chunks from the AI model.
    """
    client = _get_client()

    user_content = f"视频标题：{video_title}\n\n字幕内容：\n{subtitle_text}"
    # Truncate very long subtitles to stay within token limits
    if len(user_content) > 30000:
        user_content = user_content[:30000] + "\n\n[字幕内容过长，已截断]"

    stream = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        stream=True,
        temperature=0.3,
        max_tokens=4096,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def chat_stream(
    subtitle_text: str,
    video_title: str,
    history: list[dict],
    question: str,
) -> Generator[str, None, None]:
    """Stream AI chat response about video content.

    Args:
        subtitle_text: Full subtitle text of the video.
        video_title: Title of the video.
        history: Previous chat messages [{role, content}, ...].
        question: Current user question.

    Yields:
        Content chunks from the AI model.
    """
    client = _get_client()

    context = f"视频标题：{video_title}\n\n字幕内容：\n{subtitle_text}"
    if len(context) > 30000:
        context = context[:30000] + "\n\n[字幕内容过长，已截断]"

    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": f"以下是视频的参考信息：\n\n{context}"},
        {"role": "assistant", "content": "好的，我已经了解了这个视频的内容。请问有什么问题？"},
    ]

    for msg in history:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    messages.append({"role": "user", "content": question})

    stream = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        stream=True,
        temperature=0.5,
        max_tokens=2048,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
