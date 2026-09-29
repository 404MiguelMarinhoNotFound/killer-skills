"""Load, lint and list council roles from roles/*.md."""
import sys
from pathlib import Path

REQUIRED_KEYS = {"id", "name", "model", "tension_with", "use_when", "skip_when"}
ALLOWED_MODELS = {"opus", "sonnet"}
REQUIRED_SECTIONS = ("## Lens", "## You must", "## You must not")


def parse_role(path):
    text = Path(path).read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3 or parts[0].strip():
        raise ValueError(f"{path}: missing frontmatter")
    meta = {}
    for line in parts[1].strip().splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        meta[key.strip()] = value
    meta["body"] = parts[2].strip()
    return meta


def load_roles(roles_dir):
    return [parse_role(p) for p in sorted(Path(roles_dir).glob("*.md")) if not p.name.startswith("_")]


def check_roles(roles):
    errors = []
    ids = [r.get("id") for r in roles]
    if len(set(ids)) != len(ids):
        errors.append("duplicate role ids")
    for r in roles:
        rid = r.get("id", "?")
        missing = REQUIRED_KEYS - r.keys()
        if missing:
            errors.append(f"{rid}: missing keys {sorted(missing)}")
        if r.get("model") not in ALLOWED_MODELS:
            errors.append(f"{rid}: model must be opus or sonnet, got {r.get('model')}")
        for other in r.get("tension_with", []):
            if other not in ids:
                errors.append(f"{rid}: tension_with unknown role '{other}'")
        headings = {line.strip() for line in r["body"].splitlines() if line.startswith("## ")}
        for section in REQUIRED_SECTIONS:
            if section not in headings:
                errors.append(f"{rid}: missing section '{section}'")
    return errors


if __name__ == "__main__":
    roles_dir = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "roles"
    roles = load_roles(roles_dir)
    for r in roles:
        tension = ", ".join(r["tension_with"]) or "-"
        print(f"{r['id']:<17} {r['model']:<7} tension: {tension:<17} use: {r['use_when']} | skip: {r['skip_when']}")
    problems = check_roles(roles)
    for p in problems:
        print(f"ERROR: {p}")
    sys.exit(1 if problems else 0)
