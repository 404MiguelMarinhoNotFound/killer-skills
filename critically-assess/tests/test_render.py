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


# --- opening the report in the default browser ---------------------------------------

class _Launcher:
    def __init__(self):
        self.calls = []

    def __call__(self, cmd, **kwargs):
        self.calls.append(cmd)


def _clear_env(monkeypatch):
    for var in ("CRITICALLY_ASSESS_NO_OPEN", "CI", "DISPLAY", "WAYLAND_DISPLAY", "SSH_CONNECTION"):
        monkeypatch.delenv(var, raising=False)


def test_open_is_skipped_when_disabled(monkeypatch, tmp_path):
    launcher = _Launcher()
    monkeypatch.setattr(render.subprocess, "Popen", launcher)
    assert render.open_in_browser(tmp_path / "report.html") is False
    assert launcher.calls == []


def test_open_uses_the_platform_opener(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    launcher = _Launcher()
    monkeypatch.setattr(render.subprocess, "Popen", launcher)
    monkeypatch.setattr(render.sys, "platform", "darwin")
    assert render.open_in_browser(tmp_path / "report.html") is True
    assert launcher.calls[-1][0] == "open"
    monkeypatch.setattr(render.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/" + name if name == "xdg-open" else None)
    assert render.open_in_browser(tmp_path / "report.html") is True
    assert launcher.calls[-1][0] == "xdg-open"


def test_open_is_skipped_on_headless_linux_and_ci(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    launcher = _Launcher()
    monkeypatch.setattr(render.subprocess, "Popen", launcher)
    monkeypatch.setattr(render.sys, "platform", "linux")
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/" + name)
    assert render.open_in_browser(tmp_path / "report.html") is False  # no display
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("CI", "true")
    assert render.open_in_browser(tmp_path / "report.html") is False  # CI
    assert launcher.calls == []


def test_main_prints_a_link_when_it_cannot_open(run_dir, capsys):
    render.main(run_dir)
    out = capsys.readouterr().out
    assert "file://" in out and "Open it in a browser" in out
