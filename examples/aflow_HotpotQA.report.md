# realgain report: AFlow HotpotQA

7140 records · starting version `round_1` · held-out tasks: NO (gains cannot be checked on new tasks) · ground truth: no

**Noise.** Starting version: mean 0.158 over 68 tasks; task-sampling SE of a mean 0.018; run-to-run SE of a mean 0.000.

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `round_2` | 2 | **UNCHECKED GAIN** | +0.228 [+0.156, +0.299] n=68 | +0.228 [+0.156, +0.299] n=68 | +0.231 ± 0.042 | – | – | – | ≥ 0.100 | 0.000 |
| `round_3` | 3 | **UNCHECKED GAIN** | +0.230 [+0.146, +0.313] n=68 | +0.457 [+0.361, +0.554] n=68 | +0.439 ± 0.057 | – | – | – | ≥ 0.118 | 0.000 |
| `round_7` | 7 | **NOT SHOWN** | +0.006 [-0.032, +0.043] n=68 | +0.458 [+0.365, +0.551] n=68 | +0.441 ± 0.055 | – | – | – | ≥ 0.053 | 1.000 |
| `round_10` | 10 | **NOT SHOWN** | +0.006 [-0.037, +0.049] n=68 | +0.464 [+0.368, +0.560] n=68 | +0.445 ± 0.056 | – | – | – | ≥ 0.060 | 1.000 |
| `round_15` | 15 | **NOT SHOWN** | +0.003 [-0.024, +0.029] n=68 | +0.462 [+0.368, +0.556] n=68 | +0.444 ± 0.055 | – | – | – | ≥ 0.037 | 1.000 |
| `round_16` | 16 | **NOT SHOWN** | +0.015 [-0.054, +0.084] n=68 | +0.475 [+0.380, +0.569] n=68 | +0.455 ± 0.055 | – | – | – | ≥ 0.097 | 1.000 |
| `round_18` | 18 | **UNCHECKED GAIN** | +0.027 [+0.000, +0.054] n=68 | +0.027 [+0.000, +0.054] n=68 | +0.029 ± 0.016 | – | – | – | ≥ 0.038 | 0.248 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

**Best version.** `round_16` beats the average of 21 versions by +0.076; if all were equally good, picking the best would give +0.051 by chance (p = 0.03, 68 shared selection tasks).

