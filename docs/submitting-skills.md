# Submitting Skills

This repository is the canonical curated landing zone for Synthesis skills.

## What to Submit

- A skill directory under `skills/<skill-name>/`
- A `SKILL.md` with `name` and `description` front matter
- A `PROVENANCE.json` describing origin and authorship
- A `REGISTRY.json` declaring capability family, lifecycle stage, and trust level
- An optional `attestation.json` if the skill was scanned or signed with STSS
- Helper code only when the skill actually needs it
- Provenance notes in the PR description when material was adapted from another source

## Provenance and Attestation

- `PROVENANCE.json` is about authorship, upstream source, adaptation status, and licensing.
- `REGISTRY.json` is about curation state inside Synthesis: capability family, lifecycle stage, and trust level.
- `attestation.json` is about the exact skill snapshot being scanned or signed by the Synthesis registry workflow.
- Do not use `attestation.json` to imply that the original author reviewed, signed, or endorsed the mirrored package.
- External skills can carry registry attestations if their provenance stays explicit and accurate.

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

## Current Gate

- Every changed skill must pass `validate_repo.py`, catalog generation, tests, and the STSS scan gate in CI.
- Signing is not currently mandatory for merge.
- If an attestation is present, it must verify cleanly.
- Human review is still required for quality, licensing, and fit.
- Canonical duplicates should not merge. New submissions should usually improve an existing family or justify a genuinely new one.

## Agent-Generated Skills

When Synthesis generates a new skill from task work, treat that submission as a draft proposal:

- include the generated skill package and provenance
- set `REGISTRY.json` to the right lifecycle stage and capability family intent
- include evaluation notes or task evidence in the PR description
- expect STSS scan plus normal repo validation to run in CI
- do not treat scan or signing alone as approval to merge
- require curator review before the skill becomes part of the trusted canonical set

## Review Expectations

- the skill is discoverable from its description
- the package shape is valid
- the registry metadata is coherent
- helper scripts are scoped to the skill
- the generated catalog reflects the submitted skill state
- provenance is clear enough for curation
- STSS scan output is clean for the changed skill package
- attested skills can be verified with the configured public key set
- agent-generated submissions include enough evidence to judge whether the skill is actually worth curating
- the submission explains whether it is a new family, a challenger, a variant, or a replacement
