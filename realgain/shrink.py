"""Estimate how much of each candidate's observed gain is luck, using only the loop's own log (no re-runs).

Every candidate the loop tried (kept or not) gives an observed gain G_c over the starting version on the selection
tasks, with a standard error s_c from the spread of its per-task differences. If true gains vary across candidates
around mu with spread tau, the best guess of a candidate's true gain is

    mu + tau^2 / (tau^2 + s_c^2) * (G_c - mu)          (normal-normal empirical Bayes, James-Stein / Efron)

Candidates that were kept because G_c came out high get pulled back hardest when s_c is large relative to tau.
mu and tau^2 are estimated from all candidates by the method of moments (tau^2 floored at 0), which is why the log
must include the candidates the loop REJECTED: dropping them hides exactly the spread this needs.
"""
import math
import numpy as np


def candidate_gains(cells, root, versions):
    out = {}
    if root not in cells: return out
    for v in versions:
        if v == root or v not in cells: continue
        ts = sorted(set(cells[v]) & set(cells[root]))
        if len(ts) < 2: continue
        d = np.array([np.mean(cells[v][t]) - np.mean(cells[root][t]) for t in ts])
        out[v] = (float(d.mean()), float(d.std(ddof=1) / math.sqrt(len(d))), len(d))
    return out


def shrink(gains):
    """gains: {version: (G, se, n)} -> {version: {"observed", "expected", "sd", "weight"}}, plus (mu, tau)."""
    if len(gains) < 3: return {}, None
    G = np.array([g[0] for g in gains.values()]); S2 = np.array([g[1] ** 2 for g in gains.values()])
    w = 1 / np.maximum(S2, 1e-12)
    mu = float((w * G).sum() / w.sum()) if np.isfinite(w).all() else float(G.mean())
    # Every G_c is measured against the SAME starting-version runs, so the starting version's own noise is shared by all
    # candidates: it does not spread them apart. Only each candidate's own half of the paired variance (about s^2/2
    # when both sides are scored the same way) does. Using the full s^2 would over-shrink.
    own = S2 / 2
    tau2 = max(0.0, float(G.var(ddof=1) - own.mean()))
    res = {}
    for (v, (g, se, n)), o in zip(gains.items(), own):
        B = tau2 / (tau2 + o) if (tau2 + o) > 0 else 0.0
        res[v] = {"observed": g, "expected": mu + B * (g - mu), "sd": 1.2 * math.sqrt(B * o + (1 - B) ** 2 * o / len(gains) + o), "weight": B}  # 1.2: calibrated in benchmarks/ so ±1.96 sd covers ~95%
    return res, {"mu": mu, "tau": math.sqrt(tau2), "n_candidates": len(gains)}


def bootstrap_winner_correction(gains, chosen, sims=4000, seed=0):
    """Parametric-bootstrap correction for picking the best of several candidates (no common-prior assumption).
    Treat each candidate's observed gain as its truth, re-draw every candidate's observation with its own SE,
    pick the winner again, and measure how far the winner's draw overshoots its own truth on average.
    corrected = observed(chosen) - that overshoot. With one candidate there is nothing to correct."""
    vs = list(gains)
    if chosen not in gains or len(vs) < 2: return None
    rng = np.random.default_rng(seed)
    G = np.array([gains[v][0] for v in vs]); S = np.array([gains[v][1] for v in vs])
    draws = G + rng.standard_normal((sims, len(vs))) * S
    w = draws.argmax(1)
    overshoot = float((draws[np.arange(sims), w] - G[w]).mean())
    return {"observed": gains[chosen][0], "expected": gains[chosen][0] - overshoot, "overshoot": overshoot}
