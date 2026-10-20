# Log format

One JSON object per line; one line per (version, task, run). Only `version`, `task` and `score` are required.

| field | meaning |
|---|---|
| `version` | id of the system version that produced this run (a prompt, a playbook, a workflow, an agent commit) |
| `task` | id of the task / question / document |
| `score` | the number the loop optimises (benchmark accuracy, judge score, reward) |
| `parent` | version this one was derived from; empty for the starting version |
| `accepted` | whether the loop kept this version |
| `generation` | iteration number |
| `split` | `selection` (tasks the loop used to decide; default) or `heldout` (tasks it never saw in any form) |
| `phase` | `acceptance` (default: runs the loop itself used to decide) or `recheck` (fresh runs you made afterwards to check) |
| `repeat` | run number when the same version ran several times on the same task |
| `truth` | a second score the loop did NOT optimise: answer key, expert label, executed test. Optional but the most valuable field |
| `commands` | list of shell commands / tool calls the agent ran, for the grader-access audit |

How to get the most out of it, cheapest first:
1. Log every candidate's per-task scores, not just the average (gives the noise and the selection checks).
2. Keep 15-50 tasks the loop never sees and run each accepted version on them once (`split: heldout`).
3. Re-run each accepted version on its selection tasks 1-2 more times (`phase: recheck`) to measure luck.
4. If the score is an LLM judge or rubric, attach an answer-key / expert `truth` for at least the held-out tasks.
5. Log the agent's commands so access to graders, tests or expected outputs can be audited.

Adapters in `adapters/` convert AFlow and DGM published logs and our own loop logs.
