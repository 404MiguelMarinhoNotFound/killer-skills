from pathlib import Path

import role_library

ROLES_DIR = Path(__file__).resolve().parent.parent / "roles"


def test_v1_library_has_expected_roles():
    ids = {r["id"] for r in role_library.load_roles(ROLES_DIR)}
    assert ids == {"analyst", "contrarian", "first-principles", "executor", "expansionist", "outsider"}


def test_all_v1_roles_pass_checks():
    assert role_library.check_roles(role_library.load_roles(ROLES_DIR)) == []


def test_underscore_files_are_not_roles():
    names = {r["id"] for r in role_library.load_roles(ROLES_DIR)}
    assert not any(n.startswith("_") for n in names)


def test_check_roles_catches_bad_model_and_unknown_tension(tmp_path):
    (tmp_path / "x.md").write_text(
        "---\nid: x\nname: X\nmodel: gpt\ntension_with: [ghost]\nuse_when: a\nskip_when: b\n---\n"
        "## Lens\nl\n## You must\n- a\n## You must not\n- b\n",
        encoding="utf-8",
    )
    errors = role_library.check_roles(role_library.load_roles(tmp_path))
    assert any("model" in e for e in errors)
    assert any("ghost" in e for e in errors)


def test_check_roles_catches_missing_section(tmp_path):
    (tmp_path / "y.md").write_text(
        "---\nid: y\nname: Y\nmodel: opus\ntension_with: []\nuse_when: a\nskip_when: b\n---\n"
        "## Lens\nl\n## You must not\n- b\n",
        encoding="utf-8",
    )
    errors = role_library.check_roles(role_library.load_roles(tmp_path))
    assert any("## You must" in e for e in errors)


def test_check_roles_requires_a_summary(tmp_path):
    (tmp_path / "z.md").write_text(
        "---\nid: z\nname: Z\nmodel: opus\ntension_with: []\nuse_when: a\nskip_when: b\n---\n"
        "## Lens\nl\n## You must\n- a\n## You must not\n- b\n",
        encoding="utf-8",
    )
    errors = role_library.check_roles(role_library.load_roles(tmp_path))
    assert any("summary" in e for e in errors)


def test_every_v1_role_has_a_one_line_summary():
    for r in role_library.load_roles(ROLES_DIR):
        assert 20 <= len(r["summary"]) <= 160, r["id"]


def test_catalog_maps_ids_to_name_and_summary():
    catalog = role_library.catalog(ROLES_DIR)
    assert set(catalog) == {"analyst", "contrarian", "first-principles", "executor", "expansionist", "outsider"}
    assert catalog["contrarian"]["name"] == "The Contrarian"
    assert catalog["contrarian"]["summary"]
