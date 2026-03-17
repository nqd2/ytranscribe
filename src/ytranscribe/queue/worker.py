from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rq import Queue
from rq.job import Job

from ..cli.main import main as run_cli


@dataclass(frozen=True)
class JobParams:
    url: str
    fmt: Literal["txt", "srt", "vtt"]
    model: str
    lang: str
    device: Literal["auto", "cpu", "cuda"]
    compute_type: str
    timestamps: bool
    chunk_seconds: int


def redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://redis:6379/0")


def enqueue_transcribe(params: JobParams) -> str:
    from redis import Redis

    r = Redis.from_url(redis_url())
    q = Queue("transcribe", connection=r, default_timeout=60 * 60 * 6)
    job: Job = q.enqueue(run_job, params.__dict__)
    return job.get_id()


def run_job(params: dict) -> str:
    out_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "result"

    argv = [
        "--input",
        params["url"],
        "--output",
        str(out_path),
        "--format",
        params["fmt"],
        "--model",
        params["model"],
        "--lang",
        params["lang"],
        "--device",
        params["device"],
        "--compute-type",
        params["compute_type"],
        "--overwrite",
    ]
    if params.get("timestamps"):
        argv.append("--timestamps")
    if params.get("chunk_seconds"):
        argv.extend(["--chunk-seconds", str(params["chunk_seconds"])])

    code = run_cli(argv)
    if code != 0:
        raise RuntimeError("yts failed")
    return str(out_path.with_suffix(f".{params['fmt']}"))

