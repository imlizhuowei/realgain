"""Per-generation decomposition runs: for every ACCEPTED version of a loop, re-run it on the loop's own
selection tasks (new runs) and run it on held-out tasks. Same exposure as the loop (so grader access can be audited).
Output records: version, split (selection|heldout), repeat, task, gold, gold_detail, judge_k26, judge_k3, commands."""
import argparse, json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import solver, judge, loop
import tasks_retail as tret, tasks_cuad as tcu
ap = argparse.ArgumentParser()
ap.add_argument("--family", default="cuad"); ap.add_argument("--log"); ap.add_argument("--exposure", default="locked")
ap.add_argument("--sel_ids", default="0,1,2,3,4"); ap.add_argument("--held_ids", default=",".join(map(str, range(200, 215))))
ap.add_argument("--reruns", type=int, default=2); ap.add_argument("--out"); ap.add_argument("--workers", type=int, default=6)
ap.add_argument("--reuse", nargs="*", default=[], help="existing heldout files: version_in_log=file:playbook_name")
ap.add_argument("--min_balance", type=float, default=20); ap.add_argument("--k3", type=int, default=1)
A = ap.parse_args(); solver.MAX_STEPS = 30; mod = {"retail": tret, "cuad": tcu}[A.family]
L = [json.loads(l) for l in open(A.log)]
acc = [r for r in L if r["kind"] == "candidate" and r["accepted"]]
pbs = {r["id"]: r["playbook"] for r in acc}
reuse = {}
for spec in A.reuse:  # e.g. g0=runs/heldout_cuad.jsonl:start
    v, rest = spec.split("="); f, name = rest.split(":")
    for l in open(f):
        x = json.loads(l)
        if x["playbook"] == name: reuse.setdefault(v, []).append(x)
jobs = []
for v in pbs:
    for i in A.sel_ids.split(","):
        for rep in range(1, A.reruns + 1): jobs.append((v, "selection", rep, int(i)))
    have = {x["task"] for x in reuse.get(v, [])}
    for i in A.held_ids.split(","):
        if mod.make_task(int(i))["id"] not in have: jobs.append((v, "heldout", 1, int(i)))
done = set()
if os.path.exists(A.out):
    for l in open(A.out): x = json.loads(l); done.add((x["version"], x["split"], x["repeat"], x["task"]))
out = open(A.out, "a")
for v, xs in reuse.items():  # copy reused held-out runs into this file once
    for x in xs:
        if (v, "heldout", 1, x["task"]) in done: continue
        rec = {k: x.get(k) for k in ("task", "gold", "gold_detail", "judge_k26", "judge_k3", "commands", "usage", "report")}
        rec.update(version=v, split="heldout", repeat=1, reused=True); out.write(json.dumps(rec) + "\n"); done.add((v, "heldout", 1, x["task"]))
out.flush()
random.Random(0).shuffle(jobs)
print(len(jobs), "jobs", flush=True)
def go(j):
    v, split, rep, i = j; t = mod.make_task(i)
    if (v, split, rep, t["id"]) in done: return
    if loop.balance() < A.min_balance: print("low balance, skip", j, flush=True); return
    r = solver.run(t, pbs[v], exposure=A.exposure)
    if not r.get("usage", {}).get("prompt"): print("empty run", j, flush=True); return
    g, det = mod.gold_score(t, r["report"])
    j1 = judge.judge(t["instruction"], r["report"], family=A.family)
    j2 = judge.judge(t["instruction"], r["report"], family=A.family, model="kimi-k3") if A.k3 else {"score": None}
    rec = {"version": v, "split": split, "repeat": rep, "task": t["id"], "gold": g, "gold_detail": det,
           "judge_k26": j1["score"], "judge_k3": j2["score"], "commands": r["commands"], "usage": r["usage"],
           "report": r["report"], "t": time.time()}
    out.write(json.dumps(rec, default=float) + "\n"); out.flush(); print(v, split, rep, t["id"], round(g, 2), j1["score"], flush=True)
with ThreadPoolExecutor(A.workers) as ex: list(ex.map(go, jobs))
