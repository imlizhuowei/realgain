# realgain report: AFlow GSM8K

12000 records · starting version `None` · held-out tasks: NO (gains cannot be checked on new tasks) · ground truth: no

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `round_2` | 2 | **NO DATA** | – | – | – | – | – | – | – | – |
| `round_3` | 3 | **NOT SHOWN** | +0.046 [-0.010, +0.102] n=100 | – | – | – | – | – | – | 0.411 |
| `round_8` | 8 | **NOT SHOWN** | +0.016 [-0.027, +0.059] n=100 | – | – | – | – | – | – | 0.921 |
| `round_10` | 10 | **NOT SHOWN** | +0.010 [-0.021, +0.041] n=100 | – | – | – | – | – | – | 0.921 |
| `round_13` | 13 | **NOT SHOWN** | +0.008 [-0.002, +0.018] n=100 | – | – | – | – | – | – | 0.411 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

**Best version.** `round_13` beats the average of 24 versions by +0.039; if all were equally good, picking the best would give +0.034 by chance (p = 0.29, 100 shared selection tasks).

