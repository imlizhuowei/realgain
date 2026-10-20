# realgain report: contracts R1

210 records · starting version `g0` · held-out tasks: yes · ground truth: yes

**Noise.** Starting version: mean 7.400 over 15 tasks; task-sampling SE of a mean 0.349.

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `g1c1` | 1 | **NOT SHOWN** | -0.133 [-1.778, +1.512] n=5 | +0.400 [-2.320, +3.120] n=5 | +0.782 ± 0.865 | -0.400 [-1.746, +0.946] n=5 | +0.600 [-0.283, +1.483] n=15 | -0.007 [-0.046, +0.032] n=15 | ≥ 0.051 | 1.000 |
| `g2c0` | 2 | **SCORE ONLY** | +0.600 [-0.388, +1.588] n=5 | +1.000 [-1.150, +3.150] n=5 | +0.782 ± 0.684 | +0.200 [-0.741, +1.141] n=5 | +1.200 [+0.499, +1.901] n=15 | +0.027 [-0.027, +0.080] n=15 | ≥ 0.069 | 1.000 |
| `g4c0` | 4 | **SCORE ONLY** | +0.133 [-0.093, +0.360] n=5 | +0.800 [-0.819, +2.419] n=5 | +0.782 ± 0.515 | +0.500 [-0.260, +1.260] n=5 | +1.333 [+0.559, +2.107] n=15 | +0.020 [-0.023, +0.063] n=15 | ≥ 0.056 | 1.000 |
| `g5c0` | 5 | **SCORE ONLY** | -0.333 [-0.919, +0.252] n=5 | +0.800 [-0.819, +2.419] n=5 | +0.782 ± 0.515 | +0.000 [-1.161, +1.161] n=5 | +1.467 [+0.843, +2.090] n=15 | +0.000 [-0.042, +0.042] n=15 | ≥ 0.055 | 1.000 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

## Where the claimed gain went

| version | luck (seen − re-run) | fitting selection tasks (re-run − held-out) | survives on held-out |
|---|---|---|---|
| `g1c1` | +0.800 | -1.000 | +0.600 |
| `g2c0` | +0.800 | -1.000 | +1.200 |
| `g4c0` | +0.300 | -0.833 | +1.333 |
| `g5c0` | +0.800 | -1.467 | +1.467 |

**Score vs ground truth.** Record-level correlation r = -0.08 (n = 210). Held-out gains point the same direction for 2 of 4 versions.

**Best version.** `g2c1` beats the average of 13 versions by +0.354; if all were equally good, picking the best would give +0.371 by chance (p = 0.97, 5 shared selection tasks).

