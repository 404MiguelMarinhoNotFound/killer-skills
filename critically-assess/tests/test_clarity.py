import copy

import clarity
import sample_run

OPTS = {"A": "Postgres", "B": "DynamoDB"}


def issues(text, **kw):
    return clarity.check_text(text, OPTS, **kw)


def test_plain_sentences_pass():
    assert issues("Use Postgres. Finance can run new reports on the same data without a second system.") == []


def test_long_sentences_are_not_capped():
    # A big idea needs the words it takes; length alone is never a problem.
    long = ("Moving to the managed service means nobody on the team has to patch or restart database servers any more, "
            "which frees roughly a day a month for the two engineers who carry the pager at night today.")
    assert len(long.split()) > 35 and issues(long) == []


def test_note_style_is_flagged():
    for text in ("Adds a dependency to the skill; not installed here; a missing import stops every run.",
                 "Broker -> extra runtime to run and patch.",
                 "Works w/ the current schema.",
                 "Lower ops burden vs. the incumbent; migration risk: real."):
        assert any("reads like notes" in i for i in issues(text)), text


def test_items_that_lean_on_unseen_text_are_flagged():
    for text in ("It adds a second failure point.", "This cuts both ways.", "They would need retraining.",
                 "Same cost story, but worse at scale.", "As noted above, Postgres is cheaper."):
        assert any("leans on text" in i for i in issues(text)), text
    assert issues("Postgres adds no second system to run. It stays one database.") == []
    assert issues("Itemised billing makes DynamoDB costs easy to trace.") == []


def test_option_letters_are_flagged_but_the_article_a_is_not():
    for text in ("Favour A because it is simpler.", "B's reporting path is slow.", "Pick option B.", "A and B both work.", "Choose A (Postgres)."):
        assert any("option letter" in i for i in issues(text)), text
    assert issues("A hybrid would create two code paths.") == []
    assert issues("A small team can run it.") == []


def test_internal_terms_are_flagged():
    for text in ("My sealed pre-commitment was Postgres.", "The brief says nothing about volume.",
                 "All four council voices agreed.", "Every run stops at step 7."):
        assert any("internal term" in i for i in issues(text)), text


def test_unexplained_acronyms_are_flagged_unless_common_known_or_defined():
    assert any("PITR" in i for i in issues("Enable PITR before launch."))
    assert issues("The API returns JSON over HTTP.") == []
    assert issues("Enable PITR before launch.", known={"PITR"}) == []
    assert issues("Turn on point-in-time recovery (PITR) and test PITR restores.") == []


def test_check_result_passes_the_sample_and_names_the_field():
    assert clarity.check_result(sample_run.RESULT) == []
    result = copy.deepcopy(sample_run.RESULT)
    result["verdict"]["summary"] = "Favour A; B is slower; the brief is thin."
    found = clarity.check_result(result)
    assert found and all(f.startswith("verdict.summary") for f in found)


def test_terms_the_user_used_are_allowed():
    result = copy.deepcopy(sample_run.RESULT)
    result["brief"]["question"] = "Postgres or DynamoDB with PITR for the order service?"
    result["first_step"] = "Enable PITR on the RDS instance."
    assert clarity.check_result(result) == []


def test_council_reports_are_checked_as_warnings():
    report = sample_run.role_report("contrarian")
    report["position"] = "Favour A; B needs a pipeline; the brief is silent."
    warnings = clarity.check_reports([report], sample_run.BRIEF)
    assert warnings and warnings[0].startswith("contrarian.position")


def test_council_evidence_is_checked_without_its_tag_or_url():
    report = sample_run.role_report("contrarian")
    report["evidence"] = ["Source: https://example.com/README.md shows the retry path -> double writes."]
    warnings = clarity.check_reports([report], sample_run.BRIEF)
    assert any(w.startswith("contrarian.evidence[0]") and "notes" in w for w in warnings)
    assert not any("README" in w for w in warnings)
