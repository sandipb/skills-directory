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
            "schema_version": 1,
            "id": "docs-preservation",
            "prompt": "Edit this fictional runbook.",
            "expected_skills": ["technical-docs", "technical-writing"],
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
            self.assertIn("subagent", text)
            self.assertIn("weaker context isolation", text)
            self.assertIn("avoid-ai-writing", text)


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
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Result"}},
            {"type": "turn.completed", "usage": {"output_tokens": 1}},
        ]
        return ("\n".join(json.dumps(event) for event in events) + "\n").encode()

    def test_successful_main_removes_owned_state(self):
        with tempfile.TemporaryDirectory() as fixtures_directory:
            self.write_fixture(Path(fixtures_directory))
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
                with mock.patch.object(writing_smoke, "run_with_pty", return_value=(7, self.completed_stream())):
                    with mock.patch.object(writing_smoke.OwnedSandbox, "remove") as remove:
                        status = writing_smoke.main(["--fixtures-dir", fixtures_directory])
            self.assertTrue(Path(run_directory, "docs-preservation.jsonl").exists())
        self.assertEqual(2, status)
        remove.assert_not_called()


if __name__ == "__main__":
    unittest.main()
