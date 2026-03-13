# Compliance and Audit Guidance

## Purpose
Because lands.ai operates in a legal-information context, every answer must be traceable to source evidence.

## Minimum Audit Record Per Query

Capture and persist:
- Request ID and timestamp
- User query (or redacted variant where needed)
- Retrieved source IDs/chunk IDs and rank scores
- Model/provider identifier and version
- Final response hash and citation list
- Processing durations and error status

## Citation Policy

- Substantive legal/process claims require at least one source citation.
- Citation references must map to stored chunk provenance.
- If no reliable evidence exists, do not fabricate an answer.

## Response Safety Policy

For low-confidence or missing evidence:
- Return a constrained response indicating uncertainty
- Suggest escalation path (human legal professional or official office)
- Preserve uncertainty reason in audit events

## Data Handling Notes

- Keep source provenance immutable once published.
- Version knowledge updates; do not overwrite without revision history.
- Separate operational logs from legal audit events.

## Operational Controls

- Enforce schema validation on responses before returning to user.
- Add periodic integrity checks between citations and stored source chunks.
- Maintain provider outage/fallback logs for post-incident review.

## Review Cadence

- Weekly: citation integrity and ingestion quality checks
- Monthly: audit schema and retention policy review
- Quarterly: legal-content update process review for policy changes