"""Normalize subagent replies and validate every file in a critically-assess run dir."""
import json
import re
import sys
from pathlib import Path

CONFIDENCE = ("low", "medium", "high")
SINGLE_DECISIONS = ("go", "no-go", "conditional-go")
RESULT_KEYS = ("title", "brief", "precommit", "roster", "reports", "analyst", "ledger", "scores",
               "dissent", "blind_spots", "drift", "verdict", "first_step", "confidence", "unknowns")
ROLE_KEYS = ("role", "position", "reasoning", "per_option", "surprise", "confidence", "evidence")


def extract_json(text):
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("no JSON object found")
        text = text[start:end + 1]
    return json.loads(text)


def _is_score(x):
    return isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= 5


def _unique_ids(items):
    ids = [i.get("id") for i in items]
    return None not in ids and len(set(ids)) == len(ids)


def validate_brief(brief):
    e = []
    mode = brief.get("mode")
    if mode not in ("single", "multi"):
        e.append("brief.mode must be 'single' or 'multi'")
    if not str(brief.get("question", "")).strip():
        e.append("brief.question is empty")
    options = brief.get("options") or []
    if not _unique_ids(options):
        e.append("brief.options need unique ids")
    if mode == "single" and len(options) != 2:
        e.append("single mode needs exactly 2 options: the idea and the status quo")
    if mode == "multi" and len(options) < 2:
        e.append("multi mode needs at least 2 options")
    criteria = brief.get("criteria") or []
    if not criteria:
        e.append("brief.criteria is empty")
    if not _unique_ids(criteria):
        e.append("brief.criteria need unique ids")
    for c in criteria:
        w = c.get("weight")
        if isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0:
            e.append(f"criterion {c.get('id')}: weight must be a positive number")
    return e


def validate_role_report(report, option_ids):
    role = report.get("role", "?")
    e = [f"{role}: missing '{k}'" for k in ROLE_KEYS if k not in report]
    if e:
        return e
    if not 1 <= len(report["reasoning"]) <= 3:
        e.append(f"{role}: reasoning needs 1-3 items")
    covered = sorted(str(p.get("option")) for p in report["per_option"])
    if covered != sorted(option_ids):
        e.append(f"{role}: per_option must cover exactly {sorted(option_ids)}, got {covered}")
    if report["confidence"] not in CONFIDENCE:
        e.append(f"{role}: confidence must be low, medium or high")
    if not report["evidence"]:
        e.append(f"{role}: evidence is empty")
    return e


def validate_analyst_report(report, option_ids, criterion_ids):
    e = []
    ledger = report.get("ledger", [])
    for item in ledger:
        claim = item.get("claim")
        if item.get("option") not in option_ids:
            e.append(f"analyst: ledger item for unknown option {item.get('option')}")
        if item.get("kind") not in ("pro", "con"):
            e.append(f"analyst: ledger kind must be pro or con: {claim}")
        if not _is_score(item.get("severity")) or not _is_score(item.get("likelihood")):
            e.append(f"analyst: severity and likelihood must be 1-5: {claim}")
        if not str(item.get("evidence", "")).strip():
            e.append(f"analyst: ledger item without evidence: {claim}")
    for opt in option_ids:
        for kind in ("pro", "con"):
            n = sum(1 for i in ledger if i.get("option") == opt and i.get("kind") == kind)
            if n < 2:
                e.append(f"analyst: option {opt} needs at least 2 {kind}s, got {n}")
    seen = {}
    for s in report.get("scores", []):
        key = (s.get("option"), s.get("criterion"))
        seen[key] = seen.get(key, 0) + 1
        if not _is_score(s.get("score")):
            e.append(f"analyst: score for {key} must be 1-5")
    for opt in option_ids:
        for crit in criterion_ids:
            if seen.get((opt, crit), 0) != 1:
                e.append(f"analyst: need exactly one score for option {opt} x criterion {crit}")
    return e


def validate_result(result):
    e = [f"result: missing '{k}'" for k in RESULT_KEYS if k not in result]
    if e:
        return e
    mode = result["brief"].get("mode")
    option_ids = [o.get("id") for o in result["brief"].get("options", [])]
    decision = result["verdict"].get("decision")
    if mode == "single" and decision not in SINGLE_DECISIONS:
        e.append(f"result: single-mode decision must be one of {SINGLE_DECISIONS}, got {decision}")
    if mode == "multi" and decision not in option_ids + ["hybrid"]:
        e.append(f"result: multi-mode decision must be an option id or 'hybrid', got {decision}")
    if decision == "conditional-go" and not result["verdict"].get("conditions"):
        e.append("result: conditional-go needs verdict.conditions")
    if result["confidence"] not in CONFIDENCE:
        e.append("result: confidence must be low, medium or high")
    if not result["blind_spots"]:
        e.append("result: blind_spots is empty; name what every voice missed")
    roles = [r.get("role") for r in result["roster"]]
    council = [r for r in roles if r != "analyst"]
    if "analyst" not in roles:
        e.append("result: roster must include the analyst")
    if not 3 <= len(council) <= 5:
        e.append(f"result: roster needs 3-5 council roles, got {len(council)}")
    return e


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_run(run_dir):
    run = Path(run_dir)
    errors = []
    for raw in sorted((run / "reports").glob("*.raw.txt")):
        role = raw.name.removesuffix(".raw.txt")
        try:
            data = extract_json(raw.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"{role}: reply is not valid JSON ({exc})")
            continue
        (run / "reports" / f"{role}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    brief = _read(run / "brief.json")
    errors += validate_brief(brief)
    option_ids = [o.get("id") for o in brief.get("options", [])]
    criterion_ids = [c.get("id") for c in brief.get("criteria", [])]
    for path in sorted((run / "reports").glob("*.json")):
        report = _read(path)
        if report.get("role") == "analyst":
            errors += validate_analyst_report(report, option_ids, criterion_ids)
        else:
            errors += validate_role_report(report, option_ids)
    if (run / "result.json").exists():
        errors += validate_result(_read(run / "result.json"))
    return errors


if __name__ == "__main__":
    problems = validate_run(sys.argv[1])
    for p in problems:
        print(f"ERROR: {p}")
    print("OK" if not problems else f"{len(problems)} error(s)")
    sys.exit(1 if problems else 0)
