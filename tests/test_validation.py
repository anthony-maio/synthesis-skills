from __future__ import annotations

from pathlib import Path

from scripts.catalog_tools import iter_skill_dirs, validate_skill_dir

ROOT = Path(__file__).resolve().parents[1]


def test_seed_batch_validates_cleanly() -> None:
    for skill_dir in iter_skill_dirs(ROOT):
        issues = validate_skill_dir(skill_dir)
        assert issues == []


def test_external_provenance_requires_license_and_upstream(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "mirrored-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: mirrored-skill",
                "description: Use when mirroring an external skill into the canonical registry.",
                "---",
                "",
                "# Mirrored Skill",
            ]
        ),
        encoding="utf-8",
    )
    (skill_dir / "PROVENANCE.json").write_text(
        '{"kind":"mirrored_external","author":"Example Author","source":"https://example.com/skill"}',
        encoding="utf-8",
    )

    issues = validate_skill_dir(skill_dir)

    messages = {issue.message for issue in issues}
    assert "external provenance must include an upstream URL or repo reference" in messages
    assert "external provenance must include source_license" in messages
