"""Low-level driver for the codex / claude / copilot CLIs.

RoboRSI runs the Planner, Reviewer and Manager as persistent CLI sessions
through ``codex_runner.CodexRunner`` (see ``roborsi/agents/sessions/persistent_agent.py``).
Adapted from the MIT-licensed ArgusBot ``codex_autoloop`` module
(https://github.com/waltstephen/ArgusBot); only the runner, backend and model
modules are kept.
"""
from __future__ import annotations

__all__: list[str] = []
