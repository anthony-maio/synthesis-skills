"""Generate or verify the canonical machine-readable skill catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_REPO = "anthony-maio/synthesis-skills"


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    from catalog_tools import build_catalog, load_catalog, repo_root_from, write_catalog

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if catalog/skills.json is stale",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help="GitHub repo slug for catalog metadata",
    )
    parser.add_argument(
        "--root",
        default=str(repo_root_from(__file__)),
        help="Repository root containing skills/, catalog/, and scripts/",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    generated = build_catalog(root, args.repo)
    target = root / "catalog" / "skills.json"

    if args.check:
        if not target.exists():
            print("catalog/skills.json is missing", file=sys.stderr)
            return 1
        existing = load_catalog(target)
        if existing != generated:
            print(
                "catalog/skills.json is stale; run python scripts/build_catalog.py",
                file=sys.stderr,
            )
            print(json.dumps(generated, indent=2), file=sys.stderr)
            return 1
        print("catalog/skills.json is current")
        return 0

    output = write_catalog(root, generated)
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
