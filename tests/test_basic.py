"""Synthetic checks with known answers. Run: python -m pytest tests  (or python tests/test_basic.py)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realgain import report

def sim(effect=0.0, judge_bias=0.0, tamper=False, lucky_first_run=0.0, n_sel=60, n_held=200, reruns=2, seed=0):
    """root v0 and accepted child v1. effect = true change in success rate. judge_bias = score-only inflation.
    lucky_first_run = extra score on v1's FIRST selection run only (what a loop sees after picking a lucky candidate)."""
    rng = np.random.default_rng(seed); recs = []
    base = rng.uniform(0.2, 0.8, n_sel + n_held)
    for v, eff in [("v0", 0.0), ("v1", effect)]:
        for i in range(n_sel + n_held):
            split = "selection" if i < n_sel else "heldout"
            for rep in (range(reruns + 1) if split == "selection" else [1]):
                truth = float(rng.random() < np.clip(base[i] + eff, 0, 1))
                score = truth + (judge_bias if v == "v1" else 0.0) + (lucky_first_run if (v == "v1" and rep == 0 and split == "selection") else 0.0)
                r = {"version": v, "parent": None if v == "v0" else "v0", "accepted": True, "generation": 0 if v == "v0" else 1,
                     "task": f"t{i}", "split": split, "repeat": rep, "phase": "acceptance" if (rep == 0 and split == "selection") else "recheck", "score": score, "truth": truth}
                if tamper and v == "v1" and i % 5 == 0:
                    r["commands"] = ["cat .grader/gold.json"]; r["score"] = 1.0
                recs.append(r)
    return report(recs)["versions"]["v1"]

def test_no_change_is_not_called_a_gain():
    assert sim(0.0)["verdict"] == "NOT SHOWN"

def test_real_change_is_detected():
    assert sim(0.3)["verdict"] == "REAL"

def test_real_loss_is_detected():
    assert sim(-0.3)["verdict"] == "WORSE"

def test_fooled_judge():
    assert sim(0.0, judge_bias=1.0)["verdict"] == "SCORE ONLY"

def test_luck_from_lucky_first_run():
    row = sim(0.0, lucky_first_run=0.5)
    assert row["verdict"] == "LUCK"
    assert row["decomposition"]["luck (seen - re-run)"] > 0.3

def test_grader_access_flagged():
    assert sim(0.0, tamper=True)["verdict"] == "GRADER ACCESS"

def test_unchecked_gain_without_heldout_or_reruns():
    import numpy as np
    from realgain import report
    rng = np.random.default_rng(1); recs = []
    for v, eff in [("v0", 0.0), ("v1", 0.3)]:
        for i in range(100):
            recs.append({"version": v, "parent": None if v == "v0" else "v0", "accepted": True, "task": f"t{i}",
                         "score": float(rng.random() < 0.4 + eff)})
    assert report(recs)["versions"]["v1"]["verdict"] == "UNCHECKED GAIN"

def test_shrink_pulls_lucky_winner_back():
    from realgain.shrink import shrink
    gains = {f"c{i}": (g, 0.05, 30) for i, g in enumerate([0.0, 0.01, -0.02, 0.03, 0.12])}   # one lucky-looking winner
    est, prior = shrink(gains)
    assert est["c4"]["expected"] < 0.12

def test_audit_never_confirms_a_fooled_judge_often():
    import numpy as np
    from realgain.audit import label_budget
    rng = np.random.default_rng(0); T = rng.normal(0, 15, 200); J = 1 + rng.normal(0, 1, 200)
    r = label_budget(J, T, budgets=[10], reps=400)
    assert r["by_m"][10]["classical"]["false_better"] < 0.06

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
