"""Manager chat entry — feed a Feishu user message straight to the persistent
RoboRSI Manager session and return its reply.

Per operator spec (2026-06-29): a Feishu message IS a turn of conversation with
the Manager. We reuse ``persistent_agent.run`` (one persistent Claude session,
thread_id persisted across turns) with the Manager role prompt (``manager/
MANAGER.md``) so the Manager — the approver + dispatcher — reads the user, can
drive the Planner→Engineer→Reviewer triangle and apply gated proposals itself,
and replies. A flock serialises concurrent Feishu messages onto the single
Manager session so they don't interleave / corrupt the thread.
"""
from __future__ import annotations

import fcntl
from pathlib import Path

from roborsi.agents.sessions import persistent_agent

_REPO = Path(__file__).resolve().parents[3]
_MANAGER_MD = Path(__file__).resolve().parent / "manager" / "MANAGER.md"
_LOCK = Path.home() / ".roborsi" / "manager_chat.lock"
_MODEL = "claude-opus-4-8"


def _system_prompt() -> str:
    try:
        return _MANAGER_MD.read_text(encoding="utf-8")
    except Exception:
        return "You are the RoboRSI Manager. Respond concisely and act on the user's request."


def list_sessions() -> list[str]:
    """The Manager has a single session."""
    return ["manager"]


def reply(text: str, session: str | None = None) -> str:
    """One Manager turn for an operator message, in the same persistent
    ``manager:manager`` session the review cycle uses, so the Manager keeps one
    memory. flock serialises concurrent messages. ``session`` is accepted for
    the dashboard's API and ignored."""
    _LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        return persistent_agent.run_role(
            "manager", "manager", text,
            system_prompt=_system_prompt(), model=_MODEL,
        )
