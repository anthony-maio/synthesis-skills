---
name: csv-parsing-basics
description: Use when parsing CSV files, checking delimiters, or inspecting column headers before heavier data work.
---

# CSV Parsing Basics

## Overview

Use this skill to inspect a CSV file quickly before deeper analysis or transformation work. It helps an agent confirm delimiter, header shape, and a few example rows without inventing a larger pipeline first.

## Workflow

1. Confirm the file path and whether the user wants a quick inspection or a full transform.
2. Inspect a small sample before loading the whole file into a heavier toolchain.
3. Report delimiter, detected headers, row count sampled, and obvious data quality issues.
4. Escalate to a richer parser only if the quick pass reveals inconsistent structure.

## Quick Checks

- header row present or missing
- delimiter looks like comma, tab, pipe, or semicolon
- first few rows have stable column counts
- obvious blank or malformed cells

## Helper Script

Use `scripts/inspect_csv.py` for a fast structural pass when the workspace contains a local CSV file.
