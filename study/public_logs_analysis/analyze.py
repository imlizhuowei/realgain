"""First-pass analysis of AFlow's published logs.

A. Noise: how big is run-to-run randomness (visible in AFlow's 5 repeats)
   vs question-sampling error (invisible to the repeats, because every repeat
   uses the same validation questions)?
B. Decisions: for every child workflow, compare it with its parent question by
   question. How many accepted steps are clearly larger than noise?
C. Winner's curse by re-selection: pick the best round using half the data,
   measure it on the other half. The gap is the inflation that selection
   alone produces. Done separately for (i) run randomness and (ii) question
   sampling.
"""
import json
import numpy as np
from load import load_benchmark, benchmarks

rng = np.random.default_rng(0)
B = 2000


def valid(R):
    return {rn: v for rn, v in R.items() if v["M"].mean() > 0 and v["M"].shape[0] >= 2}


out = {}
for ds in benchmarks():
    R, qs = load_benchmark(ds)
    V = valid(R)
    n = len(qs)
    res = {"n_questions": n, "n_rounds": len(V)}

    # ---- A. noise -------------------------------------------------------
    run_sd, item_se = [], []
    for v in V.values():
        M = v["M"]
        run_sd.append(M.mean(1).std(ddof=1))                 # sd of the round score across repeats
        item_se.append(M.mean(0).std(ddof=1) / np.sqrt(n))   # se from which questions were drawn
    res["run_sd_median"] = float(np.median(run_sd))
    res["item_se_median"] = float(np.median(item_se))

    # ---- B. accept/reject decisions --------------------------------------
    dec = []
    for rn, v in V.items():
        e = v["exp"]
        if not e or e.get("father node") not in V:
            continue
        P, C = V[e["father node"]]["M"], v["M"]
        d_q = C.mean(0) - P.mean(0)               # per-question gain, repeats averaged
        delta = d_q.mean()
        boots = d_q[rng.integers(0, n, (B, n))].mean(1)   # resample questions
        lo, hi = np.percentile(boots, [2.5, 97.5])
        # run-noise only: sd of difference of means across repeats
        se_run = np.sqrt(C.mean(1).var(ddof=1) / C.shape[0] + P.mean(1).var(ddof=1) / P.shape[0])
        dec.append({"round": rn, "parent": e["father node"], "accepted": bool(e["succeed"]),
                    "delta": float(delta), "ci_questions": [float(lo), float(hi)],
                    "z_run_only": float(delta / se_run) if se_run > 0 else None,
                    "logged_before": e["before"], "logged_after": e["after"],
                    "recomputed_parent": float(P.mean()), "recomputed_child": float(C.mean())})
    res["decisions"] = dec
    acc = [d for d in dec if d["accepted"]]
    res["n_accepted"] = len(acc)
    res["accepted_beyond_run_noise"] = sum(1 for d in acc if d["z_run_only"] and d["z_run_only"] > 2)
    res["accepted_beyond_question_noise"] = sum(1 for d in acc if d["ci_questions"][0] > 0)

    # ---- C. winner's curse by split-half re-selection ---------------------
    rounds = sorted(V)
    stack = np.stack([V[r]["M"][:5] for r in rounds if V[r]["M"].shape[0] >= 5])  # rounds x 5 x n
    infl_q, infl_r = [], []
    for _ in range(500):
        # (ii) question split, all repeats
        perm = rng.permutation(n); a, b = perm[: n // 2], perm[n // 2:]
        sA = stack[:, :, a].mean((1, 2)); sB = stack[:, :, b].mean((1, 2))
        k = sA.argmax()
        infl_q.append((sA[k] - sB[k]) - (sA - sB).mean())
        # (i) repeat split, all questions
        rp = rng.permutation(5); ra, rb = rp[:2], rp[2:4]
        tA = stack[:, ra, :].mean((1, 2)); tB = stack[:, rb, :].mean((1, 2))
        k = tA.argmax()
        infl_r.append((tA[k] - tB[k]) - (tA - tB).mean())
    full = stack.mean((1, 2))
    res["best_round_val"] = float(full.max())
    res["median_round_val"] = float(np.median(full))
    res["inflation_question_split"] = float(np.mean(infl_q))
    res["inflation_repeat_split"] = float(np.mean(infl_r))
    out[ds] = res

json.dump(out, open("aflow_first_pass.json", "w"), indent=1)
print(f"{'bench':10}{'n_q':>5}{'rounds':>7}{'run_sd':>8}{'item_se':>8}{'acc':>5}{'>run':>6}{'>q':>5}{'infl_rep':>10}{'infl_q':>8}")
for ds, r in out.items():
    print(f"{ds:10}{r['n_questions']:>5}{r['n_rounds']:>7}{r['run_sd_median']*100:>8.2f}{r['item_se_median']*100:>8.2f}"
          f"{r['n_accepted']:>5}{r['accepted_beyond_run_noise']:>6}{r['accepted_beyond_question_noise']:>5}"
          f"{r['inflation_repeat_split']*100:>10.2f}{r['inflation_question_split']*100:>8.2f}")
