#!/usr/bin/env python3
"""
validate_packets.py

Validates that research agent outputs conform to the Research Packet Contract.

Usage:
  python scripts/validate_packets.py --in packets/

The validator expects each packet file to:
  - start with a fenced ```json block
  - contain a JSON object with required keys (agent_id, sources, findings, run_log, etc.)
  - ensure findings evidence_source_ids reference sources.source_id

No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass
class ValidationError:
    file: str
    message: str


def _extract_json_block(md: str) -> Dict[str, Any]:
    m = JSON_BLOCK_RE.search(md.strip())
    if not m:
        raise ValueError("missing fenced ```json ... ``` block")
    raw = m.group(1)
    return json.loads(raw)


def _validate_packet(obj: Dict[str, Any], filename: str) -> List[ValidationError]:
    errs: List[ValidationError] = []

    def req(key: str, t: type) -> Any:
        if key not in obj:
            errs.append(ValidationError(filename, f"missing required key: {key}"))
            return None
        v = obj[key]
        if not isinstance(v, t):
            errs.append(ValidationError(filename, f"key '{key}' must be {t.__name__}, got {type(v).__name__}"))
            return None
        return v

    agent_id = req("agent_id", str)
    _ = req("partition_strategy", str)
    _ = req("partition", str)
    _ = req("user_question", str)
    queries = req("queries_run", list)
    sources = req("sources", list)
    findings = req("findings", list)
    contradictions = req("contradictions", list)
    open_questions = req("open_questions", list)
    errors = req("errors", list)
    run_log = req("run_log", list)

    if isinstance(queries, list) and not all(isinstance(x, str) for x in queries):
        errs.append(ValidationError(filename, "queries_run must be a list[str]"))

    src_ids = set()
    if isinstance(sources, list):
        for i, s in enumerate(sources):
            if not isinstance(s, dict):
                errs.append(ValidationError(filename, f"sources[{i}] must be an object"))
                continue
            sid = s.get("source_id")
            if not isinstance(sid, str) or not sid:
                errs.append(ValidationError(filename, f"sources[{i}].source_id must be non-empty string"))
                continue
            if sid in src_ids:
                errs.append(ValidationError(filename, f"duplicate source_id: {sid}"))
            src_ids.add(sid)

    if isinstance(findings, list):
        for i, f in enumerate(findings):
            if not isinstance(f, dict):
                errs.append(ValidationError(filename, f"findings[{i}] must be an object"))
                continue
            claim = f.get("claim")
            if not isinstance(claim, str) or not claim.strip():
                errs.append(ValidationError(filename, f"findings[{i}].claim must be non-empty string"))
            evid = f.get("evidence_source_ids")
            if not isinstance(evid, list) or not all(isinstance(x, str) for x in evid):
                errs.append(ValidationError(filename, f"findings[{i}].evidence_source_ids must be list[str]"))
                continue
            missing = [x for x in evid if x not in src_ids]
            if missing:
                errs.append(ValidationError(filename, f"findings[{i}] references unknown source_id(s): {missing}"))

    if isinstance(run_log, list) and not all(isinstance(x, str) for x in run_log):
        errs.append(ValidationError(filename, "run_log must be a list[str]"))

    if isinstance(errors, list):
        for i, e in enumerate(errors):
            if not isinstance(e, dict):
                errs.append(ValidationError(filename, f"errors[{i}] must be an object"))
                continue
            if "stage" not in e or "error" not in e:
                errs.append(ValidationError(filename, f"errors[{i}] must include 'stage' and 'error'"))

    if agent_id is not None and not agent_id.strip():
        errs.append(ValidationError(filename, "agent_id must be non-empty"))

    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True, help="Directory containing agent packet markdown files.")
    args = ap.parse_args()

    indir = Path(args.indir)
    if not indir.exists() or not indir.is_dir():
        print(f"Not a directory: {indir}")
        return 2

    files = sorted([p for p in indir.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".markdown"}])
    if not files:
        print(f"No .md files found in {indir}")
        return 2

    all_errs: List[ValidationError] = []
    agent_ids: List[str] = []

    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        try:
            obj = _extract_json_block(text)
        except Exception as e:
            all_errs.append(ValidationError(f.name, f"JSON header parse failed: {e}"))
            continue

        if isinstance(obj, dict) and isinstance(obj.get("agent_id"), str):
            agent_ids.append(obj["agent_id"])

        all_errs.extend(_validate_packet(obj if isinstance(obj, dict) else {}, f.name))

    # agent_id uniqueness across files
    seen = set()
    dups = set()
    for aid in agent_ids:
        if aid in seen:
            dups.add(aid)
        seen.add(aid)
    for d in sorted(dups):
        all_errs.append(ValidationError("<all>", f"duplicate agent_id across packets: {d}"))

    if all_errs:
        print("VALIDATION FAILED\n")
        for e in all_errs:
            print(f"- {e.file}: {e.message}")
        print("\nFix the above and re-run validation.")
        return 1

    print("VALIDATION OK")
    print(f"Packets validated: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
