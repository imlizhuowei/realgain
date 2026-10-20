# realgain report: AFlow HumanEval

3150 records · starting version `round_1` · held-out tasks: NO (gains cannot be checked on new tasks) · ground truth: no

**Noise.** Starting version: mean 0.933 over 30 tasks; task-sampling SE of a mean 0.039; run-to-run SE of a mean 0.009.

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `round_5` | 5 | **NOT SHOWN** | +0.007 [-0.039, +0.053] n=30 | +0.007 [-0.039, +0.053] n=30 | +0.005 ± 0.026 | – | – | – | ≥ 0.063 | 1.000 |
| `round_8` | 8 | **NOT SHOWN** | +0.020 [-0.021, +0.061] n=30 | -0.007 [-0.038, +0.024] n=30 | -0.007 ± 0.018 | – | – | – | ≥ 0.056 | 1.000 |
| `round_14` | 14 | **NOT SHOWN** | +0.027 [-0.028, +0.081] n=30 | +0.013 [-0.034, +0.061] n=30 | +0.011 ± 0.028 | – | – | – | ≥ 0.075 | 1.000 |
| `round_16` | 16 | **NOT SHOWN** | +0.013 [-0.006, +0.032] n=30 | +0.020 [-0.021, +0.061] n=30 | +0.018 ± 0.024 | – | – | – | ≥ 0.026 | 0.804 |
| `round_21` | 21 | **NOT SHOWN** | +0.013 [-0.030, +0.057] n=30 | +0.013 [-0.030, +0.057] n=30 | +0.012 ± 0.025 | – | – | – | ≥ 0.060 | 1.000 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

**Best version.** `round_16` beats the average of 21 versions by +0.057; if all were equally good, picking the best would give +0.059 by chance (p = 0.65, 30 shared selection tasks).

