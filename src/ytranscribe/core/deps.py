from __future__ import annotations

import shutil
from pathlib import Path

from .errors import DependencyError


def require_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise DependencyError(
            "ffmpeg was not found in PATH. Install ffmpeg and verify `ffmpeg -version` works."
        )
    return exe


def require_ffprobe() -> str:
    exe = shutil.which("ffprobe")
    if not exe:
        raise DependencyError(
            "ffprobe was not found in PATH. Install ffmpeg (includes ffprobe) and verify `ffprobe -version` works."
        )
    return exe


def is_probably_text_file(path: Path) -> bool:
    return path.suffix.lower() in {".txt"}

