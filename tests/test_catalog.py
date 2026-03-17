from __future__ import annotations

from pathlib import Path

from scripts.catalog_tools import build_catalog, iter_skill_dirs, repo_root_from

ROOT = Path(__file__).resolve().parents[1]
SEEDED_SKILLS = {
    "deep-research-synthesizer",
    "dispatching-parallel-agents",
    "receiving-code-review",
    "repo-surveyor",
    "requesting-code-review",
    "systematic-debugging",
    "test-driven-development",
    "using-git-worktrees",
    "verification-before-completion",
    "writing-clearly-and-concisely",
    "writing-plans",
    "writing-skills",
}


def test_catalog_contains_seed_batch() -> None:
    catalog = build_catalog(ROOT, "anthony-maio/synthesis-skills")

    assert catalog["skill_count"] == len(SEEDED_SKILLS)
    assert {entry["name"] for entry in catalog["skills"]} == SEEDED_SKILLS
    deep_research = next(
        entry for entry in catalog["skills"] if entry["name"] == "deep-research-synthesizer"
    )
    assert deep_research["source_type"] == "canonical"
    assert deep_research["provenance"]["source_license"] == "MIT"
    assert deep_research["upstream"] == (
        "https://github.com/anthony-maio/pieces-agent-skills/tree/main/deep-research-synthesizer"
    )
    mirrored = next(
        entry for entry in catalog["skills"] if entry["name"] == "requesting-code-review"
    )
    assert mirrored["provenance"]["kind"] == "mirrored_external"
    assert mirrored["provenance"]["source_license"] == "MIT"
    assert mirrored["upstream"] == (
        "https://github.com/obra/superpowers/tree/main/skills/requesting-code-review"
    )
    planning = next(entry for entry in catalog["skills"] if entry["name"] == "writing-plans")
    assert planning["provenance"]["kind"] == "mirrored_external"
    assert planning["upstream"] == "https://github.com/obra/superpowers/tree/main/skills/writing-plans"


def test_skill_discovery_finds_top_level_package() -> None:
    skills = iter_skill_dirs(ROOT)

    assert {skill.name for skill in skills} == SEEDED_SKILLS


def test_repo_root_detection_works_from_script_path() -> None:
    assert repo_root_from(ROOT / "scripts" / "build_catalog.py") == ROOT
