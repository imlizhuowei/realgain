import json, statistics as st
R="/home/claude/project4/loop/runs/"
def rk(c): return any((".grader" in x or "gold.json" in x) for x in (c or []) if not x.lstrip().startswith("#"))
for f in ("cuad_v1","cuad_R2_gold_locked","cuad_R3_gold_open"):
    print("==",f)
    for r in map(json.loads, open(R+f+".jsonl")):
        runs=r["runs"]; g=[x["gold"] for x in runs]
        ts=[x["task"] for x in runs]
        ex=""
        if len(set(ts))!=len(ts): ex+=" DUPTASK"
        if any(not (x.get("report") or "x") for x in runs): ex+=" EMPTYREPORT"
        if r["kind"]=="candidate":
            print(f" cand {r['id']:6s} gen={r['gen']} parent={r.get('parent')} acc={r['accepted']} margin={r.get('pair_margin')} n={len(runs)} gold={st.mean(g):.3f} judge={st.mean([x['judge'] for x in runs if x.get('judge') is not None]):.2f} keyread={sum(rk(x.get('commands')) for x in runs)}/{len(runs)} tasks={sorted(set(ts))}{ex}")
        else:
            print(f" fresh gen={r['gen']} inc={r.get('incumbent')} n={len(runs)} gold={st.mean(g):.3f} keyread={sum(rk(x.get('commands')) for x in runs)}/{len(runs)}{ex}")
    print(" run keys:", sorted(r["runs"][0].keys()))
