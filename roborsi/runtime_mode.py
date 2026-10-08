"""Process-local RoboRSI run mode.

``evolve`` is the normal self-evolution runtime. ``frozen`` disables
evolution: no skill, task wiki, plan archive, proposal or training dataset is
updated. Planner and Reviewer keep their persistent role sessions in both
modes. ``eval`` is accepted as a legacy name for ``frozen``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar
from enum import Enum
from typing import Iterator


class RunMode(str, Enum):
    EVOLVE = "evolve"
    FROZEN = "frozen"
    EVAL = "frozen"  # legacy alias

    @classmethod
    def _missing_(cls, value):
        if str(value).strip().lower() == "eval":
            return cls.FROZEN
        return None


class EvolutionDisabledError(RuntimeError):
    """Raised when a mutation is attempted during a frozen evaluation."""


_ACTIVE_MODE: ContextVar[RunMode | None] = ContextVar(
    "roborsi_active_run_mode", default=None
)


def parse_mode(value: str | RunMode | None) -> RunMode:
    if isinstance(value, RunMode):
        return value
    raw = str(value or RunMode.EVOLVE.value).strip().lower()
    try:
        return RunMode(raw)
    except ValueError as exc:
        choices = ", ".join(mode.value for mode in RunMode)
        raise ValueError(f"run mode must be one of: {choices}; got {value!r}") from exc


def current_mode() -> RunMode:
    active = _ACTIVE_MODE.get()
    if active is not None:
        return active
    return parse_mode(os.environ.get("ROBORSI_RUN_MODE"))


def is_eval_mode() -> bool:
    return current_mode() is RunMode.EVAL


def evolution_enabled() -> bool:
    return current_mode() is RunMode.EVOLVE


def require_evolution(action: str) -> None:
    if not evolution_enabled():
        raise EvolutionDisabledError(
            f"{action} is disabled in frozen mode; the released capability set is frozen"
        )


def evaluation_prompt() -> str:
    return (
        "FROZEN MODE (binding): the released skills, task wiki and plans are "
        "frozen. Use only existing published capabilities. You may replan within "
        "this episode, but do not create, register, propose, promote, train, or "
        "persist any capability. If the frozen system cannot complete the task, "
        "report failure honestly."
    )


@contextmanager
def use_run_mode(mode: str | RunMode) -> Iterator[RunMode]:
    parsed = parse_mode(mode)
    token = _ACTIVE_MODE.set(parsed)
    try:
        yield parsed
    finally:
        _ACTIVE_MODE.reset(token)
