from __future__ import annotations

import json
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
    (skill_dir / "REGISTRY.json").write_text(
        json.dumps(
            {
                "capability_family": "mirrored-skill",
                "lifecycle_stage": "canonical",
                "trust_level": "trusted",
                "is_primary": True,
                "variant_of": None,
                "supersedes": [],
            }
        ),
        encoding="utf-8",
    )

    issues = validate_skill_dir(skill_dir)

    messages = {issue.message for issue in issues}
    assert "external provenance must include an upstream URL or repo reference" in messages
    assert "external provenance must include source_license" in messages


def test_attestation_must_match_minimal_stss_shape(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "signed-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: signed-skill",
                "description: Use when validating optional STSS attestations.",
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
        json.dumps({"signature": "signed-payload"}),
        encoding="utf-8",
    )

    issues = validate_skill_dir(skill_dir)

    messages = {issue.message for issue in issues}
    assert "attestation.json must include an attestation object" in messages
    assert "attestation.json must include attestation.schemaVersion" in messages
    assert "attestation.json must include signingKeyId" in messages
    assert "attestation.json must include algorithm" in messages


def test_valid_attestation_passes_validation(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "signed-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: signed-skill",
                "description: Use when validating optional STSS attestations.",
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
                    "policy": {"decision": "PASS"},
                },
                "signature": "signed-payload",
                "signingKeyId": "ci-key",
                "algorithm": "ed25519",
            }
        ),
        encoding="utf-8",
    )

    issues = validate_skill_dir(skill_dir)

    assert issues == []


def test_registry_metadata_is_required_and_validated(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "governed-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: governed-skill",
                "description: Use when validating registry governance metadata.",
                "---",
                "",
                "# Governed Skill",
            ]
        ),
        encoding="utf-8",
    )
    (skill_dir / "PROVENANCE.json").write_text(
        json.dumps(
            {
                "kind": "first_party",
                "author": "Anthony Maio",
                "source": "https://example.com/governed-skill",
            }
        ),
        encoding="utf-8",
    )

    missing_registry_issues = validate_skill_dir(skill_dir)
    missing_messages = {issue.message for issue in missing_registry_issues}
    assert "missing REGISTRY.json" in missing_messages

    (skill_dir / "REGISTRY.json").write_text(
        json.dumps(
            {
                "capability_family": "governed-skill",
                "lifecycle_stage": "canonical",
                "trust_level": "trusted",
                "is_primary": True,
                "variant_of": None,
                "supersedes": [],
            }
        ),
        encoding="utf-8",
    )

    issues = validate_skill_dir(skill_dir)

    assert issues == []


def test_registry_metadata_rejects_invalid_stage_and_trust_level(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "governed-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                "name: governed-skill",
                "description: Use when validating registry governance metadata.",
                "---",
                "",
                "# Governed Skill",
            ]
        ),
        encoding="utf-8",
    )
    (skill_dir / "PROVENANCE.json").write_text(
        json.dumps(
            {
                "kind": "first_party",
                "author": "Anthony Maio",
                "source": "https://example.com/governed-skill",
            }
        ),
        encoding="utf-8",
    )
    (skill_dir / "REGISTRY.json").write_text(
        json.dumps(
            {
                "capability_family": "governed-skill",
                "lifecycle_stage": "published",
                "trust_level": "gold",
                "is_primary": True,
                "variant_of": None,
                "supersedes": [],
            }
        ),
        encoding="utf-8",
    )

    issues = validate_skill_dir(skill_dir)

    messages = {issue.message for issue in issues}
    assert (
        "REGISTRY.json lifecycle_stage must be one of: draft, challenger, canonical, deprecated"
        in messages
    )
    assert (
        "REGISTRY.json trust_level must be one of: untrusted, probation, trusted, verified"
        in messages
    )
