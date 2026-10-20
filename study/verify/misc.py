import json, random, statistics as st
R="/home/claude/project4/loop/runs/"
def rk(c): return any((".grader" in x or "gold.json" in x) for x in (c or []) if not x.lstrip().startswith("#"))
for r in map(json.loads, open(R+"decomp_R3.jsonl")):
    if rk(r["commands"]): print("R3 keyread", r["version"], r["split"], r["repeat"], r["task"], r["gold"])
H={(r["playbook"],r["task"]):r for r in map(json.loads, open(R+"heldout_cuad.jsonl"))}
same=0;n=0
for r in map(json.loads, open(R+"decomp_R1.jsonl")):
    if r.get("reused"):
        pb={"g0":"start","g5c0":"final"}[r["version"]]; h=H[(pb,r["task"])]; n+=1
        same+= (h["gold"],h["judge_k26"],h["judge_k3"],h["report"])==(r["gold"],r["judge_k26"],r["judge_k3"],r["report"])
print("R1 reused identical to heldout_cuad:", same, "/", n)
# bootstrap seed sensitivity: rerun retail per-task diffs quickly
import sys; sys.argv=[""]
F5=["revenue_prior","revenue_current","periods_comparable","top_country_by_change","unidentified_share_pct"]
from collections import defaultdict
a=defaultdict(list)
for s in "AB":
    for r in map(json.loads, open(R+f"heldout_retail_{s}.jsonl")):
        a[(r["task"],r["playbook"])].append(sum(float(r["gold_detail"][f]) for f in F5)/5)
ts=sorted({t for t,_ in a}); d=[100*(st.mean(a[(t,"final")])-st.mean(a[(t,"start")])) for t in ts]
print("per-task diffs", [round(x,1) for x in d])
for seed in range(5):
    random.seed(seed); bs=sorted(st.mean(random.choices(d,k=21)) for _ in range(10000))
    print(seed, round(bs[250],2), round(bs[9750],2))
