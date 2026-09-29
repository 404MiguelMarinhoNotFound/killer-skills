import pytest

import sample_run


@pytest.fixture
def run_dir(tmp_path):
    return sample_run.write_run(tmp_path)
