---
name: tech-blog
description: >-
  Compose, edit, or review reader-oriented technical articles from supplied authoritative context. Use for technical
  blog posts and explanatory articles that may need stronger restructuring, pacing, explanation, or information
  selection than work-oriented documentation permits.
---

# Technical blog

Use `technical-writing` as the shared discipline. Infer composition, editing, or review from the request. Work from an
existing draft or authoritative context already present or explicitly supplied. Do not research or invent missing
facts, causes, evidence, motivations, examples, analogies, risks, or conclusions.

Preserve support for technical claims, terminology, certainty, conditions, causality, commands, identifiers, and
values. Optimize for understanding and sustained reading. You may reorder, restructure, pace, and select information
more freely than `technical-docs`, but return unsupported additions, examples, analogies, removal of material claims,
changed emphasis, and unresolved gaps as author-judgment suggestions. Produce a supportable partial draft when context
is incomplete. Omit empty suggestion sections.

## Orchestrate every task

The main thread must delegate every compose, edit, or review to a fresh writer/editor subagent. It owns source selection,
user and objective decisions, the authoritative draft, the bounded source packet, orchestration, and user-facing
rendering. Send the subagent only the current draft and authoritative context required by the source and editorial
contracts, with no unrelated inherited context. The subagent owns prose and editorial judgment.

Use a new fresh writer/editor subagent for each revision. Do not use same-context or sequential fallback for prose or
editorial work.

When `avoid-ai-writing` is available, optionally send only the current edited draft to a sibling reviewer for structured
critique, not rewriting. Deduplicate its findings, reject only objective conflicts with the shared invariants, and send
substantive findings to a new editor for reconciliation. Skip this specialist pass when unnecessary. Its absence never
blocks the core workflow.

If isolated delegation is unavailable or disabled, stop before composing, editing, or reviewing. Return a concise
capability error naming isolated writer/editor delegation as missing and telling the user how to enable subagents. For
Pi, state that the official subagent extension must be installed and enabled. Do not substitute main-thread editorial
work.

The writer/editor returns revised content, source-support status, safe changes, material suggestions or questions,
unresolved gaps, checks, and pending specialist-review status in a machine-oriented result for the main thread to
render.
