import json,re,sys
sys.path.insert(0,"/home/claude/project4/loop")
from tasks_retail import make_task
R="/home/claude/project4/loop/runs/"
def keys(t): return {m.group(1): m.group(2).strip().strip("`*").strip() for m in re.finditer(r"^\s*KEY\s+(\w+)\s*=\s*(.+?)\s*$", t, re.M)}
G={}
for src in "AB":
  for l in open(R+f"heldout_retail_{src}.jsonl"):
    r=json.loads(l); i=int(r["task"][7:])
    if i not in G: G[i]=make_task(i)["gold"]["revenue_prior"]
    if not r["gold_detail"]["revenue_prior"]:
      got=keys(r.get("report") or "").get("revenue_prior")
      print(src,r["playbook"],r["task"],G[i],got, "ratio=%.3f"%(float(got)/G[i]) if got else "")
r=[json.loads(l) for l in open(R+"heldout_retail_A.jsonl") if '"retail-023"' in l and '"final"' in l][0]
print(len(r["report"]), r.get("critique_k26"), r["report"][:300])
