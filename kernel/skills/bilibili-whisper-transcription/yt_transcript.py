#!/usr/bin/env python3
"""Video transcript extractor.

Usage:
    python tools/yt_transcript.py https://youtu.be/VIDEO_ID
    python tools/yt_transcript.py https://www.bilibili.com/video/BV...
    python tools/yt_transcript.py https://youtu.be/VIDEO_ID --no-cleanup
    python tools/yt_transcript.py https://youtu.be/VIDEO_ID --browser firefox

Default auth: reads cookies directly from Chrome's database, which handles
members-only videos correctly. Exported cookie files (Netscape format) often
miss httpOnly cookies like LOGIN_INFO that YouTube requires for membership
verification, so --cookies is a fallback only.

Priority: platform subtitles (non-danmaku) > OpenAI API transcription.
Output: Markdown with [HH:MM:SS] timestamps.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "projects"
    / "media_reading_packets"
    / "artifacts"
)


def load_workspace_env() -> None:
    """Load workspace .env without overriding variables already set by the shell."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def detect_platform(url: str) -> str:
    if "bilibili.com" in url or "b23.tv" in url:
        return "bilibili"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "video"


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})",
        r"(?:bilibili\.com/video/)(BV[a-zA-Z0-9]+)",
        r"(?:bilibili\.com/video/)(av\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if "b23.tv" in url:
        return "b23_link"
    raise ValueError(f"Cannot extract video ID from: {url}")


def _build_ydl_opts(
    browser: str | None = None,
    cookies_path: Path | None = None,
) -> dict:
    opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "ignore_no_formats_error": True,
    }
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    elif cookies_path and cookies_path.exists():
        opts["cookiefile"] = str(cookies_path)
    return opts


def get_video_info(
    url: str,
    browser: str | None = None,
    cookies_path: Path | None = None,
) -> dict:
    import yt_dlp

    opts = _build_ydl_opts(browser, cookies_path)
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def find_best_manual_subtitle(info: dict) -> tuple[str, list[dict], str] | None:
    """Return (language_code, subtitle_formats, source_label), or None."""
    subtitles = {
        lang: formats
        for lang, formats in (info.get("subtitles") or {}).items()
        if lang != "danmaku" and formats
    }
    automatic_captions = {
        lang: formats
        for lang, formats in (info.get("automatic_captions") or {}).items()
        if lang != "danmaku" and formats
    }
    if not subtitles and not automatic_captions:
        return None

    video_lang = info.get("language", "")

    if video_lang and video_lang in subtitles:
        return video_lang, subtitles[video_lang], "CC"

    for lang in ["zh-Hans", "zh-CN", "zh", "ai-zh", "zh-Hant", "en", "ja", "ko"]:
        if lang in subtitles:
            return lang, subtitles[lang], "CC"

    if subtitles:
        first_lang = next(iter(subtitles))
        return first_lang, subtitles[first_lang], "CC"

    for lang in ["zh-Hans", "zh-CN", "zh", "ai-zh", "zh-Hant", "en", "ja", "ko"]:
        if lang in automatic_captions:
            return lang, automatic_captions[lang], "Automatic captions"

    first_lang = next(iter(automatic_captions))
    return first_lang, automatic_captions[first_lang], "Automatic captions"


def download_subtitle_content(sub_formats: list[dict]) -> tuple[str, str]:
    """Download subtitle directly from URL in the info dict. Returns (content, ext)."""
    import urllib.request

    preferred_order = ["vtt", "srt", "json3", "json", "srv1"]
    format_map = {
        fmt.get("ext"): fmt
        for fmt in sub_formats
        if fmt.get("url") or fmt.get("data")
    }

    chosen = None
    for ext in preferred_order:
        if ext in format_map:
            chosen = format_map[ext]
            break
    if chosen is None:
        chosen = sub_formats[0]

    ext = chosen.get("ext", "vtt")

    if chosen.get("data"):
        return chosen["data"], f".{ext}"

    url = chosen["url"]
    with urllib.request.urlopen(url) as resp:
        content = resp.read().decode("utf-8")

    return content, f".{ext}"


def _format_timestamp(seconds: float) -> str:
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _format_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "unknown"
    return _format_timestamp(float(seconds))


def _is_module_available(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


def parse_json_subtitle_to_timestamped(content: str) -> str:
    """Convert JSON/JSON3 subtitles to [HH:MM:SS] markdown format."""
    data = json.loads(content)
    segments: list[tuple[str, str]] = []

    if isinstance(data, dict) and isinstance(data.get("body"), list):
        for item in data["body"]:
            start = item.get("from")
            text = item.get("content", "")
            if start is not None and text:
                segments.append((_format_timestamp(float(start)), str(text).strip()))
    elif isinstance(data, dict) and isinstance(data.get("events"), list):
        for item in data["events"]:
            start_ms = item.get("tStartMs")
            segs = item.get("segs") or []
            text = "".join(str(seg.get("utf8", "")) for seg in segs).strip()
            if start_ms is not None and text:
                segments.append((_format_timestamp(float(start_ms) / 1000), text))
    else:
        raise ValueError("Unsupported JSON subtitle structure")

    deduped: list[tuple[str, str]] = []
    for time_str, text in sorted(segments, key=lambda item: item[0]):
        clean = re.sub(r"\s+", " ", text).strip()
        if clean and (not deduped or deduped[-1][1] != clean):
            deduped.append((time_str, clean))

    return "\n".join(f"[{t}] {txt}" for t, txt in deduped)


def parse_subtitle_to_timestamped(content: str, ext: str) -> str:
    """Convert VTT/SRT content to [HH:MM:SS] markdown format."""
    if ext.lower() in [".json", ".json3"]:
        return parse_json_subtitle_to_timestamped(content)

    lines = content.strip().split("\n")
    segments: list[tuple[str, str]] = []
    current_time = None
    current_text_parts: list[str] = []

    ts_pattern = re.compile(r"(\d{1,2}:\d{2}:\d{2})[\.,]\d{3}\s*-->")

    for line in lines:
        line = line.strip()

        if not line or line == "WEBVTT" or line.isdigit():
            continue
        if line.startswith(("Kind:", "Language:", "NOTE", "STYLE")):
            continue

        ts_match = ts_pattern.match(line)
        if ts_match:
            if current_time and current_text_parts:
                text = " ".join(current_text_parts)
                segments.append((current_time, text))

            raw_time = ts_match.group(1)
            parts = raw_time.split(":")
            current_time = f"{int(parts[0]):02d}:{parts[1]}:{parts[2]}"
            current_text_parts = []
            continue

        clean = re.sub(r"<[^>]+>", "", line)
        clean = re.sub(r"\{[^}]+\}", "", clean)
        clean = clean.strip()
        if clean:
            current_text_parts.append(clean)

    if current_time and current_text_parts:
        segments.append((current_time, " ".join(current_text_parts)))

    deduped: list[tuple[str, str]] = []
    for time_str, text in sorted(segments, key=lambda item: item[0]):
        if not deduped or deduped[-1][1] != text:
            deduped.append((time_str, text))

    return "\n".join(f"[{t}] {txt}" for t, txt in deduped)


def download_audio(
    url: str,
    browser: str | None,
    cookies_path: Path | None,
    tmp_dir: Path,
) -> Path:
    """Download best audio to a temporary MP3 file and return its path."""
    import yt_dlp

    audio_path = tmp_dir / "audio"
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(audio_path),
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"},
        ],
        "quiet": True,
    }
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    elif cookies_path and cookies_path.exists():
        opts["cookiefile"] = str(cookies_path)

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    audio_file = None
    for f in tmp_dir.iterdir():
        if f.name.startswith("audio"):
            audio_file = f
            break

    if not audio_file:
        raise FileNotFoundError("Audio file not found after download")

    return audio_file


def _segments_to_timestamped(segments: list[dict], offset_seconds: float = 0) -> str:
    segments_out = []
    for seg in segments:
        start = float(seg.get("start", 0)) + offset_seconds
        text = str(seg.get("text", "")).strip()
        if text:
            segments_out.append(f"[{_format_timestamp(start)}] {text}")
    return "\n".join(segments_out)


def transcribe_with_openai_whisper(
    audio_file: Path,
    model_name: str,
) -> tuple[str, str]:
    """Transcribe a local audio file with openai-whisper."""
    try:
        import whisper
    except ImportError:
        print(
            "Error: openai-whisper is not installed. Install it with:\n"
            "  uv pip install openai-whisper",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Transcribing with Whisper ({model_name})... This may take a while.")

    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_file))

    detected_lang = result.get("language", "en")
    return _segments_to_timestamped(result["segments"]), detected_lang


def transcribe_with_faster_whisper(
    audio_file: Path,
    model_name: str,
) -> tuple[str, str]:
    """Transcribe a local audio file with faster-whisper if installed."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper is not installed")

    print(f"Transcribing with faster-whisper ({model_name}, cpu/int8)...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(str(audio_file), vad_filter=True)
    segments = [
        {"start": segment.start, "text": segment.text}
        for segment in segments_iter
    ]
    return _segments_to_timestamped(segments), getattr(info, "language", "en")


def _split_audio_for_api(
    audio_file: Path,
) -> list[tuple[Path, float]]:
    """Split long audio into API-friendly chunks. Returns (path, offset_seconds)."""
    chunk_dir = audio_file.parent / "api_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    chunk_seconds = 20 * 60
    chunk_pattern = chunk_dir / "chunk_%03d.mp3"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(audio_file),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-reset_timestamps",
        "1",
        "-c",
        "copy",
        str(chunk_pattern),
    ]
    subprocess.run(cmd, check=True)
    chunks = sorted(chunk_dir.glob("chunk_*.mp3"))
    return [(chunk, idx * chunk_seconds) for idx, chunk in enumerate(chunks)]


def _openai_transcribe_one(
    client,
    audio_file: Path,
    model_name: str,
    offset_seconds: float = 0,
) -> tuple[str, str]:
    with audio_file.open("rb") as f:
        result = client.audio.transcriptions.create(
            model=model_name,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif isinstance(result, dict):
        data = result
    else:
        data = json.loads(result.json())

    segments = data.get("segments") or []
    if segments:
        return _segments_to_timestamped(segments, offset_seconds), data.get("language", "en")

    text = data.get("text", "").strip()
    if text:
        return f"[{_format_timestamp(offset_seconds)}] {text}", data.get("language", "en")

    raise RuntimeError("OpenAI transcription API returned no text")


def transcribe_with_openai_api(
    audio_file: Path,
    model_name: str,
    duration: float | int | None = None,
) -> tuple[str, str]:
    """Transcribe a local audio file with OpenAI's audio transcription API."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI transcription API")

    from openai import OpenAI

    print(f"Transcribing with OpenAI API ({model_name})...")
    client = OpenAI(api_key=openai_key)

    should_split = (duration is not None and duration > 20 * 60) or audio_file.stat().st_size > 24 * 1024 * 1024
    if not should_split:
        return _openai_transcribe_one(client, audio_file, model_name)

    print("Splitting audio into 20-minute chunks for OpenAI API transcription...")
    parts = []
    language = "en"
    for chunk, offset in _split_audio_for_api(audio_file):
        print(f"  Transcribing chunk at { _format_timestamp(offset) }...")
        text, language = _openai_transcribe_one(client, chunk, model_name, offset)
        parts.append(text)
    return "\n".join(parts), language


def choose_transcription_plan(
    duration: float | int | None,
    backend: str,
    whisper_model: str,
    openai_transcription_model: str,
) -> tuple[str, str]:
    """Choose transcription backend and model from duration and availability."""
    if backend != "auto":
        if backend == "openai-api":
            if not os.environ.get("OPENAI_API_KEY"):
                raise RuntimeError("OPENAI_API_KEY is required for OpenAI transcription API")
            return backend, openai_transcription_model
        return backend, "small" if whisper_model == "auto" else whisper_model

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "No platform subtitles were found, and auto transcription now requires "
            "OPENAI_API_KEY for cloud transcription. Pass --transcription-backend "
            "openai-whisper or faster-whisper only for explicit local testing."
        )

    return "openai-api", openai_transcription_model


def transcribe_audio_file(
    audio_file: Path,
    backend: str,
    model_name: str,
    duration: float | int | None = None,
) -> tuple[str, str, str]:
    """Transcribe a local audio file. Returns (text, language, source_label)."""
    if backend == "faster-whisper":
        transcript, lang = transcribe_with_faster_whisper(audio_file, model_name)
        return transcript, lang, f"Whisper ({backend}:{model_name})"
    if backend == "openai-api":
        transcript, lang = transcribe_with_openai_api(audio_file, model_name, duration)
        return transcript, lang, f"OpenAI transcription API ({model_name})"
    if backend == "openai-whisper":
        transcript, lang = transcribe_with_openai_whisper(audio_file, model_name)
        return transcript, lang, f"Whisper ({backend}:{model_name})"
    raise ValueError(f"Unsupported transcription backend: {backend}")


def fallback_transcribe(
    url: str,
    browser: str | None,
    cookies_path: Path | None,
    tmp_dir: Path,
    duration: float | int | None,
    backend: str,
    whisper_model: str,
    openai_transcription_model: str,
    keep_audio_dir: Path | None = None,
) -> tuple[str, str, str]:
    """Download audio and transcribe it with the selected fallback backend."""
    selected_backend, selected_model = choose_transcription_plan(
        duration,
        backend,
        whisper_model,
        openai_transcription_model,
    )
    print(
        f"Transcription plan: duration={_format_duration(duration)}, "
        f"backend={selected_backend}, model={selected_model}"
    )

    print("No platform subtitles found. Downloading audio for transcription...")
    audio_file = download_audio(url, browser, cookies_path, tmp_dir)

    if keep_audio_dir is not None:
        keep_audio_dir.mkdir(parents=True, exist_ok=True)
        target = keep_audio_dir / audio_file.name
        shutil.copy2(audio_file, target)
        print(f"Kept audio copy: {target}")

    try:
        return transcribe_audio_file(audio_file, selected_backend, selected_model, duration)
    except Exception as e:
        if backend != "auto":
            raise
        raise RuntimeError(
            f"Cloud transcription failed with {selected_backend}:{selected_model}. "
            "Auto mode does not fall back to local Whisper."
        ) from e


def _get_llm_caller():
    """Return a callable (prompt: str) -> str for LLM cleanup.

    Tries OpenCode first, then OpenAI, then Gemini as fallback.
    """
    try:
        opencode_dir = Path(__file__).resolve().parent.parent / "periodic_jobs" / "ai_heartbeat"
        if str(opencode_dir) not in sys.path:
            sys.path.insert(0, str(opencode_dir))
        from opencode_client import OpenCodeClient

        client = OpenCodeClient()
        if client.list_sessions() is not None:

            def call_opencode(system: str, user: str) -> str:
                session_id = client.create_session("Video transcript cleanup")
                if not session_id:
                    raise RuntimeError("OpenCode session creation failed")
                prompt = (
                    f"{system}\n\n"
                    f"Clean this transcript and return ONLY the cleaned transcript. "
                    f"Do not edit files and do not add commentary.\n\n{user}"
                )
                result = client.send_message(
                    session_id,
                    prompt,
                    model_id="openai/gpt-5.4-mini",
                    agent="build",
                )
                if not result:
                    client.wait_for_session_complete(session_id, poll_interval=5, max_wait=900)
                    messages = client.get_session_messages(session_id) or []
                    for msg in reversed(messages):
                        if (msg.get("info") or {}).get("role") != "assistant":
                            continue
                        parts = msg.get("parts") or []
                        text = "\n".join(part.get("text", "") for part in parts if part.get("type") == "text").strip()
                        if text:
                            return text
                    raise RuntimeError("OpenCode cleanup returned no text")
                parts = result.get("parts") or []
                text = "\n".join(part.get("text", "") for part in parts if part.get("type") == "text").strip()
                if not text:
                    raise RuntimeError("OpenCode cleanup returned no text")
                return text

            print("  Using OpenCode (openai/gpt-5.4-mini)")
            return call_opencode
    except Exception as e:
        print(f"  OpenCode unavailable ({e.__class__.__name__}), trying API keys...")

    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    for name in ["openai_api_key", "gemini_api_key"]:
        if openai_key and gemini_key:
            break
        try:
            result = subprocess.run(
                ["op", "read", f"op://dev/dev-api-keys/{name}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                val = result.stdout.strip()
                if name == "openai_api_key" and not openai_key:
                    openai_key = val
                elif name == "gemini_api_key" and not gemini_key:
                    gemini_key = val
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    if openai_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            client.models.list()

            def call_openai(system: str, user: str) -> str:
                resp = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                return resp.choices[0].message.content.strip()

            print("  Using OpenAI (gpt-4.1-mini)")
            return call_openai
        except Exception as e:
            print(f"  OpenAI unavailable ({e.__class__.__name__}), trying Gemini...")

    if gemini_key:
        from google import genai

        client = genai.Client(api_key=gemini_key)

        def call_gemini(system: str, user: str) -> str:
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system}\n\n{user}",
            )
            return resp.text.strip()

        print("  Using Gemini (gemini-2.5-flash)")
        return call_gemini

    return None


def _chunk_transcript(text: str, max_lines: int = 300) -> list[str]:
    """Split transcript into chunks at timestamp boundaries."""
    lines = text.strip().split("\n")
    if len(lines) <= max_lines:
        return [text]

    chunks = []
    current_chunk: list[str] = []
    for line in lines:
        current_chunk.append(line)
        if len(current_chunk) >= max_lines and line.startswith("["):
            chunks.append("\n".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def llm_cleanup(text: str, language: str, title: str = "") -> str:
    """Clean up transcript with Gemini: remove fillers, fix errors, add punctuation.

    Merges fragmented one-second segments into coherent sentences and
    keeps a timestamp marker roughly every 30 seconds.
    """
    llm_call = _get_llm_caller()
    if llm_call is None:
        print(
            "Warning: No LLM API key found. Skipping cleanup.\n"
            "Set OPENAI_API_KEY or GEMINI_API_KEY env var.",
            file=sys.stderr,
        )
        return text

    lang_map = {
        "zh": "简体中文",
        "zh-Hans": "简体中文",
        "zh-Hant": "简体中文",
        "zh-CN": "简体中文",
        "zh-TW": "简体中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
    }
    lang_name = lang_map.get(language, language)

    system_prompt = (
        f"You are cleaning up a video transcript. Video title: {title}\n"
        f"Output language: {lang_name}\n\n"
        f"Rules:\n"
        f"1. Merge fragmented lines into complete sentences with proper punctuation.\n"
        f"2. Keep timestamp markers in [HH:MM:SS] format, but reduce density: "
        f"retain one marker roughly every 20-30 seconds of content. "
        f"Always keep the first timestamp of a new topic or speaker turn.\n"
        f"3. Remove filler words (嗯、啊、那个、就是说、you know、like、um、uh, etc.).\n"
        f"4. Fix obvious transcription errors.\n"
        f"5. If Traditional Chinese, convert to Simplified Chinese.\n"
        f"6. Do NOT restructure, reorder, summarize, or add headings.\n"
        f"7. Do NOT change the meaning or add content.\n"
        f"8. Preserve speaker turns if identifiable.\n\n"
        f"Output ONLY the cleaned transcript."
    )

    chunks = _chunk_transcript(text)
    cleaned_parts = []

    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"  Cleaning chunk {i + 1}/{len(chunks)}...")

        for attempt in range(3):
            try:
                result = llm_call(system_prompt, chunk)
                cleaned_parts.append(result)
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait = min(20 * (2**attempt), 120)
                    print(f"  Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise

    return "\n\n".join(cleaned_parts)


def get_transcript(
    url: str,
    browser: str | None = "chrome",
    cookies_path: Path | None = None,
    output_dir: Path | None = None,
    cleanup: bool = True,
    whisper_model: str = "auto",
    transcription_backend: str = "auto",
    openai_transcription_model: str = "whisper-1",
    keep_audio_dir: Path | None = None,
) -> Path:
    """Extract transcript from a YouTube or Bilibili video.

    Args:
        url: YouTube or Bilibili video URL
        browser: Browser to read cookies from (default: chrome).
                 Set to None to skip browser cookies.
        cookies_path: Path to cookies file (Netscape format). Fallback if
                      browser cookies fail or are not available.
        output_dir: Where to save the transcript
        cleanup: Whether to run LLM cleanup
        whisper_model: Whisper model size for explicit local transcription
        transcription_backend: Backend when platform subtitles are unavailable:
                               auto/openai-whisper/faster-whisper/openai-api.
                               auto uses OpenAI API.
        openai_transcription_model: OpenAI transcription model when using openai-api
        keep_audio_dir: Optional directory to keep a copy of downloaded audio

    Returns:
        Path to the saved transcript file
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    platform = detect_platform(url)
    video_id = extract_video_id(url)
    print(f"Processing: {platform}:{video_id}")

    info = get_video_info(url, browser=browser, cookies_path=cookies_path)
    title = info.get("title", "unknown")
    video_id = info.get("id") or video_id
    duration = info.get("duration")
    print(f"Title: {title}")
    print(f"Duration: {_format_duration(duration)}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        sub_result = find_best_manual_subtitle(info)

        if sub_result:
            lang, sub_formats, subtitle_source = sub_result
            print(f"Found subtitles: {lang} ({subtitle_source})")
            content, ext = download_subtitle_content(sub_formats)
            transcript = parse_subtitle_to_timestamped(content, ext)
        else:
            transcript, lang, subtitle_source = fallback_transcribe(
                url=url,
                browser=browser,
                cookies_path=cookies_path,
                tmp_dir=tmp_dir,
                duration=duration,
                backend=transcription_backend,
                whisper_model=whisper_model,
                openai_transcription_model=openai_transcription_model,
                keep_audio_dir=keep_audio_dir,
            )

    if cleanup:
        print("Running LLM cleanup...")
        try:
            transcript = llm_cleanup(transcript, lang, title)
        except Exception as e:
            print(f"LLM cleanup failed: {e}", file=sys.stderr)
            print("Saving raw transcript instead.", file=sys.stderr)

    date_str = datetime.now().strftime("%Y%m%d")
    slug = re.sub(r"[^\w\s-]", "", title)[:50].strip().replace(" ", "_").lower()
    filename = f"{date_str}_{platform}_{video_id}_{slug}.md"
    output_path = output_dir / filename

    header = (
        f"# {title}\n\n"
        f"- Source: {url}\n"
        f"- Platform: {platform}\n"
        f"- Video ID: {video_id}\n"
        f"- Duration: {_format_duration(duration)}\n"
        f"- Extracted: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"- Subtitle source: {subtitle_source}\n\n"
        f"---\n\n"
    )
    output_path.write_text(header + transcript, encoding="utf-8")

    print(f"\nSaved: {output_path}")
    return output_path


def main():
    load_workspace_env()

    parser = argparse.ArgumentParser(description="Extract video transcript")
    parser.add_argument("url", help="YouTube or Bilibili video URL")
    parser.add_argument(
        "--browser",
        default="chrome",
        help="Browser to read cookies from (default: chrome). "
        "Use 'none' to disable.",
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        default=None,
        help="Path to cookies file (Netscape format). "
        "Only used if --browser is 'none'.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory (default: projects/media_reading_packets/artifacts)",
    )
    parser.add_argument("--no-cleanup", action="store_true", help="Skip LLM cleanup")
    parser.add_argument(
        "--whisper-model",
        default="auto",
        help="Whisper model for explicit local transcription (default: auto)",
    )
    parser.add_argument(
        "--transcription-backend",
        choices=["auto", "openai-whisper", "faster-whisper", "openai-api"],
        default="auto",
        help=(
            "Backend when platform subtitles are unavailable. "
            "auto: use OpenAI API with --openai-transcription-model. "
            "Local backends are only used when explicitly selected."
        ),
    )
    parser.add_argument(
        "--openai-transcription-model",
        default="whisper-1",
        help="OpenAI transcription model for --transcription-backend openai-api (default: whisper-1)",
    )
    parser.add_argument(
        "--keep-audio-dir",
        type=Path,
        default=None,
        help="Optional directory to keep a copy of downloaded audio. By default audio is temporary.",
    )

    args = parser.parse_args()

    browser = None if args.browser == "none" else args.browser

    get_transcript(
        url=args.url,
        browser=browser,
        cookies_path=args.cookies,
        output_dir=args.output_dir,
        cleanup=not args.no_cleanup,
        whisper_model=args.whisper_model,
        transcription_backend=args.transcription_backend,
        openai_transcription_model=args.openai_transcription_model,
        keep_audio_dir=args.keep_audio_dir,
    )


if __name__ == "__main__":
    main()
