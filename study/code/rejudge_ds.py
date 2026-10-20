"""Re-score every saved report with a non-Kimi judge (DeepSeek), same rubric, same inputs (assignment + report only)."""
import json, os, re, sys, time, urllib.request, hashlib
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import judge as J, tasks_retail as tret, tasks_cuad as tcu
ENV = dict(l.strip().split("=", 1) for l in open(os.environ.get("DEEPSEEK_ENV", "secrets/deepseek.env")) if "=" in l)
MODEL = sys.argv[1] if len(sys.argv) > 1 else "deepseek-v4-pro"
OUT = f"runs/rejudge_{MODEL}.jsonl"
SPEC = {"retail": None, "cuad": tcu.SPEC}
def instr(fam, task):
    return tcu.SPEC if fam == "cuad" else tret.make_task(int(task.split("-")[1]))["instruction"]
def ds_judge(fam, assignment, report):
    sysmsg = {"cuad": J.RUBRIC_CUAD, "retail": J.RUBRIC_RETAIL}[fam]
    body = json.dumps({"model": MODEL, "max_tokens": 8000, "messages": [{"role": "system", "content": sysmsg},
            {"role": "user", "content": f"ASSIGNMENT:\n{assignment}\n\nMEMO:\n{report or '(empty)'}"}]}).encode()
    req = urllib.request.Request(ENV["DEEPSEEK_BASE_URL"] + "/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + ENV["DEEPSEEK_API_KEY"], "Content-Type": "application/json"})
    for a in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r: d = json.loads(r.read())
            out = json.loads(re.search(r"\{.*\}", d["choices"][0]["message"]["content"], re.S).group(0))
            return float(out["score"]), out.get("critique", ""), d.get("usage", {})
        except Exception as e:
            err = str(e); time.sleep(5 * (a + 1))
    return None, "error: " + err, {}
# collect reports
items = []
def add(src, fam, key, task, report, gold, extra):
    if report is None: return
    items.append({"src": src, "fam": fam, "key": key, "task": task, "report": report, "gold": gold, **extra})
for f, tag in [("runs/heldout_retail_A.jsonl", "heldout_retail_A"), ("runs/heldout_retail_B.jsonl", "heldout_retail_B"), ("runs/heldout_cuad.jsonl", "heldout_cuad")]:
    for l in open(f):
        x = json.loads(l); fam = "cuad" if "cuad" in x["task"] else "retail"
        add(tag, fam, f"{tag}|{x['playbook']}|{x['task']}", x["task"], x["report"], x["gold"],
            {"playbook": x["playbook"], "judge_k26": x.get("judge_k26"), "judge_k3": x.get("judge_k3"), "gold_detail": x.get("gold_detail")})
for R in ["R1", "R2", "R3"]:
    for l in open(f"runs/decomp_{R}.jsonl"):
        x = json.loads(l)
        if x.get("reused"): continue
        add(f"decomp_{R}", "cuad", f"decomp_{R}|{x['version']}|{x['split']}|{x['repeat']}|{x['task']}", x["task"], x.get("report"), x["gold"],
            {"version": x["version"], "split": x["split"], "judge_k26": x.get("judge_k26"), "judge_k3": x.get("judge_k3")})
for f, R in [("runs/cuad_R2_gold_locked.jsonl", "R2"), ("runs/cuad_R3_gold_open.jsonl", "R3")]:
    for l in open(f):
        r = json.loads(l)
        if r["kind"] != "candidate": continue
        for x in r["runs"]:
            add(f"loop_{R}", "cuad", f"loop_{R}|{r['id']}|{x['task']}", x["task"], x.get("report"), x["gold"], {"version": r["id"], "judge_k26": x.get("judge")})
done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)["key"])
todo = [it for it in items if it["key"] not in done]
print(len(items), "reports,", len(todo), "to score", flush=True)
out = open(OUT, "a")
def go(it):
    s, c, u = ds_judge(it["fam"], instr(it["fam"], it["task"]), it["report"])
    rec = {k: v for k, v in it.items() if k != "report"}; rec.update(judge_ds=s, critique_ds=c, usage_ds=u)
    out.write(json.dumps(rec) + "\n"); out.flush()
with ThreadPoolExecutor(20) as ex: list(ex.map(go, todo))
print("done", flush=True)
