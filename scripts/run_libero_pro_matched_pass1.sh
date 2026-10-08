#!/usr/bin/env bash
set -euo pipefail

# Current-release, frozen LIBERO-PRO seed-0 baseline matching the resource
# budget used by the historical adaptive campaign. This does not replay or
# claim to reproduce the historical cross-release 80/120 result.

: "${ROBORSI_LIBERO_BDDLDIR:?configure the official LIBERO-PRO BDDL directory}"
: "${ROBORSI_LIBERO_INITDIR:?configure the official LIBERO-PRO init directory}"
: "${ROBORSI_PYROKI_PORT:?start PyRoKi and export its port}"

output="${1:-$HOME/.roborsi/evals/suites/libero-pro-matched-pass1}"
workers="${ROBORSI_EVAL_WORKERS:-8}"
model="${ROBORSI_EVAL_MODEL:?set ROBORSI_EVAL_MODEL to the model id served by your endpoint}"

export ROBORSI_OPENAI_TRANSPORT="${ROBORSI_OPENAI_TRANSPORT:-responses}"
export ROBORSI_LIBERO_SUITES="${ROBORSI_LIBERO_SUITES:-libero_goal_task,libero_goal_object,libero_goal_swap,libero_goal_lan,libero_spatial_task,libero_spatial_object,libero_spatial_swap,libero_spatial_lan,libero_object_task,libero_object_object,libero_object_swap,libero_object_lan}"
exec roborsi eval-suite \
  --backend libero-pro \
  --atomic libero_pick_place \
  --pass-at 1 \
  --seed-start 0 \
  --workers "${workers}" \
  --tool-budget 80 \
  --infra-retries 2 \
  --planner-model "${model}" \
  --engineer-model "${model}" \
  --reviewer-model "${model}" \
  --reasoning-effort medium \
  --out "${output}"
