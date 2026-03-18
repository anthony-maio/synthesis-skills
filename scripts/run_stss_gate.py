"""Run STSS scans for changed skill packages and verify optional attestations."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

if __package__ in {None, ""}:
    script_dir = Path(__file__).resolve().parent
    if str(script_dir.parent) not in sys.path:
        sys.path.insert(0, str(script_dir.parent))
    from scripts.catalog_tools import ATTESTATION_FILENAME, load_attestation, repo_root_from
else:
    from scripts.catalog_tools import ATTESTATION_FILENAME, load_attestation, repo_root_from


def changed_skill_dirs(repo_root: Path, changed_files: Iterable[str]) -> list[Path]:
    """Return unique top-level skill directories referenced by a changed file list."""
    skills: dict[str, Path] = {}
    for raw_path in changed_files:
        normalized = raw_path.replace("\\", "/").strip()
        parts = normalized.split("/")
        if len(parts) < 2 or parts[0] != "skills":
            continue
        skill_path = repo_root / parts[0] / parts[1]
        if skill_path.is_dir():
            skills[skill_path.as_posix()] = skill_path
    return sorted(skills.values())


def load_public_keys(payload: str | None) -> dict[str, str]:
    """Parse a JSON object mapping signing key ids to STSS public keys."""
    if not payload:
        return {}
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("STSS_PUBLIC_KEYS_JSON must be a JSON object")
    result: dict[str, str] = {}
    for key_id, public_key in parsed.items():
        if not isinstance(key_id, str) or not isinstance(public_key, str):
            raise ValueError("STSS_PUBLIC_KEYS_JSON values must be string pairs")
        result[key_id] = public_key
    return result


def resolve_public_key(
    skill_dir: Path,
    signing_key_id: str | None,
    public_keys: dict[str, str],
    fallback_key: str | None,
) -> str | None:
    """Resolve a verifier public key for an attested skill."""
    if signing_key_id and signing_key_id in public_keys:
        return public_keys[signing_key_id]
    if fallback_key:
        return fallback_key
    return None


def git_changed_files(repo_root: Path, base: str | None, head: str | None) -> list[str]:
    """Read changed files between two git revisions."""
    if not head:
        raise ValueError("--head is required")

    if not base or set(base) == {"0"}:
        command = ["git", "show", "--pretty=", "--name-only", head]
    else:
        command = ["git", "diff", "--name-only", base, head]

    result = subprocess.run(
        command,
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def run_command(command: list[str], *, cwd: Path) -> None:
    """Run one subprocess and stream output to the caller."""
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(repo_root_from(__file__)),
        help="Repository root containing skills/, catalog/, and scripts/",
    )
    parser.add_argument("--base", help="Base git revision for diff")
    parser.add_argument("--head", help="Head git revision for diff")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()

    if shutil.which("stss") is None:
        print("stss CLI is not installed or not on PATH", file=sys.stderr)
        return 2

    try:
        changed_files = git_changed_files(repo_root, args.base, args.head)
        public_keys = load_public_keys(os.environ.get("STSS_PUBLIC_KEYS_JSON"))
    except (ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    fallback_key = os.environ.get("STSS_PUBLIC_KEY")
    skill_dirs = changed_skill_dirs(repo_root, changed_files)
    if not skill_dirs:
        print("no changed skills detected; skipping STSS gate")
        return 0

    for skill_dir in skill_dirs:
        print(f"running STSS scan for {skill_dir.relative_to(repo_root).as_posix()}")
        try:
            run_command(["stss", "scan", str(skill_dir)], cwd=repo_root)
        except subprocess.CalledProcessError:
            return 1

        attestation_path = skill_dir / ATTESTATION_FILENAME
        if not attestation_path.exists():
            continue

        attestation = load_attestation(skill_dir)
        public_key = resolve_public_key(
            skill_dir,
            attestation.get("signingKeyId"),
            public_keys,
            fallback_key,
        )
        if not public_key:
            print(
                f"{skill_dir.relative_to(repo_root).as_posix()}: no STSS public key configured "
                "for attestation verification",
                file=sys.stderr,
            )
            return 1

        print(f"verifying attestation for {skill_dir.relative_to(repo_root).as_posix()}")
        try:
            run_command(
                [
                    "stss",
                    "verify",
                    str(skill_dir),
                    "--attestation",
                    str(attestation_path),
                    "--public-key",
                    public_key,
                ],
                cwd=repo_root,
            )
        except subprocess.CalledProcessError:
            return 1

    print(f"STSS gate passed for {len(skill_dirs)} changed skill(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
