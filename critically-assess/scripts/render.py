"""Inject result.json into the HTML template and print a terminal summary."""
import json
import sys
from pathlib import Path

import scoring
import validate

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "report.html"
TOKEN = "__RESULT_JSON__"


def embed_json(data):
    # "<" only occurs inside JSON strings, so < keeps it valid JSON and inert HTML
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def render_html(result, template_text):
    if TOKEN not in template_text:
        raise ValueError("template is missing the data token")
    return template_text.replace(TOKEN, embed_json(result))


def terminal_summary(result):
    brief, verdict = result["brief"], result["verdict"]
    names = {o["id"]: o["name"] for o in brief["options"]}
    lines = [f"## {result['title']}",
             f"Verdict: {names.get(verdict['decision'], verdict['decision'])} — {verdict['summary']}"]
    for cond in verdict.get("conditions") or []:
        lines.append(f"  if: {cond}")
    totals = scoring.weighted_totals(brief["criteria"], result["scores"])
    for option, total in sorted(totals.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {names.get(option, option)}: {total:.2f} / 5")
    flips = [r["criterion"] for r in scoring.sensitivity(brief["criteria"], result["scores"]) if r["flips"]]
    if flips:
        lines.append("Sensitivity: winner changes if these weights move ±0.1: " + ", ".join(flips))
    else:
        lines.append("Sensitivity: stable under ±0.1 weight shifts")
    lines.append(f"Strongest dissent ({result['dissent']['role']}): {result['dissent']['position']}")
    lines.append(f"First step: {result['first_step']}")
    lines.append(f"Confidence: {result['confidence']}")
    return "\n".join(lines)


def main(run_dir):
    run = Path(run_dir)
    result = json.loads((run / "result.json").read_text(encoding="utf-8"))
    problems = validate.validate_result(result)
    if problems:
        print("result.json is not valid; fix it and run validate.py first:")
        print("\n".join(f"ERROR: {p}" for p in problems))
        sys.exit(1)
    out = run / "report.html"
    out.write_text(render_html(result, TEMPLATE.read_text(encoding="utf-8")), encoding="utf-8")
    print(terminal_summary(result))
    print(f"\nReport: {out.resolve()}")


if __name__ == "__main__":
    main(sys.argv[1])
