from __future__ import annotations

import json
import logging
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp

from ..core.errors import DownloadError
from ..utils.paths import sanitize_filename


@dataclass(frozen=True)
class DownloadResult:
    url: str
    title: str
    video_id: str | None
    audio_path: Path
    info_json_path: Path


def _ydl_opts(*, outtmpl: str, quiet: bool) -> dict[str, Any]:
    return {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": quiet,
        "no_warnings": True,
        "ignoreerrors": False,
        "retries": 3,
        "fragment_retries": 3,
        "continuedl": True,
        "consoletitle": False,
        "overwrites": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
    }


def download_audio(
    url: str,
    *,
    cache_dir: Path,
    logger: logging.Logger,
    retries: int = 3,
    verbose: bool = False,
) -> DownloadResult:
    cache_dir.mkdir(parents=True, exist_ok=True)
    quiet = not verbose

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with yt_dlp.YoutubeDL(_ydl_opts(outtmpl=str(cache_dir / "%(id)s.%(ext)s"), quiet=quiet)) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise DownloadError("Failed to fetch metadata from yt-dlp.")

                video_id = info.get("id")
                title_raw = info.get("title") or (video_id or "untitled")
                title = sanitize_filename(str(title_raw))

                info2 = ydl.extract_info(url, download=True)
                if not info2:
                    raise DownloadError("yt-dlp download failed.")

                vid = info2.get("id") or video_id
                if not vid:
                    raise DownloadError("Could not determine video id.")

                audio_path = cache_dir / f"{vid}.wav"
                if not audio_path.exists():
                    matches = sorted(cache_dir.glob(f"{vid}.*"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if matches:
                        audio_path = matches[0]
                    else:
                        raise DownloadError("Audio file not found after download.")

                info_json_path = cache_dir / f"{vid}.info.json"
                with suppress(Exception):
                    info_json_path.write_text(
                        json.dumps(info2, ensure_ascii=False, indent=2), encoding="utf-8"
                    )

                logger.info("Downloaded audio: %s", audio_path)
                return DownloadResult(
                    url=url,
                    title=title,
                    video_id=str(vid),
                    audio_path=audio_path,
                    info_json_path=info_json_path,
                )
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning("Download attempt %s/%s failed: %s", attempt, retries, e)
            time.sleep(min(2**attempt, 8))

    raise DownloadError(f"Download failed after {retries} attempts: {last_err}")

