# Seeding The Registry

Start small. The goal of the first seed is not breadth. It is trustable shape.

## Founding Seed Set

Use three sources only for the first pass:

1. high-signal skills you already use repeatedly
2. skills synthesized locally that solved real work and deserve promotion
3. carefully mirrored external skills with clear provenance

Aim for 10 to 20 initial curated skills, not hundreds.

## Suggested First Categories

- repository inspection and codebase orientation
- testing and review workflows
- documentation and release support
- common data/file handling utilities
- one or two integration-heavy skills with helper scripts

## Admission Rule

Every founding skill should satisfy all of these:

- the trigger is easy for an agent to discover
- `SKILL.md` is coherent without extra narration
- helper code is minimal and local to the package
- provenance is documented in the PR
- the package passes `validate_repo.py` and lands in the generated catalog

## Practical Bootstrap Flow

1. Pick a candidate skill from an existing repo or local agent skill root.
2. Copy it into `skills/<name>/`.
3. Trim front matter to `name` and `description`.
4. Remove empty directories and nonessential assets.
5. Regenerate the catalog.
6. Open a PR with provenance, intended hosts, and why the skill belongs in the canonical set.

## What Not To Seed Yet

- huge reference-only skills with weak triggers
- one-off personal workflow notes
- duplicate variants of the same skill
- skills with unclear licensing or provenance

The first seed should define quality expectations for everything that follows.
