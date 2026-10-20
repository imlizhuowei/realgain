"""Optional figure (needs matplotlib): for each accepted version, the claimed gain and what survives each check."""
def plot(rep, path, title=""):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, numpy as np
    rows = [(v, r) for v, r in rep["versions"].items() if r["accepted"]] or list(rep["versions"].items())
    rows.sort(key=lambda x: (x[1]["generation"] or 0, x[0]))
    keys = [("seen", "seen by loop", "#c0392b"), ("rerun", "re-run (same tasks)", "#e8a598"),
            ("heldout", "held-out score", "#1f5f8b"), ("truth_heldout", "held-out ground truth", "#2e8b57")]
    keys = [k for k in keys if any(r.get(k[0]) for _, r in rows)]
    fig, ax = plt.subplots(figsize=(max(5, 1.3 * len(rows) + 2), 3.6)); w = 0.8 / max(1, len(keys)); x = np.arange(len(rows))
    ax2 = ax.twinx() if any(k[0] == "truth_heldout" for k in keys) else None
    for i, (k, lab, c) in enumerate(keys):
        a = ax2 if (k == "truth_heldout" and ax2 is not None) else ax
        m = np.array([r[k]["diff"] if r.get(k) else np.nan for _, r in rows])
        lo = np.array([r[k]["ci"][0] if r.get(k) else np.nan for _, r in rows]); hi = np.array([r[k]["ci"][1] if r.get(k) else np.nan for _, r in rows])
        off = x - 0.4 + w * (i + 0.5)
        a.bar(off, m, w, color=c, label=lab); a.errorbar(off, m, yerr=[m - lo, hi - m], fmt="none", ecolor="#333", lw=.8, capsize=2)
    if ax2 is not None:
        lim1 = max(abs(v) for v in ax.get_ylim()); sr, tr = rep.get("score_range"), rep.get("truth_range")
        # same visual scale: a bar of a given height is the same fraction of each measure's observed range
        k = (tr[1] - tr[0]) / (sr[1] - sr[0]) if sr and tr and sr[1] > sr[0] and tr[1] > tr[0] else 1.0
        lim = max(lim1 * k, max(abs(v) for v in ax2.get_ylim()) if k == 1.0 else 0); ax2.set_ylim(-lim, lim)
        ax2.set_ylabel("ground-truth gain (right axis, same relative scale)", color="#2e8b57", fontsize=8); h2, l2 = ax2.get_legend_handles_labels()
    else: h2, l2 = [], []
    lim = max(abs(v) for v in ax.get_ylim()); ax.set_ylim(-lim, lim)
    ax.axhline(0, c="k", lw=.7); ax.set_xticks(x); ax.set_xticklabels([f"{v}\n{r['verdict']}" for v, r in rows], fontsize=8)
    ax.set_ylabel("optimised-score gain vs start"); h1, l1 = ax.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=7, frameon=False, loc="lower left"); ax.set_title(title, fontsize=10, loc="left")
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close(fig); return path
