# Synthesis Skills

Canonical curated skill repository for Synthesis.

This repo is the public review and distribution layer for skill-first self-extension. It keeps the registry model simple:

1. Skills live as normal directories under `skills/`.
2. Metadata is derived from `SKILL.md` and package structure.
3. `catalog/skills.json` is generated for machine search.
4. STSS scans every changed skill in CI, and optional attestations are tracked in the catalog.
5. Pull requests are the curation and trust-promotion path.

## Repository Layout

```text
synthesis-skills/
├── skills/                  # Curated skill packages
├── catalog/                 # Generated machine-readable search metadata
├── scripts/                 # Validation and catalog generation
├── tests/                   # Registry automation tests
└── .github/                 # CI and contribution templates
```

## Skill Package Rules

- Each skill lives at `skills/<skill-name>/`.
- Each skill must include `SKILL.md`.
- Each skill must include `PROVENANCE.json`.
- Each skill may include `attestation.json` from STSS.
- Optional directories are `scripts/`, `assets/`, `references/`, and `agents/`.
- Skill front matter is intentionally small: `name` and `description`.
- `description` must start with `Use when`.

## Local Workflow

```bash
python scripts/validate_repo.py
python scripts/build_catalog.py
pytest -q
```

To run the STSS gate locally before a PR:

```bash
npm install -g stss@0.4.3
python scripts/run_stss_gate.py --base origin/main --head HEAD
```

To verify that the checked-in catalog is current:

```bash
python scripts/build_catalog.py --check
```

## Governance Model

- `UNTRUSTED`: local drafts in agent environments, not curated here yet
- `PROBATION`: proposed in an open PR or being prepared for review
- `TRUSTED`: merged curated skills in this repository
- `VERIFIED`: reserved for system or explicitly elevated skills

This repository primarily stores curated `TRUSTED` skills plus the automation needed to review new submissions.

## STSS Tracking

- CI runs `stss scan` against every changed skill directory in a PR or push.
- `attestation.json` is optional, but when present CI also runs `stss verify`.
- `catalog/skills.json` records whether a skill has an attestation plus its signing and policy metadata.
- Verification keys can be supplied through `STSS_PUBLIC_KEYS_JSON` or `STSS_PUBLIC_KEY` in GitHub Actions secrets.

## Submission Path

1. Open a PR that adds or updates a skill under `skills/`.
2. Run validation and regenerate the catalog.
3. Include `PROVENANCE.json`, intended host agents, and any helper scripts in the PR.
4. Let CI and review decide whether the skill should merge.

More detail lives in [docs/submitting-skills.md](docs/submitting-skills.md).

## Seeding

If you are bootstrapping the first curated set, use [docs/seeding.md](docs/seeding.md). The short version is to start with a small founding set of high-signal skills, keep provenance explicit, and treat the first 10 to 20 merged skills as the quality bar for the registry.
