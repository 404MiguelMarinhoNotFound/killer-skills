import pytest

import sample_run


@pytest.fixture(autouse=True)
def _never_open_a_browser(monkeypatch):
    # Tests must never launch a real browser, whatever machine they run on.
    monkeypatch.setenv("CRITICALLY_ASSESS_NO_OPEN", "1")


@pytest.fixture
def run_dir(tmp_path):
    return sample_run.write_run(tmp_path)
