import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import writing_smoke


class FixtureTests(unittest.TestCase):
    def fixture(self, **overrides):
        fixture = {
            "schema_version": 2,
            "id": "docs-preservation",
            "prompt": "Edit this fictional runbook.",
            "expected_skills": ["technical-docs", "technical-writing"],
            "requires_isolated_editor": True,
            "assertions": {
                "contains": ["widgetctl start"],
                "forbids": ["real customer"],
                "sections": ["Revised content"],
            },
            "manual_review": ["Check pacing."],
        }
        fixture.update(overrides)
        return fixture

    def test_valid_fixture_is_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "fixture.json")
            path.write_text(json.dumps(self.fixture()), encoding="utf-8")
            loaded = writing_smoke.load_fixtures(Path(directory))
        self.assertEqual(["docs-preservation"], [item.identifier for item in loaded])

    def test_invalid_fixture_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "fixture.json")
            path.write_text(json.dumps(self.fixture(prompt="")), encoding="utf-8")
            with self.assertRaisesRegex(writing_smoke.HarnessError, "prompt"):
                writing_smoke.load_fixtures(Path(directory))

    def test_version_one_fixture_requires_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "fixture.json")
            path.write_text(json.dumps(self.fixture(schema_version=1)), encoding="utf-8")
            with self.assertRaisesRegex(writing_smoke.HarnessError, "schema_version must be 2"):
                writing_smoke.load_fixtures(Path(directory))

    def test_fixture_must_declare_isolated_editor_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "fixture.json")
            data = self.fixture()
            del data["requires_isolated_editor"]
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(writing_smoke.HarnessError, "requires_isolated_editor"):
                writing_smoke.load_fixtures(Path(directory))

    def test_isolated_editor_fixture_requires_source_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "fixture.json")
            data = self.fixture(assertions={"contains": [], "forbids": [], "sections": ["Findings"]})
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(writing_smoke.HarnessError, "assertions.contains evidence"):
                writing_smoke.load_fixtures(Path(directory))

    def test_duplicate_fixture_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("one.json", "two.json"):
                Path(directory, name).write_text(json.dumps(self.fixture()), encoding="utf-8")
            with self.assertRaisesRegex(writing_smoke.HarnessError, "duplicate"):
                writing_smoke.load_fixtures(Path(directory))

    def test_skill_acceptance_fixture_set_is_present(self):
        fixtures = writing_smoke.load_fixtures(Path("tests/fixtures/writing-smoke"))
        identifiers = {fixture.identifier for fixture in fixtures}
        self.assertTrue(
            {
                "blog-compose-from-research",
                "blog-review-only",
                "comparison-docs-contract",
                "comparison-blog-contract",
                "local-convention-precedence",
                "multiple-missing-facts",
            }.issubset(identifiers)
        )

    def test_umbrella_fixtures_require_an_isolated_editor(self):
        fixtures = writing_smoke.load_fixtures(Path("tests/fixtures/writing-smoke"))
        for fixture in fixtures:
            with self.subTest(fixture=fixture.identifier):
                expected = bool({"technical-docs", "tech-blog"} & set(fixture.expected_skills))
                self.assertEqual(expected, fixture.requires_isolated_editor)

    def test_each_umbrella_skill_has_explicit_and_implicit_fixtures(self):
        fixtures = writing_smoke.load_fixtures(Path("tests/fixtures/writing-smoke"))
        for skill in ("technical-docs", "tech-blog"):
            matching = [fixture for fixture in fixtures if skill in fixture.expected_skills]
            with self.subTest(skill=skill):
                self.assertTrue(any(f"${skill}" in fixture.prompt for fixture in matching))
                self.assertTrue(any(f"${skill}" not in fixture.prompt for fixture in matching))


class ReadmeContractTests(unittest.TestCase):
    def readme(self, skill: str) -> str:
        return Path(f"skills/{skill}/README.md").read_text(encoding="utf-8")

    def test_every_public_writing_skill_documents_direct_invocation(self):
        for skill in ("technical-writing", "technical-docs", "tech-blog"):
            with self.subTest(skill=skill):
                self.assertIn(f"${skill}", self.readme(skill))

    def test_umbrella_readmes_document_compose_edit_and_review_examples(self):
        docs = self.readme("technical-docs")
        blog = self.readme("tech-blog")
        for verb in ("Compose", "Edit", "Review"):
            self.assertIn(verb, docs)
        for phrase in ("rough draft", "researched notes", "without rewriting"):
            self.assertIn(phrase, blog)

    def test_readmes_document_source_and_isolation_boundaries(self):
        for skill in ("technical-writing", "technical-docs", "tech-blog"):
            with self.subTest(skill=skill):
                text = self.readme(skill)
                self.assertRegex(text, r"supplied|already gathered|existing")
                self.assertRegex(text, r"does not research|writes only from")
        for skill in ("technical-docs", "tech-blog"):
            text = self.readme(skill)
            self.assertRegex(text, r"fresh (?:writer/)?editor subagent")
            self.assertIn("must", text.lower())
            self.assertIn("stop", text.lower())
            self.assertNotIn("sequentially with weaker context isolation", text)
            self.assertIn("avoid-ai-writing", text)

    def test_umbrella_skills_require_delegation_and_reject_same_context_fallback(self):
        for skill in ("technical-docs", "tech-blog"):
            with self.subTest(skill=skill):
                text = Path(f"skills/{skill}/SKILL.md").read_text(encoding="utf-8")
                self.assertRegex(text, r"(?i)must delegate every compose, edit, or review")
                self.assertRegex(text, r"(?i)fresh writer/editor subagent")
                self.assertRegex(text, r"(?i)stop before (?:composing|editing|reviewing)")
                self.assertIn("Do not use same-context or sequential fallback", text)
                self.assertNotIn("Without subagents", text)
                self.assertIn("If isolated delegation is unavailable or disabled", text)
                self.assertIn("official subagent extension must be installed and enabled", text)


class StreamTests(unittest.TestCase):
    def test_ansi_and_pty_line_endings_are_normalized(self):
        raw = b'\x1b[32m{"type":"thread.started"}\x1b[0m\r\r\n'
        self.assertEqual('{"type":"thread.started"}\n', writing_smoke.normalize_pty_output(raw))

    def test_json_events_and_final_response_are_extracted(self):
        stream = "noise\n" + "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "abc"}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "Result"}}),
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 2}}),
            ]
        )
        parsed = writing_smoke.parse_event_stream(stream)
        self.assertEqual("Result", parsed.final_response)
        self.assertEqual({"input_tokens": 3, "output_tokens": 2}, parsed.usage)
        self.assertTrue(parsed.completed)

    def test_completed_child_agent_is_observed_and_correlated(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "status": "completed",
                    "prompt": "Act as the fresh editor. Revise the supplied ValeStore draft.",
                    "receiverThreadIds": ["child-1"],
                    "agentsStates": {"child-1": {"status": "running"}},
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "wait",
                    "status": "completed",
                    "receiverThreadIds": ["child-1"],
                    "agentsStates": {"child-1": {"status": "completed"}},
                },
            },
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.VERIFIED, observation.status)
        self.assertEqual(("child-1",), observation.started_children)
        self.assertEqual(("child-1",), observation.completed_children)

    def test_snake_case_child_agent_events_are_supported(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collab_agent_tool_call",
                    "tool": "spawn_agent",
                    "status": "completed",
                    "prompt": "Edit the ValeStore documentation.",
                    "receiver_thread_ids": ["child-2"],
                    "agents_states": {"child-2": {"status": "completed"}},
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.VERIFIED, observation.status)

    def test_model_self_report_is_not_delegation_evidence(self):
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": "I used a fresh subagent."}},
            {"type": "turn.completed", "usage": {}},
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.INCONCLUSIVE, observation.status)

    def test_visible_collaboration_without_completed_child_fails(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "status": "completed",
                    "prompt": "Edit the ValeStore draft.",
                    "receiverThreadIds": ["child-3"],
                    "agentsStates": {"child-3": {"status": "running"}},
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.FAILED, observation.status)

    def test_completed_unrelated_child_is_not_editor_evidence(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "status": "completed",
                    "prompt": "Inspect ValeStore code for test coverage.",
                    "receiverThreadIds": ["child-4"],
                    "agentsStates": {"child-4": {"status": "completed"}},
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.FAILED, observation.status)

    def test_review_editor_prompt_may_use_critique(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "prompt": "Critique and review the MistQueue draft for pacing.",
                    "receiverThreadIds": ["child-review"],
                    "agentsStates": {"child-review": {"status": "completed"}},
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("MistQueue",))
        self.assertEqual(writing_smoke.DelegationStatus.VERIFIED, observation.status)

    def test_ai_pattern_reviewer_is_not_editor_evidence(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "prompt": "Review the MistQueue draft for pacing and AI-writing patterns; return safe-fix findings.",
                    "receiverThreadIds": ["child-specialist"],
                    "agentsStates": {"child-specialist": {"status": "completed"}},
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("MistQueue",))
        self.assertEqual(writing_smoke.DelegationStatus.FAILED, observation.status)

    def test_editor_prompt_may_preserve_contract_labels(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "prompt": (
                        "Edit the ValeStore draft; apply safe-fix items and return additions as author-judgment "
                        "suggestions."
                    ),
                    "receiverThreadIds": ["child-contract"],
                    "agentsStates": {"child-contract": {"status": "completed"}},
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.VERIFIED, observation.status)

    def test_spawn_role_and_child_can_arrive_in_separate_events(self):
        events = [
            {
                "type": "item.started",
                "item": {
                    "id": "call-1",
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "prompt": "Edit the ValeStore draft.",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "id": "call-1",
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "receiverThreadIds": ["child-5"],
                    "agentsStates": {"child-5": {"status": "completed"}},
                },
            },
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.VERIFIED, observation.status)

    def test_missing_spawn_prompt_is_inconclusive(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "receiverThreadIds": ["child-6"],
                    "agentsStates": {"child-6": {"status": "completed"}},
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.INCONCLUSIVE, observation.status)

    def test_missing_spawn_child_id_is_inconclusive(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "prompt": "Edit the ValeStore draft.",
                },
            }
        ]
        observation = writing_smoke.observe_isolated_editor(events, ("ValeStore",))
        self.assertEqual(writing_smoke.DelegationStatus.INCONCLUSIVE, observation.status)

    def test_failed_turn_is_not_completed(self):
        event = json.dumps({"type": "turn.failed", "error": {"message": "401 Unauthorized"}})
        parsed = writing_smoke.parse_event_stream(event)
        self.assertFalse(parsed.completed)
        self.assertIn("401 Unauthorized", parsed.error)

    def test_pty_runner_captures_process_output(self):
        command = [sys.executable, "-c", "print('\\033[32mstream\\033[0m')"]
        returncode, raw = writing_smoke.run_with_pty(command, Path.cwd())
        self.assertEqual(0, returncode)
        self.assertEqual("stream\n", writing_smoke.normalize_pty_output(raw))

    def test_pty_runner_stops_child_when_interrupted(self):
        process = mock.Mock()
        process.poll.return_value = None
        with mock.patch.object(writing_smoke.subprocess, "Popen", return_value=process):
            with mock.patch.object(writing_smoke.select, "select", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    writing_smoke.run_with_pty(["ignored"], Path.cwd())
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)


class AssertionTests(unittest.TestCase):
    def test_all_assertion_types_pass(self):
        assertions = {"contains": ["widgetctl start"], "forbids": ["guaranteed"], "sections": ["Questions"]}
        self.assertEqual([], writing_smoke.evaluate_assertions("Questions\nRun widgetctl start.", assertions))

    def test_assertion_failures_are_reported_independently(self):
        assertions = {"contains": ["MAY"], "forbids": ["guaranteed"], "sections": ["Questions"]}
        failures = writing_smoke.evaluate_assertions("It is guaranteed.", assertions)
        self.assertEqual(3, len(failures))


class ClassificationTests(unittest.TestCase):
    def test_assertion_failure_is_distinct_from_environment_failure(self):
        completed = writing_smoke.ParsedRun([], "text", {}, True, None)
        failed = writing_smoke.ParsedRun([], "", {}, False, "network policy denied")
        self.assertEqual(writing_smoke.ResultKind.FIXTURE_FAILURE, writing_smoke.classify_result(completed, ["missing"]))
        self.assertEqual(writing_smoke.ResultKind.HARNESS_FAILURE, writing_smoke.classify_result(failed, []))
        self.assertEqual(1, writing_smoke.exit_status(writing_smoke.ResultKind.FIXTURE_FAILURE))
        self.assertEqual(2, writing_smoke.exit_status(writing_smoke.ResultKind.HARNESS_FAILURE))

    def test_required_delegation_changes_result_classification(self):
        completed = writing_smoke.ParsedRun([], "text", {}, True, None)
        verified = writing_smoke.DelegationObservation(
            writing_smoke.DelegationStatus.VERIFIED, ("child-1",), ("child-1",)
        )
        failed = writing_smoke.DelegationObservation(writing_smoke.DelegationStatus.FAILED, (), ())
        inconclusive = writing_smoke.DelegationObservation(writing_smoke.DelegationStatus.INCONCLUSIVE, (), ())
        self.assertEqual(
            writing_smoke.ResultKind.SUCCESS,
            writing_smoke.classify_result(completed, [], verified),
        )
        self.assertEqual(
            writing_smoke.ResultKind.FIXTURE_FAILURE,
            writing_smoke.classify_result(completed, [], failed),
        )
        self.assertEqual(
            writing_smoke.ResultKind.HARNESS_FAILURE,
            writing_smoke.classify_result(completed, [], inconclusive),
        )

    def test_result_keeps_skill_routing_separate_from_editor_evidence(self):
        fixture = writing_smoke.validate_fixture(FixtureTests().fixture(), Path("fixture.json"))
        parsed = writing_smoke.ParsedRun([], "Result", {}, True, None)
        delegation = writing_smoke.DelegationObservation(
            writing_smoke.DelegationStatus.VERIFIED, ("child-1",), ("child-1",)
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "result.json")
            writing_smoke.write_result(
                path,
                fixture,
                parsed,
                [],
                writing_smoke.ResultKind.SUCCESS,
                None,
                delegation,
                "isolated editor did not complete",
            )
            result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("unverified", result["routing"])
        self.assertEqual("verified", result["isolated_editor"])
        self.assertEqual([], result["assertion_failures"])
        self.assertEqual("isolated editor did not complete", result["delegation_failure"])


class CleanupTests(unittest.TestCase):
    def test_success_is_removed_unless_keep_requested(self):
        self.assertEqual((True, False), writing_smoke.cleanup_decision(writing_smoke.ResultKind.SUCCESS, keep=False))
        self.assertEqual((False, True), writing_smoke.cleanup_decision(writing_smoke.ResultKind.SUCCESS, keep=True))

    def test_failure_and_interrupt_are_retained(self):
        self.assertEqual((False, True), writing_smoke.cleanup_decision(writing_smoke.ResultKind.FIXTURE_FAILURE, False))
        self.assertEqual((False, True), writing_smoke.cleanup_decision(writing_smoke.ResultKind.INTERRUPTED, False))

    def test_owned_sandbox_name_is_required_for_cleanup(self):
        owner = writing_smoke.OwnedSandbox("writing-smoke-123", lambda command: command)
        self.assertEqual(["sbx", "rm", "--force", "writing-smoke-123"], owner.remove())
        with self.assertRaises(writing_smoke.HarnessError):
            writing_smoke.OwnedSandbox("codex-writing-smoke", lambda command: command).remove()


class CommandTests(unittest.TestCase):
    def test_workspace_is_passed_only_when_creating_sandbox(self):
        fixture = FixtureTests().fixture()
        parsed = writing_smoke.validate_fixture(fixture, Path("fixture.json"))
        workspace = Path("/tmp/writing-smoke-test/workspace")
        create = writing_smoke.command_for_fixture("writing-smoke-123", workspace, parsed, None, attach=False)
        attach = writing_smoke.command_for_fixture("writing-smoke-123", workspace, parsed, None, attach=True)
        self.assertIn(str(workspace), create)
        self.assertNotIn(str(workspace), attach)
        self.assertEqual(["sbx", "run", "codex", "--name", "writing-smoke-123"], attach[:5])


class OrchestrationTests(unittest.TestCase):
    def write_fixture(self, directory: Path) -> None:
        data = FixtureTests().fixture(assertions={"contains": ["Result"], "forbids": [], "sections": []})
        Path(directory, "fixture.json").write_text(json.dumps(data), encoding="utf-8")

    def completed_stream(self) -> bytes:
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collabAgentToolCall",
                    "tool": "spawnAgent",
                    "status": "completed",
                    "prompt": "Edit the Result draft.",
                    "receiverThreadIds": ["child-1"],
                    "agentsStates": {"child-1": {"status": "completed"}},
                },
            },
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Result"}},
            {"type": "turn.completed", "usage": {"output_tokens": 1}},
        ]
        return ("\n".join(json.dumps(event) for event in events) + "\n").encode()

    def test_successful_main_removes_owned_state(self):
        with tempfile.TemporaryDirectory() as fixtures_directory:
            self.write_fixture(Path(fixtures_directory))
            with mock.patch.object(writing_smoke.shutil, "which", return_value="/usr/local/bin/sbx"):
                with mock.patch.object(writing_smoke, "run_with_pty", return_value=(0, self.completed_stream())):
                    with mock.patch.object(
                        writing_smoke.OwnedSandbox,
                        "remove",
                        return_value=subprocess.CompletedProcess([], 0),
                    ) as remove:
                        status = writing_smoke.main(["--fixtures-dir", fixtures_directory])
        self.assertEqual(0, status)
        remove.assert_called_once_with()

    def test_nonzero_sbx_exit_retains_failure_artifacts(self):
        with tempfile.TemporaryDirectory() as fixtures_directory, tempfile.TemporaryDirectory() as run_directory:
            self.write_fixture(Path(fixtures_directory))
            with mock.patch.object(writing_smoke.tempfile, "mkdtemp", return_value=run_directory):
                with mock.patch.object(writing_smoke.shutil, "which", return_value="/usr/local/bin/sbx"):
                    with mock.patch.object(writing_smoke, "run_with_pty", return_value=(7, self.completed_stream())):
                        with mock.patch.object(writing_smoke.OwnedSandbox, "remove") as remove:
                            status = writing_smoke.main(["--fixtures-dir", fixtures_directory])
            self.assertTrue(Path(run_directory, "docs-preservation.jsonl").exists())
        self.assertEqual(2, status)
        remove.assert_not_called()


if __name__ == "__main__":
    unittest.main()
