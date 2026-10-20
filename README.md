# realgain

**Is the improvement real?** A small, dependency-light toolkit for checking the gains a self-improving AI system
claims: prompt/playbook evolution, workflow search (AFlow-style), self-modifying agents (DGM-style), or anything
that tries changes, scores them and keeps the winners.

Every kept change *claims* a gain. `realgain` reads your evaluation log and tells you, for each kept change, how much
of that gain is

| | what it means | what reveals it |
|---|---|---|
| **real** | better on tasks the loop never saw, by a measure it did not optimise | held-out tasks + ground truth |
| **luck** | kept because its evaluation happened to come out high (winner's curse) | re-running the same tasks |
| **fitting the selection tasks** | better only on the tasks used to choose it | held-out tasks |
| **a pleased scorer** | an LLM judge / rubric likes it, the answer key does not | a `truth` score next to the optimised `score` |
| **grader access** | the agent read or touched answers, tests, the scorer | the agent's command log |

```bash
pip install -e .            # numpy only; add [plot] for figures
realgain --demo             # our contract-review loop, judged by an LLM
realgain my_log.jsonl --json report.json --plot report.png
```

```python
from realgain import Logger, report, to_markdown
log = Logger("evals.jsonl")                       # call inside your loop
log.record(version="v7", parent="v4", task="doc-12", score=8.0, truth=0.9,
           split="heldout", phase="recheck", accepted=True, generation=7, commands=cmds)
print(to_markdown(report("evals.jsonl")))
```

## What you get

For each accepted version, compared with the starting version on the same tasks (paired, averaged over tasks,
95% t intervals over tasks):

- **step vs parent**: is the accepted step bigger than task-sampling noise?
- **seen by loop**: the gain in the runs the loop used to decide.
- **expected on new tasks**: the loop's number corrected for having picked winners, from the log alone (no re-runs).
- **re-run**: the gain in fresh runs on the same tasks. *seen − re-run* = luck.
- **held-out score / truth**: the gain on tasks the loop never saw. *re-run − held-out* = fitting the selection tasks.
- **detectable**: the smallest true change your tasks could reveal (~80% power). "Not shown" with a detectable
  threshold of 10 points means *you could not have seen* a 5-point gain, not that there was none.
- **p, Holm-adjusted** across all accepted versions (a loop that accepts 10 changes will find one "significant" by chance).
- a **verdict**: `REAL`, `WORSE`, `SCORE ONLY`, `FITS SELECTION`, `LUCK`, `GRADER ACCESS`, `UNCHECKED GAIN`, `NOT SHOWN`.

And for the loop as a whole: noise levels (task sampling vs run-to-run), whether the best version's lead over the rest
exceeds what picking the best of k equal versions gives by chance, the correlation between the optimised score and the
ground truth, and every run that touched a grader file with how much it gained by doing so.

## What it found on real logs (`examples/`)

| log | accepted changes | verdicts |
|---|---|---|
| AFlow, 6 benchmarks (public logs) | 30 | 8 beyond task noise but uncheckable, since AFlow logs no held-out tasks or re-runs (`UNCHECKED GAIN`; several are recoveries from a broken first round on DROP); 20 `NOT SHOWN`; 2 without paired data. On HumanEval the best workflow's lead over the average is what picking the best of 21 equal workflows gives by chance (p = 0.66). |
| DGM, SWE-bench, 3 runs (public logs) | 89 archived | 3 steps beyond task noise (all in the main run), 86 `NOT SHOWN` |
| Our loop R1: LLM judge selects, contract review | 4 | 3 `SCORE ONLY` (judge +1.2 to +1.5 / 10 on held-out contracts, answer-key accuracy +0.0 to +2.7 pts), 1 `NOT SHOWN` |
| Our loop R2: answer key selects | 3 | 3 `NOT SHOWN`; the loop saw +2/+4/+6 pts, re-runs gave −3/+4/0 |
| Our loop R3: answer key selects, key visible in the agent's folder | 1 | `GRADER ACCESS`: runs that read the key scored +14 pts over honest runs of the same version |

## How reliable is it? (`benchmarks/`)

The toolkit is itself tested on simulated loops whose truth is known, on AFlow's public logs, and on our own loops:

- **It rarely cries wolf.** On simulated loops it said REAL for a version that was not better in ≤ 2.2% of cases, and
  WORSE for one that was not worse in ≤ 1.7%.
- **It misses small gains unless you give it enough held-out tasks.** With 30 held-out tasks it found 8% of true gains
  above 10 points; with 100, 71%. Every report prints the smallest change your tasks could detect.
- **Intervals are calibrated** (t intervals: 95–96% coverage even with 5 tasks; the percentile bootstrap used before
  v0.3 covered only 85%).
- **`expected on new tasks` removes most of a loop's over-claim without any re-runs** (simulations: +22 → +3 pts with
  10 selection tasks; AFlow half-splits: over-claim reduced on all 4 benchmarks tested) but not with very few
  selection tasks, where it can only say the candidates are indistinguishable.
- **`realgain.audit`**: a handful of ground-truth labels reliably stops a false "B is better" claim (never confirmed in
  any case tested); confirming a small real gain takes dozens of labels.

Details and every number: [`benchmarks/README.md`](benchmarks/README.md).

## Auditing a judge's claim with a few labels

```python
from realgain import label_budget, classical, ppi
r = label_budget(judge_diff, truth_diff)      # per-task differences B - A, on tasks where you HAVE labels (pilot)
classical(truth_diff_on_m_labelled_tasks)      # -> estimate, 95% interval, verdict
ppi(judge_diff_all_tasks, labelled_idx, truth_diff_labelled)   # uses the judge on all tasks; helps only if it tracks truth
```

## Files

- `FORMAT.md`: the log format, and the five cheapest things to log so the checks have something to work with.
- `CHECKLIST.md`: a ten-minute self-check before you believe a curve that goes up.
- `adapters/`: AFlow and DGM public logs, and our own loop, to the realgain format.
- `examples/`: reports (`.report.md`, `.report.json`, figures) on all of the above.
- `tests/`: simulations with known answers.
- `benchmarks/`: how well the toolkit itself works (simulations, AFlow, our loops).

The study this came from, with all code, logs, the pre-registration and an independent re-check: [`study/`](study/). Write-up (Chinese): [`study/writeup_zh.md`](study/writeup_zh.md).

MIT licence.
