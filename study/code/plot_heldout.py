import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
VALID=["revenue_prior","revenue_current","periods_comparable","top_country_by_change","unidentified_share_pct"]
def rows(files, fam):
    R=[json.loads(l) for f in files for l in open(f)]; d={}
    for r in R:
        g=np.mean([bool(r["gold_detail"][f]) for f in VALID])*100 if fam=="retail" else r["gold"]*100
        e=d.setdefault(r["task"],{}).setdefault(r["playbook"],{"truth":[],"judge_k26":[],"judge_k3":[]})
        e["truth"].append(g)
        for k in ["judge_k26","judge_k3"]:
            if r.get(k) is not None: e[k].append(r[k])
    return d
def ci(x):
    rng=np.random.default_rng(0); b=[rng.choice(x,len(x)).mean() for _ in range(10000)]; return np.percentile(b,[2.5,97.5])
fig,ax=plt.subplots(2,2,figsize=(10,7))
for i,(fam,files,title) in enumerate([("retail",["runs/heldout_retail_A.jsonl","runs/heldout_retail_B.jsonl"],"A  Retail YoY memo (21 unseen tasks)"),
                                     ("cuad",["runs/heldout_cuad.jsonl"],"D  Contract review (15 unseen contracts)")]):
    d=rows(files,fam)
    for j,(keys,lab,ylim) in enumerate([(["judge_k26","judge_k3"],"LLM judge score (1-10)",(4,10.3)),(["truth"],"correct vs ground truth (%)",(0,105))]):
        a=ax[i,j]
        for k,c in zip(keys,["#c0392b","#e67e22"] if j==0 else ["#1f5f8b"]):
            pairs=[(np.mean(v["start"][k]),np.mean(v["final"][k])) for v in d.values() if "start" in v and "final" in v and v["start"][k] and v["final"][k]]
            for s,f in pairs: a.plot([0,1],[s,f],c=c,alpha=.12,lw=1)
            P=np.array(pairs); m=P.mean(0); diff=P[:,1]-P[:,0]; lo,hi=ci(diff)
            name={"judge_k26":"kimi-k2.6 (judge used in loop)","judge_k3":"kimi-k3 (independent judge)","truth":"ground truth"}[k]
            a.plot([0,1],m,"o-",c=c,lw=2.5,label=f"{name}: {diff.mean():+.2f} [{lo:+.2f}, {hi:+.2f}]" if j==0 else f"{name}: {diff.mean():+.1f} pts [{lo:+.1f}, {hi:+.1f}]")
        a.set_xticks([0,1]); a.set_xticklabels(["starting playbook","loop's 'best' playbook"]); a.set_xlim(-.2,1.2); a.set_ylim(*ylim)
        a.set_ylabel(lab); a.legend(fontsize=7.5,loc="lower center"); a.set_title(title if j==0 else "", fontsize=10, loc="left")
fig.suptitle("Held-out check: what the judges see vs what is true\n(faint lines = individual tasks; numbers = mean change with 95% bootstrap CI)",fontsize=10.5)
plt.tight_layout(); plt.savefig("heldout_v1.png",dpi=150)
