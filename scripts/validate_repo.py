"""Validate canonical skill packages and repository structure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    from catalog_tools import iter_skill_dirs, repo_root_from, validate_skill_dir

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(repo_root_from(__file__)),
        help="Repository root containing skills/, catalog/, and scripts/",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skills_root = root / "skills"
    if not skills_root.exists():
        print("skills/ directory is missing", file=sys.stderr)
        return 1

    skill_dirs = iter_skill_dirs(root)
    if not skill_dirs:
        print("skills/ does not contain any skill packages", file=sys.stderr)
        return 1

    failures = []
    for skill_dir in skill_dirs:
        failures.extend(validate_skill_dir(skill_dir))

    if failures:
        for failure in failures:
            print(f"{failure.path}: {failure.message}", file=sys.stderr)
        return 1

    print(f"validated {len(skill_dirs)} skill package(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
