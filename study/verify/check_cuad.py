import json, statistics as st
from collections import defaultdict, Counter
R = "/home/claude/project4/loop/runs/"
def load(f): return [json.loads(l) for l in open(R + f)]
def reads_key(cmds): return any((".grader" in c or "gold.json" in c) for c in (cmds or []) if not c.lstrip().startswith("#"))
def m(x): return st.mean(x) if x else float("nan")

# --- heldout_cuad
H = load("heldout_cuad.jsonl")
print("heldout_cuad dups:", [k for k, c in Counter((r["playbook"], r["task"]) for r in H).items() if c > 1])
for k in ("gold", "judge_k26", "judge_k3"):
    a = defaultdict(list)
    for r in H:
        if r[k] is not None: a[(r["task"], r["playbook"])].append(r[k])
    ts = sorted({t for t, _ in a if (t, "start") in a and (t, "final") in a})
    sc = 100 if k == "gold" else 1
    print("heldout_cuad", k, "n=%d diff %+.3f" % (len(ts), sc * m([m(a[(t, 'final')]) - m(a[(t, 'start')]) for t in ts])))
print("heldout_cuad key-read: start", sum(reads_key(r["commands"]) for r in H if r["playbook"] == "start"),
      "final", sum(reads_key(r["commands"]) for r in H if r["playbook"] == "final"))
for r in H:
    if len((r.get("report") or "").strip()) < 200: print("short report heldout_cuad", r["playbook"], r["task"])

# --- decomposition
for R_ in ("R1", "R2", "R3"):
    D = load(f"decomp_{R_}.jsonl")
    print(f"\n== decomp_{R_}: n={len(D)}")
    c = Counter((r["version"], r["split"], r["repeat"], r["task"]) for r in D)
    print(" dups:", [k for k, v in c.items() if v > 1])
    print(" cells:", sorted(Counter((r["version"], r["split"], r["repeat"]) for r in D).items()))
    for r in D:
        if len((r.get("report") or "").strip()) < 200: print(" short report", r["version"], r["split"], r["repeat"], r["task"], len(r.get("report") or ""))
        for k in ("gold", "judge_k26", "judge_k3"):
            if r.get(k) is None: print(" None", k, r["version"], r["split"], r["task"])
    if any("reused" in r for r in D): print(" reused:", Counter((r["version"], r["split"], r.get("reused")) for r in D if "reused" in r))
    vers = sorted({r["version"] for r in D})
    for split in ("heldout", "selection"):
        a = defaultdict(list)
        for r in D:
            if r["split"] == split:
                for k in ("gold", "judge_k26", "judge_k3"):
                    if r[k] is not None: a[(r["version"], k, r["task"])].append(r[k])
        for v in vers:
            if v == "g0": continue
            out = []
            for k in ("gold", "judge_k26", "judge_k3"):
                ts = sorted({t for (vv, kk, t) in a if vv == v and kk == k and ("g0", k, t) in a})
                sc = 100 if k == "gold" else 1
                out.append("%s %+.2f (n=%d)" % (k, sc * m([m(a[(v, k, t)]) - m(a[("g0", k, t)]) for t in ts]), len(ts)))
            print(f" {split} {v} vs g0:", "; ".join(out))
        for v in vers:
            rs = [r for r in D if r["split"] == split and r["version"] == v]
            print(f"  {split} {v}: runs={len(rs)} mean gold={m([r['gold'] for r in rs]):.3f} key-read={sum(reads_key(r['commands']) for r in rs)}/{len(rs)}")
