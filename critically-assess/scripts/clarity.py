"""Plain-English checks for the text a reader sees in the report.

Flags the habits that made early reports hard to read: note-style text (arrows, slashes, clauses
chained with semicolons), items that open by pointing at text the reader cannot see, options called
by their letter instead of their name, the skill's internal vocabulary, and acronyms the reader was
never told the meaning of.

There is deliberately no length limit. A word cap pushed writers to compress ideas into shorthand,
which is the opposite of clear; a big idea needs the words it takes to explain it.
"""
import re

# Acronyms most technical readers know. Anything else must be spelled out once, e.g.
# "point-in-time recovery (PITR)", or appear in the user's own question or options.
COMMON_ACRONYMS = {
    "AI", "API", "APIs", "AWS", "CD", "CI", "CLI", "CPU", "CRUD", "CSS", "CSV", "DB", "EU", "GB", "GCP",
    "GPU", "HTML", "HTTP", "HTTPS", "ID", "IDs", "IO", "JSON", "KB", "LLM", "LLMs", "MB", "OK", "OS", "PDF",
    "RAM", "REST", "SDK", "SQL", "SSD", "TB", "UI", "UK", "URL", "URLs", "US", "USD", "UX", "XML", "YAML",
}

INTERNAL_TERMS = [
    (r"\bpre-?commit(?:ment|ted|s)?\b", "pre-commitment"),
    (r"\bthe brief\b", "the brief"),
    (r"\bcouncil voices?\b", "council voice"),
    (r"\bstep \d+\b", "step number"),
    (r"\broster\b", "roster"),
    (r"\bper_option\b|\braised_by\b|\bresult\.json\b|\bbrief\.json\b", "file or field name"),
    (r"\blens(?:es)?\b", "lens"),
]

_LETTER_CONTEXT = (r"option|options|favour|favor|favours|favors|choose|chose|pick|picked|reject|rejects|rejected|keep|"
                   r"adopt|over|than|vs\.?|versus|and|or|with|to|prefer|prefers|recommend|recommends")
# Each item is shown on its own, so an opening pronoun or a pointer to "above" refers to nothing.
_LEANING_START = re.compile(r"^(?:it|this|that|these|those|they|same)\b(?!-)", re.IGNORECASE)
_POINTS_ELSEWHERE = re.compile(r"\b(?:as (?:noted|mentioned|said|discussed) (?:above|earlier|before)|see above|as above)\b", re.IGNORECASE)
_NOTE_STYLE = re.compile(r"->|=>|→|←|(?<!\w)w/o?(?=\s)|(?<!\w)b/c\b")
_URL = re.compile(r"\S+://\S+")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,6}s?\b")
_DEFINED = re.compile(r"\(([A-Z][A-Z0-9]{1,6}s?)\)")


def _sentences(text):
    return [s.strip() for s in _SENTENCE_SPLIT.split(str(text).strip()) if s.strip()]


def _excerpt(s, n=70):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + "…"


def _letter_patterns(option_ids):
    pats = []
    for letter in (o for o in option_ids if isinstance(o, str) and re.fullmatch(r"[A-Z]", o)):
        pats.append(re.compile(
            rf"\b{letter}['’]s\b"
            rf"|\b(?i:{_LETTER_CONTEXT})\s+{letter}\b"
            rf"|\({letter}\)"
            rf"|\b{letter}\s+(?:and|or|vs\.?|versus|over)\s+[A-Z]\b"
            rf"|\b{letter}\s+\("))
    return pats


def check_text(text, options, known=frozenset(), defined=frozenset()):
    """Return clarity problems in one piece of text. `options` maps option id to option name."""
    problems = []
    text = str(text or "")
    letter_pats = _letter_patterns(options)
    allowed = COMMON_ACRONYMS | set(known) | set(defined) | set(_DEFINED.findall(text))
    if _LEANING_START.match(text.strip()) or _POINTS_ELSEWHERE.search(text):
        problems.append(f"leans on text the reader cannot see; name the subject so the item stands alone: {_excerpt(text)}")
    for s in _sentences(text):
        if s.count(";") >= 2 or (";" in s and ":" in s) or _NOTE_STYLE.search(s):
            problems.append(f"reads like notes; write out how the ideas connect, in full sentences: {_excerpt(s)}")
    if any(p.search(text) for p in letter_pats):
        names = ", ".join(f"{k} = {v}" for k, v in options.items())
        problems.append(f"uses an option letter, write the option's name ({names}): {_excerpt(text)}")
    for pattern, label in INTERNAL_TERMS:
        if re.search(pattern, text, re.IGNORECASE):
            problems.append(f"internal term '{label}', say it in plain words: {_excerpt(text)}")
    unexplained = sorted({a for a in _ACRONYM.findall(text) if a not in allowed and a.rstrip("s") not in allowed and a not in options})
    if unexplained:
        problems.append(f"unexplained acronym {', '.join(unexplained)}, spell it out once, e.g. 'full name (ABBR)': {_excerpt(text)}")
    return problems


def _user_terms(brief):
    """Acronyms the user already used: the question and the option names and descriptions."""
    source = " ".join([str(brief.get("question", ""))] +
                      [f"{o.get('name', '')} {o.get('description', '')}" for o in brief.get("options", []) if isinstance(o, dict)])
    return set(_ACRONYM.findall(source))


def _fields(result):
    verdict = result.get("verdict") or {}
    dissent = result.get("dissent") or {}
    yield "title", result.get("title")
    yield "verdict.summary", verdict.get("summary")
    for i, c in enumerate(verdict.get("conditions") or []):
        yield f"verdict.conditions[{i}]", c
    yield "first_step", result.get("first_step")
    yield "drift", result.get("drift")
    yield "dissent.position", dissent.get("position")
    yield "dissent.why_rejected", dissent.get("why_rejected")
    for i, b in enumerate(result.get("blind_spots") or []):
        yield f"blind_spots[{i}]", b
    for i, u in enumerate(result.get("unknowns") or []):
        yield f"unknowns[{i}]", u
    for i, item in enumerate(result.get("ledger") or []):
        if isinstance(item, dict):
            yield f"ledger[{i}].claim", item.get("claim")
    for i, s in enumerate(result.get("scores") or []):
        if isinstance(s, dict):
            yield f"scores[{i}].rationale", s.get("rationale")


def _defined_anywhere(texts):
    return set(_DEFINED.findall(" ".join(str(t or "") for t in texts)))


def check_result(result):
    """Clarity problems in every user-facing field of result.json, each prefixed with its field."""
    brief = result.get("brief") or {}
    options = {o.get("id"): o.get("name") for o in brief.get("options", []) if isinstance(o, dict)}
    fields = list(_fields(result))
    known, defined = _user_terms(brief), _defined_anywhere(t for _, t in fields)
    return [f"{name}: {p}" for name, text in fields if text for p in check_text(text, options, known, defined)]


def check_reports(reports, brief):
    """The same checks on the council text the report shows; the caller treats these as warnings."""
    options = {o.get("id"): o.get("name") for o in brief.get("options", []) if isinstance(o, dict)}
    known = _user_terms(brief)
    out = []
    for r in reports:
        if not isinstance(r, dict):
            continue
        role = r.get("role", "?")
        texts = [("position", r.get("position")), ("surprise", r.get("surprise"))]
        texts += [(f"reasoning[{i}]", x) for i, x in enumerate(r.get("reasoning") or [])]
        # Evidence is shown too; drop the tag and any URL before checking the prose around them.
        texts += [(f"evidence[{i}]", _URL.sub("", re.sub(r"^\w+:\s*", "", str(x))))
                  for i, x in enumerate(r.get("evidence") or [])]
        defined = _defined_anywhere(t for _, t in texts)
        out += [f"{role}.{name}: {p}" for name, text in texts if text for p in check_text(text, options, known, defined)]
    return out
