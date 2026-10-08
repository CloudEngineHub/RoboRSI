# Contributing

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,web]"
pytest -q
```

The simulator-specific tests require their upstream checkouts and runtime
dependencies. Configure those paths with `ROBORSI_ROBOTWIN_ROOT` and
`ROBORSI_BICOORD_ROOT`.

## Required invariants

- Keep hidden simulator state and success criteria out of Planner, Engineer,
  Reviewer, plans, skills, prompts, and tool outputs.
- Count success only from the final post-episode simulator verdict.
- Keep credentials, internal endpoints, and machine-specific paths outside the
  repository.
- Preserve failed runs and exact resume state in runtime storage.
- Submit complete skill implementations through the existing proposal and
  harness-gate path.
- Keep `eval` frozen: evaluation records may not enter skill history, task
  memory, proposal queues, persistent role sessions, or training datasets.

## Before opening a pull request

```bash
python -m roborsi.agents.safety.wiki_gt_check
python -m compileall -q roborsi scripts tests
pytest -q
```

Also check the terminal UI when changing it:

```bash
npm --prefix roborsi/frontend/tui install
npm --prefix roborsi/frontend/tui run typecheck
```
