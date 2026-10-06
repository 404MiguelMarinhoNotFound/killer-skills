import copy
import json

import pytest

import sample_run
import validate

OPTS = ["A", "B"]


def reopen_council(run_dir):
    """Step back to before the synthesis and the unsealing, when replies may still be written."""
    for name in ("result.json", "precommit.json"):
        (run_dir / name).unlink(missing_ok=True)
CRITS = ["fit", "ops"]


def test_reply_file_must_be_exactly_one_json_object(tmp_path):
    f = tmp_path / "x.reply.json"
    f.write_text('  {"a": 1}\n', encoding="utf-8")
    assert validate.read_reply(f) == {"a": 1}
    for bad in ('Sure!\n```json\n{"a": 1}\n```', '```json\n{"a": 1}\n```', '{"a": 1}\nDone.', '[1, 2]'):
        f.write_text(bad, encoding="utf-8")
        with pytest.raises(ValueError):
            validate.read_reply(f)


def test_read_reply_raises_when_no_object(tmp_path):
    with pytest.raises(ValueError):
        f = tmp_path / "x.reply.json"
        f.write_text("Sorry, I can't help with that.", encoding="utf-8")
        validate.read_reply(f)


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


def test_validate_run_reads_reply_files_and_leaves_them_untouched(run_dir):
    before = (run_dir / "reports" / "analyst.reply.json").read_text(encoding="utf-8")
    assert validate.validate_run(run_dir) == []
    saved = json.loads((run_dir / "reports" / "analyst.json").read_text(encoding="utf-8"))
    assert saved["role"] == "analyst"
    assert (run_dir / "reports" / "analyst.reply.json").read_text(encoding="utf-8") == before


def test_validate_run_reports_unparseable_reply_per_role(run_dir):
    (run_dir / "reports" / "executor.reply.json").write_text("Sorry, I can't.", encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert any(e.startswith("executor:") and "not a single JSON object" in e for e in errors)


def test_validate_run_uses_filename_as_role_id(run_dir):
    reopen_council(run_dir)
    renamed = sample_run.role_report("contrarian")
    renamed["role"] = "red-team"
    (run_dir / "reports" / "contrarian.reply.json").write_text(json.dumps(renamed), encoding="utf-8")
    analyst = dict(sample_run.ANALYST, role="neutral analyst")
    (run_dir / "reports" / "analyst.reply.json").write_text(json.dumps(analyst), encoding="utf-8")
    assert validate.validate_run(run_dir) == []
    saved = json.loads((run_dir / "reports" / "contrarian.json").read_text(encoding="utf-8"))
    assert saved["role"] == "contrarian"


def test_validate_run_reports_missing_brief_without_crashing(run_dir):
    (run_dir / "brief.json").unlink()
    assert any("brief.json" in e for e in validate.validate_run(run_dir))


# --- Review Focus 1: odd replies become per-role errors, never a crash -------------------

def test_a_reply_file_with_prose_around_the_json_is_rejected_and_names_the_fix(run_dir):
    (run_dir / "reports" / "executor.reply.json").write_text(
        "Here you go:\n" + json.dumps(sample_run.role_report("executor")), encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert any(e.startswith("executor:") and "only the JSON object" in e for e in errors)


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
    (run_dir / "reports" / "contrarian.reply.json").write_text('{"role": "x", "per_option": 7}', encoding="utf-8")
    (run_dir / "result.json").write_text("{broken", encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert any(e.startswith("contrarian:") for e in errors)
    assert any("result.json is not valid JSON" in e for e in errors)
    (run_dir / "brief.json").write_text("{broken", encoding="utf-8")
    assert any("brief.json is not valid JSON" in e for e in validate.validate_run(run_dir))


def test_stale_json_is_removed_when_a_later_reply_fails(run_dir):
    assert validate.validate_run(run_dir) == []
    (run_dir / "reports" / "analyst.reply.json").write_text("I refuse.", encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert not (run_dir / "reports" / "analyst.json").exists()
    assert [e for e in errors if e.startswith("analyst:")] == [e for e in errors if "not a single JSON object" in e]


def test_dropped_roles_moved_to_subfolder_are_ignored(run_dir):
    (run_dir / "reports" / "executor.reply.json").write_text("Sorry, I can't.", encoding="utf-8")
    dropped = run_dir / "reports" / "dropped"
    dropped.mkdir()
    (run_dir / "reports" / "executor.reply.json").rename(dropped / "executor.reply.json")
    reopen_council(run_dir)  # replies are written before the council closes
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
    lambda r: r["ledger"][0].pop("point"),
    lambda r: r["reports"][0].update(pick="Z"),
    lambda r: r.update(view_changed="no"),
    lambda r: r.pop("confidence_why"),
    lambda r: r.update(unknowns=None),
])
def test_result_fields_the_report_reads_are_required(mutate):
    assert _result_with(mutate)


# --- evidence tags and the research setting -------------------------------------------

def test_role_evidence_must_carry_a_known_tag():
    report = sample_run.role_report("contrarian")
    report["evidence"] = ["Finance needs joins"]
    assert any("evidence" in e and "Brief:" in e for e in validate.validate_role_report(report, OPTS))
    for tag in ("Brief:", "Source:", "Mechanism:", "Knowledge:"):
        report["evidence"] = [f"{tag} something concrete"]
        assert validate.validate_role_report(report, OPTS) == []


def test_analyst_evidence_must_carry_a_known_tag():
    analyst = copy.deepcopy(sample_run.ANALYST)
    analyst["ledger"][0]["evidence"] = "trust me"
    assert any("evidence tag" in e for e in validate.validate_analyst_report(analyst, OPTS, CRITS))
    analyst["ledger"][0]["evidence"] = "Supervisor: written by the supervisor"
    assert validate.validate_analyst_report(analyst, OPTS, CRITS) == []


def test_brief_research_setting_is_optional_but_checked():
    brief = copy.deepcopy(sample_run.BRIEF)
    brief.pop("research")
    assert validate.validate_brief(brief) == []
    brief["research"] = "everything"
    assert any("research" in e for e in validate.validate_brief(brief))



def test_role_pick_and_point_are_required():
    report = sample_run.role_report("contrarian")
    report["pick"] = "D"
    assert any("pick" in e for e in validate.validate_role_report(report, OPTS))
    report["pick"] = "B"
    report["point"] = " "
    assert any("point" in e for e in validate.validate_role_report(report, OPTS))
    report.pop("pick")
    assert any("missing 'pick'" in e for e in validate.validate_role_report(report, OPTS))


# --- supervisor patches for a missing pick or point -----------------------------------

def _without(run_dir, role, *keys):
    report = sample_run.role_report(role)
    for k in keys:
        report.pop(k)
    (run_dir / "reports" / f"{role}.reply.json").write_text(json.dumps(report), encoding="utf-8")


def test_patch_fills_a_missing_pick_and_point(run_dir):
    reopen_council(run_dir)  # replies are written before the council closes
    _without(run_dir, "contrarian", "pick", "point")
    assert any("missing 'pick'" in e for e in validate.validate_run(run_dir))
    (run_dir / "reports" / "contrarian.patch.json").write_text(
        json.dumps({"pick": "B", "point": "DynamoDB: fewer servers to run."}), encoding="utf-8")
    assert validate.validate_run(run_dir) == []
    filled = json.loads((run_dir / "reports" / "contrarian.json").read_text(encoding="utf-8"))
    assert filled["pick"] == "B" and filled["filled_by_supervisor"] == ["pick", "point"]


def test_patch_never_replaces_the_council_s_own_words(run_dir):
    (run_dir / "reports" / "contrarian.patch.json").write_text(json.dumps({"pick": "B"}), encoding="utf-8")
    assert any("already has a usable 'pick'" in e for e in validate.validate_run(run_dir))
    (run_dir / "reports" / "contrarian.patch.json").write_text(json.dumps({"position": "x"}), encoding="utf-8")
    assert any("may only fill" in e for e in validate.validate_run(run_dir))


def test_patch_file_is_not_read_as_a_role_report(run_dir):
    reopen_council(run_dir)  # replies are written before the council closes
    _without(run_dir, "contrarian", "point")
    (run_dir / "reports" / "contrarian.patch.json").write_text(json.dumps({"point": "x"}), encoding="utf-8")
    assert validate.validate_run(run_dir) == []


def test_a_reply_cannot_claim_to_be_filled_by_the_supervisor(run_dir):
    report = dict(sample_run.role_report("contrarian"), filled_by_supervisor=["pick"])
    (run_dir / "reports" / "contrarian.reply.json").write_text(json.dumps(report), encoding="utf-8")
    validate.validate_run(run_dir)
    assert "filled_by_supervisor" not in json.loads((run_dir / "reports" / "contrarian.json").read_text(encoding="utf-8"))


# --- The synthesis may weigh the council but never rewrite it --------------------------------

def _result_errors(run_dir, mutate):
    result = copy.deepcopy(sample_run.RESULT)
    result["scores"] = copy.deepcopy(result["scores"])  # unshare from the analyst's scores
    mutate(result)
    (run_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
    return validate.validate_run(run_dir)


@pytest.mark.parametrize("mutate, expected", [
    (lambda r: r["ledger"][0].update(raised_by=["ghost"]), "raised_by names roles not in the roster"),
    (lambda r: r["dissent"].update(role="ghost"), "dissent.role must be a role in the roster"),
    (lambda r: r["reports"].pop(), "one report per council role"),
    (lambda r: r["roster"].append({"role": "executor", "model": "opus", "why": "x"}), "more than once"),
    (lambda r: r.update(analyst={}), "result.analyst: ledger must be a list"),
])
def test_result_roles_must_agree_with_the_roster(run_dir, mutate, expected):
    assert any(expected in e for e in _result_errors(run_dir, mutate))


def test_result_must_carry_the_brief_the_council_answered(run_dir):
    errors = _result_errors(run_dir, lambda r: r["brief"]["criteria"][1].update(weight=5))
    assert any("brief must be brief.json exactly" in e for e in errors)


@pytest.mark.parametrize("mutate, role", [
    (lambda r: r["reports"][0].update(position="Now agrees with the lead reviewer"), "contrarian"),
    (lambda r: r["analyst"]["ledger"][0].update(claim="A rewritten claim"), "analyst"),
])
def test_result_must_copy_reports_unchanged(run_dir, mutate, role):
    errors = _result_errors(run_dir, mutate)
    assert any(f"the {role} report must be copied unchanged" in e for e in errors)


def test_a_changed_score_must_say_the_supervisor_changed_it(run_dir):
    errors = _result_errors(run_dir, lambda r: r["scores"][2].update(score=4))
    assert any("differs from the analyst's 2" in e for e in errors)
    errors = _result_errors(run_dir, lambda r: r["scores"][2].update(
        score=4, rationale="Supervisor: the reporting replica covers most joins"))
    assert errors == []


# --- The sealed view: fixed before the council, unchanged after --------------------------------

def test_view_must_be_sealed_before_any_reply(run_dir):
    (run_dir / "precommit.sha256").unlink()
    assert any("seal your view" in e for e in validate.validate_run(run_dir))
    reply = run_dir / "reports" / "contrarian.reply.json"
    validate.seal(run_dir / "precommit.json", run_dir)
    import os
    os.utime(reply, ns=(1, 1))  # a reply written long before the seal
    assert any("newer than a council reply" in e for e in validate.validate_run(run_dir))


def test_view_cannot_change_after_sealing(run_dir):
    pre = dict(sample_run.RESULT["precommit"], position="Whatever the council said")
    (run_dir / "precommit.json").write_text(json.dumps(pre), encoding="utf-8")
    assert any("differs from the view sealed" in e for e in validate.validate_run(run_dir))


def test_result_precommit_must_be_the_sealed_one(run_dir):
    errors = _result_errors(run_dir, lambda r: r["precommit"].update(main_risk="Something else"))
    assert any("precommit must be precommit.json exactly" in e for e in errors)


def test_a_changed_pick_needs_view_changed(run_dir):
    def flip(r):
        r["verdict"]["decision"] = "B"
    errors = _result_errors(run_dir, flip)
    assert any("view_changed is false" in e for e in errors)


# --- The roster is fixed before launch -----------------------------------------------------------

def test_a_role_leaves_the_council_only_by_being_dropped(run_dir):
    roster = sample_run.RESULT["roster"] + [{"role": "outsider", "model": "sonnet", "why": "x"}]
    (run_dir / "roster.json").write_text(json.dumps(roster), encoding="utf-8")
    errors = validate.validate_run(run_dir)
    assert any("roster must be roster.json minus" in e for e in errors)
    dropped = run_dir / "reports" / "dropped"
    dropped.mkdir()
    (dropped / "outsider.reply.json").write_text("Sorry", encoding="utf-8")
    assert validate.validate_run(run_dir) == []


# --- Source: evidence must point at something the role could open ------------------------------

def _with_evidence(run_dir, research, evidence, in_workdir=True):
    brief = dict(sample_run.BRIEF, research=research)
    (run_dir / "brief.json").write_text(json.dumps(brief), encoding="utf-8")
    reopen_council(run_dir)  # replies are written before the council closes
    report = dict(sample_run.role_report("contrarian"), evidence=[evidence])
    (run_dir / "reports" / "contrarian.reply.json").write_text(json.dumps(report), encoding="utf-8")
    return validate.validate_run(run_dir)


@pytest.fixture
def nested_run(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "queue.py").write_text("x", encoding="utf-8")
    return sample_run.write_run(tmp_path / ".critically-assess" / "runs" / "20260101-000000-db")


@pytest.mark.parametrize("research, evidence, ok", [
    ("none", "Source: https://example.com shows x", False),
    ("online", "Source: the docs say so", False),
    ("online", "Source: https://example.com/limits shows a 1 MB cap", True),
    ("repo", "Source: src/queue.py retries forever", True),
    ("repo", "Source: src/missing.py retries forever", False),
    ("repo", "Source: ../outside.py shows x", False),
    ("both", "Source: `src/queue.py:12` retries forever", True),
    ("both", "Source: I read it somewhere", False),
])
def test_source_items_point_at_what_the_role_could_open(nested_run, research, evidence, ok):
    errors = _with_evidence(nested_run, research, evidence)
    assert (not any(e.startswith("contrarian") and "Source:" in e for e in errors)) == ok, errors


# --- Coherence warnings never fail the run ----------------------------------------------------

def test_pick_that_the_point_does_not_name_is_warned(run_dir):
    reopen_council(run_dir)  # replies are written before the council closes
    report = dict(sample_run.role_report("contrarian"), pick="A", point="DynamoDB: fewer servers to run.")
    (run_dir / "reports" / "contrarian.reply.json").write_text(json.dumps(report), encoding="utf-8")
    warnings = []
    assert validate.validate_run(run_dir, warnings) == []
    assert any("picked Postgres" in w and "point names DynamoDB instead" in w for w in warnings)


def test_verdict_against_the_scores_and_agreeing_dissent_are_warned(run_dir):
    warnings = []
    assert validate.validate_run(run_dir, warnings) == []
    assert any("who picked the option you recommend" in w for w in warnings)  # the sample dissent picked A
    def against(r):
        r["verdict"]["decision"] = "B"
        r["view_changed"] = True
    result = copy.deepcopy(sample_run.RESULT); against(result)
    (run_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
    warnings = []
    assert validate.validate_run(run_dir, warnings) == []
    assert any("weighted scores rank Postgres first" in w for w in warnings)


def test_supervisor_written_analyst_must_say_so_everywhere(run_dir):
    def mark(r):
        r["roster"][-1]["model"] = "supervisor"
    assert any("must start with 'Supervisor:'" in e for e in _result_errors(run_dir, mark))


def test_analyst_cannot_be_patched(run_dir):
    (run_dir / "reports" / "analyst.patch.json").write_text(json.dumps({"point": "x"}), encoding="utf-8")
    assert any("analyst cannot be patched" in e for e in validate.validate_run(run_dir))


def test_unseal_refuses_while_a_reply_has_errors_and_closes_the_council(run_dir, tmp_path):
    import os
    (run_dir / "result.json").unlink()
    sealed_dir = tmp_path / "sealed"; sealed_dir.mkdir()
    sealed = sealed_dir / "view.json"
    (run_dir / "precommit.json").rename(sealed)
    (run_dir / "reports" / "executor.reply.json").write_text("oops", encoding="utf-8")
    errors = validate.unseal(sealed, run_dir)
    assert any("stays sealed" in e for e in errors) and sealed.exists()
    (run_dir / "reports" / "executor.reply.json").write_text(
        json.dumps(sample_run.role_report("executor")), encoding="utf-8")
    for reply in (run_dir / "reports").glob("*.reply.json"):
        os.utime(reply, ns=(reply.stat().st_mtime_ns, (run_dir / "precommit.sha256").stat().st_mtime_ns))
    assert validate.unseal(sealed, run_dir) == []
    assert not sealed.exists() and (run_dir / "precommit.json").exists()
    late = run_dir / "reports" / "executor.reply.json"
    os.utime(late, ns=(late.stat().st_atime_ns, (run_dir / "precommit.json").stat().st_mtime_ns + 10**9))
    assert any("written after the view was unsealed" in e for e in validate.validate_run(run_dir))


def test_a_summary_that_does_not_name_the_choice_is_warned(run_dir):
    result = copy.deepcopy(sample_run.RESULT)
    result["verdict"]["summary"] = "The relational option fits the reporting needs"
    (run_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
    warnings = []
    assert validate.validate_run(run_dir, warnings) == []
    assert any("verdict.summary does not name it" in w for w in warnings)
