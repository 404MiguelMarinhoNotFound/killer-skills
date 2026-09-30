import json

import render
import sample_run

TINY = "<script id='data' type='application/json'>__RESULT_JSON__</script>"


def test_embedded_script_close_is_neutralized_and_round_trips():
    evil = "x</script><script>alert(1)</script><!--"
    html = render.render_html({"title": evil}, TINY)
    assert "</script><script>alert" not in html
    payload = html.split(">", 1)[1].rsplit("</script>", 1)[0]
    assert json.loads(payload)["title"] == evil


def test_template_contains_token_and_no_external_urls():
    text = render.TEMPLATE.read_text(encoding="utf-8")
    assert render.TOKEN in text
    assert "http://" not in text and "https://" not in text


def test_terminal_summary():
    out = render.terminal_summary(sample_run.RESULT)
    assert "Verdict: Postgres" in out
    assert "Postgres: 4.20 / 5" in out
    assert "DynamoDB: 3.20 / 5" in out
    assert "stable" in out
    assert "First step: Prototype the finance report query on RDS" in out


def test_main_writes_report(run_dir, capsys):
    render.main(run_dir)
    html = (run_dir / "report.html").read_text(encoding="utf-8")
    assert "Postgres vs DynamoDB for orders" in html
    assert "Report:" in capsys.readouterr().out


def test_main_refuses_an_invalid_result(run_dir, capsys):
    import pytest
    (run_dir / "result.json").write_text(json.dumps(dict(sample_run.RESULT, scores=[])), encoding="utf-8")
    with pytest.raises(SystemExit):
        render.main(run_dir)
    assert "exactly one score" in capsys.readouterr().out
    assert not (run_dir / "report.html").exists()


def test_main_embeds_role_summaries_without_touching_result_json(run_dir):
    before = (run_dir / "result.json").read_text(encoding="utf-8")
    render.main(run_dir)
    html = (run_dir / "report.html").read_text(encoding="utf-8")
    assert '"role_catalog"' in html and "The Contrarian" in html
    assert (run_dir / "result.json").read_text(encoding="utf-8") == before
