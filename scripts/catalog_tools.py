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
    attestation = load_attestation(skill_dir)
    relative_path = str(skill_dir.relative_to(skill_dir.parents[1]).as_posix())
    package_dirs = sorted(path.name for path in skill_dir.iterdir() if path.is_dir())
    keyword_source = " ".join([skill_dir.name, metadata["name"], metadata["description"], body])
    keywords = tokenize(keyword_source)[:24]

    return {
        "name": metadata["name"],
        "description": metadata["description"],
        "keywords": keywords,
        "trust_level": "trusted",
        "source_type": "canonical",
        "relative_path": relative_path,
        "repo": repo_slug,
        "package_dirs": package_dirs,
        "upstream": provenance.get("upstream") or provenance.get("source"),
        "provenance": provenance,
        "stss": stss_metadata_from_attestation(attestation),
    }


def build_catalog(root: Path, repo_slug: str) -> dict[str, Any]:
    """Build the complete catalog document."""
    skills = [discover_skill_entry(skill_dir, repo_slug) for skill_dir in iter_skill_dirs(root)]
    return {
        "repo": repo_slug,
        "schema_version": 1,
        "skill_count": len(skills),
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
