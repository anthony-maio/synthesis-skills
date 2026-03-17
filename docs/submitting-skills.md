# Submitting Skills

This repository is the canonical curated landing zone for Synthesis skills.

## What to Submit

- A skill directory under `skills/<skill-name>/`
- A `SKILL.md` with `name` and `description` front matter
- A `PROVENANCE.json` describing origin and authorship
- Helper code only when the skill actually needs it
- Provenance notes in the PR description when material was adapted from another source

## Required Checks

Run these before opening or updating a PR:

```bash
python scripts/validate_repo.py
python scripts/build_catalog.py
python scripts/build_catalog.py --check
pytest -q
```

## Review Expectations

- the skill is discoverable from its description
- the package shape is valid
- helper scripts are scoped to the skill
- the generated catalog reflects the submitted skill state
- provenance is clear enough for curation
