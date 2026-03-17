from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..core.deps import require_ffmpeg, require_ffprobe
from ..core.errors import AudioProcessError


@dataclass(frozen=True)
class AudioInfo:
    path: Path
    duration_sec: float | None
    sample_rate: int | None


def probe_audio(path: Path) -> AudioInfo:
    ffprobe = require_ffprobe()
    try:
        p = subprocess.run(
            [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except Exception as e:  # noqa: BLE001
        raise AudioProcessError(f"ffprobe error: {e}") from e

    import json

    data = json.loads(p.stdout or "{}")
    duration = None
    sr = None
    try:
        duration = float(data.get("format", {}).get("duration")) if data.get("format", {}).get("duration") else None
    except Exception:
        duration = None
    for s in data.get("streams", []) or []:
        if s.get("codec_type") == "audio":
            try:
                sr = int(s.get("sample_rate")) if s.get("sample_rate") else None
            except Exception:
                sr = None
            break
    return AudioInfo(path=path, duration_sec=duration, sample_rate=sr)


def normalize_audio(
    in_path: Path,
    *,
    out_path: Path,
    sample_rate: int = 16000,
    channels: int = 1,
    logger: logging.Logger,
    overwrite: bool = False,
) -> AudioInfo:
    ffmpeg = require_ffmpeg()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not overwrite:
        return probe_audio(out_path)

    cmd = [
        ffmpeg,
        "-y" if overwrite else "-n",
        "-i",
        str(in_path),
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-vn",
        str(out_path),
    ]
    logger.info("Normalize audio: %s -> %s", in_path, out_path)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    except subprocess.CalledProcessError as e:
        raise AudioProcessError(f"ffmpeg convert error: {e.stderr or e.stdout}") from e
    return probe_audio(out_path)


def split_audio(
    in_path: Path,
    *,
    out_dir: Path,
    chunk_seconds: int,
    logger: logging.Logger,
    overwrite: bool = False,
) -> list[Path]:
    ffmpeg = require_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / "chunk_%05d.wav"
    cmd = [
        ffmpeg,
        "-y" if overwrite else "-n",
        "-i",
        str(in_path),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-c",
        "copy",
        str(pattern),
    ]
    logger.info("Split audio into %ss chunks: %s", chunk_seconds, in_path)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    except subprocess.CalledProcessError as e:
        raise AudioProcessError(f"ffmpeg split error: {e.stderr or e.stdout}") from e

    chunks = sorted(out_dir.glob("chunk_*.wav"))
    if not chunks:
        raise AudioProcessError("No audio chunks were created.")
    return chunks

