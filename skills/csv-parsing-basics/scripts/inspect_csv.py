"""Inspect CSV structure from the command line."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python inspect_csv.py <path>", file=sys.stderr)
        return 1

    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f"missing file: {target}", file=sys.stderr)
        return 1

    with target.open("r", encoding="utf-8", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        dialect = csv.Sniffer().sniff(sample or ",")
        reader = csv.reader(handle, dialect)
        rows = []
        for index, row in enumerate(reader):
            rows.append(row)
            if index >= 4:
                break

    print(f"delimiter={dialect.delimiter!r}")
    print(f"sample_rows={len(rows)}")
    if rows:
        print(f"header={rows[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
