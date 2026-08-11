# Testing agent skills

Repository validation checks skill structure, package synchronization, manifests, scripts, and Markdown. It does not
execute skills through a model. Use the manual smoke workflow below to test invocation and observable behavior until the
repository has a deterministic evaluation harness.

Manual results are evidence, not stable CI gates. Model, host, installed instructions, and runtime changes can affect
them.

## Create an isolated skill workspace

Create a temporary working directory and expose only the skills under test at the repository skill-discovery path:

```bash
test_root=$(mktemp -d /tmp/codex-skill-test.XXXXXX)
mkdir -p "$test_root/.agents/skills"
ln -s "$PWD/skills/technical-writing" "$test_root/.agents/skills/technical-writing"
ln -s "$PWD/skills/technical-docs" "$test_root/.agents/skills/technical-docs"
ln -s "$PWD/skills/tech-blog" "$test_root/.agents/skills/tech-blog"
```

Codex still discovers system and user-scoped skills. For an isolation-sensitive run, pass `skills.config` overrides
that disable relevant user-scoped skills. Record those overrides with the result. Never copy authentication files into
the temporary workspace.

Run Codex with the existing login, read-only sandboxing, ephemeral session storage, and JSON events:

```bash
codex --ask-for-approval never exec \
  --ephemeral \
  --skip-git-repo-check \
  --sandbox read-only \
  --json \
  --ignore-user-config \
  -C "$test_root" \
  '<prompt>'
```

`--ignore-user-config` ignores user configuration, not user-scoped skill discovery. Treat explicit `skills.config`
disables as part of the test setup when another installed skill could match the prompt.

Use fictional fixtures. Do not send repository secrets, private operational data, customer data, or unpublished
measurements to the model.

## Test invocation

Run both forms:

- Explicit: name the skill, such as `$technical-writing`.
- Implicit: describe the artifact and task without naming a skill.

Ask the response to list loaded skills, but verify the JSON trace instead of trusting that claim. A successful trace
shows Codex reading the expected `SKILL.md`. Umbrella workflows should also read `technical-writing/SKILL.md`.

At minimum, verify these routes:

| Request | Expected skills |
| --- | --- |
| Tighten a small technical note | `technical-writing` |
| Edit or compose a runbook, README, report, or PR description | `technical-docs`, `technical-writing` |
| Edit or compose a reader-oriented technical article | `tech-blog`, `technical-writing` |
| Review without rewriting | Matching umbrella skill, `technical-writing` |

## Test behavior

Use small fixtures with independently checkable literals. Cover:

- preservation of commands, identifiers, paths, values, units, conditions, causality, uncertainty, and requirement
  strength;
- composition from supplied notes without unsupported facts or causal claims;
- partial output plus questions when required information is absent;
- safe grammar and clarity fixes applied inline;
- examples, analogies, material removal, changed emphasis, and major restructuring returned as author-judgment items;
- documentation preserving distinct information while blog editing permits stronger selection and reordering;
- review-only requests returning findings without a rewrite;
- formulaic prose reduction without synonym-cycling technical terms;
- omission of empty findings or suggestions sections.

Use substantive fixtures separately to exercise fresh editor delegation, bounded source packets, anti-AI reviewer input,
finding classification, reconciliation, and the sequential fallback. Confirm these properties from agent and tool events,
not only from final prose.

## Record results

For each run, retain or summarize:

- Codex version and model;
- commit SHA under test;
- prompt and fictional source fixture;
- enabled and disabled skills;
- expected route and observed `SKILL.md` reads;
- final output;
- pass, fail, or inconclusive for each asserted behavior;
- runtime warnings, unexpected tool use, and token usage.

Report environmental failures separately from skill failures. Examples include authentication errors, shell snapshot
errors, unavailable reviewer skills, rate limits, and model-service failures.

## Future deterministic testing

Agent-driven smoke tests provide early coverage but are variable and expensive. After the behavior matrix is mature,
replace repeated manual checks with a specified evaluation harness. Preserve the same public skill boundary and fixtures;
add deterministic assertions where literals or structure are sufficient, and use model grading only for behavior that
cannot be checked mechanically.
