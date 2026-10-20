"""DGM published run -> realgain records (per-task resolved = 1/0).
Usage: python adapters/dgm.py <run_dir> <dgm_metadata.jsonl> out.jsonl"""
import json, os, sys
run, meta, out = sys.argv[1:4]
txt = open(meta).read(); dec = json.JSONDecoder(); i = 0; gens = []
while i < len(txt):
    while i < len(txt) and txt[i].isspace(): i += 1
    if i >= len(txt): break
    o, i = dec.raw_decode(txt, i); gens.append(o)
gen_of, archive = {}, set()
for g in gens:
    for c in g["children"]: gen_of[c] = g["generation"]
    archive |= set(g["archive"])
recs = []
for v in sorted(os.listdir(run)):
    p = f"{run}/{v}/metadata.json"
    if not os.path.exists(p): continue
    m = json.load(open(p)); op = m.get("overall_performance")
    if not isinstance(op, dict): continue
    parent = m.get("parent_commit")
    for t in op.get("total_resolved_ids", []):
        recs.append({"version": v, "parent": parent, "accepted": v in archive, "generation": gen_of.get(v, 0), "task": t, "score": 1.0})
    for t in op.get("total_unresolved_ids", []) + op.get("total_emptypatch_ids", []):
        recs.append({"version": v, "parent": parent, "accepted": v in archive, "generation": gen_of.get(v, 0), "task": t, "score": 0.0})
# DGM's initial agent has no parent; the archive root is called 'initial'
with open(out, "w") as f:
    for r in recs: f.write(json.dumps(r) + "\n")
print(len(recs), "records,", len({r['version'] for r in recs}), "versions")
