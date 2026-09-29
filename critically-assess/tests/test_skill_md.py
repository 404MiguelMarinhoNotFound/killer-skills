import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _split():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    _, fm, body = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return text, meta, body


def test_frontmatter():
    _, meta, _ = _split()
    assert meta["name"] == "critically-assess"
    assert 0 < len(meta["description"]) <= 1024


def test_body_under_500_lines():
    _, _, body = _split()
    assert len(body.splitlines()) < 500


def test_every_referenced_file_exists():
    text, _, _ = _split()
    refs = set(re.findall(r"(?:scripts|roles|reference|templates)/[\w\-]+\.(?:py|md|html)", text))
    assert refs, "SKILL.md should reference its scripts and files"
    for rel in refs:
        assert (ROOT / rel).exists(), rel
