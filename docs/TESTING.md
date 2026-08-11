# Testing agent skills

Repository validation checks skill structure, package synchronization, manifests, scripts, Markdown, and deterministic
smoke-runner behavior. It does not execute skills through a model. Use the opt-in smoke harness to test invocation and
observable writing behavior.

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

Version 1 fixtures are JSON files under `tests/fixtures/writing-smoke/`. Each fixture contains:

- `schema_version`: `1`;
- `id`: a unique lowercase kebab-case identifier;
- `prompt`: complete fictional input passed to Codex unchanged;
- `expected_skills`: informational routing metadata;
- `assertions.contains`: required exact literals;
- `assertions.forbids`: prohibited exact literals;
- `assertions.sections`: required Markdown heading or standalone section labels;
- `manual_review`: subjective checks that the runner reports but does not grade.

At least one deterministic assertion is required. Unknown fields and malformed fixtures fail before the runner creates
a sandbox or makes a model request. Do not add private operational data, customer data, unpublished measurements, or
exact full-response snapshots.

## Results and cleanup

The runner reports expected skills as `unverified`. Codex's JSON stream does not currently provide trustworthy
skill-loading evidence. Model self-reporting is not proof of routing.

Exit statuses are:

| Status | Meaning |
| --- | --- |
| `0` | Every deterministic fixture assertion passed. |
| `1` | At least one fixture assertion failed. |
| `2` | An environment or harness failure occurred. |
| `130` | The run was interrupted. |

Successful traces, temporary files, and the owned sandbox are removed by default. `--keep` retains successful state.
Fixture failures, environment failures, and interrupted runs retain artifacts and the owned sandbox. The runner prints
the artifact path, sandbox name, and exact `sbx rm --force <name>` cleanup command.

The cleanup code accepts only the unique `writing-smoke-` sandbox name created by the current process. Never use
`sbx reset` for harness cleanup because reset deletes unrelated sandbox data.

## Troubleshoot Docker Sandboxes

Keep the JSON event stream as the test trace. Verify the final output and observable completion events. Record expected
skills as unverified metadata; do not treat model prose as routing evidence.

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
its prose. Treat routing as inconclusive until Codex emits trustworthy skill-loading events.

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

Delegation, bounded source packets, reviewer input boundaries, fresh editorial contexts, and subjective prose quality
remain manual or inconclusive until their events are externally observable. Model-backed results remain variable.
Both `task test:writing-smoke` and `task smoke:writing` are opt-in local checks and do not run through `task test`,
`task validate`, or required CI.
