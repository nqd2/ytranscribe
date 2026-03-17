from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from ..core.errors import TranscribeError


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Transcript:
    language: str | None
    segments: list[Segment]


def resolve_device(device: str) -> str:
    if device in {"cpu", "cuda"}:
        return device
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cuda"


def transcribe_file(
    audio_path: Path,
    *,
    model_name: str,
    device: str,
    compute_type: str,
    language: str,
    logger: logging.Logger,
) -> Transcript:
    try:
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        segments_iter, info = model.transcribe(
            str(audio_path),
            language=None if language == "auto" else language,
            vad_filter=True,
        )
        segs: list[Segment] = []
        for s in segments_iter:
            segs.append(Segment(start=float(s.start), end=float(s.end), text=str(s.text or "").strip()))
        lang = getattr(info, "language", None)
        logger.info("Transcribed %s segments (lang=%s)", len(segs), lang)
        return Transcript(language=lang, segments=segs)
    except Exception as e:  # noqa: BLE001
        raise TranscribeError(f"Transcription error: {e}") from e

