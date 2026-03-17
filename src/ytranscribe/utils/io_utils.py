from __future__ import annotations

from pathlib import Path

from .paths import ensure_parent


def write_text_utf8(path: Path, content: str, *, overwrite: bool) -> None:
    ensure_parent(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def read_lines(path: Path) -> list[str]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    return [ln.strip() for ln in txt.splitlines() if ln.strip() and not ln.strip().startswith("#")]

