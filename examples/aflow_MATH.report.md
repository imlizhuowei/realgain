# realgain report: AFlow MATH

10353 records · starting version `None` · held-out tasks: NO (gains cannot be checked on new tasks) · ground truth: no

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `round_2` | 2 | **NO DATA** | – | – | – | – | – | – | – | – |
| `round_3` | 3 | **NOT SHOWN** | +0.003 [-0.054, +0.061] n=119 | – | – | – | – | – | – | 1.000 |
| `round_5` | 5 | **NOT SHOWN** | +0.024 [-0.020, +0.067] n=119 | – | – | – | – | – | – | 1.000 |
| `round_9` | 9 | **NOT SHOWN** | +0.010 [-0.017, +0.037] n=119 | – | – | – | – | – | – | 1.000 |
| `round_14` | 14 | **NOT SHOWN** | +0.003 [-0.027, +0.033] n=119 | – | – | – | – | – | – | 1.000 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

**Best version.** `round_5` beats the average of 19 versions by +0.116; if all were equally good, picking the best would give +0.048 by chance (p = 0.00, 119 shared selection tasks).

