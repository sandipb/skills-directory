---
name: technical-docs
description: >-
  Compose, edit, or review work-oriented technical documentation from supplied authoritative context while preserving
  technical meaning and distinct information. Use for READMEs, runbooks, procedures, reports, design documents, API
  documentation, PR descriptions, commit messages, warnings, and code comments.
---

# Technical documentation

Use `technical-writing` as the shared discipline. Infer whether to compose, edit, or review from the request. Existing
prose is optional; every resulting claim must map to authoritative context already present or explicitly supplied.
Return a supportable partial draft plus author-judgment questions when information is missing. Do not research or inspect
unrelated sources to fill gaps.

## Preserve documentation

Preserve every distinct fact, relationship, condition, exception, reason, consequence, warning, risk, sequence, scope
limit, cross-reference, command, identifier, value, unit, technical term, requirement level, and certainty. Remove only
semantic duplication that carries no distinct information.

Use the project's structure. With no convention, add only enough organization for task completion and lookup. Treat
20-word procedural and 25-word descriptive sentences as review thresholds, not compliance limits. Prefer explicit
conditions, one operation per step, consistent terms, and controlled-language clarity without claiming ASD-STE100
compliance.

Apply safe language corrections inline. Return additions, examples, removal of distinct information, major
restructuring, changed emphasis, and unresolved ambiguity as author-judgment suggestions. Use native comments or
suggestions when practical; otherwise separate suggestions from revised prose. Omit empty suggestion sections.

## Orchestrate substantive work

When subagents are available and the artifact is substantive, have the main thread send only the bounded source packet
to a fresh writer/editor. Use a fresh editor for each revision. The main thread owns sources, the authoritative draft,
user decisions, and objective invariant conflicts; the editor owns prose and editorial judgment.

When `avoid-ai-writing` is available, send only the current edited draft to a sibling reviewer. Ask it to critique, not
rewrite, and return location, pattern, severity, `safe-fix` or `author-judgment`, rationale, and suggested direction.
Deduplicate findings and reject only objective conflicts with the shared invariants. Send substantive findings to a
fresh editor for reconciliation. Skip this specialist pass for tiny artifacts. If unavailable, continue and report the
omission briefly.

Prefer sibling agents; nested delegation is optional. Without subagents, run writer, specialist review, and
reconciliation as explicit sequential phases and acknowledge weaker context isolation.

Return a machine-oriented result containing revised content, source-preservation status, safe changes, material
suggestions or questions, unresolved gaps, checks, and pending specialist-review status. The main thread renders the
user-facing result.
