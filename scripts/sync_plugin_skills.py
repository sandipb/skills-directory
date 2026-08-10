#!/usr/bin/env python3
"""Generate or verify host-specific plugin skill trees from canonical skills."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import stat
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "skills"
TARGETS = {
    "codex": REPO / "plugins/codex/sandipb-agents/skills",
    "claude": REPO / "plugins/claude/sandipb-agents/skills",
}
CLAUDE_MANUAL_ONLY_SKILLS: frozenset[str] = frozenset()
CLAUDE_MANUAL_FIELD = "disable-model-invocation: true"
FORBIDDEN_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache", ".ruff_cache"}


def fail(message: str) -> None:
    raise SystemExit(message)


def validate_source() -> list[Path]:
    if SOURCE.is_symlink() or not SOURCE.is_dir():
        fail(f"canonical source must be a real directory: {SOURCE}")
    skills = sorted(path for path in SOURCE.iterdir() if path.is_dir())
    if not skills or any(not (path / "SKILL.md").is_file() for path in skills):
        fail("every canonical skill directory must contain SKILL.md")
    for path in SOURCE.rglob("*"):
        if path.is_symlink():
            fail(f"skill packages cannot contain symlinks: {path}")
        if path.name in FORBIDDEN_NAMES or path.suffix in {".pyc", ".pyo"}:
            fail(f"canonical skills contain a generated artifact: {path}")
    return skills


def add_claude_manual_field(path: Path) -> None:
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(f"missing YAML frontmatter: {path}")
    closing = text.find("\n---\n", 4)
    if closing == -1:
        fail(f"unterminated YAML frontmatter: {path}")
    frontmatter = text[4:closing]
    if "disable-model-invocation:" in frontmatter:
        fail(f"canonical frontmatter must remain host-neutral: {path}")
    path.write_text(
        text[:closing] + f"\n{CLAUDE_MANUAL_FIELD}" + text[closing:]
    )


def generate(root: Path, host: str, skills: list[Path]) -> None:
    root.mkdir(parents=True)
    for source in skills:
        destination = root / source.name
        shutil.copytree(source, destination, copy_function=shutil.copy2)
    if host == "claude":
        available_skills = {skill.name for skill in skills}
        unknown_skills = CLAUDE_MANUAL_ONLY_SKILLS - available_skills
        if unknown_skills:
            fail(
                "unknown Claude manual-only skills: "
                + ", ".join(sorted(unknown_skills))
            )
        for skill in sorted(CLAUDE_MANUAL_ONLY_SKILLS):
            add_claude_manual_field(root / skill / "SKILL.md")


def compare(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []
    if not actual.is_dir() or actual.is_symlink():
        return [f"missing or invalid generated directory: {actual}"]
    comparison = filecmp.dircmp(expected, actual)
    for name in comparison.left_only:
        differences.append(f"missing: {actual / name}")
    for name in comparison.right_only:
        differences.append(f"extra: {actual / name}")
    for name in comparison.funny_files:
        differences.append(f"type mismatch: {actual / name}")
    for name in comparison.common_funny:
        differences.append(f"type mismatch: {actual / name}")
    for name in comparison.common_files:
        expected_file = expected / name
        actual_file = actual / name
        if expected_file.read_bytes() != actual_file.read_bytes():
            differences.append(f"content differs: {actual_file}")
        expected_mode = stat.S_IMODE(expected_file.stat().st_mode)
        actual_mode = stat.S_IMODE(actual_file.stat().st_mode)
        if expected_mode != actual_mode:
            differences.append(f"mode differs: {actual_file}")
    for name in comparison.common_dirs:
        differences.extend(compare(expected / name, actual / name))
    return differences


def replace(target: Path, generated: Path) -> None:
    allowed_parent = (REPO / "plugins").resolve()
    if target.parent.parent.parent.resolve() != allowed_parent:
        fail(f"refusing to replace unexpected target: {target}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(generated, target, copy_function=shutil.copy2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("write", "check"))
    args = parser.parse_args()
    skills = validate_source()

    with tempfile.TemporaryDirectory(prefix="skill-packages-") as temp:
        temp_root = Path(temp)
        differences: list[str] = []
        for host, target in TARGETS.items():
            generated = temp_root / host / "skills"
            generate(generated, host, skills)
            if args.mode == "write":
                replace(target, generated)
            else:
                differences.extend(compare(generated, target))
        if differences:
            print("Generated plugin skills are out of sync:", file=sys.stderr)
            print("\n".join(f"- {item}" for item in differences), file=sys.stderr)
            fail("Run: task package")


if __name__ == "__main__":
    main()
