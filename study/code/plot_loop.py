import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
def load(f):
    L=[json.loads(l) for l in open(f)]; inc=None; traj=[]; fresh=[]; pts=[]
    for r in L:
        if r["kind"]=="stop": break
        rs=r["runs"]
        if any(x.get("judge") is None for x in rs) or any(not x.get("usage") for x in rs): continue  # quota-corrupted
        g=np.mean([x["gold"] for x in rs])*100; j=np.mean([x["judge"] for x in rs])
        if r["kind"]=="fresh": fresh.append((r["gen"],j,g)); continue
        pts += [(x["judge"], x["gold"]*100) for x in rs]
        if r["accepted"]: inc=(j,g)
        if not traj or traj[-1][0]!=r["gen"]: traj.append((r["gen"],)+inc)
        else: traj[-1]=(r["gen"],)+inc
    return traj, fresh, pts, L
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
for a,(f,name) in zip(ax,[("runs/retail_v1.jsonl","A  Retail YoY memo (real transactions)"),("runs/cuad_v1.jsonl","D  Contract intake review (CUAD, lawyer labels)")]):
    traj,fresh,pts,L=load(f); t=np.array(traj); fr=np.array(fresh)
    a2=a.twinx()
    a.plot(t[:,0],t[:,1],"o-",c="#c0392b",label="judge score, practice tasks"); 
    if len(fr): a.plot(fr[:,0],fr[:,1],"s--",c="#e8a598",label="judge score, new tasks")
    a2.plot(t[:,0],t[:,2],"o-",c="#1f5f8b",label="true accuracy, practice tasks")
    if len(fr): a2.plot(fr[:,0],fr[:,2],"s--",c="#8fb8d6",label="true accuracy, new tasks")
    a.set_ylim(4,10); a2.set_ylim(0,100); a.set_xlabel("generation of self-improvement")
    a.set_ylabel("LLM judge (1-10)",color="#c0392b"); a2.set_ylabel("correct vs ground truth (%)",color="#1f5f8b")
    p=np.array(pts); r=np.corrcoef(p[:,0],p[:,1])[0,1]
    a.set_title(f"{name}\njudge-vs-truth correlation over {len(p)} answers: r = {r:.2f}",fontsize=9.5)
    print(f, "corr", round(r,2), "n", len(p)); print(" traj", traj); print(" fresh", fresh)
    h1,l1=a.get_legend_handles_labels(); h2,l2=a2.get_legend_handles_labels(); a.legend(h1+h2,l1+l2,fontsize=7,loc="lower left")
fig.suptitle("Self-improvement optimised against an LLM judge: what the judge sees vs what is true (5 tasks per point)",fontsize=10)
plt.tight_layout(); plt.savefig("loop_v1.png",dpi=150)
