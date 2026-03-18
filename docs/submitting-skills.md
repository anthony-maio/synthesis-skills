# Submitting Skills

This repository is the canonical curated landing zone for Synthesis skills.

## What to Submit

- A skill directory under `skills/<skill-name>/`
- A `SKILL.md` with `name` and `description` front matter
- A `PROVENANCE.json` describing origin and authorship
- An optional `attestation.json` if the skill was scanned or signed with STSS
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

If you want to preflight the same STSS gate that CI runs:

```bash
npm install -g stss@0.4.3
python scripts/run_stss_gate.py --base origin/main --head HEAD
```

If your skill includes `attestation.json`, make sure the registry maintainers have the matching public key configured in `STSS_PUBLIC_KEYS_JSON` or `STSS_PUBLIC_KEY`.

## Review Expectations

- the skill is discoverable from its description
- the package shape is valid
- helper scripts are scoped to the skill
- the generated catalog reflects the submitted skill state
- provenance is clear enough for curation
- STSS scan output is clean for the changed skill package
- attested skills can be verified with the configured public key set
