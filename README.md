# ytranscribe

YouTube transcription tool built on `ffmpeg` + `whisper`.

- Input: a single YouTube URL or a `.txt` file (one URL per line)
- Output: a single file or a folder (one transcript per video)
- Formats: `txt`, `srt`, `vtt`

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe` available in your PATH

Verify:

```bash
ffmpeg -version
ffprobe -version
```

## Install (editable)

```bash
pip install -e ".[dev]"
```

## CLI usage

Transcribe a single video:

```bash
yts --input "https://www.youtube.com/watch?v=..." --output out.txt
```

Batch mode (`list.txt` contains one URL per line):

```bash
yts --input list.txt --output outputs/ --format vtt
```

Add timestamps for TXT output:

```bash
yts --input "https://www.youtube.com/watch?v=..." --output out.txt --format txt --timestamps
```

Name outputs using a JSON title map (your `list.json`):

```bash
yts --input list.txt --output outputs/ --title-map list.json
```

## GPU vs CPU notes (Windows)

If you see a CUDA error like `cublas64_12.dll is not found`, run CPU mode:

```bash
yts --input "https://www.youtube.com/watch?v=..." --output out.txt --device cpu
```

or download CUDA 12.1 and follow the steps below:

### Step 1: Download CUDA 12.1

[https://developer.nvidia.com/cuda-12-1-0-download-archive](https://developer.nvidia.com/cuda-12-1-0-download-archive)

### Step 2: Install

- Choose **Custom**
- Only need:
  - CUDA Runtime
  - cuBLAS

### Step 3: Add PATH (very important)

Add to PATH in system variables:

```bash
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin
```

## API (optional)

Sync API:

```bash
pip install -e ".[api]"
python -m uvicorn ytranscribe.apps.api_app:create_app --factory --host 0.0.0.0 --port 8000
```

Queue API + Redis worker:

```bash
pip install -e ".[api,queue]"
docker compose up --build
```

Endpoints:

- `POST /jobs`
- `GET /jobs/{job_id}`

