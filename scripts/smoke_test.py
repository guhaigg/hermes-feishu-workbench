"""Minimal smoke test for the publishable plugin repo."""

from __future__ import annotations

from pathlib import Path

from feishu_workbench_plugin import register


class FakeContext:
    def __init__(self) -> None:
        self.hooks = []
        self.skills = []
        self.commands = []

    def register_hook(self, hook_name, callback):
        self.hooks.append((hook_name, callback))

    def register_skill(self, name, path, description=""):
        self.skills.append((name, Path(path), description))

    def register_cli_command(self, name, help, setup_fn, handler_fn=None, description=""):
        raise AssertionError("This plugin should not register Hermes CLI commands.")


def main() -> None:
    ctx = FakeContext()
    register(ctx)

    assert any(name == "pre_llm_call" for name, _callback in ctx.hooks)
    assert len(ctx.skills) == 3
    assert all(path.exists() for _, path, _ in ctx.skills)
    assert ctx.commands == []
    print("smoke test passed")


if __name__ == "__main__":
    main()
