"""Normalize subagent replies and validate every file in a critically-assess run dir.

Validation never raises on bad data: every problem becomes an error line, prefixed
with the role (or file) it belongs to, so one broken reply cannot sink the run.
"""
import json
import sys
from pathlib import Path


CONFIDENCE = ("low", "medium", "high")
SINGLE_DECISIONS = ("go", "no-go", "conditional-go")
RESULT_KEYS = ("title", "brief", "precommit", "roster", "reports", "analyst", "ledger", "scores",
               "dissent", "blind_spots", "drift", "verdict", "first_step", "confidence", "unknowns")
ROLE_KEYS = ("role", "position", "reasoning", "per_option", "surprise", "confidence", "evidence")
RESEARCH = ("online", "repo", "both", "none")
COUNCIL_TAGS = ("Brief:", "Source:", "Mechanism:", "Knowledge:")
ANALYST_TAGS = ("Brief:", "Mechanism:", "Knowledge:", "Supervisor:")


def extract_json(text):
    """Return the last top-level JSON object in a reply.

    Models sometimes write a draft or an example before their final JSON, so the last
    complete object wins. Objects nested inside another are not counted on their own,
    and code fences or prose around the JSON are ignored.
    """
    decoder = json.JSONDecoder()
    last, pos = None, 0
    while (start := text.find("{", pos)) != -1:
        try:
            obj, end = decoder.raw_decode(text, start)
        except ValueError:
            pos = start + 1
            continue
        if isinstance(obj, dict):
            last = obj
        pos = end
    if last is None:
        raise ValueError("no JSON object found")
    return last


def _is_score(x):
    return isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= 5


def _is_text(x):
    return isinstance(x, str) and bool(x.strip())


def _is_text_list(x, allow_empty=True):
    return isinstance(x, list) and all(isinstance(i, str) for i in x) and (allow_empty or bool(x))


def _dicts(x):
    return isinstance(x, list) and all(isinstance(i, dict) for i in x)


def _unique_ids(items):
    ids = [i.get("id") for i in items]
    return all(_is_text(i) for i in ids) and len(set(ids)) == len(ids)


def validate_brief(brief):
    if not isinstance(brief, dict):
        return ["brief must be a JSON object"]
    e = []
    mode = brief.get("mode")
    if mode not in ("single", "multi"):
        e.append("brief.mode must be 'single' or 'multi'")
    if not _is_text(brief.get("question")):
        e.append("brief.question is empty")
    options = brief.get("options")
    if not _dicts(options):
        e.append("brief.options must be a list of objects")
        options = []
    if not _unique_ids(options):
        e.append("brief.options need unique string ids")
    for o in options:
        if not _is_text(o.get("name")):
            e.append(f"option {o.get('id')}: name is empty")
    if mode == "single":
        if len(options) != 2:
            e.append("single mode needs exactly 2 options: the idea and the status quo")
        elif options[1].get("id") != "B" or str(options[1].get("name", "")).strip().lower() != "status quo":
            e.append("single mode: option B must be {\"id\": \"B\", \"name\": \"Status quo\"}")
    if mode == "multi" and len(options) < 2:
        e.append("multi mode needs at least 2 options")
    if "research" in brief and brief["research"] not in RESEARCH:
        e.append(f"brief.research must be one of {RESEARCH}")
    if not isinstance(brief.get("context", ""), str):
        e.append("brief.context must be a string")
    if not _is_text_list(brief.get("constraints", [])):
        e.append("brief.constraints must be a list of strings")
    criteria = brief.get("criteria")
    if not _dicts(criteria) or not criteria:
        return e + ["brief.criteria must be a non-empty list of objects"]
    if not _unique_ids(criteria):
        e.append("brief.criteria need unique string ids")
    for c in criteria:
        w = c.get("weight")
        if isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0:
            e.append(f"criterion {c.get('id')}: weight must be a positive number")
        if not _is_text(c.get("name")):
            e.append(f"criterion {c.get('id')}: name is empty")
        if not isinstance(c.get("why", ""), str):
            e.append(f"criterion {c.get('id')}: why must be a string")
    return e


def validate_role_report(report, option_ids):
    if not isinstance(report, dict):
        return ["?: report must be a JSON object"]
    role = report.get("role", "?")
    e = [f"{role}: missing '{k}'" for k in ROLE_KEYS if k not in report]
    if e:
        return e
    for key in ("position", "surprise"):
        if not _is_text(report[key]):
            e.append(f"{role}: {key} must be a non-empty string")
    if not _is_text_list(report["reasoning"]) or not 1 <= len(report["reasoning"]) <= 3:
        e.append(f"{role}: reasoning must be a list of 1-3 strings")
    if not _is_text_list(report["evidence"], allow_empty=False):
        e.append(f"{role}: evidence must be a non-empty list of strings")
    else:
        for item in report["evidence"]:
            if not item.strip().startswith(COUNCIL_TAGS):
                e.append(f"{role}: evidence must start with one of {', '.join(COUNCIL_TAGS)}: {item[:60]}")
    if report["confidence"] not in CONFIDENCE:
        e.append(f"{role}: confidence must be low, medium or high")
    per_option = report["per_option"]
    if not _dicts(per_option):
        return e + [f"{role}: per_option must be a list of objects"]
    covered = sorted(str(p.get("option")) for p in per_option)
    expected = sorted(str(o) for o in option_ids)
    if covered != expected:
        e.append(f"{role}: per_option must cover exactly {expected}, got {covered}")
    for p in per_option:
        for key in ("pros", "cons", "risks"):
            if not _is_text_list(p.get(key, [])):
                e.append(f"{role}: per_option {p.get('option')}.{key} must be a list of strings")
    return e


def _check_scores(scores, option_ids, criterion_ids, who):
    if not _dicts(scores):
        return [f"{who}: scores must be a list of objects"]
    e = []
    seen = {}
    for s in scores:
        key = (str(s.get("option")), str(s.get("criterion")))
        seen[key] = seen.get(key, 0) + 1
        if key[0] not in option_ids or key[1] not in criterion_ids:
            e.append(f"{who}: score for unknown option/criterion {key}")
        if not _is_score(s.get("score")):
            e.append(f"{who}: score for {key} must be an integer 1-5")
    for opt in option_ids:
        for crit in criterion_ids:
            if seen.get((opt, crit), 0) != 1:
                e.append(f"{who}: need exactly one score for option {opt} x criterion {crit}")
    return e


def _check_ledger_item(item, option_ids, who):
    e = []
    claim = item.get("claim")
    if item.get("option") not in option_ids:
        e.append(f"{who}: ledger item for unknown option {item.get('option')}")
    if item.get("kind") not in ("pro", "con"):
        e.append(f"{who}: ledger kind must be pro or con: {claim}")
    if not _is_text(claim):
        e.append(f"{who}: ledger item without a claim")
    if not _is_score(item.get("severity")) or not _is_score(item.get("likelihood")):
        e.append(f"{who}: severity and likelihood must be integers 1-5: {claim}")
    return e


def validate_analyst_report(report, option_ids, criterion_ids):
    if not isinstance(report, dict):
        return ["analyst: report must be a JSON object"]
    e = []
    ledger = report.get("ledger")
    if not _dicts(ledger):
        e.append("analyst: ledger must be a list of objects")
        ledger = []
    for item in ledger:
        e += _check_ledger_item(item, option_ids, "analyst")
        if not _is_text(item.get("evidence")):
            e.append(f"analyst: ledger item without evidence: {item.get('claim')}")
        elif not item["evidence"].strip().startswith(ANALYST_TAGS):
            e.append(f"analyst: ledger evidence tag must be one of {', '.join(ANALYST_TAGS)}: {item.get('claim')}")
    for opt in option_ids:
        for kind in ("pro", "con"):
            n = sum(1 for i in ledger if i.get("option") == opt and i.get("kind") == kind)
            if n < 2:
                e.append(f"analyst: option {opt} needs at least 2 {kind}s, got {n}")
    return e + _check_scores(report.get("scores"), option_ids, criterion_ids, "analyst")


def validate_result(result):
    if not isinstance(result, dict):
        return ["result: must be a JSON object"]
    e = [f"result: missing '{k}'" for k in RESULT_KEYS if k not in result]
    if e:
        return e
    brief_errors = validate_brief(result["brief"])
    e += [f"result.brief: {x}" for x in brief_errors]
    if brief_errors:
        return e
    brief = result["brief"]
    mode = brief["mode"]
    option_ids = [o["id"] for o in brief["options"]]
    criterion_ids = [c["id"] for c in brief["criteria"]]

    for key in ("title", "drift", "first_step"):
        if not _is_text(result[key]):
            e.append(f"result: {key} must be a non-empty string")
    for key, parent in (("position", "precommit"), ("role", "dissent"), ("position", "dissent"),
                        ("why_rejected", "dissent"), ("summary", "verdict")):
        if not isinstance(result[parent], dict) or not _is_text(result[parent].get(key)):
            e.append(f"result: {parent}.{key} must be a non-empty string")
    if not _is_text_list(result["blind_spots"], allow_empty=False):
        e.append("result: blind_spots is empty; name what every voice missed")
    if not _is_text_list(result["unknowns"]):
        e.append("result: unknowns must be a list of strings")
    if result["confidence"] not in CONFIDENCE:
        e.append("result: confidence must be low, medium or high")

    verdict = result["verdict"] if isinstance(result["verdict"], dict) else {}
    decision = verdict.get("decision")
    if mode == "single" and decision not in SINGLE_DECISIONS:
        e.append(f"result: single-mode decision must be one of {SINGLE_DECISIONS}, got {decision}")
    if mode == "multi" and decision not in option_ids + ["hybrid"]:
        e.append(f"result: multi-mode decision must be an option id or 'hybrid', got {decision}")
    if not _is_text_list(verdict.get("conditions", [])):
        e.append("result: verdict.conditions must be a list of strings")
    elif decision == "conditional-go" and not verdict.get("conditions"):
        e.append("result: conditional-go needs verdict.conditions")

    roster = result["roster"]
    if not _dicts(roster):
        e.append("result: roster must be a list of objects")
        roster = []
    roles = [r.get("role") for r in roster]
    council = [r for r in roles if r != "analyst"]
    if "analyst" not in roles:
        e.append("result: roster must include the analyst")
    if not 3 <= len(council) <= 5:
        e.append(f"result: roster needs 3-5 council roles, got {len(council)}")

    if not _dicts(result["reports"]):
        e.append("result: reports must be a list of report objects")
    else:
        for report in result["reports"]:
            e += [f"result.reports: {x}" for x in validate_role_report(report, option_ids)]
    if not _dicts(result["ledger"]):
        e.append("result: ledger must be a list of objects")
    else:
        for item in result["ledger"]:
            e += _check_ledger_item(item, option_ids, "result")
            if not _is_text_list(item.get("raised_by"), allow_empty=False):
                e.append(f"result: ledger raised_by must be a non-empty list of role ids: {item.get('claim')}")
    return e + _check_scores(result["scores"], option_ids, criterion_ids, "result")


def _read(path):
    """Return (data, error) so a missing or corrupt file becomes an error line, not a crash."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"{Path(path).name} not found in {Path(path).parent.resolve()}"
    except ValueError as exc:
        return None, f"{Path(path).name} is not valid JSON ({exc})"


def _safe(fn, who, *args):
    try:
        return fn(*args)
    except Exception as exc:  # last line of defence; the validators should never get here
        return [f"{who}: malformed ({type(exc).__name__}: {exc})"]


def validate_run(run_dir):
    run = Path(run_dir)
    reports = run / "reports"
    errors = []
    failed = set()
    for raw in sorted(reports.glob("*.raw.txt")):
        role = raw.name.removesuffix(".raw.txt")
        normalized = reports / f"{role}.json"
        normalized.unlink(missing_ok=True)  # never validate a stale copy of an older reply
        try:
            data = extract_json(raw.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"{role}: reply is not valid JSON ({exc})")
            failed.add(role)
            continue
        # The file name is the role id; subagents sometimes rename themselves.
        data["role"] = role
        normalized.write_text(json.dumps(data, indent=2), encoding="utf-8")
    brief, err = _read(run / "brief.json")
    if err:
        return errors + [err]
    errors += _safe(validate_brief, "brief", brief)
    if errors and not isinstance(brief, dict):
        return errors
    options = brief.get("options") if _dicts(brief.get("options")) else []
    criteria = brief.get("criteria") if _dicts(brief.get("criteria")) else []
    option_ids = [str(o.get("id")) for o in options]
    criterion_ids = [str(c.get("id")) for c in criteria]
    for path in sorted(reports.glob("*.json")):
        if path.stem in failed:
            continue
        report, err = _read(path)
        if err:
            errors.append(f"{path.stem}: {err}")
        elif path.stem == "analyst":
            errors += _safe(validate_analyst_report, "analyst", report, option_ids, criterion_ids)
        else:
            errors += _safe(validate_role_report, path.stem, report, option_ids)
    if (run / "result.json").exists():
        result, err = _read(run / "result.json")
        if err:
            errors.append(err)
        else:
            errors += _safe(validate_result, "result", result)
    return errors


if __name__ == "__main__":
    problems = validate_run(sys.argv[1])
    for p in problems:
        print(f"ERROR: {p}")
    print("OK" if not problems else f"{len(problems)} error(s)")
    sys.exit(1 if problems else 0)
