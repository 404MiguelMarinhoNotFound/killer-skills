"""Inject result.json into the HTML template and print a terminal summary."""
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import role_library
import scoring
import validate

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "report.html"
ROLES_DIR = Path(__file__).resolve().parent.parent / "roles"
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


def open_in_browser(path):
    """Open the report in the default browser when this machine has one. Returns True if launched.

    Skipped when disabled (--no-open or CRITICALLY_ASSESS_NO_OPEN), in CI, and on Linux without a
    display, where a generic opener could fall back to a text browser and hang the terminal.
    """
    if os.environ.get("CRITICALLY_ASSESS_NO_OPEN") or os.environ.get("CI"):
        return False
    target = str(Path(path).resolve())
    quiet = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "stdin": subprocess.DEVNULL}
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", target], **quiet)
            return True
        if sys.platform.startswith("win"):
            os.startfile(target)  # type: ignore[attr-defined]
            return True
        if "microsoft" in platform.uname().release.lower() and shutil.which("wslview"):  # WSL: use the Windows browser
            subprocess.Popen(["wslview", target], start_new_session=True, **quiet)
            return True
        if (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) and shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", target], start_new_session=True, **quiet)
            return True
    except OSError:
        pass
    return False


def main(run_dir, open_report=True):
    run = Path(run_dir)
    result = json.loads((run / "result.json").read_text(encoding="utf-8"))
    problems = validate.validate_result(result)
    if problems:
        print("result.json is not valid; fix it and run validate.py first:")
        print("\n".join(f"ERROR: {p}" for p in problems))
        sys.exit(1)
    out = run / "report.html"
    # Role names and one-line summaries come from the role files, so the report never drifts from the library.
    page_data = {**result, "role_catalog": role_library.catalog(ROLES_DIR)}
    out.write_text(render_html(page_data, TEMPLATE.read_text(encoding="utf-8")), encoding="utf-8")
    print(terminal_summary(result))
    print(f"\nReport: {out.resolve()}")
    if open_report and open_in_browser(out):
        print("Opened in your default browser.")
    else:
        print(f"Open it in a browser: {out.resolve().as_uri()}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--no-open"]
    main(args[0], open_report="--no-open" not in sys.argv[1:])
