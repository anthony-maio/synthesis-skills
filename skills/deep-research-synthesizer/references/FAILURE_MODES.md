# Failure modes + mitigations (for 5-agent deep research)

This file is intentionally generic, but includes real-world failure patterns seen in “deep research” workflows.

## 1) Missing / malformed agent outputs
**Symptom:** synthesis step errors, or produces nonsense due to missing inputs.

Mitigation:
- enforce the Research Packet Contract (`AGENT_PACKET_CONTRACT.md`)
- validate packets with `scripts/validate_packets.py`
- if a packet is missing, synthesize anyway and mark “NO DATA”

## 2) Silent tool failures upstream
**Symptom:** sub-agents return empty “findings” but don’t say why.

Mitigation:
- require each agent to include `errors[]` and `run_log[]`
- bubble tool errors into the final report appendix verbatim

Example failure class:
- an MCP retrieval tool responds with an error while other tools still work
  - see: https://github.com/pieces-app/support/issues/747

## 3) Overly heterogeneous agent formats
**Symptom:** coordinator can’t reliably merge content because each agent wrote differently.

Mitigation:
- strict JSON header + mandatory headings
- deterministic merge step (`merge_packets.py`) before LLM synthesis

## 4) Contradictions get flattened into false certainty
**Symptom:** final report picks one claim and discards the other without notice.

Mitigation:
- contradictions are first-class in the packet schema
- final report must include a Contradictions/Uncertainties section

## 5) “Big synthesis prompt” exceeds context window / times out
**Symptom:** coordinator fails intermittently, often without a clear reason.

Mitigation:
- normalize + compress packets into a merged JSON artifact
- render a report skeleton and then fill section-by-section
- chunk synthesis (Executive Summary → Direct Answer → Findings → Recommendations)

## 6) Local service instability / backpressure
**Symptom:** internal HTTP calls fail (connection closed, timeouts) during heavy synthesis.

Mitigation:
- implement retries with exponential backoff
- limit payload sizes and chunk requests
- emit structured error logs (endpoint, duration, payload size)

Example failure class:
- connection closed before headers
  - see: https://github.com/pieces-app/support/issues/751
