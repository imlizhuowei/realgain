"""AFlow published logs -> realgain records. Usage: python adapters/aflow.py <results_dir>/<BENCH> out.jsonl"""
import csv, glob, json, os, sys
csv.field_size_limit(10**9)
src, out = sys.argv[1], sys.argv[2]
recs, qid = [], {}
for d in sorted(glob.glob(f"{src}/graphs/round_*")):
    rn = int(d.rsplit("_", 1)[1]); exp = json.load(open(d + "/experience.json")) if os.path.exists(d + "/experience.json") else None
    for rep, c in enumerate(sorted(glob.glob(d + "/*.csv"))):
        rows = list(csv.DictReader(open(c, encoding="utf-8", errors="ignore")))
        if not rows: continue
        key = "question" if "question" in rows[0] else "inputs"
        for r in rows:
            q = qid.setdefault(r[key], f"q{len(qid)}")
            recs.append({"version": f"round_{rn}", "parent": f"round_{exp['father node']}" if exp else None,
                         "accepted": bool(exp["succeed"]) if exp else True, "generation": rn,
                         "task": q, "repeat": rep, "score": float(r["score"]), "split": "selection"})
with open(out, "w") as f:
    for r in recs: f.write(json.dumps(r) + "\n")
print(len(recs), "records")
