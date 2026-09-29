from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / ".refs"


@pytest.mark.skipif(not REFS.exists(), reason="run scripts/fetch_refs.sh first")
def test_shipped_text_does_not_copy_reference_lines():
    ref_text = " ".join(
        " ".join(p.read_text(encoding="utf-8", errors="ignore").split())
        for p in REFS.iterdir() if p.is_file()
    )
    shipped = [ROOT / "SKILL.md", *ROOT.glob("roles/*.md"), *ROOT.glob("reference/*.md")]
    for path in shipped:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            norm = " ".join(line.split())
            if len(norm) >= 60:
                assert norm not in ref_text, f"{path.name} copies a reference line: {norm[:60]}"
