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

## Orchestrate every task

The main thread must delegate every compose, edit, or review to a fresh writer/editor subagent. It owns source selection,
user and objective decisions, the authoritative draft, the bounded source packet, orchestration, and user-facing
rendering. Send the subagent only the context required by the source and editorial contracts, with no unrelated inherited
context. The subagent owns prose and editorial judgment.

Use a new fresh writer/editor subagent for each revision. Provide only the current authoritative draft, accepted
decisions, relevant sources, and applicable invariants. Do not use same-context or sequential fallback for prose or
editorial work.

When `avoid-ai-writing` is available, send only the current edited draft to a sibling reviewer. Ask it to critique, not
rewrite, and return location, pattern, severity, `safe-fix` or `author-judgment`, rationale, and suggested direction.
Deduplicate findings and reject only objective conflicts with the shared invariants. Send substantive findings to a new
editor for reconciliation. Skip this optional specialist pass when unnecessary. Its absence never blocks the core
workflow.

If isolated delegation is unavailable or disabled, stop before composing, editing, or reviewing. Return a concise
capability error naming isolated writer/editor delegation as missing and telling the user how to enable subagents. For
Pi, state that the official subagent extension must be installed and enabled. Do not substitute main-thread editorial
work.

The writer/editor returns a machine-oriented result containing revised content, source-preservation status, safe
changes, material suggestions or questions, unresolved gaps, checks, and pending specialist-review status. The main
thread adopts the result as appropriate and renders it for the user.
