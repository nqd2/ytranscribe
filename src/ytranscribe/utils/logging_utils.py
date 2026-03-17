from __future__ import annotations

import logging
import os
from pathlib import Path


def setup_logging(*, verbose: bool, log_file: Path | None = None) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("ytranscribe")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    for name in ["urllib3", "httpx", "yt_dlp", "faster_whisper", "ctranslate2"]:
        logging.getLogger(name).setLevel(logging.WARNING if not verbose else logging.INFO)

    os.environ.setdefault("PYTHONUTF8", "1")
    return logger

