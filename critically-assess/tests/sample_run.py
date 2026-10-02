"""One valid multi-mode run, shared by validate/scoring/render tests."""
import json
from pathlib import Path

BRIEF = {
    "mode": "multi",
    "question": "Postgres or DynamoDB for the new order service?",
    "options": [
        {"id": "A", "name": "Postgres", "description": "Managed Postgres on RDS"},
        {"id": "B", "name": "DynamoDB", "description": "On-demand DynamoDB"},
    ],
    "context": "Team of 3, heavy relational reporting, about 5k orders per day.",
    "evidence": [{"claim": "Finance needs ad-hoc SQL joins", "source": "user"}],
    "constraints": ["Launch in 8 weeks"],
    "stakes": "Hard to migrate once live",
    "research": "both",
    "criteria": [
        {"id": "fit", "name": "Data model fit", "weight": 0.6, "why": "reporting needs joins"},
        {"id": "ops", "name": "Operational load", "weight": 0.4, "why": "small team"},
    ],
}

COUNCIL = ["contrarian", "first-principles", "executor"]


def role_report(role):
    return {
        "role": role,
        "pick": "A",
        "point": f"{role} point",
        "position": f"{role} position",
        "reasoning": ["r1", "r2"],
        "per_option": [
            {"option": "A", "pros": ["p"], "cons": ["c"], "risks": ["k"]},
            {"option": "B", "pros": ["p"], "cons": ["c"], "risks": ["k"]},
        ],
        "surprise": "s",
        "confidence": "medium",
        "evidence": ["Brief: Finance needs ad-hoc SQL joins", "Source: https://example.com/docs"],
    }


def _ledger(option):
    return [
        {"option": option, "kind": kind, "claim": f"{kind} {i} for {option}",
         "evidence": "Brief: stated by the user", "severity": 3, "likelihood": 3}
        for kind in ("pro", "con") for i in (1, 2)
    ]


ANALYST = {
    "role": "analyst",
    "ledger": _ledger("A") + _ledger("B"),
    "scores": [
        {"option": "A", "criterion": "fit", "score": 5, "rationale": "joins"},
        {"option": "A", "criterion": "ops", "score": 3, "rationale": "patching"},
        {"option": "B", "criterion": "fit", "score": 2, "rationale": "no joins"},
        {"option": "B", "criterion": "ops", "score": 5, "rationale": "serverless"},
    ],
}

RESULT = {
    "title": "Postgres vs DynamoDB for orders",
    "brief": BRIEF,
    "precommit": {"position": "Postgres", "reasons": ["joins", "team knows SQL", "RDS is managed"],
                  "main_risk": "ops load"},
    "roster": [{"role": r, "model": "opus", "why": "test"} for r in COUNCIL + ["analyst"]],
    "reports": [role_report(r) for r in COUNCIL],
    "analyst": ANALYST,
    "ledger": [{"option": "A", "kind": "pro", "point": "SQL joins", "claim": "SQL joins for finance", "severity": 4,
                "likelihood": 5, "raised_by": ["analyst", "executor"]}],
    "scores": ANALYST["scores"],
    "dissent": {"role": "executor", "position": "DynamoDB ships faster",
                "why_rejected": "reporting cost dominates"},
    "blind_spots": ["Nobody priced the reporting replica"],
    "drift": "No change: the council agreed with the first view",
    "view_changed": False,
    "verdict": {"decision": "A", "summary": "Postgres fits the reporting needs", "conditions": []},
    "first_step": "Prototype the finance report query on RDS",
    "confidence": "medium",
    "confidence_why": "Peak traffic growth is still a guess",
    "unknowns": ["Peak traffic growth"],
}


def write_run(path):
    path = Path(path)
    (path / "reports").mkdir(parents=True, exist_ok=True)
    (path / "brief.json").write_text(json.dumps(BRIEF), encoding="utf-8")
    for r in COUNCIL:
        (path / "reports" / f"{r}.raw.txt").write_text(json.dumps(role_report(r)), encoding="utf-8")
    (path / "reports" / "analyst.raw.txt").write_text(
        "Here you go:\n```json\n" + json.dumps(ANALYST) + "\n```", encoding="utf-8")
    (path / "result.json").write_text(json.dumps(RESULT), encoding="utf-8")
    return path
