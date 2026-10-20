# realgain report: AFlow MBPP

8170 records · starting version `round_1` · held-out tasks: NO (gains cannot be checked on new tasks) · ground truth: no

**Noise.** Starting version: mean 0.728 over 86 tasks; task-sampling SE of a mean 0.048; run-to-run SE of a mean 0.001.

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `round_2` | 2 | **UNCHECKED GAIN** | +0.107 [+0.039, +0.175] n=86 | +0.107 [+0.039, +0.175] n=86 | +0.106 ± 0.041 | – | – | – | ≥ 0.096 | 0.005 |
| `round_15` | 15 | **NOT SHOWN** | +0.012 [-0.015, +0.038] n=86 | +0.114 [+0.049, +0.179] n=86 | +0.113 ± 0.039 | – | – | – | ≥ 0.037 | 0.387 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

**Best version.** `round_15` beats the average of 19 versions by +0.138; if all were equally good, picking the best would give +0.058 by chance (p = 0.00, 86 shared selection tasks).

