"""Audit a judge-claimed improvement with a small number of ground-truth labels.

Setting: an LLM judge (cheap) says version B beats version A. Ground truth (an expert, an answer key) is expensive.
You have both versions' outputs on N tasks and the judge's score for each; you can afford to label m of the N tasks.

Two estimators of the true difference B - A:
  classical  label m random tasks; t-interval on their truth differences.
  ppi        prediction-powered inference (Angelopoulos et al., 2023): use the judge's differences on ALL N tasks,
             corrected by how far the judge was off on the m labelled ones. Unbiased whatever the judge's quality;
             tighter than classical exactly when the judge tracks the truth, never meaningfully worse.
Both give a verdict: "B truly better" (interval above 0), "B truly worse" (below 0), or "not settled".

label_budget() answers: with m labels, how often does each method reach the verdict that labelling everything would?
"""
import math
import numpy as np
from .checks import _t975


def _verdict(lo, hi):
    return "better" if lo > 0 else "worse" if hi < 0 else "not settled"


def classical(truth_diff_labelled):
    d = np.asarray(truth_diff_labelled, float); m = len(d)
    if m < 2: return None
    se = d.std(ddof=1) / math.sqrt(m); q = _t975(m - 1)
    lo, hi = d.mean() - q * se, d.mean() + q * se
    return {"estimate": float(d.mean()), "ci": [float(lo), float(hi)], "verdict": _verdict(lo, hi)}


def ppi(judge_diff_all, labelled_idx, truth_diff_labelled):
    """Prediction-powered estimate of mean truth difference. The judge difference is first mapped to truth units with a
    least-squares line fitted on the labelled tasks (leave-one-out, so the correction stays unbiased)."""
    J = np.asarray(judge_diff_all, float); idx = np.asarray(labelled_idx); Y = np.asarray(truth_diff_labelled, float)
    m, N = len(idx), len(J)
    if m < 3: return None
    Jl = J[idx]
    # leave-one-out predictions on the labelled tasks; full-data fit for the unlabelled ones
    def fit(x, y):
        vx = x.var()
        b = 0.0 if vx == 0 else float(((x - x.mean()) * (y - y.mean())).mean() / vx)
        return float(y.mean() - b * x.mean()), b
    a, b = fit(Jl, Y)
    pred_all = a + b * J
    loo = np.empty(m)
    for i in range(m):
        keep = np.arange(m) != i; ai, bi = fit(Jl[keep], Y[keep]); loo[i] = ai + bi * Jl[i]
    rect = Y - loo
    est = pred_all.mean() + rect.mean()
    var = pred_all.var(ddof=1) / N + rect.var(ddof=1) / m
    q = _t975(m - 1); se = math.sqrt(var)
    lo, hi = est - q * se, est + q * se
    return {"estimate": float(est), "ci": [float(lo), float(hi)], "verdict": _verdict(lo, hi)}


def label_budget(judge_diff, truth_diff, budgets=None, reps=2000, seed=0):
    """For each label budget m: how often each method agrees with the verdict from labelling every task,
    how often it wrongly says 'better' when the full data does not, and the typical interval width."""
    J = np.asarray(judge_diff, float); T = np.asarray(truth_diff, float); N = len(T)
    full = classical(T)
    budgets = budgets or [m for m in (3, 5, 8, 10, 15, 20, 30, 50, 100) if m < N]
    rng = np.random.default_rng(seed); out = {"N": N, "full": full, "judge_mean_diff": float(J.mean()), "by_m": {}}
    for m in budgets:
        acc = {"classical": [], "ppi": []}
        for _ in range(reps):
            idx = rng.choice(N, m, replace=False)
            c, p = classical(T[idx]), ppi(J, idx, T[idx])
            for name, r in (("classical", c), ("ppi", p)):
                if r: acc[name].append((r["verdict"] == full["verdict"], r["verdict"] == "better" and full["verdict"] != "better",
                                        r["ci"][1] - r["ci"][0]))
        out["by_m"][m] = {k: {"agrees_with_full": float(np.mean([a for a, _, _ in v])),
                              "false_better": float(np.mean([f for _, f, _ in v])),
                              "median_width": float(np.median([w for _, _, w in v]))} for k, v in acc.items() if v}
    return out
