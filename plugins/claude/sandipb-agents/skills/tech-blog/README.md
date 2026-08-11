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

For substantive drafts, a fresh editor subagent is preferred. An optional `avoid-ai-writing` reviewer critiques only
the current draft. Hosts without subagents run the phases sequentially with weaker context isolation; missing specialist
review does not block writing.
