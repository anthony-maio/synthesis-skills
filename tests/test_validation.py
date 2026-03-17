from __future__ import annotations

from pathlib import Path

from scripts.catalog_tools import validate_skill_dir

ROOT = Path(__file__).resolve().parents[1]


def test_sample_skill_validates_cleanly() -> None:
    issues = validate_skill_dir(ROOT / "skills" / "csv-parsing-basics")
    assert issues == []
