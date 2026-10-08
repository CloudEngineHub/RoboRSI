"""Episode-level simulator gate for a skill change without its own harness.

Applies the candidate in a throw-away git worktree at HEAD and runs frozen
RoboRSI episodes on the source task with development seeds that are disjoint
from the evaluation seeds. The candidate passes when enough episodes succeed.
Nothing is published here; the Manager applies the change afterwards.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

R = Path(__file__).resolve().parents[3]
DEV_SEEDS = [int(s) for s in os.environ.get("ROBORSI_GATE_SEEDS", "21,22").split(",")]
MIN_PASS = int(os.environ.get("ROBORSI_GATE_MIN_PASS", str(len(DEV_SEEDS))))


@dataclass
class EpisodeGateReport:
    overall_pass: bool
    note: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"overall_pass": self.overall_pass, "note": self.note,
                "details": self.details, "kind": "episode_gate"}


def _write_candidate(tree: Path, q: dict) -> None:
    name, code = str(q.get("name", "")), str(q.get("new_code", ""))
    if not name or not code:
        raise ValueError("candidate has no skill name or code")
    target = tree / "roborsi/embodied/skills/base" / name / "libero"
    target.mkdir(parents=True, exist_ok=True)
    (target / "policy.py").write_text(code, encoding="utf-8")
    if q.get("skill_md"):
        (target / "SKILL.md").write_text(str(q["skill_md"]), encoding="utf-8")
    if not (target / "SKILL.md").exists():
        raise ValueError("a new skill needs a SKILL.md")


def run(q: dict, task_key: str | None) -> EpisodeGateReport:
    if not task_key:
        return EpisodeGateReport(False, "no source task to validate on")
    tmp = Path(tempfile.mkdtemp(prefix="roborsi-gate-"))
    tree = tmp / "tree"
    try:
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), "HEAD"],
                       cwd=R, check=True, capture_output=True)
        _write_candidate(tree, q)
        # Eval mode needs a clean tree; commit the candidate in the throw-away worktree.
        subprocess.run(["git", "add", "-A"], cwd=tree, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=RoboRSI Gate", "-c", "user.email=gate@localhost",
                        "commit", "-q", "-m", "gate candidate"], cwd=tree, check=True,
                       capture_output=True)
        out = tmp / "campaign"
        model = os.environ.get("ROBORSI_EVAL_MODEL") or os.environ.get(
            "ROBORSI_MANAGER_MODEL", "gpt-5.6-sol")
        env = {**os.environ, "PYTHONPATH": str(tree), "ROBORSI_RUN_MODE": "frozen",
               # Gate episodes must not touch the campaign's role sessions.
               "ROBORSI_ROLE_SESSION": "0"}
        cmd = [sys.executable, "-c",
               "import sys; from roborsi.cli.commands import app; "
               "sys.argv[0] = 'roborsi'; app()", "eval-suite",
               "--backend", os.environ.get("ROBORSI_HARNESS_BACKEND", "libero-pro"),
               "--task", task_key, "--seed-start", str(DEV_SEEDS[0]),
               "--pass-at", str(len(DEV_SEEDS)), "--workers", "1",
               "--tool-budget", os.environ.get("ROBORSI_GATE_TOOL_BUDGET", "80"),
               "--run-mode", "frozen", "--run-all-seeds", "--planner-model", model,
               "--engineer-model", model, "--reviewer-model", model,
               "--out", str(out)]
        proc = subprocess.run(cmd, cwd=tree, env=env, capture_output=True,
                              text=True, timeout=int(os.environ.get(
                                  "ROBORSI_GATE_TIMEOUT_S", "7200")))
        rows = []
        journal = out / "episodes.jsonl"
        if journal.exists():
            rows = [json.loads(line) for line in journal.read_text().splitlines() if line.strip()]
        verdicts = {}
        for row in rows:
            if row.get("verdict") in ("success", "failure"):
                verdicts[int(row["seed"])] = row["verdict"]
        passes = sum(v == "success" for v in verdicts.values())
        ok = passes >= MIN_PASS and len(verdicts) == len(DEV_SEEDS)
        return EpisodeGateReport(
            ok, f"episode gate {passes}/{len(DEV_SEEDS)} on {task_key} "
                f"seeds {DEV_SEEDS} (need {MIN_PASS})",
            {"verdicts": verdicts, "returncode": proc.returncode})
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(tree)],
                       cwd=R, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
