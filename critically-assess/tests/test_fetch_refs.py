import subprocess


def test_fetch_refs_lists_six_raw_github_sources():
    out = subprocess.run(
        ["bash", "scripts/fetch_refs.sh", "--list"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert len(out) == 6
    assert all(u.startswith("https://raw.githubusercontent.com/") for u in out)
