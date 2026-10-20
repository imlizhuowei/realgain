import json, re, sys, random, statistics as st
from collections import defaultdict, Counter
sys.path.insert(0, "/home/claude/project4/loop")
R = "/home/claude/project4/loop/runs/"
F5 = ["revenue_prior", "revenue_current", "periods_comparable", "top_country_by_change", "unidentified_share_pct"]

def load(f): return [json.loads(l) for l in open(R + f)]
A, B = load("heldout_retail_A.jsonl"), load("heldout_retail_B.jsonl")
for r in A: r["_src"] = "A"
for r in B: r["_src"] = "B"
allr = A + B

# data sanity
print("dup (src,playbook,task):", [k for k, c in Counter((r["_src"], r["playbook"], r["task"]) for r in allr).items() if c > 1])
print("B pb vs playbook:", Counter((r["pb"], r["playbook"]) for r in B))
for src, rs in (("A", A), ("B", B)):
    s = {r["task"] for r in rs if r["playbook"] == "start"}; f = {r["task"] for r in rs if r["playbook"] == "final"}
    print(src, "tasks start-only", s - f, "final-only", f - s)
print("A tasks", sorted({r['task'] for r in A})); print("B tasks", sorted({r['task'] for r in B}))
for r in allr:
    rep = r.get("report") or ""
    if len(rep.strip()) < 200 or "KEY" not in rep:
        print("short/no-KEY report:", r["_src"], r["playbook"], r["task"], len(rep), repr(rep[:120]))
    for k in ("judge_k26", "judge_k3", "judge"):
        if k in r and r[k] is None: print("None judge:", r["_src"], r["playbook"], r["task"], k)

def g5(r): return sum(float(r["gold_detail"][f]) for f in F5) / 5

# per task, per playbook: mean over replicates
agg = defaultdict(list)
for r in allr: agg[(r["task"], r["playbook"])].append(g5(r))
tasks = sorted({t for t, _ in agg})
d = [100 * (st.mean(agg[(t, "final")]) - st.mean(agg[(t, "start")])) for t in tasks]
print("n tasks", len(tasks), "mean diff pts %.2f" % st.mean(d))
print("down/up/same", sum(x < -1e-9 for x in d), sum(x > 1e-9 for x in d), sum(abs(x) <= 1e-9 for x in d))
random.seed(0)
bs = sorted(st.mean(random.choices(d, k=len(d))) for _ in range(20000))
print("bootstrap 95%% CI [%.2f, %.2f]" % (bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]))
# alt: unpooled run-level difference
for src, rs in (("A", A), ("B", B)):
    s = [g5(r) for r in rs if r["playbook"] == "start"]; f = [g5(r) for r in rs if r["playbook"] == "final"]
    print(src, "run-level diff pts %.2f" % (100 * (st.mean(f) - st.mean(s))))
# full 7-field gold for reference
d7 = defaultdict(list)
for r in allr: d7[(r["task"], r["playbook"])].append(r["gold"])
print("7-field pooled diff %.2f" % (100 * st.mean(st.mean(d7[(t, 'final')]) - st.mean(d7[(t, 'start')]) for t in tasks)))

# judges
def jdiff(key, rs):
    a = defaultdict(list)
    for r in rs:
        if r.get(key) is not None: a[(r["task"], r["playbook"])].append(r[key])
    ts = sorted({t for t, p in a if (t, "start") in a and (t, "final") in a})
    pooled = st.mean(st.mean(a[(t, "final")]) - st.mean(a[(t, "start")]) for t in ts)
    runs = st.mean(r[key] for r in rs if r["playbook"] == "final" and r.get(key) is not None) - \
           st.mean(r[key] for r in rs if r["playbook"] == "start" and r.get(key) is not None)
    return len(ts), pooled, runs
for key in ("judge_k26", "judge_k3", "judge"):
    for name, rs in (("A", A), ("B", B), ("A+B", allr)):
        if any(r.get(key) is not None for r in rs):
            print(key, name, "ntasks=%d task-pooled %+.3f run-level %+.3f" % jdiff(key, rs))
print("B judge==judge_k26?", sum(r["judge"] == r["judge_k26"] for r in B), "/", len(B), " B judge_k3 non-null:", sum(r["judge_k3"] is not None for r in B))

# revenue_prior direction
from tasks_retail import make_task
def keys(text): return {m.group(1): m.group(2).strip().strip("`*").strip() for m in re.finditer(r"^\s*KEY\s+(\w+)\s*=\s*(.+?)\s*$", text, re.M)}
gold_cache = {}
cnt = Counter(); mism = 0
for r in allr:
    i = int(r["task"].split("-")[1])
    if i not in gold_cache: gold_cache[i] = make_task(i)["gold"]
    g = gold_cache[i]["revenue_prior"]
    got = keys(r.get("report") or "").get("revenue_prior")
    try: x = float(got.replace(",", "").replace("%", "").replace("£", "")) if got is not None else None
    except ValueError: x = None
    ok = x is not None and abs(x - g) <= max(0.005 * abs(g), 1.0)
    if ok != bool(r["gold_detail"]["revenue_prior"]): mism += 1; print("detail mismatch", r["_src"], r["playbook"], r["task"], got, g)
    p = r["playbook"]
    if not bool(r["gold_detail"]["revenue_prior"]):
        cnt[(p, "wrong")] += 1
        if x is None: cnt[(p, "missing")] += 1
        elif x < g: cnt[(p, "low")] += 1
        else: cnt[(p, "high")] += 1
    cnt[(p, "n")] += 1
print("recomputed-vs-logged revenue_prior mismatches:", mism)
print(dict(cnt))
