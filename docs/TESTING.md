# Testing agent skills

Repository validation checks skill structure, package synchronization, manifests, scripts, Markdown, and deterministic
smoke-runner behavior. Deterministic writing-smoke tests run through `task test`, `task validate`, and CI. They do not
execute skills through a model. Use the opt-in model-backed smoke harness to test invocation and observable writing
behavior.

Manual results are evidence, not stable CI gates. Model, host, installed instructions, and runtime changes can affect
them.

## Contents

- [Run the writing smoke harness](#run-the-writing-smoke-harness)
- [Prerequisites](#prerequisites)
- [Fixture contract](#fixture-contract)
- [Results and cleanup](#results-and-cleanup)
- [Troubleshoot Docker Sandboxes](#troubleshoot-docker-sandboxes)
- [Test coverage and evidence limits](#test-coverage-and-evidence-limits)

## Run the writing smoke harness

Run deterministic harness tests locally:

```bash
task test:writing-smoke
```

These deterministic tests also run through `task test`, `task validate`, and CI.

Run all writing fixtures serially:

```bash
task smoke:writing
```

Select one fixture, override the configured Codex model, or retain a successful run for diagnosis:

```bash
task smoke:writing -- --fixture implicit-docs-preservation
task smoke:writing -- --model <model>
task smoke:writing -- --fixture review-only --keep
```

The runner validates every fixture before creating a sandbox. It copies only the canonical `technical-writing`,
`technical-docs`, and `tech-blog` skills into a unique temporary workspace. It creates one uniquely named sandbox for
the suite and starts an ephemeral `codex exec` session for each fixture. The runner allocates the PTY required by
`sbx run` to return Codex JSON events.

The runner does not copy authentication files, the home directory, SSH sockets, the Docker socket, or unrelated
repository content. It preserves Docker's sandbox-local Codex configuration for the credential proxy. It does not pass
`--ignore-user-config`.

## Prerequisites

Install `sbx` and complete its host-side setup before starting an unattended test:

- Sign in with `sbx login`.
- Store OpenAI OAuth credentials with `sbx secret set openai --oauth`, or store an API key with
  `sbx secret set openai`.
- Run `sbx diagnose` and resolve all failures.
- On Linux, enable KVM and add the user to the `kvm` group. Start a new login session after changing group membership.
- Complete the initial global network-policy prompt once. Use a policy that permits the model endpoint required by the
  test.

If `sandboxd` started before the current login acquired the `kvm` group, restart it:

```bash
sbx daemon restart
```

Docker documents the current platform requirements and authentication commands in its
[getting-started guide](https://docs.docker.com/ai/sandboxes/get-started/) and
[Codex guide](https://docs.docker.com/ai/sandboxes/agents/codex/).

## Fixture contract

Version 2 fixtures are JSON files under `tests/fixtures/writing-smoke/`. Each fixture contains:

- `schema_version`: `2`;
- `id`: a unique lowercase kebab-case identifier;
- `prompt`: complete fictional input passed to Codex unchanged;
- `expected_skills`: informational routing metadata;
- `requires_isolated_editor`: required in every fixture; must be `true` when `expected_skills` includes
  `technical-docs` or `tech-blog`;
- `assertions.contains`: required exact literals;
- `assertions.forbids`: prohibited exact literals;
- `assertions.sections`: required Markdown heading or standalone section labels;
- `manual_review`: subjective checks that the runner reports but does not grade.

At least one deterministic assertion is required. Unknown fields and malformed fixtures fail before the runner creates
a sandbox or makes a model request. Do not add private operational data, customer data, unpublished measurements, or
exact full-response snapshots.

To migrate a version 1 fixture, set `schema_version` to `2`, add `requires_isolated_editor: true` for `technical-docs`
and `tech-blog` fixtures or `false` otherwise, and ensure each required-editor fixture has at least one source literal
in `assertions.contains`.

## Results and cleanup

Each result records `routing: "unverified"` because `expected_skills` is informational routing metadata; the harness
does not observe skill loading. The separate `isolated_editor` field uses ordinary observable spawn-prompt evidence: an
editorial action term plus at least one source literal already present in the fixture's `assertions.contains` list. The
harness correlates the matching spawn's receiver child ID with that child's observed state; skills do not inject test
sentinels.

The adapter excludes prompts containing explicit specialist context—`avoid-ai-writing`, `AI-writing` or AI-pattern
references, or `critique, not rewrite`—so a completed specialist review cannot satisfy mandatory editor evidence.

- `verified`: a matching editor spawn is correlated with an observed `completed` state for its receiver child;
- `failed`: the spawn prompt, receiver child ID, and child state are sufficiently visible, but no spawn matches the
  editor evidence or a matched child has an observed state other than `completed`;
- `inconclusive`: a required spawn prompt, receiver child ID, or child state is missing; this produces an environment or
  harness failure, not success;
- `not-required`: the fixture does not require an isolated editor.

Model self-report is rejected as routing or delegation evidence. Final-prose assertions are evaluated separately and
cannot establish or override `isolated_editor`.

`assertion_failures` contains only final-prose failures; the separate `delegation_failure` field records a required
isolated-editor behavior failure.

Exit statuses are:

| Status | Meaning |
| --- | --- |
| `0` | Every final-prose assertion passed and every required isolated editor was verified. |
| `1` | A final-prose assertion or required-isolation behavior failed. |
| `2` | An environment or harness failure occurred. |
| `130` | The run was interrupted. |

Successful traces, temporary files, and the owned sandbox are removed by default. `--keep` retains successful state.
Fixture failures, environment failures, and interrupted runs retain artifacts and the owned sandbox. The runner prints
the artifact path, sandbox name, and exact `sbx rm --force <name>` cleanup command.

The cleanup code accepts only the unique `writing-smoke-` sandbox name created by the current process. Never use
`sbx reset` for harness cleanup because reset deletes unrelated sandbox data.

## Troubleshoot Docker Sandboxes

Keep the JSON event stream as the test trace. Verify the final output and observable completion events. Do not treat
model prose as routing evidence.

Classify setup failures as environmental failures. Useful checks include:

```bash
sbx diagnose
sbx policy log
sbx daemon status
```

For a hidden sandbox-creation error, inspect recent errors in the daemon log reported by `sbx daemon status`. A KVM
permission error usually means `sandboxd` does not have the user's current supplementary groups. Restart the daemon
before considering `sbx reset`; reset deletes sandbox data.

If Codex returns `401 Unauthorized`, confirm that the command did not use `--ignore-user-config` and that the OpenAI
credential is current. Docker's [troubleshooting guide](https://docs.docker.com/ai/sandboxes/troubleshooting/) covers
credential-proxy and network-policy checks.

## Test coverage and evidence limits

Run both forms:

- Explicit: name the skill, such as `$technical-writing`.
- Implicit: describe the artifact and task without naming a skill.

Expected-skill metadata records routing intent only. Do not ask the model to list loaded skills or infer routing from
its prose.

At minimum, verify these routes:

| Request | Expected skills |
| --- | --- |
| Tighten a small technical note | `technical-writing` |
| Edit or compose a runbook, README, report, or PR description | `technical-docs`, `technical-writing` |
| Edit or compose a reader-oriented technical article | `tech-blog`, `technical-writing` |
| Review without rewriting | Matching umbrella skill, `technical-writing` |

Fixtures use small fictional inputs with independently checkable literals. They cover:

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

Deterministic writing-smoke tests cover fixture validation, event parsing, isolated-editor correlation, result metadata,
and cleanup. They run through `task test`, `task validate`, and required CI. Only the model-backed `task smoke:writing`
remains an opt-in local check. Bounded source-packet transfer, absence of inherited context, reviewer input boundaries,
and subjective prose quality remain manual checks; model-backed results remain variable.
