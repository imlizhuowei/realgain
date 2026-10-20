"""How many ground-truth labels does it take to check a judge's claim? Real cases from our study plus simulations."""
import json, os, sys
import numpy as np
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from realgain.audit import label_budget, classical, ppi
LOOP = os.environ.get("STUDY_RUNS", os.path.join(os.path.dirname(HERE), "study", "runs"))
VALID = ["revenue_prior", "revenue_current", "periods_comparable", "top_country_by_change", "unidentified_share_pct"]


def real_cases():
    ds = {}
    for l in open(f"{LOOP}/rejudge_deepseek-v4-pro.jsonl"):
        r = json.loads(l); ds[r["key"]] = r["judge_ds"]
    cases = {}
    # retail: start vs final, judge = DeepSeek (non-Kimi), truth = 5 unambiguous fields
    by = defaultdict(dict)
    for src in ["heldout_retail_A", "heldout_retail_B"]:
        for l in open(f"{LOOP}/{src}.jsonl"):
            x = json.loads(l)
            if x["task"] in by and x["playbook"] in by[x["task"]]: continue
            by[x["task"]][x["playbook"]] = (ds.get(f"{src}|{x['playbook']}|{x['task']}"), np.mean([bool(x["gold_detail"][f]) for f in VALID]) * 100)
    pairs = [(v["final"][0] - v["start"][0], v["final"][1] - v["start"][1]) for v in by.values() if len(v) == 2 and None not in (v["final"][0], v["start"][0])]
    cases["retail memos: final vs start playbook (judge says better)"] = pairs
    # contracts: judge-selected loop's final version vs start (held-out contracts)
    by = defaultdict(dict)
    for l in open(f"{LOOP}/heldout_cuad.jsonl"):
        x = json.loads(l); by[x["task"]][x["playbook"]] = (ds.get(f"heldout_cuad|{x['playbook']}|{x['task']}"), x["gold"] * 100)
    cases["contracts: judge-picked final vs start (judge says better)"] = [(v["final"][0] - v["start"][0], v["final"][1] - v["start"][1]) for v in by.values()]
    return cases


def sim_case(N=200, true_gain=0.0, judge_gain=1.0, rho=0.0, seed=0):
    """Judge difference = judge_gain + noise correlated rho with the truth difference."""
    rng = np.random.default_rng(seed)
    T = true_gain + rng.normal(0, 15, N)                 # truth diff per task, in points
    J = judge_gain + rho * (T - true_gain) / 15 + np.sqrt(1 - rho ** 2) * rng.normal(0, 1, N)
    return list(zip(J, T))


if __name__ == "__main__":
    res = {}
    for name, pairs in real_cases().items():
        J, T = np.array(pairs).T
        res[name] = label_budget(J, T, reps=3000) | {"judge_truth_corr": float(np.corrcoef(J, T)[0, 1])}
    for name, kw in {"sim: judge fooled (true 0, judge +1, uncorrelated)": dict(true_gain=0, rho=0),
                     "sim: real 3-pt gain, judge informative (rho .6)": dict(true_gain=3, rho=.6),
                     "sim: real 3-pt gain, judge uninformative": dict(true_gain=3, rho=0),
                     "sim: real 3-pt LOSS, judge says better (rho .3)": dict(true_gain=-3, rho=.3)}.items():
        J, T = np.array(sim_case(**kw)).T
        res[name] = label_budget(J, T, budgets=[5, 10, 20, 30, 50, 100], reps=1500)
    json.dump(res, open(os.path.join(HERE, "results_audit.json"), "w"), indent=1, default=float)
    for name, r in res.items():
        print("==", name, f"| N={r['N']} full-label verdict: {r['full']['verdict']} ({r['full']['estimate']:+.1f} [{r['full']['ci'][0]:+.1f},{r['full']['ci'][1]:+.1f}])",
              f"| judge-truth r={r.get('judge_truth_corr', float('nan')):+.2f}")
        for m, d in r["by_m"].items():
            print(f"   m={m:3d}  " + "   ".join(f"{k}: agrees {v['agrees_with_full']:.2f}, false 'better' {v['false_better']:.2f}, width {v['median_width']:.1f}" for k, v in d.items()))
