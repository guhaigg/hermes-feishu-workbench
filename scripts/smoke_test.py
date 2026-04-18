"""Minimal smoke test for the publishable plugin repo."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from feishu_workbench_plugin import register


class FakeContext:
    def __init__(self) -> None:
        self.hooks = []
        self.skills = []
        self.commands = []
        self.tools = []

    def register_hook(self, hook_name, callback):
        self.hooks.append((hook_name, callback))

    def register_skill(self, name, path, description=""):
        self.skills.append((name, Path(path), description))

    def register_tool(self, name, toolset, schema, handler, **kwargs):
        self.tools.append((name, toolset, schema, handler, kwargs))

    def register_cli_command(self, name, help, setup_fn, handler_fn=None, description=""):
        raise AssertionError("This plugin should not register Hermes CLI commands.")


def main() -> None:
    ctx = FakeContext()
    register(ctx)

    assert any(name == "pre_llm_call" for name, _callback in ctx.hooks)
    assert len(ctx.skills) == 3
    assert all(path.exists() for _, path, _ in ctx.skills)
    assert len(ctx.tools) == 9
    assert {toolset for _, toolset, *_ in ctx.tools} == {"feishu-workbench-lite"}
    assert all(name.startswith("feishu_lite_") for name, *_ in ctx.tools)
    assert ctx.commands == []
    print("smoke test passed")


if __name__ == "__main__":
    main()
