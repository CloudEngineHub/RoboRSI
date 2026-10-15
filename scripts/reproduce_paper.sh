#!/usr/bin/env bash
# One-click reproduction of the simulation results in Table 1 of the paper
# (arXiv:2610.12424).
#
#   scripts/reproduce_paper.sh libero        # 30 tasks x 5 episodes, evolve
#   scripts/reproduce_paper.sh libero-pro    # 120 tasks x 5 episodes, evolve
#   scripts/reproduce_paper.sh libero-plus   # 840 instances, frozen LIBERO library
#
# libero and libero-pro set up everything that scripts/reproduce_libero_pro.sh
# sets up (environment, LIBERO-PRO checkout and assets, PyRoKi, optional
# GraspGen) and then run scripts/run_paper_campaign.sh. libero-plus holds the
# skill library and wiki produced by the libero run fixed, as in the paper, so
# run libero first.
#
# Same requirements as scripts/reproduce_libero_pro.sh (OPENAI_API_KEY,
# ROBORSI_EVAL_MODEL, optional GraspGen variables). Every step is resumable:
# re-run the same command to continue an interrupted campaign.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUITES="${HOME}/.roborsi/evals/suites"
LIBERO_OUT="${ROBORSI_PAPER_LIBERO_OUT:-${SUITES}/paper-libero}"
benchmark="${1:?usage: reproduce_paper.sh libero|libero-pro|libero-plus [out]}"

case "${benchmark}" in
  libero)
    ROBORSI_REPRO_BENCHMARK=libero exec "${REPO_ROOT}/scripts/reproduce_libero_pro.sh" "${2:-${LIBERO_OUT}}" ;;
  libero-pro)
    ROBORSI_REPRO_BENCHMARK=libero-pro exec "${REPO_ROOT}/scripts/reproduce_libero_pro.sh" "${2:-${SUITES}/paper-libero-pro}" ;;
  libero-plus)
    library="${LIBERO_OUT}/library"
    if [ ! -f "${LIBERO_OUT}/summary.json" ] || [ ! -d "${library}/roborsi" ]; then
      echo "run 'scripts/reproduce_paper.sh libero' first: LIBERO-Plus evaluates the library it produces (${library})" >&2
      exit 2
    fi
    # The LIBERO library and its wiki, held fixed (frozen mode).
    export ROBORSI_HOME="${ROBORSI_HOME:-${HOME}/.roborsi-paper-libero}"
    # Import RoboRSI from the library copy, not from the installed checkout.
    export PYTHONPATH="${library}${PYTHONPATH:+:${PYTHONPATH}}"
    exec "${library}/scripts/reproduce_libero_plus.sh" "${2:-${SUITES}/paper-libero-plus}" ;;
  *)
    echo "unknown benchmark '${benchmark}' (libero | libero-pro | libero-plus)" >&2; exit 2 ;;
esac
