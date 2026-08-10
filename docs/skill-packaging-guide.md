# Skill authoring and cross-host packaging

This repository keeps one source for each workflow while remaining installable in Codex, ChatGPT
Work, and Claude Code. Real canonical skills live at the repository root. A deterministic script
creates committed, host-specific plugin packages.

## Canonical layout

```text
.
├── skills/                          # canonical skill directories
│   └── <skill>/
│       ├── SKILL.md
│       ├── agents/openai.yaml      # optional Codex UI/policy metadata
│       ├── references/             # optional disclosed detail
│       └── scripts/                # optional deterministic helpers
├── plugins/
│   ├── codex/sandipb-agents/        # generated skills plus Codex manifest
│   └── claude/sandipb-agents/       # generated skills plus Claude manifest
├── scripts/sync_plugin_skills.py
├── Taskfile.yml
├── .agents/plugins/marketplace.json
└── .claude-plugin/marketplace.json
```

OpenAI defines a skill as `SKILL.md` plus optional `agents/openai.yaml`, scripts, references, and
assets. Its current authoring guidance permits only `name` and `description` in portable `SKILL.md`
frontmatter and recommends `agents/openai.yaml` for Codex-facing UI and invocation policy
([OpenAI skill creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)).
Claude keeps `.claude-plugin/plugin.json` separate from components and permits explicit skill paths
([Claude plugin structure](https://code.claude.com/docs/en/plugins)).

Each host installs a self-contained generated package. Keep drafts, retired skills, and private
material outside canonical `skills/` because every canonical skill is packaged. Codex accepts one
skills path and discovers `SKILL.md` files recursively beneath it. A real-world packaging ADR
documents that Codex rejects skill arrays and cached installs drop symlinked skill entries
([mattpocock packaging ADR](https://github.com/mattpocock/skills/blob/main/.agents/adr/0002-ship-as-a-claude-code-plugin.md)).

## Host manifests are separate

The skill content is portable; plugin catalogs are not.

- Codex uses `.codex-plugin/plugin.json` and a marketplace at `.agents/plugins/marketplace.json`.
  Its manifest `skills` field is a single relative path string. Keep the folder name, manifest name,
  and marketplace entry aligned; use strict semantic versions; include only components that exist
  ([OpenAI plugin creator](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/SKILL.md),
  [OpenAI manifest and marketplace specification](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md)).
- Claude uses `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Its manifest may
  select skills with a string or array, and plugin skills are invoked under the plugin namespace. A
  marketplace entry must provide `name` and `source`; when `version` is present, bump it for every
  released update ([Claude plugin reference](https://code.claude.com/docs/en/plugins-reference),
  [Claude marketplace reference](https://code.claude.com/docs/en/plugin-marketplaces)).

Do not attempt one manifest that satisfies both schemas. Keep shared identity fields synchronized,
then validate each host independently.

## Cache and path rules

Treat the plugin directory as the installation boundary. Claude copies marketplace plugins into
`~/.claude/plugins/cache`, so installed components cannot depend on `../` paths outside the plugin
([Claude marketplace reference](https://code.claude.com/docs/en/plugin-marketplaces)). Codex also
installs into a cache; tested symlinked skill collections were dropped during installation
([mattpocock packaging ADR](https://github.com/mattpocock/skills/blob/main/.agents/adr/0002-ship-as-a-claude-code-plugin.md)).

Therefore:

- Keep every runtime dependency inside its canonical skill directory.
- Edit real canonical directories under top-level `skills/` only.
- Commit generated host copies. Do not use symlinks in a plugin package.
- Use relative links only between files that are all inside the plugin boundary.
- Never reference a separately installed skill as a hard dependency. Bundle the dependency or
  degrade explicitly and safely.

## Portable skill metadata

Use this common denominator in canonical skills:

```yaml
---
name: lowercase-kebab-case
description: What the skill does and the concrete situations that should trigger it.
---
```

Keep host behavior out of this block. Codex uses `name` and `description` for discovery and stores
UI data such as `display_name`, `short_description`, `default_prompt`, and
`policy.allow_implicit_invocation` in `agents/openai.yaml`
([OpenAI skill creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)).
Claude accepts additional frontmatter such as `disable-model-invocation`, `user-invocable`,
`allowed-tools`, and `context`, but those fields are not part of the portable Codex subset
([Claude skills reference](https://code.claude.com/docs/en/skills)).

Write descriptions for model selection, not for users browsing a marketplace. Put what the skill
does and distinct trigger branches in the description; put execution instructions in the body. Keep
product invocation syntax (`$skill`, `@skill`, `/plugin:skill`) in installation documentation, not
canonical discovery metadata.

## Invocation controls

Manual-only invocation has no single portable metadata switch:

- Codex: set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`
  ([OpenAI `openai.yaml` reference](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/references/openai_yaml.md)).
- Claude: set `disable-model-invocation: true` in skill frontmatter; this removes the description
  from model context until the user invokes the skill
  ([Claude skills reference](https://code.claude.com/docs/en/skills)).

Default to model invocation when acceptable. The technical-editing skill uses that default, so its
Codex metadata omits `policy.allow_implicit_invocation` and its Claude frontmatter omits
`disable-model-invocation`. For a future manual-only skill, add its name to
`CLAUDE_MANUAL_ONLY_SKILLS` in `scripts/sync_plugin_skills.py` and set its Codex policy in
`agents/openai.yaml`. The packaging script then adds Claude's host-specific field only to the
generated Claude copy while keeping the canonical skill portable.

With no skills currently configured as manual-only, the packaging script copies the same portable
skill to both hosts:

```text
skills/edit-technical-docs/SKILL.md
plugins/claude/sandipb-agents/skills/edit-technical-docs/SKILL.md
```

The sync check rejects differences other than configured host-specific metadata, so substantive
instructions remain canonical.

## Writing and maintaining strong skills

Optimize for predictable process, not identical prose. A skill should contain only instructions that
change agent behavior.

1. Give every ordered step a checkable completion condition.
2. Keep common-path actions in `SKILL.md`; move branch-specific detail to directly linked
   references.
3. Keep a concept's definition, rules, and caveats together.
4. Split only for a distinct invocation branch or when later steps cause premature completion.
5. Keep every meaning in one authoritative place; remove duplication, stale sediment, no-op
   guidance, and unnecessary negation.
6. Prefer deterministic scripts for repeated fragile transformations; run them during validation.
7. Forward-test material revisions with fresh agents on realistic prompts.

These principles follow OpenAI's guidance on concise skills, progressive disclosure, deterministic
scripts, validation, and forward tests
([OpenAI skill creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md))
and the `writing-great-skills` model of checkable completion criteria, information hierarchy,
pruning, and invocation trade-offs
([mattpocock writing-great-skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-great-skills/SKILL.md)).

For vendor-domain skills, keep only differentiated operational knowledge. Grafana's maintained Loki
skill already covers core LogQL syntax, architecture, ingestion methods, structured metadata, and
Logs Drilldown; compare local Loki guidance against that baseline and retain local content only when
it adds a workflow, environment constraint, or tested detail the upstream skill lacks
([Grafana Loki skill](https://github.com/grafana/skills/blob/main/skills/grafana-lgtm/loki/SKILL.md)).

### Why retain the local Loki skill

Grafana's official skill covers the core Loki model, LogQL, ingestion, structured metadata, and Logs Drilldown. This
repository retains a local skill because it adds an executable HTTP helper with explicit write guards, offline API and
`logcli` references, and mocked behavior tests. Recheck this decision when Grafana adds equivalent operational tooling;
remove local overlap when it no longer provides a distinct, tested workflow.

## Change and validation workflow

For every skill or packaging change:

1. Edit the canonical workflow under top-level `skills/` once.
2. Run `task package` to regenerate committed host copies.
3. Review `agents/openai.yaml` so its UI text and invocation policy still match
   `SKILL.md`
   ([OpenAI skill creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)).
4. Update both host manifests and marketplaces when identity, paths, inventory, or version changes.
5. Update repository instructions and installation documentation in the same change.
6. Run `task validate`; CI runs the same entry point and rejects stale generated copies.
7. Validate the Codex plugin with OpenAI's `validate_plugin.py`; for an already installed local
   plugin, use the cachebuster/reinstall workflow rather than editing its cache
   ([OpenAI plugin creator](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/SKILL.md)).
8. Run `claude plugin validate . --strict`; then test marketplace add, install, invocation, and
   update on a clean cache or machine
   ([Claude marketplace reference](https://code.claude.com/docs/en/plugin-marketplaces)).
9. Test at least one automatic trigger and one non-trigger for model-invoked skills. Test explicit
   invocation for manual-only skills.
10. Inspect the packaged/cache copy, not only the source tree, to catch missing files and broken
   relative paths.

OpenAI describes skills as reusable workflows and plugins as their installable distribution unit; a
plugin may contain several skills, so packaging related skills together is expected
([OpenAI skills](https://help.openai.com/en/articles/20001066),
[OpenAI plugins](https://help.openai.com/en/articles/20001256/)).
