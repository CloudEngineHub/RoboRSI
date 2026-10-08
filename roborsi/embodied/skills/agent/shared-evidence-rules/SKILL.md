---
name: shared-evidence-rules
kind: agent
role: shared
description: Rules and artifact layout every role follows - public evidence only, where an episode's evidence lives, and how to read skills and memory.
---

# Shared Evidence Rules

1. Use only public evidence: camera images, robot proprioception, tool
   results, plans, summaries, the task wiki and skill source. Never read or
   request simulator ground truth (object poses, BDDL goal state, success
   predicates). The simulator verdict exists only after an episode ends.
2. An episode workspace contains `plan.md`, `summary.md`, `review.md` and
   `rollout/round_NN/`. Each round directory holds `*/trace.json` (every
   tool call, arguments and result), `tick_*.jpg` camera frames and
   `final_view_*.jpg`, the camera views captured when the round ended.
3. Engineer capabilities live in `roborsi/embodied/skills/base/<skill>/<ns>/`
   (`SKILL.md` contract, `policy.py` implementation) and compound skills in
   `roborsi/embodied/skills/atomic/`. Read the source before blaming or
   changing a skill.
4. Task memory is the task wiki: observed traces, Manager-approved leads and
   cross-task lessons. Treat it as evidence from earlier episodes, never as a
   description of the current scene.
5. Cite the step, round or image behind every claim. Unknown stays unknown.
