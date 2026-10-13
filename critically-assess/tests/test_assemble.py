import json

import assemble
import render
import sample_run
import validate


def _synthesis(tmp_path, **changes):
    data = {k: v for k, v in sample_run.RESULT.items() if k not in assemble.COPIED}
    data.update(changes)
    path = tmp_path / "synthesis.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_assembled_result_equals_the_hand_built_one(run_dir, tmp_path):
    (run_dir / "result.json").unlink()
    assert validate.validate_run(run_dir) == []  # writes the checked copies
    assert assemble.assemble(run_dir, _synthesis(tmp_path)) == []
    built = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert built == sample_run.RESULT
    assert validate.validate_run(run_dir) == []


def test_scores_default_to_the_analysts(run_dir, tmp_path):
    (run_dir / "result.json").unlink()
    validate.validate_run(run_dir)
    synthesis = json.loads(_synthesis(tmp_path).read_text())
    synthesis.pop("scores")
    (tmp_path / "s.json").write_text(json.dumps(synthesis))
    assert assemble.assemble(run_dir, tmp_path / "s.json") == []
    assert json.loads((run_dir / "result.json").read_text())["scores"] == sample_run.ANALYST["scores"]


def test_synthesis_may_not_carry_the_copied_parts(run_dir, tmp_path):
    path = _synthesis(tmp_path, brief={"mode": "multi"})
    assert any("leave ['brief']" in e for e in assemble.assemble(run_dir, path))


def test_synthesis_must_hold_every_judgement_field(run_dir, tmp_path):
    synthesis = json.loads(_synthesis(tmp_path).read_text())
    synthesis.pop("dissent")
    (tmp_path / "s.json").write_text(json.dumps(synthesis))
    assert any("missing ['dissent']" in e for e in assemble.assemble(run_dir, tmp_path / "s.json"))


def test_assembly_needs_a_closed_council(run_dir, tmp_path):
    (run_dir / "precommit.json").unlink()
    assert any("--unseal" in e for e in assemble.assemble(run_dir, _synthesis(tmp_path)))


def test_terminal_summary_does_not_double_the_if():
    result = json.loads(json.dumps(sample_run.RESULT))
    result["verdict"]["conditions"] = ["If the load test passes, go ahead."]
    out = render.terminal_summary(result)
    assert "if: If" not in out and "condition: If the load test passes" in out
