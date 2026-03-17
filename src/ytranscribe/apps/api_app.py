from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..cli.main import main as run_cli


class TranscribeRequest(BaseModel):
    input: str = Field(..., description="YouTube URL")
    format: Literal["txt", "srt", "vtt"] = "txt"
    model: str = "medium"
    lang: str = "auto"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    compute_type: str = "int8_float16"
    timestamps: bool = False
    chunk_seconds: int = 0


class TranscribeResponse(BaseModel):
    output_path: str


def create_app() -> FastAPI:
    app = FastAPI(title="ytranscribe", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/transcribe", response_model=TranscribeResponse)
    def transcribe(req: TranscribeRequest) -> TranscribeResponse:
        out_dir = Path("outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "result"

        argv = [
            "--input",
            req.input,
            "--output",
            str(out_path),
            "--format",
            req.format,
            "--model",
            req.model,
            "--lang",
            req.lang,
            "--device",
            req.device,
            "--compute-type",
            req.compute_type,
        ]
        if req.timestamps:
            argv.append("--timestamps")
        if req.chunk_seconds:
            argv.extend(["--chunk-seconds", str(req.chunk_seconds)])

        code = run_cli(argv)
        if code != 0:
            raise HTTPException(status_code=500, detail="Transcribe failed")

        return TranscribeResponse(output_path=str(out_path.with_suffix(f".{req.format}")))

    return app

