"""Our loop logs (loop.py, heldout.py, decompose.py) -> realgain records.
proxy = what the loop selected on ('judge' or 'gold'); truth = answer-key score.
Usage: python adapters/ourloop.py <loop.jsonl> <proxy: judge|gold> out.jsonl [extra heldout/decompose jsonl ...]"""
import json, sys
log, proxy, out, extra = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
L = [json.loads(l) for l in open(log)]
recs = []
def ok(x): return bool(x.get("usage"))  # runs that failed for lack of API credit are dropped
for r in L:
    if r["kind"] == "candidate":
        for x in r["runs"]:
            if not ok(x): continue
            recs.append({"version": r["id"], "parent": r["parent"], "accepted": r["accepted"], "generation": r["gen"],
                         "task": x["task"], "split": "selection", "repeat": 0,
                         "score": x["gold"] if proxy == "gold" else x.get("judge"), "truth": x["gold"],
                         "judge": x.get("judge"), "commands": x.get("commands", [])})
    elif r["kind"] == "fresh":
        for x in r["runs"]:
            if not ok(x): continue
            recs.append({"version": r["incumbent"], "task": x["task"], "split": "fresh_check", "repeat": r["gen"],
                         "score": x["gold"] if proxy == "gold" else x.get("judge"), "truth": x["gold"], "judge": x.get("judge")})
for f in extra:
    for l in open(f):
        x = json.loads(l)
        recs.append({"version": x["version"], "task": x["task"], "split": x["split"], "repeat": x.get("repeat", 1), "phase": "recheck",
                     "score": x["gold"] if proxy == "gold" else x.get("judge_k26"), "truth": x["gold"],
                     "judge": x.get("judge_k26"), "judge_k3": x.get("judge_k3"), "commands": x.get("commands", [])})
with open(out, "w") as f:
    for r in recs: f.write(json.dumps(r) + "\n")
print(len(recs), "records")
