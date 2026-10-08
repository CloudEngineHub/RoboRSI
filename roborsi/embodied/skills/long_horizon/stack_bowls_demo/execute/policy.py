"""long_horizon.stack_bowls_demo.execute — retired direct entry point.

The long-horizon execution path is the 3-role triangle
(Planner.decompose → LHExecutor → Reviewer.review_lh), driven by ``run_long_horizon_episode`` in
``roborsi.channels.core.agent``. This skill dir is kept
only so discover() registers ``stack_bowls_demo.execute`` (the wiki +
LH-intent enumeration both key off the ``.execute`` name); it no longer
runs anything itself.
"""

from __future__ import annotations

from typing import Any


def run(**_: Any) -> dict[str, Any]:
    raise NotImplementedError(
        "stack_bowls_demo.execute is not directly runnable — long-horizon "
        "tasks run through the 3-role triangle (run_long_horizon_episode: "
        "Planner.decompose → LHExecutor → Reviewer.review_lh)."
    )
