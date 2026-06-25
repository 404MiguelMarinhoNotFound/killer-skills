---
name: markitdown
description: Convert files and URLs to markdown with MarkItDown for LLM ingestion. Use when users request document-to-markdown extraction from PDFs, Office files, HTML, images, audio, ZIPs, EPUBs, or YouTube URLs.
disable-model-invocation: true
---

# MarkItDown

## Use Cases

Use this skill when the user needs to:

- Convert documents into Markdown for LLM pipelines.
- Preserve structure (headings, lists, tables, links) during extraction.
- Convert common formats like PDF, PPTX, DOCX, XLSX, HTML, JSON, CSV, XML, images, audio, ZIP, EPUB, and YouTube transcripts.
- Route conversions through Azure Document Intelligence or Azure Content Understanding.

## Security Rules (Mandatory)

MarkItDown performs I/O with current-process privileges. Treat it like `open()` plus network fetch capability.

Before calling MarkItDown in any untrusted workflow:

1. Sanitize and constrain file paths.
2. Restrict allowed URI schemes and destinations.
3. Block access to loopback, private, link-local, and metadata-service addresses.
4. Use the narrowest API:
   - `convert_local()` for local files.
   - `convert_stream()` for pre-opened streams.
   - `convert_response()` when the caller controls HTTP fetching.
   - Avoid generic `convert()` unless permissive behavior is explicitly intended.

## Prerequisites

- Python 3.10+
- Prefer an isolated environment (`venv`, `uv`, or `conda`).

Examples:

```bash
python -m venv .venv
source .venv/bin/activate
pip install 'markitdown[all]'
```

```bash
uv venv --python=3.12 .venv
source .venv/bin/activate
uv pip install 'markitdown[all]'
```

### Local environment (this skill folder)

A `.venv` next to this file can hold `markitdown[all]` for CLI and Python use. On Windows (PowerShell), from `markitdown/`:

```powershell
.\.venv\Scripts\Activate.ps1
markitdown --version
```

Reinstall: `pip install -r requirements.txt`. See `README.md` for FFmpeg and Azure notes.

## CLI Patterns

Basic conversion:

```bash
markitdown path-to-file.pdf > document.md
```

Explicit output file:

```bash
markitdown path-to-file.pdf -o document.md
```

Piped content:

```bash
cat path-to-file.pdf | markitdown
```

List plugins:

```bash
markitdown --list-plugins
```

Enable plugins:

```bash
markitdown --use-plugins path-to-file.pdf
```

## Python API Patterns

Basic conversion:

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)
result = md.convert("test.xlsx")
print(result.text_content)
```

Document Intelligence:

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

LLM image descriptions:

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="optional custom prompt",
)
result = md.convert("example.jpg")
print(result.text_content)
```

## Optional Dependencies

Install all extras:

```bash
pip install 'markitdown[all]'
```

Install selected extras:

```bash
pip install 'markitdown[pdf,docx,pptx]'
```

Common extras include:

- `pptx`, `docx`, `xlsx`, `xls`, `pdf`, `outlook`
- `az-doc-intel`, `az-content-understanding`
- `audio-transcription`, `youtube-transcription`

## markitdown-ocr Plugin

Adds OCR support to embedded images in PDF/DOCX/PPTX/XLSX using the same `llm_client` + `llm_model` setup.

```bash
pip install markitdown-ocr
pip install openai
```

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)
result = md.convert("document_with_images.pdf")
print(result.text_content)
```

## Azure Content Understanding

Use CU when you need:

- Audio/video support (including video extraction).
- Structured field extraction as YAML front matter.
- Analyzer-based, domain-specific extraction.
- Higher-quality cloud OCR/layout for complex documents.

CLI:

```bash
markitdown path-to-file.pdf --use-cu --cu-endpoint "<content_understanding_endpoint>"
```

Python:

```python
from markitdown import MarkItDown

md = MarkItDown(cu_endpoint="<content_understanding_endpoint>")
print(md.convert("report.pdf").markdown)
print(md.convert("meeting.mp4").markdown)
print(md.convert("call.wav").markdown)
```

Custom analyzer:

```python
md = MarkItDown(
    cu_endpoint="<content_understanding_endpoint>",
    cu_analyzer_id="my-invoice-analyzer",
)
result = md.convert("invoice.pdf")
print(result.markdown)
```

Restrict CU billing scope:

```python
from markitdown import MarkItDown
from markitdown.converters import ContentUnderstandingFileType

md = MarkItDown(
    cu_endpoint="<content_understanding_endpoint>",
    cu_file_types=[ContentUnderstandingFileType.PDF],
)
```

## Azure Document Intelligence (CLI)

```bash
markitdown path-to-file.pdf -o document.md -d -e "<document_intelligence_endpoint>"
```

## Docker

```bash
docker build -t markitdown:latest .
docker run --rm -i markitdown:latest < ~/your-file.pdf > output.md
```

## Testing and Contribution Commands

```bash
cd packages/markitdown
pip install hatch
hatch shell
hatch test
pre-commit run --all-files
```

## Notes

- Prefer Markdown output for token-efficient downstream LLM consumption.
- Output quality prioritizes structure and machine readability over presentation fidelity.
- For plugin discovery, search GitHub for `#markitdown-plugin`.

