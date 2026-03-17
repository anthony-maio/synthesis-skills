# Deep Research Report Template (Markdown)

Use this template for the final synthesized report.

---

# {{TITLE}}

## Executive Summary
- Bullet 1
- Bullet 2
- Bullet 3
- Bullet 4
- Bullet 5

## Direct Answer
Write 2–6 paragraphs that answer the user’s question directly.
- Avoid meandering background.
- Make the answer falsifiable and specific where possible.

## Key Findings
Group findings into 3–7 clusters. For each cluster:
- 2–6 bullets
- each bullet references finding ids like `[A2:F7]` and source ids like `(S3, S8)`

Example bullet:
- The system fails under load due to backpressure at the MCP boundary. [A4:F2] (S5)

## Evidence & Citations
A compact table mapping key sources:

| Source ID | Publisher | Title | Published | Why it matters |
|---|---|---|---:|---|
| S1 | ... | ... | 2025-... | ... |

## Contradictions / Uncertainties
- List contradictions found across agent packets
- If there are none, explicitly say “No material contradictions detected.”

## Recommendations
Prioritize:
1. High impact / low effort
2. High impact / high effort
3. Low impact items (optional)

For each recommendation:
- what to do
- why it matters (tie to findings)
- how to validate success (metric / test)

## Limitations
- Missing agent packets?
- Weak sources?
- Any tool failures?
- Any unresolved open questions?

## Appendix A — Agent Run Logs
Include each agent’s run log (or a summarized version).

## Appendix B — Raw Findings (optional)
If you need full traceability, include an enumerated list:
- `[A1:F1] claim … evidence …`
