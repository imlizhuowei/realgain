"""Load AFlow's published run logs into per-question score matrices.

For each benchmark and round we build a (runs x questions) array of scores,
aligned by question text so rounds can be compared question by question.
"""
import csv, glob, json, os
import numpy as np

ROOT = "/home/claude/data/aflow/results"
csv.field_size_limit(10**9)


def load_benchmark(ds):
    rounds = {}
    for d in glob.glob(f"{ROOT}/{ds}/graphs/round_*"):
        rn = int(d.rsplit("_", 1)[1])
        runs = []
        for c in sorted(glob.glob(d + "/*.csv")):
            rows = list(csv.DictReader(open(c, encoding="utf-8", errors="ignore")))
            key = "question" if rows and "question" in rows[0] else "inputs"
            runs.append({r[key]: float(r["score"]) for r in rows})
        exp = None
        if os.path.exists(d + "/experience.json"):
            exp = json.load(open(d + "/experience.json"))
        rounds[rn] = {"runs": runs, "exp": exp}
    # common question set = questions present in every run of every round with data
    qsets = [set(r) for v in rounds.values() for r in v["runs"]]
    qs = sorted(set.intersection(*qsets)) if qsets else []
    out = {}
    for rn, v in rounds.items():
        if not v["runs"]:
            continue
        M = np.array([[r[q] for q in qs] for r in v["runs"]])
        out[rn] = {"M": M, "exp": v["exp"]}
    return out, qs


def benchmarks():
    return sorted(os.listdir(ROOT))


if __name__ == "__main__":
    for ds in benchmarks():
        R, qs = load_benchmark(ds)
        broken = [rn for rn, v in R.items() if v["M"].mean() == 0]
        print(ds, "rounds", len(R), "questions", len(qs),
              "runs/round", sorted({v['M'].shape[0] for v in R.values()}),
              "score values", np.unique(np.concatenate([v['M'].ravel() for v in R.values()]))[:6],
              "broken(all-zero) rounds", broken)
