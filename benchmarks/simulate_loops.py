"""Evaluate the evaluator: run realgain on simulated self-improvement loops whose truth we know.

Each simulated loop: a starting version, G generations, K candidates per generation, each scored on the same S selection
tasks (0/1 answers). The best candidate is kept if it beats the incumbent's score (that is how luck gets in). Every
candidate has a TRUE change in success rate; a judge score adds a per-version bias that is unrelated to the truth for some
versions (a fooled judge); some runs read the answer key (score 1, flagged in commands). Every accepted version is also
re-run twice on the selection tasks and once on H held-out tasks, as in our study.

What we measure, per accepted version, against the known truth:
  - verdict accuracy (REAL / WORSE / SCORE ONLY / GRADER ACCESS / no real change)
  - coverage of the 95% interval for the held-out truth gain
  - bias of the loop's own number vs. of 'expected on new tasks'
"""
import json, os, sys
import numpy as np
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from realgain import report


def one_loop(rng, G=6, K=2, S=10, H=30, step_sd=0.04, judge_bias_p=0.0, judge_bias=1.0, tamper_p=0.0, judge_scale=10):
    p_sel, p_held = rng.uniform(.3, .85, S), rng.uniform(.3, .85, H)
    truth = {"v0": 0.0}; jb = {"v0": 0.0}; tam = {"v0": False}; recs = []
    def run(v, tasks, split, phase, rep, parent, gen, acc):
        for i, pt in enumerate(tasks):
            cheat = tam[v] and rng.random() < .3
            y = 1.0 if cheat else float(rng.random() < np.clip(pt + truth[v], 0, 1))
            score = (y if judge_scale == 1 else judge_scale * (0.45 + 0.1 * y + rng.normal(0, .08)) + jb[v])
            recs.append({"version": v, "parent": parent, "generation": gen, "accepted": acc, "task": f"{split[0]}{i}",
                         "split": split, "phase": phase, "repeat": rep, "score": float(score), "truth": y,
                         "commands": ["cat .grader/gold.json"] if cheat else []})
    run("v0", p_sel, "selection", "acceptance", 0, None, 0, True)
    inc, inc_score = "v0", None
    sel_mean = lambda v: np.mean([r["score"] for r in recs if r["version"] == v and r["split"] == "selection" and r["phase"] == "acceptance"])
    inc_score = sel_mean("v0"); accepted = []
    for g in range(1, G + 1):
        kids = []
        for k in range(K):
            v = f"g{g}c{k}"
            truth[v] = truth[inc] + rng.normal(0, step_sd)
            jb[v] = jb[inc] + (judge_bias / G * 2 if rng.random() < judge_bias_p else 0.0)
            tam[v] = tam[inc] or (rng.random() < tamper_p)
            run(v, p_sel, "selection", "acceptance", 0, inc, g, False); kids.append(v)
        best = max(kids, key=sel_mean)
        if sel_mean(best) > inc_score:
            for r in recs:
                if r["version"] == best: r["accepted"] = True
            inc, inc_score = best, sel_mean(best); accepted.append(best)
    for v in ["v0"] + accepted:          # the checks: two re-runs on selection tasks, one pass on held-out tasks
        for rep in (1, 2): run(v, p_sel, "selection", "recheck", rep, None if v == "v0" else "_", 0, True)
        run(v, p_held, "heldout", "recheck", 1, None if v == "v0" else "_", 0, True)
    for r in recs:                        # recheck rows carry the real parent
        if r["parent"] == "_": r["parent"] = next(x["parent"] for x in recs if x["version"] == r["version"] and x["phase"] == "acceptance")
    return recs, truth, jb, tam, accepted


def truth_label(v, truth, jb, tam, delta):
    if tam[v]: return "GRADER ACCESS"
    if truth[v] > delta: return "REAL"
    if truth[v] < -delta: return "WORSE"
    if jb[v] > 0.3: return "SCORE ONLY"
    return "NO REAL CHANGE"


def evaluate(n_loops=150, seed=0, delta=0.05, **kw):
    rng = np.random.default_rng(seed)
    conf = defaultdict(Counter); cover = []; bias_seen = []; bias_exp = []; pairs = []
    for _ in range(n_loops):
        recs, truth, jb, tam, acc = one_loop(rng, **kw)
        if not acc: continue
        rep = report(recs)
        for v in acc:
            row = rep["versions"].get(v)
            if not row: continue
            lab = truth_label(v, truth, jb, tam, delta)
            conf[lab][row["verdict"]] += 1
            pairs.append((truth[v], tam[v], jb[v], row["verdict"]))
            th = row.get("truth_heldout")
            if th and not tam[v]: cover.append(th["ci"][0] <= truth[v] <= th["ci"][1])
            if kw.get("judge_scale", 10) == 1 and row.get("seen") and row.get("expected_new_tasks") and not tam[v]:
                bias_seen.append(row["seen"]["diff"] - truth[v]); bias_exp.append(row["expected_new_tasks"]["expected"] - truth[v])
    P = pairs
    rate = lambda cond, verd: (lambda xs: float(np.mean([x[3] in verd for x in xs])) if xs else None)([x for x in P if cond(x)])
    out = {"errors": {
              "says REAL or better when true change <= 0": rate(lambda x: x[0] <= 0 and not x[1], ("REAL",)),
              "says WORSE when true change >= 0": rate(lambda x: x[0] >= 0 and not x[1], ("WORSE",)),
              "flags grader access when there was none": rate(lambda x: not x[1], ("GRADER ACCESS",)),
              "flags grader access when there was": rate(lambda x: x[1], ("GRADER ACCESS",)),
              "finds REAL when true gain > 5 pts": rate(lambda x: x[0] > .05 and not x[1], ("REAL",)),
              "finds REAL when true gain > 10 pts": rate(lambda x: x[0] > .10 and not x[1], ("REAL",)),
           },
           "confusion": {k: dict(v) for k, v in conf.items()},
           "heldout_truth_ci_coverage": float(np.mean(cover)) if cover else None}
    if bias_seen:
        out["bias_loop_number"] = float(np.mean(bias_seen)); out["bias_expected_new_tasks"] = float(np.mean(bias_exp))
    return out


if __name__ == "__main__":
    configs = {
        "answer-key loop, 10 sel / 30 held-out tasks": dict(judge_scale=1, S=10, H=30),
        "answer-key loop, 10 sel / 100 held-out tasks": dict(judge_scale=1, S=10, H=100),
        "judge loop, half the versions flatter the judge": dict(judge_scale=10, judge_bias_p=.5, S=10, H=30),
        "answer-key loop, grader reachable": dict(judge_scale=1, tamper_p=.15, S=10, H=30),
    }
    res = {name: evaluate(**kw) for name, kw in configs.items()}
    json.dump(res, open(os.path.join(HERE, "results_loops.json"), "w"), indent=1)
    for name, r in res.items():
        print("==", name)
        for lab, c in r["confusion"].items():
            tot = sum(c.values()); print(f"   truly {lab:15s} (n={tot:3d}): " + ", ".join(f"{k} {v/tot:.0%}" for k, v in sorted(c.items(), key=lambda x: -x[1])))
        for k, v in r["errors"].items(): print(f"   {k:45s} {('%.1f%%' % (100 * v)) if v is not None else '–'}")
        print("   95% interval for held-out truth covers the truth:", r["heldout_truth_ci_coverage"])
        if "bias_loop_number" in r: print(f"   bias of loop's own number {r['bias_loop_number']:+.3f}  vs  'expected on new tasks' {r['bias_expected_new_tasks']:+.3f}")
