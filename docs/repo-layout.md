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
├── REGISTRY.json    # required governance metadata
├── attestation.json # optional STSS output tracked in the catalog
├── scripts/        # optional
├── assets/         # optional
├── references/     # optional
└── agents/         # optional
```

`PROVENANCE.json` records origin, authorship, and licensing context without bloating `SKILL.md`. `REGISTRY.json` records lifecycle stage, trust level, and capability family. `attestation.json` is optional and records STSS scan or signing output for the exact registry snapshot when available. Machine-readable search metadata, including governance and STSS status, is generated into the catalog.
