# realgain report: contracts R2

185 records · starting version `g0` · held-out tasks: yes · ground truth: yes

**Noise.** Starting version: mean 0.907 over 15 tasks; task-sampling SE of a mean 0.021.

## Accepted versions

| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |
|---|---|---|---|---|---|---|---|---|---|---|
| `g1c0` | 1 | **NOT SHOWN** | -0.013 [-0.089, +0.062] n=5 | +0.020 [-0.084, +0.124] n=5 | -0.001 ± 0.033 | -0.030 [-0.101, +0.041] n=5 | -0.007 [-0.046, +0.032] n=15 | -0.007 [-0.046, +0.032] n=15 | ≥ 0.051 | 1.000 |
| `g2c1` | 2 | **NOT SHOWN** | +0.053 [-0.022, +0.129] n=5 | +0.040 [-0.102, +0.182] n=5 | -0.001 ± 0.045 | +0.040 [-0.012, +0.092] n=5 | +0.027 [-0.022, +0.076] n=15 | +0.027 [-0.022, +0.076] n=15 | ≥ 0.064 | 0.786 |
| `g4c1` | 4 | **NOT SHOWN** | -0.020 [-0.111, +0.071] n=5 | +0.060 [-0.128, +0.248] n=5 | -0.001 ± 0.060 | -0.000 [-0.088, +0.088] n=5 | +0.013 [-0.037, +0.064] n=15 | +0.013 [-0.037, +0.064] n=15 | ≥ 0.066 | 1.000 |

All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners (empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes most of the average over-claim but each single estimate stays noisy; with very few selection tasks it shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.

## Where the claimed gain went

| version | luck (seen − re-run) | fitting selection tasks (re-run − held-out) | survives on held-out |
|---|---|---|---|
| `g1c0` | +0.050 | -0.023 | -0.007 |
| `g2c1` | +0.000 | +0.013 | +0.027 |
| `g4c1` | +0.060 | -0.013 | +0.013 |

**Score vs ground truth.** Record-level correlation r = +1.00 (n = 185). Held-out gains point the same direction for 3 of 3 versions.

**Best version.** `g5c0` beats the average of 13 versions by +0.059; if all were equally good, picking the best would give +0.050 by chance (p = 0.33, 5 shared selection tasks).

