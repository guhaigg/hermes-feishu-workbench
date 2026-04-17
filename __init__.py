"""Directory-plugin entrypoint for Hermes.

This keeps git-installed / folder-installed plugin loading working while the
publishable Python package lives under ``feishu_workbench_plugin/``.
"""

from .feishu_workbench_plugin import register

__all__ = ["register"]
