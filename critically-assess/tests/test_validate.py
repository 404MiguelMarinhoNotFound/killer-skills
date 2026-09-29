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
    result["brief"]["options"][1]["name"] = "Status quo"
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


def test_validate_run_uses_filename_as_role_id(run_dir):
    renamed = sample_run.role_report("contrarian")
    renamed["role"] = "red-team"
    (run_dir / "reports" / "contrarian.raw.txt").write_text(json.dumps(renamed), encoding="utf-8")
    analyst = dict(sample_run.ANALYST, role="neutral analyst")
    (run_dir / "reports" / "analyst.raw.txt").write_text(json.dumps(analyst), encoding="utf-8")
    assert validate.validate_run(run_dir) == []
    saved = json.loads((run_dir / "reports" / "contrarian.json").read_text(encoding="utf-8"))
    assert saved["role"] == "contrarian"


def test_validate_run_reports_missing_brief_without_crashing(run_dir):
    (run_dir / "brief.json").unlink()
    assert any("brief.json" in e for e in validate.validate_run(run_dir))


# --- Review Focus 1: odd replies become per-role errors, never a crash -------------------

def test_extract_json_survives_two_fences_and_braces_in_prose():
    text = 'Draft:\n```json\n{"a": 1}\n```\nNotes {not json}\n```json\n{"b": 2}\n```'
    assert validate.extract_json(text) == {"a": 1}
    assert validate.extract_json('```json\n{"a": 1}\n```\nSee {x} above.') == {"a": 1}


@pytest.mark.parametrize("field,value", [
    ("per_option", ["A", "B"]), ("per_option", None), ("reasoning", 5), ("reasoning", "abc"),
    ("evidence", "one string"), ("per_option", [{"option": "A", "pros": "p"}, {"option": "B"}]),
])
def test_wrong_typed_role_fields_are_errors_not_crashes(field, value):
    report = sample_run.role_report("contrarian")
    report[field] = value
    errors = validate.validate_role_report(report, OPTS)
    assert errors and all(e.startswith("contrarian:") for e in errors)


@pytest.mark.parametrize("field,value", [
    ("ledger", ["x"]), ("ledger", None), ("scores", {"a": 1}),
    ("scores", [{"option": ["A"], "criterion": "fit", "score": 3}]),
])
def test_wrong_typed_analyst_fields_are_errors_not_crashes(field, value):
    analyst = copy.deepcopy(sample_run.ANALYST)
    analyst[field] = value
    assert validate.validate_analyst_report(analyst, OPTS, CRITS)


@pytest.mark.parametrize("brief", [
    {"mode": "multi", "question": "q", "options": ["A", "B"], "criteria": [{"id": "c", "weight": 1}]},
    {"mode": "multi", "question": "q", "options": [{"id": None}, {"id": 2}], "criteria": "x"},
    ["not", "an", "object"],
])
def test_malformed_briefs_are_errors_not_crashes(brief):
    assert validate.validate_brief(brief)


def test_corrupt_files_in_run_dir_are_errors_not_crashes(run_dir):
    (run_dir / "reports" / "contrarian.raw.txt").write_text('{"role": "x", "per_option": 7}', encoding="utf-8")
    (run_dir / "result.json").write_text("{broken", encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert any(e.startswith("contrarian:") for e in errors)
    assert any("result.json is not valid JSON" in e for e in errors)
    (run_dir / "brief.json").write_text("{broken", encoding="utf-8")
    assert any("brief.json is not valid JSON" in e for e in validate.validate_run(run_dir))


def test_stale_json_is_removed_when_a_later_reply_fails(run_dir):
    assert validate.validate_run(run_dir) == []
    (run_dir / "reports" / "analyst.raw.txt").write_text("I refuse.", encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert not (run_dir / "reports" / "analyst.json").exists()
    assert [e for e in errors if e.startswith("analyst:")] == [e for e in errors if "not valid JSON" in e]


def test_dropped_roles_moved_to_subfolder_are_ignored(run_dir):
    (run_dir / "reports" / "executor.raw.txt").write_text("Sorry, I can't.", encoding="utf-8")
    dropped = run_dir / "reports" / "dropped"
    dropped.mkdir()
    (run_dir / "reports" / "executor.raw.txt").rename(dropped / "executor.raw.txt")
    assert validate.validate_run(run_dir) == []


# --- Review Focus 2: single mode is the idea vs "Status quo" -----------------------------

def test_single_mode_option_b_must_be_status_quo():
    brief = copy.deepcopy(sample_run.BRIEF)
    brief["mode"] = "single"
    assert any("Status quo" in e for e in validate.validate_brief(brief))
    brief["options"][1] = {"id": "B", "name": "Status quo", "description": "Keep today's setup"}
    assert validate.validate_brief(brief) == []


# --- result.json must guarantee everything render.py and report.html read ----------------

def _result_with(mutate):
    result = copy.deepcopy(sample_run.RESULT)
    mutate(result)
    return validate.validate_result(result)


def test_result_scores_need_the_full_known_grid():
    assert any("exactly one score" in e for e in _result_with(lambda r: r.update(scores=[])))
    assert any("exactly one score for option B x criterion ops" in e
               for e in _result_with(lambda r: r.update(scores=r["scores"][:3])))
    assert any("unknown option/criterion" in e for e in _result_with(
        lambda r: r["scores"].append({"option": "A", "criterion": "zzz", "score": 3})))


def test_result_brief_is_validated():
    assert any("result.brief" in e for e in _result_with(lambda r: r["brief"]["criteria"][0].update(weight=0)))
    assert any("result.brief" in e for e in _result_with(lambda r: r["brief"]["options"][0].pop("name")))


@pytest.mark.parametrize("mutate", [
    lambda r: r["verdict"].pop("summary"),
    lambda r: r.update(verdict="A"),
    lambda r: r["dissent"].pop("why_rejected"),
    lambda r: r.update(first_step=""),
    lambda r: r.update(roster="analyst"),
    lambda r: r["ledger"][0].update(raised_by="analyst"),
    lambda r: r["ledger"][0].update(severity="high"),
    lambda r: r["reports"][0].update(reasoning="abc"),
    lambda r: r.update(unknowns=None),
])
def test_result_fields_the_report_reads_are_required(mutate):
    assert _result_with(mutate)
