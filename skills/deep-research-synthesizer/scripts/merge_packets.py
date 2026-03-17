#!/usr/bin/env python3
"""
merge_packets.py

Merge validated agent research packets into a single normalized JSON artifact.

Usage:
  python scripts/merge_packets.py --in packets/ --out merged.json

Behavior:
- Extracts the JSON header from each packet file
- Prefixes source_ids and finding_ids with agent_id to avoid collisions:
    S1 -> A3:S1
    F2 -> A3:F2
- Rewrites evidence_source_ids to the prefixed ids
- Produces a merged JSON with flattened sources/findings and per-agent run logs

No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json_block(md: str) -> Dict[str, Any]:
    m = JSON_BLOCK_RE.search(md.strip())
    if not m:
        raise ValueError("missing fenced ```json ... ``` block")
    raw = m.group(1)
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("JSON header must be an object")
    return obj


def _prefix_ids(packet: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = str(packet.get("agent_id") or "").strip() or "UNKNOWN"

    # Prefix sources
    src_map: Dict[str, str] = {}
    sources = packet.get("sources") or []
    if isinstance(sources, list):
        for s in sources:
            if isinstance(s, dict) and isinstance(s.get("source_id"), str):
                old = s["source_id"]
                new = f"{agent_id}:{old}"
                src_map[old] = new
                s["source_id"] = new

    # Prefix findings and rewrite evidence_source_ids
    findings = packet.get("findings") or []
    if isinstance(findings, list):
        for f in findings:
            if not isinstance(f, dict):
                continue
            if isinstance(f.get("finding_id"), str):
                f["finding_id"] = f"{agent_id}:{f['finding_id']}"
            evid = f.get("evidence_source_ids")
            if isinstance(evid, list):
                f["evidence_source_ids"] = [src_map.get(x, f"{agent_id}:{x}") for x in evid]

    packet["agent_id"] = agent_id
    return packet


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True, help="Directory containing agent packet markdown files.")
    ap.add_argument("--out", dest="out", required=True, help="Output JSON file path.")
    args = ap.parse_args()

    indir = Path(args.indir)
    out = Path(args.out)

    files = sorted([p for p in indir.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".markdown"}])
    if not files:
        print(f"No packet files found in {indir}")
        return 2

    packets: List[Dict[str, Any]] = []
    for f in files:
        md = f.read_text(encoding="utf-8", errors="replace")
        pkt = _extract_json_block(md)
        packets.append(_prefix_ids(pkt))

    user_question = packets[0].get("user_question") if packets else ""

    merged_sources: List[Dict[str, Any]] = []
    merged_findings: List[Dict[str, Any]] = []
    merged_contradictions: List[Dict[str, Any]] = []
    merged_open_questions: List[str] = []

    for pkt in packets:
        if isinstance(pkt.get("sources"), list):
            merged_sources.extend([s for s in pkt["sources"] if isinstance(s, dict)])
        if isinstance(pkt.get("findings"), list):
            merged_findings.extend([f for f in pkt["findings"] if isinstance(f, dict)])
        if isinstance(pkt.get("contradictions"), list):
            merged_contradictions.extend([c for c in pkt["contradictions"] if isinstance(c, dict)])
        if isinstance(pkt.get("open_questions"), list):
            merged_open_questions.extend([q for q in pkt["open_questions"] if isinstance(q, str)])

    merged = {
        "user_question": user_question,
        "packet_count": len(packets),
        "packets": packets,
        "sources": merged_sources,
        "findings": merged_findings,
        "contradictions": merged_contradictions,
        "open_questions": merged_open_questions,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote merged JSON: {out}")
    print(f"Packets: {len(packets)} | Sources: {len(merged_sources)} | Findings: {len(merged_findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
