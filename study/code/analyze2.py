import json, numpy as np
def load(f):
    by={}
    for l in open(f):
        r=json.loads(l); by.setdefault(r["task"],{})[r["playbook"]]=r
    return by
for f in ["runs/heldout_retail_A.jsonl","runs/heldout_retail_B.jsonl","runs/heldout_cuad.jsonl"]:
    by=load(f); P=[(v["start"],v["final"]) for v in by.values() if len(v)==2]
    print("=====",f,len(P))
    for k in ["gold","judge_k26","judge_k3"]:
        Q=[(a[k],b[k]) for a,b in P if a.get(k) is not None and b.get(k) is not None]
        if not Q: continue
        d=np.array([y-x for x,y in Q])
        rng=np.random.default_rng(0); bs=[rng.choice(d,len(d)).mean() for _ in range(10000)]
        print(f"  {k:9s} n={len(Q)} start {np.mean([x for x,y in Q]):.3f} final {np.mean([y for x,y in Q]):.3f} diff {d.mean():+.3f} CI[{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}] up/down/same {sum(d>0)}/{sum(d<0)}/{sum(d==0)}")
    allr=[r for v in by.values() for r in v.values()]
    for k in ["judge_k26","judge_k3"]:
        x=[(r[k],r["gold"]) for r in allr if r.get(k) is not None]
        if x: print(f"  corr {k} vs gold n={len(x)}: {np.corrcoef(*zip(*x))[0,1]:+.2f}")
    fields=list(P[0][0]["gold_detail"])
    print("  field correct start->final:", {f:(sum(bool(a["gold_detail"][f]) for a,b in P), sum(bool(b["gold_detail"][f]) for a,b in P)) for f in fields})
    print("  words", round(np.mean([len(a["report"].split()) for a,b in P])), "->", round(np.mean([len(b["report"].split()) for a,b in P])),
          " forced", sum(any(c.startswith("#forced") for c in a["commands"]) for a,b in P), "->", sum(any(c.startswith("#forced") for c in b["commands"]) for a,b in P),
          " empty", sum(not a["report"].strip() for a,b in P), "->", sum(not b["report"].strip() for a,b in P),
          " judge None", sum(a.get("judge_k26") is None for a,b in P), sum(b.get("judge_k26") is None for a,b in P))
