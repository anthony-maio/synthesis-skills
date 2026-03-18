# Repository Layout

The canonical Synthesis skill repo stays deliberately flat.

## Top Level

- `skills/`: one directory per curated skill package
- `catalog/skills.json`: generated search index consumed by Synthesis runtimes
- `scripts/`: standard-library Python scripts for validation and catalog generation
- `tests/`: regression coverage for registry automation

## Skill Directory Contract

Each skill package must look like:

```text
skills/<skill-name>/
├── SKILL.md
├── PROVENANCE.json
├── attestation.json # optional STSS output tracked in the catalog
├── scripts/        # optional
├── assets/         # optional
├── references/     # optional
└── agents/         # optional
```

`PROVENANCE.json` records origin, authorship, and licensing context without bloating `SKILL.md`. `attestation.json` is optional and records STSS scan or signing output when available. Machine-readable search metadata, including STSS status, is generated into the catalog.
