"""Does 'expected on new tasks' (empirical Bayes over all candidates) predict held-out gains better than the loop's
own number? Three tests: (1) AFlow public logs, picking the best round on a random half of the tasks and measuring it on
the other half (40 splits per benchmark); (2) simulated loops with known true gains; (3) our three contract loops,
predicting the 15-contract held-out gain of each accepted version. Output: benchmarks/results_shrink.json."""
import json, os, sys, math
import numpy as np
from collections import defaultdict, Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from realgain.shrink import candidate_gains, shrink
EX = os.path.join(os.path.dirname(HERE), "examples")


def summarize(rows):
    R = np.array(rows)
    e_n, e_s = R[:, 0] - R[:, 2], R[:, 1] - R[:, 2]
    return {"n": len(R), "bias_naive": float(e_n.mean()), "bias_corrected": float(e_s.mean()),
            "mae_naive": float(np.abs(e_n).mean()), "mae_corrected": float(np.abs(e_s).mean())}


def aflow(splits=40, seed=0):
    rng = np.random.default_rng(seed); out = {}
    for b in ["HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP"]:
        cells = defaultdict(lambda: defaultdict(list))
        for l in open(f"{EX}/aflow_{b}.jsonl"):
            r = json.loads(l); cells[r["version"]][r["task"]].append(r["score"])
        root = "round_1"
        cnt = Counter(t for v in cells for t in cells[v])
        tasks = sorted(t for t, c in cnt.items() if c >= .9 * len(cells))
        vs = [v for v in cells if v != root and set(tasks) <= set(cells[v])]
        if root not in cells or not set(tasks) <= set(cells[root]): continue
        rows = []
        for s in range(splits):
            perm = rng.permutation(tasks); A, Bt = set(perm[: len(perm) // 2]), perm[len(perm) // 2:]
            g = candidate_gains({v: {t: x for t, x in c.items() if t in A} for v, c in cells.items()}, root, vs)
            g = {v: x for v, x in g.items() if x[1] > 0}
            est, _ = shrink(g)
            if not est: continue
            win = max(g, key=lambda v: g[v][0])
            actual = float(np.mean([np.mean(cells[win][t]) - np.mean(cells[root][t]) for t in Bt]))
            rows.append((g[win][0], est[win]["expected"], actual))
        if rows: out[b] = summarize(rows) | {"tasks": len(tasks), "candidates": len(vs)}
    allrows = None
    return out


def simulate(k=12, n_sel=10, tau=0.03, base_sd=0.0, sims=600, seed=1):
    """k candidates; true gains ~ N(0, tau); each scored on n_sel 0/1 tasks; the loop keeps the best."""
    rng = np.random.default_rng(seed); rows = []
    for _ in range(sims):
        p = rng.uniform(.3, .8, n_sel); theta = rng.normal(0, tau, k)
        cells = {"root": {t: [float(rng.random() < p[t])] for t in range(n_sel)}}
        for i in range(k): cells[f"c{i}"] = {t: [float(rng.random() < np.clip(p[t] + theta[i], 0, 1))] for t in range(n_sel)}
        g = candidate_gains(cells, "root", [f"c{i}" for i in range(k)]); g = {v: x for v, x in g.items() if x[1] > 0}
        est, _ = shrink(g)
        if not est: continue
        win = max(g, key=lambda v: g[v][0])
        rows.append((g[win][0], est[win]["expected"], theta[int(win[1:])]))
    return summarize(rows)


def ours():
    LOOP = os.environ.get("STUDY_RUNS", os.path.join(os.path.dirname(HERE), "study", "runs"))
    touched = lambda cmds: any((".grader" in c or "gold.json" in c) for c in (cmds or []) if not c.startswith("#"))
    held = defaultdict(lambda: defaultdict(list))
    for R in ["R1", "R2", "R3"]:
        for l in open(f"{LOOP}/decomp_{R}.jsonl"):
            x = json.loads(l)
            if x["split"] == "heldout" and not touched(x.get("commands")): held[(R, x["version"])][x["task"]].append(x)
    out = {}
    for R, f, key in [("R1 (judge picks; target = judge score)", "cuad_v1", "judge"), ("R2 (answer key picks)", "cuad_R2_gold_locked", "gold"),
                      ("R3 (answer key visible)", "cuad_R3_gold_open", "gold")]:
        Rk = R[:2]; cells = defaultdict(lambda: defaultdict(list)); acc = []
        for l in open(f"{LOOP}/{f}.jsonl"):
            r = json.loads(l)
            if r["kind"] != "candidate": continue
            if r["accepted"] and r["id"] != "g0": acc.append(r["id"])
            for x in r["runs"]:
                v = x.get("judge") if key == "judge" else x["gold"] * 100
                if v is not None: cells[r["id"]][x["task"]].append(v)
        est, prior = shrink(candidate_gains(cells, "g0", list(cells)))
        rows = []
        for v in acc:
            base = {t: [z for RR in ["R1", "R2", "R3"] for z in held[(RR, "g0")][t]] for t in held[(Rk, v)]}
            pick = (lambda z: z["judge_k26"]) if key == "judge" else (lambda z: z["gold"] * 100)
            a = np.mean([np.mean([pick(z) for z in held[(Rk, v)][t]]) - np.mean([pick(z) for z in base[t]]) for t in base])
            rows.append((est[v]["observed"], est[v]["expected"], float(a)))
        out[R] = summarize(rows) | {"prior_tau": prior["tau"], "versions": [(v,) + tuple(round(x, 2) for x in r) for v, r in zip(acc, rows)]}
    return out


if __name__ == "__main__":
    res = {"aflow_half_split": aflow(),
           "simulated": {f"k={k}, n_sel={n}, tau={t}": simulate(k, n, t) for k, n, t in
                         [(12, 5, .03), (12, 10, .03), (12, 30, .03), (12, 30, .0), (12, 30, .1), (30, 30, .03), (4, 30, .03)]},
           "our_loops_heldout": ours()}
    json.dump(res, open(os.path.join(HERE, "results_shrink.json"), "w"), indent=1)
    f = lambda d: f"bias {d['bias_naive']*1:+.4f} -> {d['bias_corrected']:+.4f}   mean|err| {d['mae_naive']:.4f} -> {d['mae_corrected']:.4f}  (n={d['n']})"
    for sec, d in res.items():
        print("==", sec)
        for k, v in d.items(): print(f"  {k:42s} {f(v)}")
