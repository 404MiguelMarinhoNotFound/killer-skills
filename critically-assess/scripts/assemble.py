"""Build result.json from the supervisor's judgement plus the run's files, copied exactly as they are on disk.

The supervisor writes only its own judgement (ledger, dissent, verdict and so on) to a synthesis file.
This script copies in the brief, the sealed view, the roster and every checked report unchanged, so the
synthesis can never rewrite the council by accident, then validates the whole run.
"""
import json
import sys
from pathlib import Path

import validate

COPIED = ("brief", "precommit", "roster", "reports", "analyst")
JUDGEMENT = tuple(k for k in validate.RESULT_KEYS if k not in COPIED and k != "scores")


def assemble(run_dir, synthesis_file):
    """Write <run_dir>/result.json. Returns errors; an empty list means it was written."""
    run = Path(run_dir)
    synthesis, err = validate._read(synthesis_file)
    if err:
        return [err]
    if not isinstance(synthesis, dict):
        return ["the synthesis file must hold one JSON object"]
    copied = [k for k in COPIED if k in synthesis]
    if copied:
        return [f"leave {copied} out of the synthesis file: they are copied from the run folder unchanged"]
    missing = [k for k in JUDGEMENT if k not in synthesis]
    if missing:
        return [f"the synthesis file is missing {missing}"]
    unknown = sorted(set(synthesis) - set(validate.RESULT_KEYS))
    if unknown:
        return [f"the synthesis file has keys result.json does not use: {unknown}"]
    if not (run / "precommit.json").exists():
        return ["precommit.json not found: close the council with validate.py --unseal before assembling"]

    parts = {}
    for name in ("brief.json", "precommit.json", "roster.json", "reports/analyst.json"):
        data, err = validate._read(run / name)
        if err:
            return [err + " (run validate.py on the run folder first, so the checked copies exist)"]
        parts[name] = data
    if not validate._dicts(parts["roster.json"]):
        return ["roster.json must be a list of {role, model, why} objects"]
    dropped = validate._dropped(run)
    roster = [r for r in parts["roster.json"] if r.get("role") not in dropped]
    reports = []
    for entry in roster:
        if entry.get("role") == "analyst":
            continue
        report, err = validate._read(run / "reports" / f"{entry.get('role')}.json")
        if err:
            return [err + " (run validate.py on the run folder first, so the checked copies exist)"]
        reports.append(report)

    result = {"title": synthesis["title"], "brief": parts["brief.json"], "precommit": parts["precommit.json"],
              "roster": roster, "reports": reports, "analyst": parts["reports/analyst.json"]}
    result.update({k: v for k, v in synthesis.items() if k != "title"})
    result.setdefault("scores", parts["reports/analyst.json"].get("scores"))
    ordered = {k: result[k] for k in validate.RESULT_KEYS if k in result}
    (run / "result.json").write_text(json.dumps(ordered, indent=2, ensure_ascii=False), encoding="utf-8")
    return []


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: assemble.py <run_dir> <synthesis.json>")
        sys.exit(2)
    problems = assemble(sys.argv[1], sys.argv[2])
    if not problems:
        found = []
        problems = validate.validate_run(sys.argv[1], found)
        for w in found:
            print(f"WARNING: {w}")
    for p in problems:
        print(f"ERROR: {p}")
    print(f"Wrote {Path(sys.argv[1]) / 'result.json'}; OK" if not problems else f"{len(problems)} error(s)")
    sys.exit(1 if problems else 0)
