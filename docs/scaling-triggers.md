# Scaling Triggers for lands.ai

## Principle
Microservices are not a default target. Service extraction must be justified by measurable constraints.

## Trigger Categories

### 1) Performance Trigger
Extract a service only if both are true over sustained periods:
- Interactive query latency breaches agreed SLOs
- Root cause is an independently scalable workload (for example document ingestion)

### 2) Team/Ownership Trigger
Extract when:
- Distinct teams need autonomous deploy/release cycles
- Shared deployment causes recurring coordination bottlenecks

### 3) Compliance/Regional Trigger
Extract or region-split when:
- Legal or contractual requirements mandate runtime/data isolation
- Country-specific policies require separate processing boundaries

### 4) Reliability Trigger
Extract when:
- A failure domain repeatedly impacts unrelated user flows
- Isolating a component materially reduces blast radius

## Recommended Extraction Sequence

1. Document ingestion/OCR worker service
2. Region-specific runtime split (same codebase, isolated deployments)
3. Admin/control-plane split from public query path

## Anti-Patterns to Avoid Early

- Premature Kubernetes/service-mesh adoption
- Event streaming platform without demonstrated need
- Multiple databases per domain before clear data ownership boundaries

## Decision Checklist

Before any extraction, answer yes to all:
- Is there a measurable pain point with evidence?
- Can optimization inside monolith not solve it?
- Is ownership boundary stable for at least one quarter?
- Does extraction improve reliability or compliance materially?

If any answer is no, keep the module inside the monolith.