"""Web layer for the board: the self-evolution dashboard (:8787,
:mod:`.evo_app` + :mod:`.page`, over :mod:`.evo_readers`), reading trace.db,
campaign logs, the wiki and review queues through the shared readers here."""

from roborsi.embodied.board.web.readers import (
    campaign_status,
    evolution_overview,
    list_sessions,
    manager_overview,
    session_turns,
    task_evolution,
    task_overview,
    task_progress,
)
from roborsi.embodied.board.web.server import main, serve

__all__ = [
    "campaign_status",
    "evolution_overview",
    "list_sessions",
    "main",
    "manager_overview",
    "serve",
    "session_turns",
    "task_evolution",
    "task_overview",
    "task_progress",
]
