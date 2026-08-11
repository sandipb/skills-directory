# Repository instructions

This repository publishes one plugin containing reusable agent skills for Codex, ChatGPT Work, and Claude Code.

## Hard stops

- Do not commit, push, publish, or open a pull request without user approval of the exact action and text.
- Preserve unrelated working-tree changes.
- Never add credentials, private endpoints, personal data, or generated output.
- Make the smallest change that satisfies the request.

## Canonical layout

- `AGENTS.md` is canonical. `CLAUDE.md` must be a relative symlink to it.
- Canonical skills live in the real top-level `skills/<skill-name>/` directories.
- Generated Codex and Claude packages live under `plugins/codex/sandipb-agents/` and
  `plugins/claude/sandipb-agents/`.
- Codex and Claude marketplace metadata lives in `.agents/plugins/marketplace.json` and
  `.claude-plugin/marketplace.json`.

Use lowercase kebab-case names. Edit only canonical skills. Never hand-edit generated plugin copies; run
`task package` after changing canonical skills.

## Skills

Every skill requires:

- `SKILL.md` with valid YAML frontmatter
- `CHANGELOG.md`
- a versioned changelog for public releases

Skill versions live in `CHANGELOG.md`, not portable `SKILL.md` frontmatter. When changing an existing skill, update its
changelog version. Preserve its trigger semantics and tool constraints unless the request changes them.

Keep `technical-writing`, `technical-docs`, and `tech-blog` available for both model and explicit invocation. Keep their
canonical `SKILL.md` files portable.
The optional `avoid-ai-writing` skill must never block the core workflow.

## Plugins

Keep both host manifest names, versions, and shared identity fields synchronized. Marketplace versions are optional;
when pinned, keep them synchronized with the corresponding manifest. Include only components that exist.

Skill versions are independent from the plugin version. For every releasable skill change, update the skill changelog
and bump both plugin manifests in the same pull request; do not defer the plugin bump to a release-preparation pull
request. Git tags and GitHub releases use the plugin version and must match both manifests.

Use the local `plugin-creator` workflow for scaffolding and validation. Do not hand-edit installed plugin caches.

## Documentation

Keep `README.md` aligned with the current repository layout and supported installation surfaces. Use placeholder domains
and credentials in examples. Avoid claims that are not tested or documented.

Every packaging change must update affected documentation and repository instructions in the same change. This includes
changes to directory layout, plugin manifests, marketplace metadata, installation commands, supported hosts, and
validation workflows. Do not leave documentation synchronization for a later task.

All changes merge through pull requests. CI must run `task validate`, and the required GitHub ruleset must block direct
updates to the default branch and require the validation check. Repository files document this policy; the owner applies
the ruleset in GitHub's UI.

## Validation

Run checks relevant to changed files:

- Skill validation for changed `SKILL.md` files
- Plugin validation for changed plugins
- Markdown/pre-commit checks when available
- Agent-instruction sync audit after changing instruction files
- Fireworks and Loki behavior tests when their scripts change
- Codex and Claude package validation when layout or manifests change

Report skipped checks and why. Do not claim prose checks validate technical behavior.

## Git workflow

Work on a topic branch unless the user explicitly approves another approach. The repository expects one commit per pull
request. Use Conventional Commits for all commit subjects. Present the proposed commit message and pull-request text
before any publishing action.
