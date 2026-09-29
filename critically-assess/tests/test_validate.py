import copy
import json

import pytest

import sample_run
import validate

OPTS = ["A", "B"]
CRITS = ["fit", "ops"]


def test_extract_json_handles_fences_and_prose():
    assert validate.extract_json('Sure!\n```json\n{"a": 1}\n```\nDone.') == {"a": 1}
    assert validate.extract_json('noise {"a": {"b": 2}} noise') == {"a": {"b": 2}}


def test_extract_json_raises_when_no_object():
    with pytest.raises(ValueError):
        validate.extract_json("Sorry, I can't help with that.")


def test_sample_run_parts_are_valid():
    assert validate.validate_brief(sample_run.BRIEF) == []
    assert validate.validate_role_report(sample_run.role_report("contrarian"), OPTS) == []
    assert validate.validate_analyst_report(sample_run.ANALYST, OPTS, CRITS) == []
    assert validate.validate_result(sample_run.RESULT) == []


def test_single_mode_requires_idea_plus_status_quo():
    brief = copy.deepcopy(sample_run.BRIEF)
    brief["mode"] = "single"
    brief["options"] = brief["options"][:1]
    assert any("exactly 2 options" in e for e in validate.validate_brief(brief))


def test_non_positive_weight_rejected():
    brief = copy.deepcopy(sample_run.BRIEF)
    brief["criteria"][0]["weight"] = 0
    assert any("weight" in e for e in validate.validate_brief(brief))


def test_role_report_must_cover_every_option():
    report = sample_run.role_report("contrarian")
    report["per_option"] = report["per_option"][:1]
    assert any("per_option" in e for e in validate.validate_role_report(report, OPTS))


def test_analyst_needs_two_pros_two_cons_and_full_grid():
    analyst = copy.deepcopy(sample_run.ANALYST)
    analyst["ledger"] = [i for i in analyst["ledger"] if not (i["option"] == "B" and i["kind"] == "con")]
    analyst["scores"] = analyst["scores"][:3]
    errors = validate.validate_analyst_report(analyst, OPTS, CRITS)
    assert any("2 cons" in e for e in errors)
    assert any("option B x criterion ops" in e for e in errors)


def test_result_multi_decision_must_be_option_or_hybrid():
    result = copy.deepcopy(sample_run.RESULT)
    result["verdict"]["decision"] = "go"
    assert any("decision" in e for e in validate.validate_result(result))


def test_conditional_go_needs_conditions():
    result = copy.deepcopy(sample_run.RESULT)
    result["brief"]["mode"] = "single"
    result["verdict"] = {"decision": "conditional-go", "summary": "s", "conditions": []}
    assert any("conditions" in e for e in validate.validate_result(result))


def test_roster_needs_analyst_and_three_to_five_council_roles():
    result = copy.deepcopy(sample_run.RESULT)
    result["roster"] = [{"role": "contrarian", "model": "opus", "why": "x"}]
    errors = validate.validate_result(result)
    assert any("analyst" in e for e in errors)
    assert any("3-5 council roles" in e for e in errors)


def test_validate_run_normalizes_raw_replies(run_dir):
    assert validate.validate_run(run_dir) == []
    saved = json.loads((run_dir / "reports" / "analyst.json").read_text(encoding="utf-8"))
    assert saved["role"] == "analyst"


def test_validate_run_reports_unparseable_reply_per_role(run_dir):
    (run_dir / "reports" / "executor.raw.txt").write_text("Sorry, I can't.", encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert any(e.startswith("executor:") and "not valid JSON" in e for e in errors)
