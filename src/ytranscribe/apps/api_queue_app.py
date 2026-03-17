from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rq.job import Job

from ..queue.worker import JobParams, redis_url
from ..queue.worker import enqueue_transcribe as enqueue


class SubmitRequest(BaseModel):
    input: str = Field(..., description="YouTube URL")
    format: Literal["txt", "srt", "vtt"] = "txt"
    model: str = "medium"
    lang: str = "auto"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    compute_type: str = "int8_float16"
    timestamps: bool = False
    chunk_seconds: int = 0


class SubmitResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    status: str
    result: str | None = None
    error: str | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="ytranscribe-queue", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/jobs", response_model=SubmitResponse)
    def submit(req: SubmitRequest) -> SubmitResponse:
        job_id = enqueue(
            JobParams(
                url=req.input,
                fmt=req.format,
                model=req.model,
                lang=req.lang,
                device=req.device,
                compute_type=req.compute_type,
                timestamps=req.timestamps,
                chunk_seconds=req.chunk_seconds,
            )
        )
        return SubmitResponse(job_id=job_id)

    @app.get("/jobs/{job_id}", response_model=StatusResponse)
    def status(job_id: str) -> StatusResponse:
        from redis import Redis

        r = Redis.from_url(redis_url())
        try:
            job = Job.fetch(job_id, connection=r)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=404, detail=str(e)) from e

        if job.is_finished:
            return StatusResponse(status="finished", result=str(job.result))
        if job.is_failed:
            return StatusResponse(status="failed", error=str(job.exc_info))
        if job.is_started:
            return StatusResponse(status="started")
        return StatusResponse(status="queued")

    return app

