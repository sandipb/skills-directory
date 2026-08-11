#!/usr/bin/env python3
"""Opt-in model-backed smoke runner for the canonical writing skills."""

from __future__ import annotations

import argparse
import dataclasses
import enum
import json
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Callable, Sequence


SUCCESS = 0
FIXTURE_FAILURE = 1
HARNESS_FAILURE = 2
INTERRUPTED = 130
SANDBOX_PREFIX = "writing-smoke-"
ANSI_PATTERN = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")


class HarnessError(RuntimeError):
    pass


class ResultKind(enum.Enum):
    SUCCESS = "success"
    FIXTURE_FAILURE = "fixture-failure"
    HARNESS_FAILURE = "environment-or-harness-failure"
    INTERRUPTED = "interrupted"


@dataclasses.dataclass(frozen=True)
class Fixture:
    schema_version: int
    identifier: str
    prompt: str
    expected_skills: tuple[str, ...]
    assertions: dict[str, list[str]]
    manual_review: tuple[str, ...]
    source: Path


@dataclasses.dataclass(frozen=True)
class ParsedRun:
    events: list[dict]
    final_response: str
    usage: dict
    completed: bool
    error: str | None


@dataclasses.dataclass
class OwnedSandbox:
    name: str
    command_runner: Callable[[Sequence[str]], object] = subprocess.run

    def remove(self) -> object:
        if not self.name.startswith(SANDBOX_PREFIX):
            raise HarnessError(f"refusing to remove unowned sandbox: {self.name}")
        return self.command_runner(["sbx", "rm", "--force", self.name])


def _string_list(value: object, field: str, source: Path, *, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise HarnessError(f"{source}: {field} must be a list of non-empty strings")
    if not allow_empty and not value:
        raise HarnessError(f"{source}: {field} must not be empty")
    return tuple(value)


def validate_fixture(data: object, source: Path) -> Fixture:
    if not isinstance(data, dict):
        raise HarnessError(f"{source}: fixture must be a JSON object")
    allowed = {"schema_version", "id", "prompt", "expected_skills", "assertions", "manual_review"}
    unknown = set(data) - allowed
    if unknown:
        raise HarnessError(f"{source}: unknown fields: {', '.join(sorted(unknown))}")
    if data.get("schema_version") != 1:
        raise HarnessError(f"{source}: schema_version must be 1")
    identifier = data.get("id")
    if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier):
        raise HarnessError(f"{source}: id must use lowercase kebab-case")
    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise HarnessError(f"{source}: prompt must be a non-empty string")
    expected_skills = _string_list(data.get("expected_skills"), "expected_skills", source, allow_empty=False)
    assertions = data.get("assertions")
    if not isinstance(assertions, dict) or set(assertions) - {"contains", "forbids", "sections"}:
        raise HarnessError(f"{source}: assertions supports only contains, forbids, and sections")
    normalized_assertions = {
        name: list(_string_list(assertions.get(name, []), f"assertions.{name}", source))
        for name in ("contains", "forbids", "sections")
    }
    if not any(normalized_assertions.values()):
        raise HarnessError(f"{source}: at least one deterministic assertion is required")
    manual_review = _string_list(data.get("manual_review", []), "manual_review", source)
    return Fixture(1, identifier, prompt, expected_skills, normalized_assertions, manual_review, source)


def load_fixtures(directory: Path) -> list[Fixture]:
    if not directory.is_dir():
        raise HarnessError(f"fixture directory does not exist: {directory}")
    fixtures: list[Fixture] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise HarnessError(f"{path}: invalid JSON: {error}") from error
        fixture = validate_fixture(data, path)
        if fixture.identifier in seen:
            raise HarnessError(f"{path}: duplicate fixture id: {fixture.identifier}")
        seen.add(fixture.identifier)
        fixtures.append(fixture)
    if not fixtures:
        raise HarnessError(f"no JSON fixtures found in {directory}")
    return fixtures


def normalize_pty_output(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace").replace("\r\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    return ANSI_PATTERN.sub("", text)


def parse_event_stream(stream: str) -> ParsedRun:
    events: list[dict] = []
    final_response = ""
    usage: dict = {}
    completed = False
    error: str | None = None
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or "type" not in event:
            continue
        events.append(event)
        if event["type"] == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                final_response = item["text"]
        elif event["type"] == "turn.completed":
            completed = True
            usage = event.get("usage", {}) if isinstance(event.get("usage", {}), dict) else {}
        elif event["type"] == "turn.failed":
            details = event.get("error", event)
            error = details.get("message") if isinstance(details, dict) else str(details)
    if not events:
        error = "malformed event stream: no JSON events found"
    elif not completed and error is None:
        error = "event stream ended without turn.completed"
    elif completed and not final_response:
        completed = False
        error = "completed turn did not contain a final agent message"
    return ParsedRun(events, final_response, usage, completed, error)


def evaluate_assertions(response: str, assertions: dict[str, list[str]]) -> list[str]:
    failures = [f"missing required literal: {value!r}" for value in assertions.get("contains", []) if value not in response]
    failures.extend(f"found forbidden literal: {value!r}" for value in assertions.get("forbids", []) if value in response)
    lines = [re.sub(r"^#{1,6}\s+", "", line.strip()).rstrip(":") for line in response.splitlines()]
    failures.extend(f"missing required section: {value!r}" for value in assertions.get("sections", []) if value not in lines)
    return failures


def classify_result(parsed: ParsedRun, assertion_failures: list[str]) -> ResultKind:
    if not parsed.completed:
        return ResultKind.HARNESS_FAILURE
    return ResultKind.FIXTURE_FAILURE if assertion_failures else ResultKind.SUCCESS


def exit_status(kind: ResultKind) -> int:
    return {
        ResultKind.SUCCESS: SUCCESS,
        ResultKind.FIXTURE_FAILURE: FIXTURE_FAILURE,
        ResultKind.HARNESS_FAILURE: HARNESS_FAILURE,
        ResultKind.INTERRUPTED: INTERRUPTED,
    }[kind]


def cleanup_decision(kind: ResultKind, keep: bool) -> tuple[bool, bool]:
    remove = kind is ResultKind.SUCCESS and not keep
    return remove, not remove


def run_with_pty(command: Sequence[str], cwd: Path) -> tuple[int, bytes]:
    master, slave = pty.openpty()
    output = bytearray()
    process: subprocess.Popen | None = None
    try:
        process = subprocess.Popen(command, cwd=cwd, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        slave = -1
        while True:
            ready, _, _ = select.select([master], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    chunk = b""
                if chunk:
                    output.extend(chunk)
                    continue
            if process.poll() is not None:
                while True:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output.extend(chunk)
                break
        return process.returncode, bytes(output)
    except BaseException:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    finally:
        if slave >= 0:
            os.close(slave)
        os.close(master)


def prepare_workspace(repo_root: Path, run_root: Path) -> Path:
    workspace = run_root / "workspace"
    destination = workspace / ".agents" / "skills"
    destination.mkdir(parents=True)
    for name in ("technical-writing", "technical-docs", "tech-blog"):
        source = repo_root / "skills" / name
        if not source.is_dir():
            raise HarnessError(f"canonical skill missing: {source}")
        shutil.copytree(source, destination / name)
    return workspace


def command_for_fixture(
    sandbox: str, workspace: Path, fixture: Fixture, model: str | None, *, attach: bool
) -> list[str]:
    command = ["sbx", "run", "codex", "--name", sandbox]
    if not attach:
        command.append(str(workspace))
    command.extend(["--", "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only", "--json"])
    if model:
        command.extend(["--model", model])
    command.append(fixture.prompt)
    return command


def write_result(path: Path, fixture: Fixture, parsed: ParsedRun, failures: list[str], kind: ResultKind, model: str | None) -> None:
    path.write_text(json.dumps({
        "fixture": fixture.identifier,
        "result": kind.value,
        "model": model or "configured-default",
        "expected_skills": list(fixture.expected_skills),
        "routing": "unverified",
        "usage": parsed.usage,
        "assertion_failures": failures,
        "manual_review": list(fixture.manual_review),
    }, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", help="run only the fixture with this id")
    parser.add_argument("--model", help="override the configured Codex model")
    parser.add_argument("--keep", action="store_true", help="retain successful artifacts and sandbox")
    parser.add_argument("--fixtures-dir", type=Path, default=Path("tests/fixtures/writing-smoke"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    try:
        fixtures = load_fixtures((repo_root / args.fixtures_dir).resolve() if not args.fixtures_dir.is_absolute() else args.fixtures_dir)
        if args.fixture:
            fixtures = [fixture for fixture in fixtures if fixture.identifier == args.fixture]
            if not fixtures:
                raise HarnessError(f"unknown fixture id: {args.fixture}")
        if shutil.which("sbx") is None:
            raise HarnessError("sbx is not installed or not on PATH")
        run_root = Path(tempfile.mkdtemp(prefix="writing-smoke-"))
        workspace = prepare_workspace(repo_root, run_root)
    except HarnessError as error:
        print(f"error: {error}", file=sys.stderr)
        return HARNESS_FAILURE

    sandbox = OwnedSandbox(f"{SANDBOX_PREFIX}{os.getpid()}-{uuid.uuid4().hex[:8]}")
    overall = ResultKind.SUCCESS
    try:
        for index, fixture in enumerate(fixtures):
            print(f"RUN {fixture.identifier} (routing: unverified; expected: {', '.join(fixture.expected_skills)})")
            command = command_for_fixture(sandbox.name, workspace, fixture, args.model, attach=index > 0)
            returncode, raw = run_with_pty(command, repo_root)
            normalized = normalize_pty_output(raw)
            (run_root / f"{fixture.identifier}.jsonl").write_text(normalized, encoding="utf-8")
            parsed = parse_event_stream(normalized)
            if returncode and parsed.completed:
                parsed = dataclasses.replace(parsed, completed=False, error=f"sbx exited with status {returncode}")
            failures = evaluate_assertions(parsed.final_response, fixture.assertions) if parsed.completed else []
            kind = classify_result(parsed, failures)
            write_result(run_root / f"{fixture.identifier}.result.json", fixture, parsed, failures, kind, args.model)
            if kind is ResultKind.HARNESS_FAILURE:
                overall = kind
                print(f"ERROR {fixture.identifier}: {parsed.error}", file=sys.stderr)
                break
            if kind is ResultKind.FIXTURE_FAILURE:
                overall = kind
                print(f"FAIL {fixture.identifier}: {'; '.join(failures)}")
            else:
                print(f"PASS {fixture.identifier}")
    except KeyboardInterrupt:
        overall = ResultKind.INTERRUPTED
        print("interrupted", file=sys.stderr)

    remove, retain = cleanup_decision(overall, args.keep)
    if remove:
        result = sandbox.remove()
        returncode = getattr(result, "returncode", 0)
        if returncode:
            overall = ResultKind.HARNESS_FAILURE
            retain = True
            print(f"error: failed to remove owned sandbox {sandbox.name}", file=sys.stderr)
        else:
            shutil.rmtree(run_root)
    if retain:
        print(f"Artifacts: {run_root}")
        print(f"Sandbox: {sandbox.name}")
        print(f"Cleanup: sbx rm --force {sandbox.name}")
    return exit_status(overall)


if __name__ == "__main__":
    raise SystemExit(main())
