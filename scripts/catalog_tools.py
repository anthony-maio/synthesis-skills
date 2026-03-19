"""Shared registry helpers for validation and catalog generation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_SKILL_DIRS = {"scripts", "assets", "references", "agents"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
PROVENANCE_KINDS = {"first_party", "mirrored_external", "adapted_external"}
ATTESTATION_FILENAME = "attestation.json"
REGISTRY_FILENAME = "REGISTRY.json"
LIFECYCLE_STAGES = {"draft", "challenger", "canonical", "deprecated"}
TRUST_LEVELS = {"untrusted", "probation", "trusted", "verified"}
SUBMISSION_TYPES = {
    "new_family_candidate",
    "canonical_improvement_candidate",
    "variant_candidate",
    "supersedes_existing",
}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "for",
    "from",
    "if",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "use",
    "when",
    "with",
}


@dataclass(slots=True)
class ValidationIssue:
    path: str
    message: str


def repo_root_from(path: str | Path) -> Path:
    """Resolve the repository root from any child path."""
    target = Path(path).resolve()
    current = target if target.is_dir() else target.parent
    for candidate in [current, *current.parents]:
        if (candidate / "skills").exists() and (candidate / "scripts").exists():
            return candidate
    return current


def parse_front_matter(text: str) -> dict[str, str]:
    """Parse the two-field YAML front matter used by canonical skills."""
    if not text.startswith("---\n"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    payload: dict[str, str] = {}
    for raw_line in parts[1].splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        payload[key.strip()] = value.strip()
    return payload


def body_without_front_matter(text: str) -> str:
    """Return markdown body without front matter."""
    if not text.startswith("---\n"):
        return text

    parts = text.split("---", 2)
    return parts[2].lstrip() if len(parts) >= 3 else text


def tokenize(text: str) -> list[str]:
    """Create normalized catalog keywords from free text."""
    tokens = TOKEN_PATTERN.findall(text.lower())
    seen: set[str] = set()
    results: list[str] = []
    for token in tokens:
        if token in STOP_WORDS or token in seen:
            continue
        seen.add(token)
        results.append(token)
    return results


def iter_skill_dirs(root: Path) -> list[Path]:
    """Return all top-level skill directories."""
    skills_root = root / "skills"
    if not skills_root.exists():
        return []
    return [
        path
        for path in sorted(skills_root.iterdir())
        if path.is_dir() and (path / "SKILL.md").exists()
    ]


def load_provenance(skill_dir: Path) -> dict[str, Any]:
    """Load optional provenance metadata for a skill package."""
    path = skill_dir / "PROVENANCE.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_attestation(skill_dir: Path) -> dict[str, Any]:
    """Load optional STSS attestation metadata for a skill package."""
    path = skill_dir / ATTESTATION_FILENAME
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry_metadata(skill_dir: Path) -> dict[str, Any]:
    """Load required registry governance metadata for a skill package."""
    path = skill_dir / REGISTRY_FILENAME
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def stss_metadata_from_attestation(attestation: dict[str, Any]) -> dict[str, Any]:
    """Build normalized catalog metadata from an optional STSS attestation."""
    if not attestation:
        return {
            "attestation_present": False,
            "schema_version": None,
            "algorithm": None,
            "signing_key_id": None,
            "policy_decision": None,
            "llm_audit_performed": None,
            "registry_audit_performed": None,
        }

    payload = attestation.get("attestation")
    if not isinstance(payload, dict):
        payload = {}
    scan = payload.get("scan")
    if not isinstance(scan, dict):
        scan = {}
    policy = payload.get("policy")
    if not isinstance(policy, dict):
        policy = {}

    return {
        "attestation_present": True,
        "schema_version": payload.get("schemaVersion"),
        "algorithm": attestation.get("algorithm"),
        "signing_key_id": attestation.get("signingKeyId"),
        "policy_decision": policy.get("decision"),
        "llm_audit_performed": scan.get("llmAuditPerformed"),
        "registry_audit_performed": scan.get("registryAuditPerformed"),
    }


def governance_metadata_from_registry(metadata: dict[str, Any]) -> dict[str, Any]:
    """Build normalized governance metadata from required registry metadata."""
    return {
        "capability_family": metadata.get("capability_family"),
        "lifecycle_stage": metadata.get("lifecycle_stage"),
        "trust_level": metadata.get("trust_level"),
        "is_primary": metadata.get("is_primary"),
        "variant_of": metadata.get("variant_of"),
        "supersedes": metadata.get("supersedes", []),
        "submission_type": metadata.get("submission_type"),
        "nearest_canonical": metadata.get("nearest_canonical"),
        "evidence_summary": metadata.get("evidence_summary"),
    }


def validate_skill_dir(skill_dir: Path) -> list[ValidationIssue]:
    """Validate one skill package against the canonical repo contract."""
    issues: list[ValidationIssue] = []
    skill_file = skill_dir / "SKILL.md"
    relative = skill_dir.relative_to(skill_dir.parents[1])

    if not skill_file.exists():
        return [ValidationIssue(str(relative), "missing SKILL.md")]

    text = skill_file.read_text(encoding="utf-8")
    metadata = parse_front_matter(text)
    body = body_without_front_matter(text)
    relative_str = str(relative).replace("\\", "/")

    if not metadata:
        issues.append(ValidationIssue(relative_str, "SKILL.md must start with YAML front matter"))
        return issues

    allowed_keys = {"name", "description"}
    extra_keys = sorted(set(metadata) - allowed_keys)
    if extra_keys:
        issues.append(
            ValidationIssue(relative_str, f"unsupported front matter keys: {', '.join(extra_keys)}")
        )

    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if not NAME_PATTERN.fullmatch(name):
        issues.append(
            ValidationIssue(
                relative_str,
                "front matter name must use lowercase letters, numbers, and hyphens only",
            )
        )

    if name and name != skill_dir.name:
        issues.append(ValidationIssue(relative_str, "front matter name must match directory name"))

    if not description.startswith("Use when"):
        issues.append(ValidationIssue(relative_str, "description must start with 'Use when'"))

    if "# " not in body:
        issues.append(ValidationIssue(relative_str, "SKILL.md must contain a top-level heading"))

    child_dirs = {path.name for path in skill_dir.iterdir() if path.is_dir()}
    unexpected = sorted(child_dirs - ALLOWED_SKILL_DIRS)
    if unexpected:
        issues.append(
            ValidationIssue(
                relative_str,
                f"unsupported subdirectories: {', '.join(unexpected)}",
            )
        )

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists() and not any(path.is_file() for path in scripts_dir.rglob("*")):
        issues.append(ValidationIssue(relative_str, "scripts/ exists but is empty"))

    provenance_path = skill_dir / "PROVENANCE.json"
    if not provenance_path.exists():
        issues.append(ValidationIssue(relative_str, "missing PROVENANCE.json"))
        return issues

    try:
        provenance = load_provenance(skill_dir)
    except json.JSONDecodeError:
        issues.append(ValidationIssue(relative_str, "PROVENANCE.json must be valid JSON"))
        return issues

    kind = provenance.get("kind")
    if kind not in PROVENANCE_KINDS:
        issues.append(
            ValidationIssue(
                relative_str,
                "PROVENANCE.json kind must be one of: "
                "first_party, mirrored_external, adapted_external",
            )
        )

    if not provenance.get("author"):
        issues.append(ValidationIssue(relative_str, "PROVENANCE.json must include author"))

    if not provenance.get("source"):
        issues.append(ValidationIssue(relative_str, "PROVENANCE.json must include source"))

    if kind in {"mirrored_external", "adapted_external"}:
        if not provenance.get("upstream"):
            issues.append(
                ValidationIssue(
                    relative_str,
                    "external provenance must include an upstream URL or repo reference",
                )
            )
        if not provenance.get("source_license"):
            issues.append(
                ValidationIssue(
                    relative_str,
                    "external provenance must include source_license",
                )
            )

    registry_path = skill_dir / REGISTRY_FILENAME
    if not registry_path.exists():
        issues.append(ValidationIssue(relative_str, f"missing {REGISTRY_FILENAME}"))
        return issues

    try:
        registry = load_registry_metadata(skill_dir)
    except json.JSONDecodeError:
        issues.append(ValidationIssue(relative_str, f"{REGISTRY_FILENAME} must be valid JSON"))
        return issues

    capability_family = registry.get("capability_family")
    if not capability_family:
        issues.append(
            ValidationIssue(relative_str, f"{REGISTRY_FILENAME} must include capability_family")
        )
    elif not NAME_PATTERN.fullmatch(str(capability_family)):
        issues.append(
            ValidationIssue(
                relative_str,
                f"{REGISTRY_FILENAME} capability_family must use lowercase kebab-case",
            )
        )

    lifecycle_stage = registry.get("lifecycle_stage")
    if lifecycle_stage not in LIFECYCLE_STAGES:
        issues.append(
            ValidationIssue(
                relative_str,
                f"{REGISTRY_FILENAME} lifecycle_stage must be one of: "
                "draft, challenger, canonical, deprecated",
            )
        )

    trust_level = registry.get("trust_level")
    if trust_level not in TRUST_LEVELS:
        issues.append(
            ValidationIssue(
                relative_str,
                f"{REGISTRY_FILENAME} trust_level must be one of: "
                "untrusted, probation, trusted, verified",
            )
        )

    is_primary = registry.get("is_primary")
    if not isinstance(is_primary, bool):
        issues.append(
            ValidationIssue(relative_str, f"{REGISTRY_FILENAME} is_primary must be a boolean")
        )

    variant_of = registry.get("variant_of")
    if variant_of is not None and not NAME_PATTERN.fullmatch(str(variant_of)):
        issues.append(
            ValidationIssue(
                relative_str,
                f"{REGISTRY_FILENAME} variant_of must be null or lowercase kebab-case",
            )
        )

    supersedes = registry.get("supersedes", [])
    if not isinstance(supersedes, list) or any(
        not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) for name in supersedes
    ):
        issues.append(
            ValidationIssue(
                relative_str,
                f"{REGISTRY_FILENAME} supersedes must be a list of lowercase kebab-case names",
            )
        )

    submission_type = registry.get("submission_type")
    if submission_type is not None and submission_type not in SUBMISSION_TYPES:
        issues.append(
            ValidationIssue(
                relative_str,
                f"{REGISTRY_FILENAME} submission_type must be one of: "
                "new_family_candidate, canonical_improvement_candidate, "
                "variant_candidate, supersedes_existing",
            )
        )

    nearest_canonical = registry.get("nearest_canonical")
    if nearest_canonical is not None and not NAME_PATTERN.fullmatch(str(nearest_canonical)):
        issues.append(
            ValidationIssue(
                relative_str,
                f"{REGISTRY_FILENAME} nearest_canonical must be null or lowercase kebab-case",
            )
        )

    evidence_summary = registry.get("evidence_summary")
    if evidence_summary is not None and not str(evidence_summary).strip():
        issues.append(
            ValidationIssue(relative_str, f"{REGISTRY_FILENAME} evidence_summary must not be empty")
        )

    attestation_path = skill_dir / ATTESTATION_FILENAME
    if not attestation_path.exists():
        return issues

    try:
        attestation = load_attestation(skill_dir)
    except json.JSONDecodeError:
        issues.append(ValidationIssue(relative_str, f"{ATTESTATION_FILENAME} must be valid JSON"))
        return issues

    payload = attestation.get("attestation")
    if not isinstance(payload, dict):
        issues.append(
            ValidationIssue(
                relative_str,
                f"{ATTESTATION_FILENAME} must include an attestation object",
            )
        )
        payload = {}

    if not payload.get("schemaVersion"):
        issues.append(
            ValidationIssue(
                relative_str,
                f"{ATTESTATION_FILENAME} must include attestation.schemaVersion",
            )
        )

    if not attestation.get("signature"):
        issues.append(
            ValidationIssue(relative_str, f"{ATTESTATION_FILENAME} must include signature")
        )

    if not attestation.get("signingKeyId"):
        issues.append(
            ValidationIssue(relative_str, f"{ATTESTATION_FILENAME} must include signingKeyId")
        )

    if not attestation.get("algorithm"):
        issues.append(
            ValidationIssue(relative_str, f"{ATTESTATION_FILENAME} must include algorithm")
        )

    return issues


def discover_skill_entry(skill_dir: Path, repo_slug: str) -> dict[str, Any]:
    """Build one machine-readable catalog entry from a skill directory."""
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    metadata = parse_front_matter(text)
    body = body_without_front_matter(text)
    provenance = load_provenance(skill_dir)
    governance = load_registry_metadata(skill_dir)
    attestation = load_attestation(skill_dir)
    relative_path = str(skill_dir.relative_to(skill_dir.parents[1]).as_posix())
    package_dirs = sorted(path.name for path in skill_dir.iterdir() if path.is_dir())
    keyword_source = " ".join([skill_dir.name, metadata["name"], metadata["description"], body])
    keywords = tokenize(keyword_source)[:24]

    return {
        "name": metadata["name"],
        "description": metadata["description"],
        "keywords": keywords,
        "trust_level": governance.get("trust_level", "trusted"),
        "source_type": "canonical",
        "relative_path": relative_path,
        "repo": repo_slug,
        "package_dirs": package_dirs,
        "upstream": provenance.get("upstream") or provenance.get("source"),
        "provenance": provenance,
        "governance": governance_metadata_from_registry(governance),
        "stss": stss_metadata_from_attestation(attestation),
    }


def build_family_index(skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a family-centric view of canonical skills, challengers, and variants."""
    families: dict[str, dict[str, Any]] = {}
    for skill in skills:
        governance = skill["governance"]
        family_name = governance["capability_family"]
        family = families.setdefault(
            family_name,
            {
                "capability_family": family_name,
                "canonical_skill": None,
                "canonical_trust_level": None,
                "challengers": [],
                "variants": [],
            },
        )

        if governance["lifecycle_stage"] == "canonical" and governance["is_primary"]:
            family["canonical_skill"] = skill["name"]
            family["canonical_trust_level"] = skill["trust_level"]
        elif governance["lifecycle_stage"] == "challenger":
            family["challengers"].append(skill["name"])

        if governance["variant_of"]:
            family["variants"].append(skill["name"])

    return [families[name] for name in sorted(families)]


def validate_registry_governance(root: Path) -> list[ValidationIssue]:
    """Validate repo-wide governance rules across all skill packages."""
    issues: list[ValidationIssue] = []
    entries: list[tuple[Path, dict[str, Any]]] = []
    family_to_primary: dict[str, list[str]] = {}
    canonical_by_family: dict[str, list[str]] = {}
    all_skill_names: set[str] = set()

    for skill_dir in iter_skill_dirs(root):
        registry = load_registry_metadata(skill_dir)
        if not registry:
            continue
        entries.append((skill_dir, registry))
        all_skill_names.add(skill_dir.name)

        family = registry.get("capability_family")
        if not family:
            continue
        if registry.get("lifecycle_stage") == "canonical":
            canonical_by_family.setdefault(family, []).append(skill_dir.name)
            if registry.get("is_primary") is True:
                family_to_primary.setdefault(family, []).append(skill_dir.name)

    for family, primaries in sorted(family_to_primary.items()):
        if len(primaries) > 1:
            issues.append(
                ValidationIssue(
                    f"skills/{family}",
                    f"capability family {family} has more than one primary canonical skill",
                )
            )

    for skill_dir, registry in entries:
        relative = str(skill_dir.relative_to(root).as_posix())
        stage = registry.get("lifecycle_stage")
        trust_level = registry.get("trust_level")
        is_primary = registry.get("is_primary")
        family = registry.get("capability_family")
        submission_type = registry.get("submission_type")
        nearest_canonical = registry.get("nearest_canonical")
        evidence_summary = registry.get("evidence_summary")
        variant_of = registry.get("variant_of")

        if stage == "canonical":
            if is_primary is not True:
                issues.append(
                    ValidationIssue(relative, "canonical skills must set is_primary to true")
                )
            if trust_level not in {"trusted", "verified"}:
                issues.append(
                    ValidationIssue(
                        relative,
                        "canonical skills must use trust_level trusted or verified",
                    )
                )

        if stage == "challenger":
            if is_primary is not False:
                issues.append(
                    ValidationIssue(relative, "challenger skills must set is_primary to false")
                )
            if trust_level != "probation":
                issues.append(
                    ValidationIssue(
                        relative,
                        "challenger skills must use trust_level probation",
                    )
                )
            if submission_type is None:
                issues.append(
                    ValidationIssue(
                        relative,
                        f"challenger skill {skill_dir.name} must declare submission_type",
                    )
                )
            if not evidence_summary:
                issues.append(
                    ValidationIssue(
                        relative,
                        f"challenger skill {skill_dir.name} must include evidence_summary",
                    )
                )
            if submission_type != "new_family_candidate" and not nearest_canonical:
                issues.append(
                    ValidationIssue(
                        relative,
                        "challenger skill "
                        f"{skill_dir.name} must reference nearest_canonical unless "
                        "it is a new family candidate",
                    )
                )
            if submission_type == "new_family_candidate" and family in canonical_by_family:
                issues.append(
                    ValidationIssue(
                        relative,
                        f"challenger skill {skill_dir.name} cannot use new_family_candidate "
                        f"because capability family {family} already has a canonical skill",
                    )
                )
            if submission_type in {
                "canonical_improvement_candidate",
                "variant_candidate",
                "supersedes_existing",
            } and family not in canonical_by_family:
                issues.append(
                    ValidationIssue(
                        relative,
                        f"challenger skill {skill_dir.name} must target a family "
                        "with an existing canonical skill",
                    )
                )
            if nearest_canonical and nearest_canonical not in all_skill_names:
                issues.append(
                    ValidationIssue(
                        relative,
                        f"challenger skill {skill_dir.name} references unknown "
                        f"nearest_canonical {nearest_canonical}",
                    )
                )
            if submission_type == "variant_candidate" and not variant_of:
                issues.append(
                    ValidationIssue(
                        relative,
                        f"challenger skill {skill_dir.name} must set variant_of "
                        "for variant_candidate",
                    )
                )

    return issues


def build_catalog(root: Path, repo_slug: str) -> dict[str, Any]:
    """Build the complete catalog document."""
    skills = [discover_skill_entry(skill_dir, repo_slug) for skill_dir in iter_skill_dirs(root)]
    families = build_family_index(skills)
    return {
        "repo": repo_slug,
        "schema_version": 1,
        "family_count": len(families),
        "skill_count": len(skills),
        "families": families,
        "skills": skills,
    }


def write_catalog(root: Path, data: dict[str, Any]) -> Path:
    """Write the generated catalog to catalog/skills.json."""
    target = root / "catalog" / "skills.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target


def load_catalog(path: Path) -> dict[str, Any]:
    """Load an existing catalog from disk."""
    return json.loads(path.read_text(encoding="utf-8"))
