from __future__ import annotations

from pathlib import Path

from scripts.catalog_tools import build_catalog, iter_skill_dirs, repo_root_from

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_contains_sample_skill() -> None:
    catalog = build_catalog(ROOT, "anthony-maio/synthesis-skills")

    assert catalog["skill_count"] == 1
    assert catalog["skills"][0]["name"] == "csv-parsing-basics"
    assert catalog["skills"][0]["source_type"] == "canonical"


def test_skill_discovery_finds_top_level_package() -> None:
    skills = iter_skill_dirs(ROOT)

    assert [skill.name for skill in skills] == ["csv-parsing-basics"]


def test_repo_root_detection_works_from_script_path() -> None:
    assert repo_root_from(ROOT / "scripts" / "build_catalog.py") == ROOT
