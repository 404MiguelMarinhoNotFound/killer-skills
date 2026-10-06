"""Read the reply files the council wrote and validate every file in a critically-assess run dir.

Validation never raises on bad data: every problem becomes an error line, prefixed
with the role (or file) it belongs to, so one broken reply cannot sink the run.
"""
import hashlib
import json
import re
import sys
from pathlib import Path


CONFIDENCE = ("low", "medium", "high")
SINGLE_DECISIONS = ("go", "no-go", "conditional-go")
RESULT_KEYS = ("title", "brief", "precommit", "roster", "reports", "analyst", "ledger", "scores",
               "dissent", "blind_spots", "drift", "view_changed", "verdict", "first_step", "confidence",
               "confidence_why", "unknowns")
ROLE_KEYS = ("role", "pick", "point", "position", "reasoning", "per_option", "surprise", "confidence", "evidence")
RESEARCH = ("online", "repo", "both", "none")
COUNCIL_TAGS = ("Brief:", "Source:", "Mechanism:", "Knowledge:")
ANALYST_TAGS = ("Brief:", "Mechanism:", "Knowledge:", "Supervisor:")


def read_reply(path):
    """Return the JSON object a council member wrote to reports/<role>.reply.json.

    The member writes the file itself, so it must hold exactly one JSON object and nothing
    else: no code fences, no notes before or after it. Anything else is an error, which
    sends the role back to rewrite its file.
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ValueError(f"{Path(path).name} is not a single JSON object ({exc}); "
                         "the file must hold only the JSON object, with no code fences or text around it")
    if not isinstance(data, dict):
        raise ValueError(f"{Path(path).name} must hold a JSON object, not a {type(data).__name__}")
    return data


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
    for key in ("point", "position", "surprise"):
        if not _is_text(report[key]):
            e.append(f"{role}: {key} must be a non-empty string")
    if report["pick"] not in option_ids:
        e.append(f"{role}: pick must be the id of the option your lens favours, one of {list(option_ids)}")
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


DECISION_TO_OPTION = {"go": "A", "conditional-go": "A", "no-go": "B"}


def validate_precommit(pre, mode, option_ids):
    """The view the supervisor sealed before the council ran."""
    if not isinstance(pre, dict):
        return ["precommit must be a JSON object"]
    e = []
    for key in ("position", "main_risk"):
        if not _is_text(pre.get(key)):
            e.append(f"precommit.{key} must be a non-empty string")
    if not _is_text_list(pre.get("reasons"), allow_empty=False):
        e.append("precommit.reasons must be a non-empty list of strings")
    allowed = list(SINGLE_DECISIONS) if mode == "single" else option_ids + ["hybrid"]
    if pre.get("pick") not in allowed:
        e.append(f"precommit.pick must be the decision you would give before the council, one of {allowed}")
    return e


def _decided_option(mode, decision):
    """The option id a verdict backs, or None for a hybrid."""
    return DECISION_TO_OPTION.get(decision) if mode == "single" else (None if decision == "hybrid" else decision)


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

    for key in ("title", "drift", "first_step", "confidence_why"):
        if not _is_text(result[key]):
            e.append(f"result: {key} must be a non-empty string")
    e += [f"result.{x}" for x in validate_precommit(result["precommit"], mode, option_ids)]
    for key, parent in (("role", "dissent"), ("position", "dissent"),
                        ("why_rejected", "dissent"), ("summary", "verdict")):
        if not isinstance(result[parent], dict) or not _is_text(result[parent].get(key)):
            e.append(f"result: {parent}.{key} must be a non-empty string")
    if not _is_text_list(result["blind_spots"], allow_empty=False):
        e.append("result: blind_spots is empty; name what every voice missed")
    if not _is_text_list(result["unknowns"]):
        e.append("result: unknowns must be a list of strings")
    if result["confidence"] not in CONFIDENCE:
        e.append("result: confidence must be low, medium or high")
    if not isinstance(result["view_changed"], bool):
        e.append("result: view_changed must be true or false: did the council change your pre-council view?")

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

    pre = result["precommit"] if isinstance(result["precommit"], dict) else {}
    if pre.get("pick") is not None and decision is not None and pre.get("pick") != decision \
            and result["view_changed"] is False:
        e.append(f"result: view_changed is false, but the verdict ({decision}) differs from the view "
                 f"written before the council ({pre.get('pick')}); set it to true and explain in drift")

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
    if len(set(map(str, roles))) != len(roles):
        e.append("result: roster lists a role more than once")
    known_roles = set(map(str, roles))

    if not _dicts(result["reports"]):
        e.append("result: reports must be a list of report objects")
    else:
        for report in result["reports"]:
            e += [f"result.reports: {x}" for x in validate_role_report(report, option_ids)]
        reported = sorted(str(r.get("role")) for r in result["reports"])
        if reported != sorted(map(str, council)):
            e.append(f"result: reports must hold one report per council role in the roster {sorted(map(str, council))}, "
                     f"got {reported}")
    analyst_errors = validate_analyst_report(result["analyst"], option_ids, criterion_ids)
    e += [f"result.{x}" for x in analyst_errors]
    if not analyst_errors:
        by_supervisor = any(r.get("role") == "analyst" and r.get("model") == "supervisor" for r in roster)
        e += _check_analyst_authorship(result["analyst"], by_supervisor)
    if isinstance(result["dissent"], dict) and _is_text(result["dissent"].get("role")) \
            and result["dissent"]["role"] not in known_roles:
        e.append(f"result: dissent.role must be a role in the roster, got {result['dissent']['role']}")
    if not _dicts(result["ledger"]):
        e.append("result: ledger must be a list of objects")
    else:
        for item in result["ledger"]:
            e += _check_ledger_item(item, option_ids, "result")
            if not _is_text(item.get("point")):
                e.append(f"result: ledger item without a point: {item.get('claim')}")
            if not _is_text_list(item.get("raised_by"), allow_empty=False):
                e.append(f"result: ledger raised_by must be a non-empty list of role ids: {item.get('claim')}")
            else:
                unknown = [r for r in item["raised_by"] if r not in known_roles]
                if unknown:
                    e.append(f"result: ledger raised_by names roles not in the roster {unknown}: {item.get('claim')}")
    score_errors = _check_scores(result["scores"], option_ids, criterion_ids, "result")
    if not score_errors and not analyst_errors:
        e += _check_supervisor_overrides(result["scores"], result["analyst"]["scores"])
    return e + score_errors


def _check_analyst_authorship(analyst, by_supervisor):
    """Only a supervisor-written analyst report may use the Supervisor: tag, and then it must use it everywhere."""
    texts = [str(i.get("evidence", "")) for i in analyst["ledger"]] + [str(s.get("rationale", "")) for s in analyst["scores"]]
    tagged = [x.strip().startswith("Supervisor:") for x in texts]
    if by_supervisor and not all(tagged):
        return ["result: the analyst's model is 'supervisor', so every analyst evidence and rationale "
                "must start with 'Supervisor:'"]
    if not by_supervisor and any(tagged):
        return ["result: the analyst report uses the 'Supervisor:' tag, but the roster says the analyst wrote it; "
                "set the analyst's model to 'supervisor' if you wrote it yourself"]
    return []


def result_warnings(result):
    """Coherence problems a script can spot but not judge: printed as warnings for the coherence pass."""
    brief, w = result["brief"], []
    names = {o["id"]: o["name"] for o in brief["options"]}
    decided = _decided_option(brief["mode"], result["verdict"].get("decision"))
    summary = str(result["verdict"].get("summary", ""))
    if decided in names and names[decided].lower() not in summary.lower():
        w.append(f"result: the verdict backs {names[decided]}, but verdict.summary does not name it")
    dissent_role = result["dissent"].get("role")
    for r in result["reports"]:
        if r.get("role") == dissent_role and decided and r.get("pick") == decided:
            w.append(f"result: the dissent comes from {dissent_role}, who picked the option you recommend "
                     f"({names.get(decided)}); the dissent should be the strongest view you did not adopt")
    if dissent_role == "analyst":
        w.append("result: the dissent names the analyst, who recommends nothing; pick a council member's view")
    if decided:
        from scoring import weighted_totals, winners  # local import keeps validate.py usable on its own
        top = winners(weighted_totals(brief["criteria"], result["scores"]))
        if decided not in top:
            w.append(f"result: the verdict backs {names.get(decided)}, but the weighted scores rank "
                     f"{' and '.join(names.get(x, x) for x in top)} first; make sure the summary says why")
    return w


def _check_supervisor_overrides(scores, analyst_scores):
    """A score that differs from the analyst's must say the supervisor changed it, and why."""
    given = {(s["option"], s["criterion"]): s["score"] for s in analyst_scores}
    e = []
    for s in scores:
        key = (s["option"], s["criterion"])
        rationale = s.get("rationale")
        if s["score"] != given.get(key) and not (isinstance(rationale, str) and rationale.strip().startswith("Supervisor:")):
            e.append(f"result: score for {key} differs from the analyst's {given.get(key)}; "
                     "start its rationale with 'Supervisor:' and say why")
    return e


def check_result_matches_run(result, brief, reports):
    """result.json must carry the brief and the checked reports exactly as they are on disk.

    The synthesis may weigh the council but never rewrite it, and the brief the council answered
    is the one the reader sees. `reports` maps role id to its checked copy in reports/<role>.json.
    """
    e = []
    if result.get("brief") != brief:
        e.append("result: brief must be brief.json exactly as the council received it")
    for report in list(result.get("reports") or []) + [result.get("analyst")]:
        if not isinstance(report, dict):
            continue
        role = "analyst" if report is result.get("analyst") else report.get("role")
        on_disk = reports.get(role)
        if on_disk is None:
            e.append(f"result: no checked report reports/{role}.json for role {role}")
        elif {k: v for k, v in report.items() if k != "role"} != {k: v for k, v in on_disk.items() if k != "role"}:
            e.append(f"result: the {role} report must be copied unchanged from reports/{role}.json")
    return e


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


FILLABLE = ("pick", "point")


def apply_patch(data, patch, option_ids, role):
    """Fill a council reply's missing `pick` or `point` from reports/<role>.patch.json.

    The supervisor may only fill these two fields, and only where the reply left them out or
    gave an unusable value, so the council's own words are never rewritten. Returns errors.
    """
    if not isinstance(patch, dict) or not patch:
        return [f"{role}: patch must be a JSON object with 'pick' and/or 'point'"]
    extra = sorted(set(patch) - set(FILLABLE))
    if extra:
        return [f"{role}: a patch may only fill {list(FILLABLE)}, not {extra}"]
    e, filled = [], []
    for key, value in patch.items():
        current = data.get(key)
        usable = current in option_ids if key == "pick" else _is_text(current)
        if usable:
            e.append(f"{role}: the reply already has a usable '{key}'; a patch only fills a missing one")
        elif not _is_text(value):
            e.append(f"{role}: patch '{key}' must be a non-empty string")
        else:
            data[key] = value
            filled.append(key)
    if filled:
        data["filled_by_supervisor"] = filled
    return e


URL = re.compile(r"https?://\S+")


def working_dir_of(run):
    """The user's working directory, when the run folder sits at <wd>/.critically-assess/runs/<id>."""
    run = Path(run).resolve()
    if run.parent.name == "runs" and run.parent.parent.name == ".critically-assess":
        return run.parent.parent.parent
    return None


def _repo_path_in(text, wd):
    """True when some token in `text` names an existing file or folder inside the working directory."""
    for token in text.split():
        token = re.sub(r"(#L?\d+.*|:\d+(-\d+)?)$", "", token.strip("`'\"()[],;."))
        if not token or URL.match(token):
            continue
        try:
            path = (wd / token).resolve()
        except (OSError, ValueError):
            continue
        inside = wd in path.parents or path == wd
        if inside and ".critically-assess" not in path.relative_to(wd).parts and path.exists():
            return True
    return False


def check_sources(report, research, wd):
    """A Source: item must point at something the role was allowed to open and could have opened."""
    role, e = report.get("role", "?"), []
    for item in report.get("evidence") or []:
        if not isinstance(item, str) or not item.strip().startswith("Source:"):
            continue
        text = item.strip()[len("Source:"):]
        has_url, short = bool(URL.search(text)), text.strip()[:60]
        has_path = wd is not None and _repo_path_in(text, wd)
        if research == "none":
            e.append(f"{role}: this run allowed no lookups, so 'Source:' cannot be used; "
                     f"retag it as Brief:, Mechanism: or Knowledge:: {short}")
        elif research == "online" and not has_url:
            e.append(f"{role}: a 'Source:' item must give the URL you opened: {short}")
        elif research == "repo" and wd is not None and not has_path:
            e.append(f"{role}: a 'Source:' item must give the path of a repository file you opened: {short}")
        elif research == "both" and not has_url and wd is not None and not has_path:
            e.append(f"{role}: a 'Source:' item must give the URL or repository path you opened: {short}")
    return e


def _pick_warnings(report, names):
    pick, point = report.get("pick"), report.get("point")
    if pick in names and _is_text(point) and names[pick].lower() not in point.lower():
        others = [n for i, n in names.items() if i != pick and n.lower() in point.lower()]
        hint = f" but names {', '.join(others)}" if others else ""
        says = f"names {', '.join(others)} instead" if others else f"does not name {names[pick]}"
        return [f"{report.get('role')}: picked {names[pick]}, but its point {says}; "
                "read its position and relaunch it if the pick contradicts it"]
    return []


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seal(sealed_file, run_dir):
    """Record the hash of the sealed view in the run folder before the council runs. The hash reveals nothing."""
    (Path(run_dir) / "precommit.sha256").write_text(sha256_of(sealed_file) + "\n", encoding="utf-8")


def unseal(sealed_file, run_dir):
    """Move the sealed view into the run folder, but only once every reply validates. Returns errors.

    The view is copied rather than moved, so precommit.json's timestamp records when the council closed:
    any reply written after it could have read the view, and validation rejects it.
    """
    run, sealed = Path(run_dir), Path(sealed_file)
    if (run / "precommit.json").exists():
        return ["precommit.json already exists: the view is already unsealed"]
    errors = validate_run(run)
    if errors:
        return errors + ["the view stays sealed until every reply validates: fix or relaunch first"]
    seal_file = run / "precommit.sha256"
    if sha256_of(sealed) != seal_file.read_text(encoding="utf-8").strip():
        return [f"{sealed} differs from the view sealed before the council ran"]
    (run / "precommit.json").write_bytes(sealed.read_bytes())
    sealed.unlink()
    try:
        sealed.parent.rmdir()  # the mktemp folder, if nothing else is in it
    except OSError:
        pass
    return validate_run(run)


def check_precommit(run, mode, option_ids):
    """precommit.json must be the file that was sealed before any council reply was written."""
    seal_file, pre_file = run / "precommit.sha256", run / "precommit.json"
    if not seal_file.exists():
        return ["precommit.sha256 not found: seal your view with validate.py --seal before launching the council"]
    errors = []
    replies = list((run / "reports").glob("*.reply.json"))
    if any(r.stat().st_mtime_ns < seal_file.stat().st_mtime_ns for r in replies):
        errors.append("precommit.sha256 is newer than a council reply: the view must be sealed before the council runs")
    if pre_file.exists():
        late = sorted(r.name for r in replies if r.stat().st_mtime_ns > pre_file.stat().st_mtime_ns)
        if late:
            errors.append(f"{', '.join(late)} written after the view was unsealed, when the council could read it; "
                          "the council closes when precommit.json appears")
        if sha256_of(pre_file) != seal_file.read_text(encoding="utf-8").strip():
            errors.append("precommit.json differs from the view sealed before the council ran")
        pre, err = _read(pre_file)
        errors += [err] if err else _safe(validate_precommit, "precommit", pre, mode, option_ids)
    return errors


def check_roster(run, result, checked):
    """result.roster must be the roster fixed before launch, minus roles dropped with their files kept."""
    planned, err = _read(run / "roster.json")
    if err:
        return [err]
    if not _dicts(planned):
        return ["roster.json must be a list of {role, model, why} objects"]
    dropped = {p.name.removesuffix(".reply.json") for p in (run / "reports" / "dropped").glob("*.reply.json")}
    expected = sorted(str(r.get("role")) for r in planned if r.get("role") not in dropped)
    got = sorted(str(r.get("role")) for r in result.get("roster") or [] if isinstance(r, dict))
    e = []
    if got != expected:
        e.append(f"result: roster must be roster.json minus the roles in reports/dropped/ {expected}, got {got}; "
                 "a role leaves the council only by being dropped, and a replacement is added to roster.json")
    missing = [r for r in expected if r not in checked]
    if missing:
        e.append(f"result: no checked report for {missing}")
    return e


def validate_run(run_dir, warnings=None):
    """Return the run's errors. Coherence warnings, which never fail the run, go into `warnings` if given."""
    warnings = [] if warnings is None else warnings
    run = Path(run_dir)
    reports = run / "reports"
    errors = []
    failed = set()
    brief, brief_err = _read(run / "brief.json")
    known_ids = [str(o.get("id")) for o in brief.get("options", []) if isinstance(o, dict)] \
        if isinstance(brief, dict) and isinstance(brief.get("options"), list) else []
    for reply in sorted(reports.glob("*.reply.json")):
        role = reply.name.removesuffix(".reply.json")
        normalized = reports / f"{role}.json"
        normalized.unlink(missing_ok=True)  # never validate a stale copy of an older reply
        try:
            data = read_reply(reply)
        except (OSError, ValueError) as exc:
            errors.append(f"{role}: {exc}")
            failed.add(role)
            continue
        # The file name is the role id; subagents sometimes rename themselves.
        data["role"] = role
        data.pop("filled_by_supervisor", None)  # only a patch file may set this
        patch_path = reports / f"{role}.patch.json"
        if patch_path.exists() and role == "analyst":
            errors.append("analyst: the analyst cannot be patched; relaunch it, or write its report yourself")
        elif patch_path.exists():
            patch, err = _read(patch_path)
            errors += [f"{role}: {err}"] if err else apply_patch(data, patch, known_ids, role)
        normalized.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if brief_err:
        return errors + [brief_err]
    errors += _safe(validate_brief, "brief", brief)
    if errors and not isinstance(brief, dict):
        return errors
    options = brief.get("options") if _dicts(brief.get("options")) else []
    criteria = brief.get("criteria") if _dicts(brief.get("criteria")) else []
    option_ids = [str(o.get("id")) for o in options]
    criterion_ids = [str(c.get("id")) for c in criteria]
    names = {str(o.get("id")): str(o.get("name", "")) for o in options}
    wd = working_dir_of(run)
    research = brief.get("research", "none")
    checked = {}
    for path in sorted(p for p in reports.glob("*.json") if not p.name.endswith((".patch.json", ".reply.json"))):
        if path.stem in failed:
            continue
        report, err = _read(path)
        if err:
            errors.append(f"{path.stem}: {err}")
            continue
        checked[path.stem] = report
        if path.stem == "analyst":
            errors += _safe(validate_analyst_report, "analyst", report, option_ids, criterion_ids)
        else:
            role_errors = _safe(validate_role_report, path.stem, report, option_ids)
            errors += role_errors
            if not role_errors:
                errors += _safe(check_sources, path.stem, report, research, wd)
                warnings += _pick_warnings(report, names)
    errors += _safe(check_precommit, "precommit", run, brief.get("mode"), option_ids)
    if (run / "result.json").exists():
        result, err = _read(run / "result.json")
        if err:
            errors.append(err)
        else:
            result_errors = _safe(validate_result, "result", result)
            # The integrity checks run even when the structure is off, so every problem shows in one round.
            if isinstance(result, dict):
                result_errors += _safe(check_result_matches_run, "result", result, brief, checked)
                result_errors += _safe(check_roster, "result", run, result, checked)
                if not (run / "precommit.json").exists():
                    result_errors.append("precommit.json not found: close the council with validate.py --unseal "
                                         "before writing result.json")
                elif result.get("precommit") != _read(run / "precommit.json")[0]:
                    result_errors.append("result: precommit must be precommit.json exactly as sealed")
            errors += result_errors
            if not result_errors:
                warnings += _safe(result_warnings, "result", result)
    return errors


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == "--seal":
        seal(args[1], args[2])
        print(f"Sealed: {Path(args[2]) / 'precommit.sha256'}")
        sys.exit(0)
    if len(args) == 3 and args[0] == "--unseal":
        problems = unseal(args[1], args[2])
        for p in problems:
            print(f"ERROR: {p}")
        print(f"Unsealed: {Path(args[2]) / 'precommit.json'}" if not problems else f"{len(problems)} error(s)")
        sys.exit(1 if problems else 0)
    if len(args) != 1:
        print("usage: validate.py <run_dir>\n       validate.py --seal <sealed_view.json> <run_dir>\n"
              "       validate.py --unseal <sealed_view.json> <run_dir>")
        sys.exit(2)
    found = []
    problems = validate_run(args[0], found)
    for p in problems:
        print(f"ERROR: {p}")
    for w in found:
        print(f"WARNING: {w}")
    print("OK" if not problems else f"{len(problems)} error(s)")
    sys.exit(1 if problems else 0)
