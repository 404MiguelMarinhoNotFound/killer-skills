import copy

import clarity
import sample_run

OPTS = {"A": "Postgres", "B": "DynamoDB"}


def issues(text, **kw):
    return clarity.check_text(text, OPTS, **kw)


def test_plain_sentences_pass():
    assert issues("Use Postgres. Finance can run new reports on the same data without a second system.") == []


def test_long_sentences_are_flagged():
    long = " ".join(["word"] * 36) + "."
    assert any("words" in i for i in issues(long))


def test_packed_sentences_are_flagged():
    packed = "Adds a dependency to the skill; not installed here; a missing import stops every run."
    assert any("several ideas" in i for i in issues(packed))


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
