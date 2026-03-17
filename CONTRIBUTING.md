# Contributing

## Local Setup

```bash
pip install -e ".[dev]"
python scripts/validate_repo.py
python scripts/build_catalog.py
pytest -q
```

## What to Change

- add or update curated skills under `skills/`
- keep helper code scoped to the relevant skill package
- regenerate `catalog/skills.json` whenever skill metadata changes

## Before Opening a PR

```bash
python scripts/validate_repo.py
python scripts/build_catalog.py
python scripts/build_catalog.py --check
ruff check scripts tests
pytest -q
```
