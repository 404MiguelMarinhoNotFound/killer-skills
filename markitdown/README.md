# markitdown skill — local runtime

This folder holds the Cursor skill (`SKILL.md`) plus an isolated Python environment for [MarkItDown](https://github.com/microsoft/markitdown).

## Prerequisites

- Python 3.10+ on `PATH` (this machine used 3.12).

## Activate (Windows PowerShell)

From this directory:

```powershell
.\.venv\Scripts\Activate.ps1
markitdown --version
```

## Reinstall / another machine

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
```

## Optional: audio / video

If you use audio transcription or similar paths, install [FFmpeg](https://ffmpeg.org/) and ensure `ffmpeg` is on `PATH` to silence pydub warnings and enable decoding.

## Azure

Document Intelligence and Content Understanding need endpoints and Azure auth (see `SKILL.md`); no keys are stored in this repo.
