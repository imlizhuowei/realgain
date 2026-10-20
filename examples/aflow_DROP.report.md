# realgain report: AFlow DROP

7140 records · starting version `round_1` · held-out tasks: NO (gains cannot be checked on new tasks) · ground truth: no

**Noise.** Starting version: mean 0.061 over 68 tasks; task-sampling SE of a mean 0.012; run-to-run SE of a mean 0.000.

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `round_2` | 2 | **UNCHECKED GAIN** | +0.679 [+0.580, +0.779] n=68 | +0.679 [+0.580, +0.779] n=68 | +0.669 ± 0.059 | – | – | – | ≥ 0.139 | 0.000 |
| `round_3` | 3 | **UNCHECKED GAIN** | – | +0.680 [+0.581, +0.778] n=68 | +0.669 ± 0.059 | – | – | – | – | – |
| `round_6` | 6 | **UNCHECKED GAIN** | +0.450 [+0.387, +0.513] n=68 | +0.450 [+0.387, +0.513] n=68 | +0.448 ± 0.038 | – | – | – | ≥ 0.088 | 0.000 |
| `round_10` | 10 | **NOT SHOWN** | +0.022 [-0.009, +0.053] n=68 | +0.702 [+0.608, +0.795] n=68 | +0.692 ± 0.056 | – | – | – | ≥ 0.044 | 0.321 |
| `round_13` | 13 | **NOT SHOWN** | +0.000 [-0.019, +0.019] n=68 | +0.679 [+0.580, +0.779] n=68 | +0.669 ± 0.060 | – | – | – | ≥ 0.026 | 1.000 |
| `round_14` | 14 | **UNCHECKED GAIN** | +0.443 [+0.368, +0.519] n=68 | +0.443 [+0.368, +0.519] n=68 | +0.440 ± 0.045 | – | – | – | ≥ 0.106 | 0.000 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

**Best version.** `round_10` beats the average of 21 versions by +0.220; if all were equally good, picking the best would give +0.079 by chance (p = 0.00, 68 shared selection tasks).

