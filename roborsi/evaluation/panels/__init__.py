"""Fixed evaluation panels shipped with RoboRSI.

``libero_plus_840.json``: the LIBERO-Plus panel, 840 perturbation instances
(7 perturbation types x 120) of the 30 LIBERO spatial/object/goal tasks.

    python -m roborsi.evaluation.panels breakdown <campaign_dir> [panel]

prints success per perturbation type from a campaign journal.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

PANEL_DIR = Path(__file__).resolve().parent


def panel_path(name: str) -> Path:
    path = Path(name)
    return path if path.exists() else PANEL_DIR / f"{name}.json"


def load_panel(name: str) -> dict:
    return json.loads(panel_path(name).read_text(encoding="utf-8"))


def breakdown(campaign_dir: str, name: str = "libero_plus_840") -> dict:
    """Success / valid episodes per perturbation type, last terminal row wins."""
    instances = load_panel(name)["instances"]
    terminal = {}
    for line in (Path(campaign_dir) / "episodes.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("verdict") in ("success", "failure"):
            terminal[row["task_key"]] = row["verdict"] == "success"
    table = defaultdict(lambda: [0, 0])
    for key, kind in instances.items():
        if key in terminal:
            table[kind][0] += int(terminal[key])
            table[kind][1] += 1
    total = [sum(v[0] for v in table.values()), sum(v[1] for v in table.values())]
    return {"per_type": {k: {"success": s, "valid": n} for k, (s, n) in sorted(table.items())},
            "total": {"success": total[0], "valid": total[1], "planned": len(instances)}}


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] != "breakdown":
        sys.exit("usage: python -m roborsi.evaluation.panels breakdown <campaign_dir> [panel]")
    result = breakdown(sys.argv[2], *(sys.argv[3:4]))
    for kind, v in result["per_type"].items():
        rate = v["success"] / v["valid"] if v["valid"] else 0.0
        print(f"{kind:12s} {v['success']:4d}/{v['valid']:<4d} ({rate:.1%})")
    t = result["total"]
    print(f"{'total':12s} {t['success']:4d}/{t['valid']:<4d} of {t['planned']} planned")
