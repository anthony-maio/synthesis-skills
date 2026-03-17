# Research Packet Contract (required)

Each of the 5 research agents MUST output a *single* Markdown document that starts with a **JSON packet header**.

This is the contract that enables deterministic validation + reliable synthesis.

---

## Required structure

### 1) JSON packet header (first thing in the file)

The very first non-empty content must be a fenced JSON block:

```json
{
  "agent_id": "A1",
  "partition_strategy": "time-slice|source-slice|sub-question",
  "partition": "Describe this agent's scope (time window / sources / sub-question)",
  "user_question": "verbatim user question",
  "queries_run": [
    "query string 1",
    "query string 2"
  ],
  "sources": [
    {
      "source_id": "S1",
      "title": "Document title",
      "url": "https://...",
      "publisher": "who published it",
      "published_date": "YYYY-MM-DD or null",
      "retrieved_date": "YYYY-MM-DD",
      "excerpt": "1–3 sentence excerpt or key lines",
      "relevance": "high|medium|low"
    }
  ],
  "findings": [
    {
      "finding_id": "F1",
      "claim": "One atomic claim.",
      "evidence_source_ids": ["S1", "S3"],
      "confidence": "high|medium|low",
      "notes": "Short reasoning about why the evidence supports the claim."
    }
  ],
  "contradictions": [
    {
      "topic": "What conflicts?",
      "details": "Describe conflicting claims + which sources disagree."
    }
  ],
  "open_questions": [
    "What you still couldn't confirm"
  ],
  "errors": [
    {
      "stage": "search|fetch|parse|tool-call|other",
      "error": "Short summary",
      "raw": "Raw error text if available"
    }
  ],
  "run_log": [
    "YYYY-MM-DDThh:mm:ssZ - did X",
    "..."
  ]
}
```

**Hard requirements:**
- JSON must parse
- `agent_id` must be unique across the 5 packets
- Each `finding.evidence_source_ids` must reference actual `sources.source_id`
- If there were no errors, use `"errors": []`
- If no contradictions found, use `"contradictions": []`

### 2) Human narrative (after the JSON)
After the JSON header, include these headings:

- `## Key Findings` (bullets; each bullet references finding ids like `[F1]`)
- `## Notes / Interpretation` (short)
- `## Run Log` (repeat or summarize run_log; include tool failures)

---

## Why this contract exists
Without a strict contract:
- synthesis becomes guessy
- failures are silent
- contradictions get flattened
- you can’t trace claims to sources

This contract is optimized for:
- deterministic validation
- debuggable synthesis
- coherent final report assembly
