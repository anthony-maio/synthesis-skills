#!/usr/bin/env python3
"""
render_report_skeleton.py

Render a Markdown report skeleton from a merged research JSON artifact.

Usage:
  python scripts/render_report_skeleton.py --in merged.json --out report.md

This is deterministic scaffolding: it does NOT attempt to write the final narrative.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _safe(s: str, n: int = 80) -> str:
    s = " ".join((s or "").strip().split())
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)

    merged = json.loads(inp.read_text(encoding="utf-8", errors="replace"))
    question = merged.get("user_question", "")
    findings: List[Dict[str, Any]] = merged.get("findings", []) if isinstance(merged.get("findings"), list) else []
    sources: List[Dict[str, Any]] = merged.get("sources", []) if isinstance(merged.get("sources"), list) else []
    packets: List[Dict[str, Any]] = merged.get("packets", []) if isinstance(merged.get("packets"), list) else []

    title = _safe(question, 60) or "Deep Research Report"

    # Build source table rows
    source_rows = []
    for s in sources:
        if not isinstance(s, dict):
            continue
        sid = s.get("source_id", "")
        pub = s.get("publisher", "")
        t = _safe(str(s.get("title", "")), 60)
        pd = s.get("published_date") or ""
        why = _safe(str(s.get("relevance", "")), 20)
        source_rows.append(f"| {sid} | {pub} | {t} | {pd} | {why} |")

    # Build findings bullets
    finding_bullets = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        fid = f.get("finding_id", "")
        claim = _safe(str(f.get("claim", "")), 140)
        evid = f.get("evidence_source_ids", [])
        if isinstance(evid, list):
            evid_str = ", ".join(str(x) for x in evid[:5])
            if len(evid) > 5:
                evid_str += ", …"
        else:
            evid_str = ""
        finding_bullets.append(f"- {claim} [{fid}] ({evid_str})")

    # Agent run logs
    runlog_sections = []
    for pkt in packets:
        if not isinstance(pkt, dict):
            continue
        aid = pkt.get("agent_id", "UNKNOWN")
        log = pkt.get("run_log", [])
        if not isinstance(log, list):
            log = []
        log_lines = "\n".join(f"- {x}" for x in log[:50] if isinstance(x, str))
        runlog_sections.append(f"### {aid}\n{log_lines}\n")

    md = []
    md.append(f"# {title}\n")
    md.append("## Executive Summary\n")
    md.append("- (fill)\n- (fill)\n- (fill)\n- (fill)\n- (fill)\n")
    md.append("## Direct Answer\n")
    md.append("(write 2–6 paragraphs answering the question)\n")
    md.append("## Key Findings\n")
    md.extend([b + "\n" for b in finding_bullets] or ["- (no findings)\n"])
    md.append("\n## Evidence & Citations\n")
    md.append("| Source ID | Publisher | Title | Published | Relevance |\n")
    md.append("|---|---|---|---:|---|\n")
    md.extend([r + "\n" for r in source_rows] or ["| (none) | | | | |\n"])
    md.append("\n## Contradictions / Uncertainties\n")
    md.append("- (fill)\n")
    md.append("\n## Recommendations\n")
    md.append("1. (fill)\n2. (fill)\n3. (fill)\n")
    md.append("\n## Limitations\n")
    md.append("- (fill)\n")
    md.append("\n## Appendix A — Agent Run Logs\n\n")
    md.extend([s + "\n" for s in runlog_sections] or ["(none)\n"])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(md), encoding="utf-8")
    print(f"Wrote report skeleton: {out}")
    print(f"Findings: {len(findings)} | Sources: {len(sources)} | Packets: {len(packets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
