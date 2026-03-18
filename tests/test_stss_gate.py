from __future__ import annotations

import json
from pathlib import Path

from scripts.run_stss_gate import (
    changed_skill_dirs,
    load_public_keys,
    resolve_public_key,
)


def test_changed_skill_dirs_only_returns_unique_skill_roots(tmp_path: Path) -> None:
    repo_root = tmp_path
    first = repo_root / "skills" / "first-skill"
    second = repo_root / "skills" / "second-skill"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    changed = [
        "skills/first-skill/SKILL.md",
        "skills/first-skill/scripts/helper.py",
        "skills/second-skill/PROVENANCE.json",
        "README.md",
    ]

    skill_dirs = changed_skill_dirs(repo_root, changed)

    assert skill_dirs == [first, second]


def test_load_public_keys_reads_json_map() -> None:
    public_keys = load_public_keys(
        json.dumps(
            {
                "ci-key": "public-key-data",
                "backup-key": "backup-key-data",
            }
        )
    )

    assert public_keys == {
        "ci-key": "public-key-data",
        "backup-key": "backup-key-data",
    }


def test_resolve_public_key_prefers_key_map_then_fallback() -> None:
    skill_dir = Path("skills/signed-skill")

    public_key = resolve_public_key(
        skill_dir,
        "ci-key",
        {"ci-key": "mapped-public-key"},
        "fallback-public-key",
    )

    assert public_key == "mapped-public-key"

    fallback_key = resolve_public_key(
        skill_dir,
        "unknown-key",
        {},
        "fallback-public-key",
    )

    assert fallback_key == "fallback-public-key"
