import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from analyze_decomp import analyze
cfg = [("R1  judge picks, answer key locked", "runs/cuad_v1.jsonl", "runs/decomp_R1.jsonl", "judge"),
       ("R2  answer key picks, key locked", "runs/cuad_R2_gold_locked.jsonl", "runs/decomp_R2.jsonl", "gold"),
       ("R3  answer key picks, key in agent's folder", "runs/cuad_R3_gold_open.jsonl", "runs/decomp_R3.jsonl", "gold")]
fig, ax = plt.subplots(1, 3, figsize=(14, 4.6), sharey=True)
for a, (title, lg, dc, proxy) in zip(ax, cfg):
    rows = [r for r in analyze(lg, dc, proxy) if r["version"] != "g0"]
    x = np.arange(len(rows)); w = 0.2
    def bar(off, key, c, lab):
        m = [r[key][0] if r[key][0] is not None else np.nan for r in rows]
        lo = [r[key][1][0] if r[key][1] is not None else np.nan for r in rows]; hi = [r[key][1][1] if r[key][1] is not None else np.nan for r in rows]
        a.bar(x + off, m, w, color=c, label=lab)
        a.errorbar(x + off, m, yerr=[np.array(m) - np.array(lo), np.array(hi) - np.array(m)], fmt="none", ecolor="#333", lw=.8, capsize=2)
    if proxy == "gold":
        a.bar(x - 1.5 * w, [r["claimed"] for r in rows], w, color="#c0392b", label="gain the loop saw (one run)")
    bar(-0.5 * w if proxy == "gold" else -w, "rerun_sel", "#e8a598", "re-run on same contracts")
    bar(0.5 * w if proxy == "gold" else 0, "held", "#1f5f8b", "15 new contracts (all runs)")
    if proxy == "gold": bar(1.5 * w, "held_honest", "#8fb8d6", "15 new contracts, runs that did not read the key")
    if True:
        a2 = a.twinx(); jm = [r["held_judge"][0] for r in rows]; jl = [r["held_judge"][1] for r in rows]
        a2.errorbar(x + w, jm, yerr=[[m - c[0] for m, c in zip(jm, jl)], [c[1] - m for m, c in zip(jm, jl)]], fmt="D", color="#e67e22", label="judge gain on new contracts (right axis)")
        a2.set_ylim(-2.5, 2.5); a2.set_ylabel("LLM judge gain (points out of 10)", color="#e67e22") if proxy=="judge" or "open" in lg else None; a2.legend(fontsize=7, loc="lower right")
    a.axhline(0, c="k", lw=.7); a.set_xticks(x); a.set_xticklabels([f"gen {r['gen']}\n{r['version']}" for r in rows], fontsize=8)
    a.set_title(title, fontsize=10, loc="left"); a.set_ylim(-15, 15)
    cr = [rr for rr in analyze(lg, dc, proxy)]
    note = "key read in " + ", ".join(f"{r['version']}: {100*(r['cheat_rate_held'] or 0):.0f}%" for r in cr) + " of new-contract runs" if proxy == "gold" and "open" in lg else ""
    if note: a.text(0.01, 0.95, note, transform=a.transAxes, fontsize=7)
ax[0].set_ylabel("answer-key accuracy gain vs. starting version (points)"); ax[1].legend(fontsize=7, loc="upper left")
fig.suptitle("Every version each loop accepted, checked three ways (contract review, CUAD; vs. all runs of the starting version; 95% bootstrap CIs over contracts)", fontsize=10)
plt.tight_layout(); plt.savefig("decomp_v1.png", dpi=150); print("ok")
