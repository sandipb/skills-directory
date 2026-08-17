# Technical blog

`tech-blog` composes, edits, or reviews reader-oriented technical articles. It shares technical precision rules with
`technical-docs` but allows stronger changes to structure, pacing, explanation, and information selection.

Use an existing rough draft or research already gathered by the main agent. The skill does not research independently.
It preserves support for technical claims and returns proposed examples, analogies, major restructuring, material
removals, changed emphasis, and missing context as suggestions rather than silently inventing or deciding them.

Examples:

- `$tech-blog Turn this rough draft into a tighter article; list major structural suggestions separately.`
- `Write a technical article from these researched notes and flag unsupported gaps.`
- `Review this post for pacing and formulaic AI-writing patterns without rewriting it.`

Every compose, edit, or review must use an isolated fresh writer/editor subagent, including small drafts. The main agent
selects sources, records decisions, maintains the authoritative draft, prepares the bounded source packet, coordinates
the work, and renders the result. Each revision uses a new editor with no unrelated inherited context. If isolated
delegation is unavailable, the skill stops before editorial work and explains how to enable subagents; Pi requires its
official subagent extension. An optional `avoid-ai-writing` reviewer may critique the current draft, but its absence
never blocks writing.
