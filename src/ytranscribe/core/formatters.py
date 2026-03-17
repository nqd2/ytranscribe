from __future__ import annotations

from dataclasses import dataclass

from ..core.transcriber import Transcript


def _format_ts(seconds: float, *, srt: bool) -> str:
    if seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    if srt:
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _format_ts_bracket(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    return f"[{h:02d}:{m:02d}:{s:02d}]"


def format_txt(t: Transcript, *, timestamps: bool) -> str:
    lines: list[str] = []
    for seg in t.segments:
        if not seg.text:
            continue
        if timestamps:
            lines.append(f"{_format_ts_bracket(seg.start)} {seg.text}")
        else:
            lines.append(seg.text)
    return "\n".join(lines).strip() + "\n"


def format_srt(t: Transcript) -> str:
    out: list[str] = []
    i = 1
    for seg in t.segments:
        if not seg.text:
            continue
        out.append(str(i))
        out.append(f"{_format_ts(seg.start, srt=True)} --> {_format_ts(seg.end, srt=True)}")
        out.append(seg.text)
        out.append("")
        i += 1
    return "\n".join(out).strip() + "\n"


def format_vtt(t: Transcript) -> str:
    out: list[str] = ["WEBVTT", ""]
    for seg in t.segments:
        if not seg.text:
            continue
        out.append(f"{_format_ts(seg.start, srt=False)} --> {_format_ts(seg.end, srt=False)}")
        out.append(seg.text)
        out.append("")
    return "\n".join(out).strip() + "\n"


@dataclass(frozen=True)
class RenderedOutput:
    ext: str
    content: str


def render(t: Transcript, *, fmt: str, timestamps: bool) -> RenderedOutput:
    fmt = fmt.lower()
    if fmt == "txt":
        return RenderedOutput(ext="txt", content=format_txt(t, timestamps=timestamps))
    if fmt == "srt":
        return RenderedOutput(ext="srt", content=format_srt(t))
    if fmt == "vtt":
        return RenderedOutput(ext="vtt", content=format_vtt(t))
    raise ValueError(f"Unsupported format: {fmt}")

