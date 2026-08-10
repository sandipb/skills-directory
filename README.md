# Agent Toolkit

Reusable skills packaged as one plugin for Codex, ChatGPT Work, and Claude Code.

## Contents

- `grafana-loki`: Query and analyze Grafana Loki logs with LogQL.
- `fireworks-billing`: Export and summarize Fireworks AI billing usage metrics.
- `edit-technical-docs`: Edit, rewrite, restructure, or review existing technical documentation while preserving its
  technical meaning. `avoid-ai-writing` is an optional final pass.

## Install in Codex or ChatGPT Work

```bash
codex plugin marketplace add sandipb/agent-toolkit
codex plugin add sandipb-agents@sandipb-agents
```

Restart the app and start a new chat after installation. Plugins are available in Codex and ChatGPT Work, not ordinary
ChatGPT chat mode.

## Install in Claude Code

```bash
claude plugin marketplace add sandipb/agent-toolkit
claude plugin install sandipb-agents@sandipb-agents
```

The model can select technical editing when a request matches the skill. You can also invoke it explicitly with
`$edit-technical-docs` in Codex, `@edit-technical-docs` in ChatGPT Work, or
`/sandipb-agents:edit-technical-docs` in Claude Code.

## Repository layout

```text
skills/                           Canonical skills; read and edit these
plugins/codex/sandipb-agents/     Generated Codex package
plugins/claude/sandipb-agents/    Generated Claude package
.agents/plugins/marketplace.json  Codex marketplace
.claude-plugin/marketplace.json   Claude marketplace
AGENTS.md                         Canonical agent instructions
CLAUDE.md                         Symlink to AGENTS.md
```

### Why skill content is duplicated

The two plugin directories duplicate content from top-level `skills/`. Codex and Claude Code install self-contained
package directories, but they require different layouts and invocation metadata. Committed host copies let both
marketplaces install valid packages without relying on symlinks or paths outside the package boundary.

Read the top-level `skills/` directories to inspect the skills. Contributors should edit only those canonical files.
The plugin `skills/` directories are generated installation artifacts; CI rejects missing, stale, or manually changed
copies.

## Develop and validate

Follow `AGENTS.md`. In particular:

- edit only top-level canonical skills and regenerate host copies;
- update skill changelogs when behavior changes;
- validate changed skills and both plugin formats;
- never include credentials or private data;
- obtain approval before committing, pushing, or opening a pull request.

Run `task validate` before requesting review. Changes merge only through pull requests after the required validation
check passes. See [Owner setup](docs/owner-setup.md) for the GitHub UI configuration.

For local installation testing, replace `sandipb/agent-toolkit` in the marketplace commands with the absolute path to
your checkout.

## License

Apache License 2.0. See `LICENSE`.
