# Evaluating the evaluator

Every number below is reproducible with the scripts in this folder (outputs: `results_*.json` / `.txt`).

## 1. Intervals: the percentile bootstrap was too narrow with few tasks

95% intervals for a paired difference with no true difference (contract-like tasks, 10 items each), 2000 simulations:

| tasks | percentile bootstrap (v0.2) | t interval (v0.3) |
|---|---|---|
| 5 | 85% | 96% |
| 10 | 90% | 95% |
| 15 | 93% | 96% |
| 30 | 93% | 95% |
| 60 | 93% | 94% |

Loops often decide on 5–10 tasks, so v0.3 uses t intervals. Because each task's difference already contains both
versions' run noise, no separate run-level resampling is needed. The study's conclusions were re-checked with t
intervals and none changed (retail: −12.4 pts, 95% interval −22.9 to −1.9).

## 2. Correcting for picking winners, without re-runs (`realgain.shrink`)

A loop keeps the candidate whose evaluation came out best, so the number in its log overstates how that candidate will
do on new tasks. `expected on new tasks` corrects it using only the log: every candidate tried, kept or not, tells us how
spread out true gains are versus noise (normal–normal empirical Bayes; the starting version's noise is shared by all
candidates and does not count as spread).

Simulated loops (12 candidates, true gains spread 3 pts, 0/1 tasks), predicting the kept candidate's true gain:

| selection tasks | over-claim of the loop's own number | after correction | mean abs. error: loop → corrected |
|---|---|---|---|
| 5 | +31 pts | +6 | 35 → 22 |
| 10 | +22 | +3 | 23 → 14 |
| 30 | +13 | +2 | 14 → 8 |
| 30, true spread 10 pts | +8 | −1 | 11 → 9 |

AFlow public logs (pick the best round on a random half of the questions, measure it on the other half, 40 splits):
over-claim HumanEval +8.2 → +7.3 pts, MBPP +0.8 → +0.6, HotpotQA +5.0 → +0.4, DROP +3.6 → +1.8; error falls on all four.

Full simulated loops (6 generations): the loop's own number over-claims by ~23 pts; the correction leaves ~10.

**Where it fails:** our own contract loops (12 candidates, 5 selection tasks). It shrinks every candidate to the average
("these tasks cannot tell them apart") and predicts held-out gains worse than the raw number (mean error 1.4 → 3.1 pts on
R2). With that little data, nothing replaces held-out tasks. Its ±band covers the truth 91% (5 tasks) to 97% of the time.

## 3. Auditing a judge's claim with a few ground-truth labels (`realgain.audit`)

You have both versions' outputs on N tasks and the judge says B is better; labels cost money. With m labels:

| case | N | answer with all labels | m needed to reach it ≥ 90% of the time | wrongly says "B better" (any m) |
|---|---|---|---|---|
| our retail memos (judge fooled, truth −12 pts) | 21 | worse | 20 | 0% |
| our contracts (judge fooled, truth 0) | 15 | not settled | 3 | ≤ 1% |
| simulated: judge fooled, truth 0 | 200 | not settled | 5 | ≤ 3% |
| simulated: real +3 pt gain | 200 | better | > 100 (64% at m = 100) | 0% |

So a handful of labels is enough to **stop a false claim** (it is never confirmed), but confirming a small real gain or
catching a real loss takes dozens. Prediction-powered inference (using the judge on all N tasks, corrected on the m
labelled ones) only helps when the judge tracks the truth: +9 points of agreement at m = 100 when the judge correlates
0.6 with the truth, none (slightly worse at small m) in our real cases, where it correlates ±0.3.

## 4. The whole toolkit on simulated loops with known truth (`simulate_loops.py`)

150 loops per setting, 6 generations, 2 candidates each, 10 selection tasks; every kept version re-run twice and tested
on held-out tasks.

| setting | wrongly says REAL (true change ≤ 0) | wrongly says WORSE (true ≥ 0) | finds REAL when true gain > 10 pts | grader access flagged |
|---|---|---|---|---|
| answer-key loop, 30 held-out tasks | 0.0% | 1.7% | 8% | – |
| answer-key loop, 100 held-out tasks | 1.5% | 1.5% | 71% | – |
| judge loop, half the versions flatter the judge | 1.3% | 0.3% | 13% | – |
| answer-key loop, grader reachable | 2.2% | 0.0% | 40% | 100% when it happened, 0% otherwise |

The 95% interval for the held-out ground-truth gain covered the truth 92–95% of the time.

**Reading:** realgain rarely cries wolf (≤ 2% false REAL/WORSE), but with 30 held-out tasks it misses most real gains
under 10 points. `NOT SHOWN` with a 30-task held-out set mostly means "too few tasks", which is why every report prints
the smallest detectable change. Grader-access detection here is easy because the simulated agent leaves the access in its
command log; an agent that hides it would not be caught.
