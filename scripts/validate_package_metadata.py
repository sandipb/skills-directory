#!/usr/bin/env python3
"""Validate shared package identity and invocation metadata."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
CODEX_ROOT = REPO / "plugins/codex/sandipb-agents"
CLAUDE_ROOT = REPO / "plugins/claude/sandipb-agents"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    return yaml.safe_load(text.split("\n---\n", 1)[0][4:])


codex = load_json(CODEX_ROOT / ".codex-plugin/plugin.json")
claude = load_json(CLAUDE_ROOT / ".claude-plugin/plugin.json")
codex_market = load_json(REPO / ".agents/plugins/marketplace.json")
claude_market = load_json(REPO / ".claude-plugin/marketplace.json")

for field in ("name", "version", "description", "license"):
    if codex.get(field) != claude.get(field):
        raise SystemExit(f"host manifests disagree on {field}")

if codex_market["plugins"][0]["name"] != codex["name"]:
    raise SystemExit("Codex marketplace and manifest names disagree")
if codex_market["plugins"][0]["source"]["path"] != "./plugins/codex/sandipb-agents":
    raise SystemExit("Codex marketplace source path is incorrect")
if claude_market["plugins"][0]["name"] != claude["name"]:
    raise SystemExit("Claude marketplace and manifest names disagree")
if claude_market["plugins"][0]["source"] != "./plugins/claude/sandipb-agents":
    raise SystemExit("Claude marketplace source path is incorrect")

canonical_edit = frontmatter(REPO / "skills/edit-technical-docs/SKILL.md")
codex_edit = frontmatter(CODEX_ROOT / "skills/edit-technical-docs/SKILL.md")
claude_edit = frontmatter(CLAUDE_ROOT / "skills/edit-technical-docs/SKILL.md")
if any(
    "disable-model-invocation" in metadata
    for metadata in (canonical_edit, codex_edit, claude_edit)
):
    raise SystemExit("Technical-editing skill must allow Claude model invocation")

openai = yaml.safe_load(
    (CODEX_ROOT / "skills/edit-technical-docs/agents/openai.yaml").read_text()
)
if "allow_implicit_invocation" in openai.get("policy", {}):
    raise SystemExit("Technical-editing skill must use Codex's default invocation policy")
