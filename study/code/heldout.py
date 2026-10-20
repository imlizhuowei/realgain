"""Held-out check: the starting playbook vs the loop's final 'best' playbook, on tasks the loop never saw.
Every run is graded against ground truth and scored by two judges (kimi-k2.6, used in the loop, and kimi-k3)."""
import argparse, json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import solver, judge, loop
import tasks_retail as tret, tasks_cuad as tcu
ap = argparse.ArgumentParser(); ap.add_argument("--family"); ap.add_argument("--log"); ap.add_argument("--final")
ap.add_argument("--ids"); ap.add_argument("--out"); ap.add_argument("--workers", type=int, default=6); ap.add_argument("--min_balance", type=float, default=20)
A = ap.parse_args(); solver.MAX_STEPS = 30; mod = {"retail": tret, "cuad": tcu}[A.family]
L = [json.loads(l) for l in open(A.log)]
pbs = {"start": L[0]["playbook"], "final": [r for r in L if r.get("id") == A.final][0]["playbook"]}
tasks = [mod.make_task(int(i)) for i in A.ids.split(",")]
jobs = [(name, t) for t in tasks for name in pbs]; random.Random(0).shuffle(jobs)
done = set()
if os.path.exists(A.out):
    for l in open(A.out): r = json.loads(l); done.add((r["playbook"], r["task"]))
out = open(A.out, "a")
def go(j):
    name, t = j
    if (name, t["id"]) in done: return
    if loop.balance() < A.min_balance: print("low balance, skip", name, t["id"]); return
    r = solver.run(t, pbs[name])
    if not r.get("usage", {}).get("prompt"): print("empty run", name, t["id"]); return
    g, det = mod.gold_score(t, r["report"])
    j1 = judge.judge(t["instruction"], r["report"], family=A.family)
    j2 = judge.judge(t["instruction"], r["report"], family=A.family, model="kimi-k3")
    rec = {"playbook": name, "task": t["id"], "meta": t["meta"], "gold": g, "gold_detail": det, "judge_k26": j1["score"],
           "judge_k3": j2["score"], "critique_k26": j1["critique"], "critique_k3": j2["critique"], "report": r["report"],
           "usage": r["usage"], "steps": r["steps"], "commands": r["commands"], "t": time.time()}
    out.write(json.dumps(rec, default=float) + "\n"); out.flush(); print(name, t["id"], round(g, 2), j1["score"], j2["score"], flush=True)
with ThreadPoolExecutor(A.workers) as ex: list(ex.map(go, jobs))
