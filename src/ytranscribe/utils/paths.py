from __future__ import annotations

import re
from pathlib import Path

from platformdirs import user_cache_dir

INVALID_WIN_CHARS = r'<>:"/\\|?*'
_invalid_re = re.compile(rf"[{re.escape(INVALID_WIN_CHARS)}]+")
_whitespace_re = re.compile(r"\s+")


def default_cache_dir() -> Path:
    return Path(user_cache_dir("ytranscribe", "ytranscribe"))


def sanitize_filename(name: str, *, replacement: str = "_", max_len: int = 180) -> str:
    name = name.strip().strip(".")
    name = _invalid_re.sub(replacement, name)
    name = _whitespace_re.sub(" ", name).strip()
    if not name:
        name = "untitled"
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

