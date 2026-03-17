from __future__ import annotations

import argparse
from pathlib import Path

from ..core.audio import normalize_audio, probe_audio, split_audio
from ..core.deps import is_probably_text_file, require_ffmpeg
from ..core.downloader import download_audio
from ..core.formatters import render
from ..core.transcriber import resolve_device, transcribe_file
from ..utils.io_utils import read_lines, write_text_utf8
from ..utils.logging_utils import setup_logging
from ..utils.paths import default_cache_dir, sanitize_filename
from ..utils.title_map import load_title_map


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="yts", description="YouTube transcriber (yt-dlp + ffmpeg + faster-whisper)."
    )
    p.add_argument("--input", required=True, help="YouTube URL or a .txt file (one URL per line).")
    p.add_argument("--output", required=True, help="Output file (single) or output folder (batch).")
    p.add_argument("--format", default="txt", choices=["txt", "srt", "vtt"], help="Output format.")
    p.add_argument("--model", default="medium", help="Whisper model name/path (default: medium).")
    p.add_argument("--lang", default="auto", help="Language code or 'auto' (default).")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Device preference.")
    p.add_argument("--compute-type", default="int8_float16", help="faster-whisper compute_type.")
    p.add_argument("--cache-dir", default=None, help="Cache directory path (optional).")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    p.add_argument("--timestamps", action="store_true", help="Include timestamps in txt output.")
    p.add_argument("--chunk-seconds", type=int, default=0, help="Split audio into chunks (seconds).")
    p.add_argument("--title-map", default=None, help="JSON file mapping URL/video_id -> title (e.g. list.json).")
    p.add_argument("--verbose", action="store_true", help="Verbose logs.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    cache_dir = Path(args.cache_dir) if args.cache_dir else default_cache_dir()
    log_file = cache_dir / "ytranscribe.log"
    logger = setup_logging(verbose=bool(args.verbose), log_file=log_file)

    try:
        require_ffmpeg()
    except Exception as e:  # noqa: BLE001
        logger.error(str(e))
        return 1

    inp = Path(args.input)
    is_batch = inp.exists() and is_probably_text_file(inp)
    urls = read_lines(inp) if is_batch else [str(args.input).strip()]

    out = Path(args.output)
    if is_batch:
        out.mkdir(parents=True, exist_ok=True)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)

    device = resolve_device(args.device)
    compute_type = str(args.compute_type)

    title_map = None
    if args.title_map:
        try:
            title_map = load_title_map(Path(args.title_map))
            logger.info("Loaded title-map: %s entries", len(title_map.by_url) + len(title_map.by_video_id))
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to read --title-map: %s", e)
            return 1

    ok = 0
    failed: list[tuple[str, str]] = []

    for url in urls:
        try:
            dl = download_audio(
                url, cache_dir=cache_dir / "downloads", logger=logger, verbose=bool(args.verbose)
            )
            norm_path = cache_dir / "normalized" / f"{dl.video_id}.wav"
            normalize_audio(dl.audio_path, out_path=norm_path, logger=logger, overwrite=False)
            info = probe_audio(norm_path)

            transcripts: list[tuple[float, object]] = []
            if args.chunk_seconds and info.duration_sec and info.duration_sec > args.chunk_seconds:
                chunks_dir = cache_dir / "chunks" / str(dl.video_id)
                chunks = split_audio(
                    norm_path,
                    out_dir=chunks_dir,
                    chunk_seconds=int(args.chunk_seconds),
                    logger=logger,
                    overwrite=False,
                )
                offset = 0.0
                for c in chunks:
                    t = transcribe_file(
                        c,
                        model_name=args.model,
                        device=device,
                        compute_type=compute_type,
                        language=args.lang,
                        logger=logger,
                    )
                    transcripts.append((offset, t))
                    c_info = probe_audio(c)
                    offset += float(c_info.duration_sec or 0.0)
            else:
                t = transcribe_file(
                    norm_path,
                    model_name=args.model,
                    device=device,
                    compute_type=compute_type,
                    language=args.lang,
                    logger=logger,
                )
                transcripts.append((0.0, t))

            from ..core.transcriber import Segment, Transcript

            merged_segments: list[Segment] = []
            lang: str | None = None
            for off, t in transcripts:
                if lang is None:
                    lang = t.language
                for s in t.segments:
                    merged_segments.append(Segment(start=s.start + off, end=s.end + off, text=s.text))
            merged = Transcript(language=lang, segments=merged_segments)

            rendered = render(merged, fmt=args.format, timestamps=bool(args.timestamps))

            mapped_title = title_map.resolve(url=url, video_id=dl.video_id) if title_map else None
            final_title = sanitize_filename(mapped_title or dl.title)

            if is_batch:
                fname = final_title + f".{rendered.ext}"
                out_path = out / fname
            else:
                out_path = out
                if out_path.exists() and out_path.is_dir():
                    out_path = out_path / (final_title + f".{rendered.ext}")
                elif out_path.suffix.lower() != f".{rendered.ext}":
                    out_path = out_path.with_suffix(f".{rendered.ext}")

            write_text_utf8(out_path, rendered.content, overwrite=bool(args.overwrite))
            logger.info("Wrote: %s", out_path)
            ok += 1
        except Exception as e:  # noqa: BLE001
            logger.error("Failed url=%s err=%s", url, e)
            failed.append((url, str(e)))

    if failed:
        logger.warning("Done with failures (%s/%s ok).", ok, len(urls))
        for url, err in failed:
            logger.warning("FAIL %s :: %s", url, err)
        return 3
    logger.info("Done (%s/%s ok).", ok, len(urls))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

