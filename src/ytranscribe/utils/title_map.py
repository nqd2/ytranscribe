from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


def _extract_video_id(url: str) -> str | None:
    try:
        u = urlparse(url)
        if u.netloc.endswith("youtu.be"):
            vid = u.path.strip("/").split("/")[0]
            return vid or None
        qs = parse_qs(u.query)
        vid = (qs.get("v") or [None])[0]
        return vid
    except Exception:
        return None


def _norm_url(url: str) -> str:
    return (url or "").strip()


@dataclass(frozen=True)
class TitleMap:
    by_url: dict[str, str]
    by_video_id: dict[str, str]

    def resolve(self, *, url: str, video_id: str | None) -> str | None:
        if video_id and video_id in self.by_video_id:
            return self.by_video_id[video_id]
        u = _norm_url(url)
        if u in self.by_url:
            return self.by_url[u]
        vid = _extract_video_id(u)
        if vid and vid in self.by_video_id:
            return self.by_video_id[vid]
        return None


def load_title_map(path: Path) -> TitleMap:
    """
    Supports a `list.json` format like:
    [
      {"title": "...", "youtube_link": "https://www.youtube.com/watch?v=..."},
      ...
    ]
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    data: Any = json.loads(raw)
    by_url: dict[str, str] = {}
    by_video_id: dict[str, str] = {}

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            link = str(item.get("youtube_link") or item.get("url") or "").strip()
            if not title or not link:
                continue
            by_url[_norm_url(link)] = title
            vid = _extract_video_id(link)
            if vid:
                by_video_id[vid] = title

    elif isinstance(data, dict):
        # Optional: allow {"url": "title"} map
        for k, v in data.items():
            link = str(k or "").strip()
            title = str(v or "").strip()
            if not link or not title:
                continue
            by_url[_norm_url(link)] = title
            vid = _extract_video_id(link)
            if vid:
                by_video_id[vid] = title

    return TitleMap(by_url=by_url, by_video_id=by_video_id)

