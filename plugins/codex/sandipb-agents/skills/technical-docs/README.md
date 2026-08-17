# Technical documentation

`technical-docs` composes, edits, or reviews work-oriented prose. State the outcome naturally; no mode name is required.

The skill writes only from existing or supplied authoritative context. It applies certain grammar, clarity,
terminology, and concision fixes inline while preserving distinct technical information. Additions, examples, removals,
major restructuring, changed emphasis, and ambiguity are returned as editorial suggestions or questions.
Accept or reject those items in the next reply. The main agent combines your decisions with the current draft and sends
that bounded context to a fresh editor for the next revision.

Every compose, edit, or review must use an isolated fresh writer/editor subagent, including small artifacts. The main
agent selects sources, records decisions, maintains the authoritative draft, prepares the bounded source packet,
coordinates the work, and renders the result. Each revision uses a new editor with no unrelated inherited context. If
isolated delegation is unavailable, the skill stops before editorial work and explains how to enable subagents; Pi
requires its official subagent extension. An optional `avoid-ai-writing` reviewer may critique the current draft, but
its absence never blocks the workflow.

Examples:

- `$technical-docs Compose a runbook from these approved investigation notes.`
- `Edit this README for clarity without removing requirements or examples.`
- `Review this incident report and return findings without rewriting it.`
- `Draft a PR description from this diff summary and test results.`
- `Tighten this procedure while preserving commands, stop conditions, and rollback steps.`

The skill follows user instructions, repository guidance, nearby examples, and the existing document before adding
minimal generic structure. It supports reports, design documents, API documentation, commit messages, warnings, and
other technical prose without imposing artifact-specific templates.
