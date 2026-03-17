# QA Checklist (deterministic gates)

Before you finalize the synthesized report, confirm:

## Structure
- [ ] Report has all required top-level sections from `REPORT_TEMPLATE.md`
- [ ] Executive summary is 5–10 bullets (not a wall of text)
- [ ] Direct Answer exists and actually answers the question

## Traceability
- [ ] Every major claim maps to at least 1 source id
- [ ] Findings reference agent+finding ids (e.g., `[A3:F4]`) somewhere in the report
- [ ] No “floating” citations (source ids that don’t exist)

## Deduplication
- [ ] The same finding isn’t repeated across clusters
- [ ] Similar findings are merged into one stronger statement with multiple sources

## Contradictions / Uncertainty
- [ ] Contradictions are explicitly called out
- [ ] Uncertain areas are labeled; no invented certainty

## Robustness / Observability
- [ ] Missing agent packets are explicitly listed in Limitations
- [ ] Tool failures are included in Appendix A
- [ ] If the report is partial, it includes next-step follow-up tasks

## Style
- [ ] Markdown headings are consistent
- [ ] Bullets are scannable
- [ ] No giant pasted logs in main body (move to appendix if needed)
