from __future__ import annotations

import json
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
    assert catalog["family_count"] == len(SEEDED_SKILLS)
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
    assert deep_research["trust_level"] == "trusted"
    assert deep_research["governance"]["lifecycle_stage"] == "canonical"
    assert deep_research["governance"]["capability_family"] == "deep-research-synthesizer"
    assert deep_research["governance"]["is_primary"] is True
    family = next(
        item
        for item in catalog["families"]
        if item["capability_family"] == "deep-research-synthesizer"
    )
    assert family["canonical_skill"] == "deep-research-synthesizer"
    assert family["challengers"] == []


def test_skill_discovery_finds_top_level_package() -> None:
    skills = iter_skill_dirs(ROOT)

    assert {skill.name for skill in skills} == SEEDED_SKILLS


def test_repo_root_detection_works_from_script_path() -> None:
    assert repo_root_from(ROOT / "scripts" / "build_catalog.py") == ROOT


def test_catalog_marks_seeded_skills_without_attestation() -> None:
    catalog = build_catalog(ROOT, "anthony-maio/synthesis-skills")

    for entry in catalog["skills"]:
        assert entry["stss"]["attestation_present"] is False
        assert entry["stss"]["schema_version"] is None
        assert entry["stss"]["algorithm"] is None
        assert entry["stss"]["policy_decision"] is None


def test_catalog_includes_stss_metadata_when_attestation_exists(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "signed-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: signed-skill",
                "description: Use when validating STSS attestation metadata in the catalog.",
                "---",
                "",
                "# Signed Skill",
            ]
        ),
        encoding="utf-8",
    )
    (skill_dir / "PROVENANCE.json").write_text(
        json.dumps(
            {
                "kind": "first_party",
                "author": "Anthony Maio",
                "source": "https://example.com/signed-skill",
            }
        ),
        encoding="utf-8",
    )
    (skill_dir / "REGISTRY.json").write_text(
        json.dumps(
            {
                "capability_family": "signed-skill",
                "lifecycle_stage": "canonical",
                "trust_level": "trusted",
                "is_primary": True,
                "variant_of": None,
                "supersedes": [],
            }
        ),
        encoding="utf-8",
    )
    (skill_dir / "attestation.json").write_text(
        json.dumps(
            {
                "attestation": {
                    "schemaVersion": "1.0.0",
                    "scan": {
                        "llmAuditPerformed": False,
                        "registryAuditPerformed": True,
                    },
                    "policy": {
                        "decision": "PASS_WITH_WARNINGS",
                    },
                },
                "signature": "signed-payload",
                "signingKeyId": "ci-key",
                "algorithm": "ed25519",
            }
        ),
        encoding="utf-8",
    )

    catalog = build_catalog(tmp_path, "anthony-maio/synthesis-skills")

    assert catalog["skill_count"] == 1
    assert catalog["family_count"] == 1
    entry = catalog["skills"][0]
    assert entry["name"] == "signed-skill"
    assert entry["trust_level"] == "trusted"
    assert entry["governance"] == {
        "capability_family": "signed-skill",
        "lifecycle_stage": "canonical",
        "trust_level": "trusted",
        "is_primary": True,
        "variant_of": None,
        "supersedes": [],
        "submission_type": None,
        "nearest_canonical": None,
        "evidence_summary": None,
    }
    assert entry["stss"] == {
        "attestation_present": True,
        "schema_version": "1.0.0",
        "algorithm": "ed25519",
        "signing_key_id": "ci-key",
        "policy_decision": "PASS_WITH_WARNINGS",
        "llm_audit_performed": False,
        "registry_audit_performed": True,
    }
    assert catalog["families"] == [
        {
            "capability_family": "signed-skill",
            "canonical_skill": "signed-skill",
            "canonical_trust_level": "trusted",
            "challengers": [],
            "variants": [],
        }
    ]
