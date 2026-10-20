"""Core checks. Everything works on a flat list of evaluation records (see FORMAT.md).

Terminology
-----------
root        the starting version (no parent). Its runs on each task are POOLED (all repeats) as the baseline.
seen gain   what the loop saw when it accepted a version: its runs with phase "acceptance" (the default) minus
            the root's, on the selection tasks. This is the number a loop's own log reports.
re-run gain the same comparison using only runs with phase "recheck" (fresh runs made afterwards to check).
            seen - re-run = luck (winner's curse: the version was kept because its first run came out high).
held-out    tasks the loop never used. re-run - held-out = fitting to the selection tasks.
truth       a second score the loop did NOT optimise (answer key, expert label, executed test).
            If score rises and truth does not, the score is being fooled.
honest      runs with no grader access found in their commands.
"""
import json, math, re
from collections import defaultdict, Counter
import numpy as np

B = 4000
DEFAULT_TAMPER = [r"\.grader", r"gold\.json", r"hidden_tests?", r"expected[_.]", r"answer[_ ]?key", r"grade\.py",
                  r"/grader/", r"eval_utils"]


# --------------------------------------------------------------------------- loading
def load(path_or_records):
    recs = path_or_records if isinstance(path_or_records, list) else \
        [json.loads(l) for l in open(path_or_records) if l.strip()]
    out = []
    for r in recs:
        if r.get("score") is None and r.get("truth") is None: continue
        r = dict(r); r.setdefault("split", "selection"); r.setdefault("repeat", 0); out.append(r)
    return out


def _meta(recs):
    meta = {}
    for r in recs:
        m = meta.setdefault(r["version"], {"parent": None, "accepted": None, "generation": None})
        for k in m:
            if m[k] is None and r.get(k) is not None: m[k] = r[k]
    roots = [v for v, m in meta.items() if not m["parent"]]
    return meta, (roots[0] if len(roots) == 1 else (sorted(roots, key=lambda v: meta[v]["generation"] or 0)[0] if roots else None))


def _accessed(r, rx):
    return any(rx.search(c) for c in (r.get("commands") or []) if isinstance(c, str) and not c.startswith("#"))


def _cells(recs, key, split, repeats=None, honest_only=False, rx=None):
    """version -> task -> list of values"""
    t = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r["split"] != split or r.get(key) is None: continue
        if repeats == "first" and r.get("phase", "acceptance") != "acceptance": continue
        if repeats == "later" and r.get("phase", "acceptance") != "recheck": continue
        if honest_only and _accessed(r, rx): continue
        t[r["version"]][r["task"]].append(float(r[key]))
    return t


# --------------------------------------------------------------------------- statistics
def paired(cells, a, b, rng=None, min_tasks=2):
    """Mean over shared tasks of (b - a), each side averaged over its runs.
    95% interval from the t distribution on the per-task differences. (A percentile bootstrap, which this toolkit
    used before v0.3, under-covers badly with few tasks: 85% at 5 tasks, 90% at 10, in our simulations; the t interval
    stays at 94-96%. See benchmarks/.) Because each task's difference already contains both versions' run noise,
    the interval covers run-to-run noise as well as task sampling."""
    if a not in cells or b not in cells: return None
    tasks = sorted(set(cells[a]) & set(cells[b]))
    if len(tasks) < min_tasks: return None
    d = np.array([np.mean(cells[b][t]) - np.mean(cells[a][t]) for t in tasks])
    n, m = len(d), float(d.mean())
    sd = float(d.std(ddof=1)) if n > 1 else 0.0
    se = sd / math.sqrt(n)
    if se > 0:
        q = _t975(n - 1); lo, hi = m - q * se, m + q * se
        p = _t_two_sided_p(m / se, n - 1)
    else:
        lo = hi = m; p = 1.0 if m == 0 else 0.0
    return {"n_tasks": n, "diff": m, "ci": [float(lo), float(hi)], "p": float(p), "se": se,
            "sd_task_diff": sd if n > 1 else None,
            "up": int((d > 0).sum()), "down": int((d < 0).sum()), "same": int((d == 0).sum())}


def _t975(df):
    """97.5% quantile of Student's t (no scipy needed): table for small df, Cornish-Fisher expansion beyond."""
    T = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
         11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}
    if df in T: return T[df]
    z = 1.959964
    return z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)


def _t_two_sided_p(t, df):
    """Two-sided p-value of Student's t via the regularized incomplete beta function (continued fraction)."""
    x = df / (df + t * t)
    return float(min(1.0, _betainc(df / 2, 0.5, x)))


def _betainc(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x > (a + 1) / (a + b + 2): return 1 - _betainc(b, a, 1 - x)
    # Lentz continued fraction
    f, c, d = 1.0, 1.0, 1 - (a + b) * x / (a + 1)
    d = 1 / (d if abs(d) > 1e-300 else 1e-300); f = d
    for m in range(1, 300):
        for num in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)), -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1 + num * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
            c = 1 + num / c; c = c if abs(c) > 1e-300 else 1e-300
            f *= d * c
        if abs(d * c - 1) < 1e-12: break
    return math.exp(lbeta) * f / a


def _rng_idx(rng, n): return rng.integers(0, n, (B, n))


def _rng_of(recs, key):
    v = [r[key] for r in recs if r.get(key) is not None]
    return [float(min(v)), float(max(v))] if v else None


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (dict name -> p)."""
    items = sorted((p, k) for k, p in pvals.items() if p is not None)
    m, out, running = len(items), {}, 0.0
    for i, (p, k) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p)); out[k] = running
    return out


def null_best_of_k(cells, versions, rng, sims=2000):
    """If none of these versions really differed, how far would the best one beat the average by chance?
    Shuffles version labels within each task (keeps task difficulty), takes max mean - mean."""
    vs = [v for v in versions if v in cells]
    if len(vs) < 2: return None
    cnt = Counter(t for v in vs for t in cells[v])
    tasks = sorted(t for t, c in cnt.items() if c >= len(vs) / 2)
    vs = [v for v in vs if set(tasks) <= set(cells[v])]
    if len(vs) < 2 or len(tasks) < 2: return None
    M = np.array([[np.mean(cells[v][t]) for t in tasks] for v in vs])
    obs = M.mean(1).max() - M.mean()
    idx = np.tile(np.arange(len(vs))[:, None], (1, len(tasks)))
    null = np.array([np.take_along_axis(M, rng.permuted(idx, axis=0), 0).mean(1).max() - M.mean() for _ in range(sims)])
    best = vs[int(M.mean(1).argmax())]
    return {"k": len(vs), "n_tasks": len(tasks), "best": best, "observed_best_minus_mean": float(obs),
            "chance_best_minus_mean": float(null.mean()), "p_value": float((null >= obs).mean())}


def noise_profile(cells, root):
    """Run-to-run noise (needs repeats of the root) and task-sampling standard error of a version's mean."""
    if root not in cells: return None
    per_task = [v for v in cells[root].values()]
    rep_sd = [np.std(v, ddof=1) for v in per_task if len(v) > 1]
    means = np.array([np.mean(v) for v in per_task])
    n = len(means)
    return {"n_tasks": n, "root_mean": float(means.mean()),
            "run_sd_within_task": float(np.mean(rep_sd)) if rep_sd else None,
            "run_sd_of_mean": float(np.mean(rep_sd) / math.sqrt(n)) if rep_sd else None,
            "task_se_of_mean": float(means.std(ddof=1) / math.sqrt(n)) if n > 1 else None}


def min_detectable(pair):
    """Smallest true change this comparison would detect ~80% of the time (two-sided 5%): 2.8 x SE."""
    if not pair or pair.get("sd_task_diff") is None: return None
    return 2.8 * pair["sd_task_diff"] / math.sqrt(pair["n_tasks"])


# --------------------------------------------------------------------------- the report
def report(path_or_records, tamper_patterns=DEFAULT_TAMPER, seed=0):
    rng = np.random.default_rng(seed)
    recs = load(path_or_records)
    rx = re.compile("|".join(tamper_patterns)) if tamper_patterns else re.compile(r"(?!x)x")
    meta, root = _meta(recs)
    has_truth = any(r.get("truth") is not None for r in recs)
    has_held = any(r["split"] == "heldout" for r in recs)
    C = {  # all the views we need
        "sel": _cells(recs, "score", "selection"),
        "sel_first": _cells(recs, "score", "selection", "first"),
        "sel_later": _cells(recs, "score", "selection", "later"),
        "held": _cells(recs, "score", "heldout"),
        "held_honest": _cells(recs, "score", "heldout", honest_only=True, rx=rx),
        "t_sel": _cells(recs, "truth", "selection"),
        "t_held": _cells(recs, "truth", "heldout"),
        "t_held_honest": _cells(recs, "truth", "heldout", honest_only=True, rx=rx),
    }
    # grader access
    access = defaultdict(int); runs_n = defaultdict(int); infl = []
    for r in recs:
        runs_n[r["version"]] += 1
        if _accessed(r, rx): access[r["version"]] += 1
    honest_by = defaultdict(list); acc_by = defaultdict(list)
    for r in recs:
        if r.get("score") is None: continue
        (acc_by if _accessed(r, rx) else honest_by)[(r["version"], r["task"], r["split"])].append(r["score"])
    for k, v in acc_by.items():
        if k in honest_by: infl.append(np.mean(v) - np.mean(honest_by[k]))

    rows = {}
    for v, m in meta.items():
        if v == root: continue
        row = {"parent": m["parent"], "accepted": m["accepted"], "generation": m["generation"],
               "runs": runs_n[v], "grader_access_runs": access.get(v, 0)}
        row["step_vs_parent"] = paired(C["sel"], m["parent"], v, rng) if m["parent"] else None
        if root:
            row["seen"] = paired(C["sel_first"], root, v, rng)
            row["rerun"] = paired(C["sel_later"], root, v, rng)
            row["heldout"] = paired(C["held"], root, v, rng)
            row["heldout_honest"] = paired(C["held_honest"], root, v, rng) if access.get(v) or access.get(root) else None
            row["truth_selection"] = paired(C["t_sel"], root, v, rng) if has_truth else None
            row["truth_heldout"] = paired(C["t_held"], root, v, rng) if has_truth else None
            row["truth_heldout_honest"] = paired(C["t_held_honest"], root, v, rng) if has_truth and (access.get(v) or access.get(root)) else None
            s, r_, h = (row["seen"] or {}).get("diff"), (row["rerun"] or {}).get("diff"), (row["heldout"] or {}).get("diff")
            row["decomposition"] = {
                "luck (seen - re-run)": (s - r_) if s is not None and r_ is not None else None,
                "fitting selection tasks (re-run - held-out)": (r_ - h) if r_ is not None and h is not None else None,
                "survives on held-out": h}
            row["min_detectable_heldout"] = min_detectable(row.get("truth_heldout") or row["heldout"] or row["rerun"] or row["step_vs_parent"])
        row["verdict"], row["why"] = verdict(row, has_truth, has_held)
        rows[v] = row

    # selection-corrected expectation for new tasks, from the loop's own log (all candidates, no re-runs needed)
    from .shrink import candidate_gains, shrink
    base = C["sel_first"] if root in C["sel_first"] else C["sel"]
    est, prior = shrink(candidate_gains(base, root, [v for v in meta if v != root]))
    for v, e in est.items():
        if v in rows: rows[v]["expected_new_tasks"] = e
    # multiple comparisons over the versions the loop accepted (held-out truth > held-out score > selection)
    pv = {}
    for v, row in rows.items():
        if not row["accepted"]: continue
        key = next((k for k in ("truth_heldout", "heldout", "rerun", "step_vs_parent") if row.get(k)), None)
        if key: pv[v] = row[key]["p"]
    for v, p in holm(pv).items(): rows[v]["p_holm"] = p

    out = {"n_records": len(recs), "root": root, "versions": rows,
           "noise": noise_profile(C["held"] if has_held else C["sel"], root),
           "best_overall": null_best_of_k(C["sel"], list(meta), rng),
           "grader_access": {"runs": int(sum(access.values())), "versions": dict(access),
                             "mean_score_gain_when_accessed": float(np.mean(infl)) if infl else None},
           "has_truth": has_truth, "has_heldout": has_held,
           "score_range": _rng_of(recs, "score"), "truth_range": _rng_of(recs, "truth"),
           "shrinkage_prior": prior}
    by_parent = defaultdict(list)
    for v, m in meta.items():
        if m["parent"]: by_parent[(m["parent"], m["generation"])].append(v)
    out["per_generation_selection"] = {f"gen {g} (children of {p})": null_best_of_k(C["sel"], vs, rng)
                                       for (p, g), vs in sorted(by_parent.items(), key=lambda x: str(x[0][1])) if len(vs) >= 2}
    both = [(r["score"], r["truth"]) for r in recs if r.get("truth") is not None and r.get("score") is not None]
    if len(both) > 3 and np.std([b[0] for b in both]) > 0 and np.std([b[1] for b in both]) > 0:
        x, y = np.array(both).T
        out["proxy_truth"] = {"n": len(both), "r_record_level": float(np.corrcoef(x, y)[0, 1])}
        sg = [(row["heldout"]["diff"], row["truth_heldout"]["diff"]) for row in rows.values()
              if row.get("heldout") and row.get("truth_heldout")]
        if sg:
            out["proxy_truth"]["versions_compared"] = len(sg)
            out["proxy_truth"]["versions_same_direction"] = int(sum(np.sign(a) == np.sign(b) for a, b in sg))
    return out


# --------------------------------------------------------------------------- verdicts
def _pos(p): return bool(p) and p["ci"][0] > 0
def _neg(p): return bool(p) and p["ci"][1] < 0


def verdict(row, has_truth, has_held):
    """A short label plus the reasons. Labels, in priority order:
    GRADER ACCESS   some runs touched the grader (score is partly copied, not earned)
    WORSE           held-out (truth if available) is significantly lower
    REAL            held-out truth (or held-out score when no truth) is significantly higher
    SCORE ONLY      held-out score up, held-out truth gain NOT SHOWN: the scorer is pleased; any real gain is too small
                    for these tasks to show (see 'detectable')
    FITS SELECTION  re-run on selection tasks is up, held-out is not
    LUCK            what the loop saw was up, re-runs are not
    UNCHECKED GAIN  beyond noise on the selection tasks, but no re-runs or held-out tasks exist to check it
    NOT SHOWN       nothing distinguishable from noise (may be too few tasks: see 'detectable')
    NO DATA         no comparison possible"""
    why = []
    if row.get("grader_access_runs"): why.append(f"{row['grader_access_runs']} run(s) touched the grader")
    T = row.get("truth_heldout_honest") or row.get("truth_heldout")
    H = row.get("heldout_honest") or row.get("heldout")
    target = T if (has_truth and T) else H
    if row.get("grader_access_runs"):
        lab = "GRADER ACCESS"
    elif _neg(target):
        lab = "WORSE"
    elif _pos(target):
        lab = "REAL"
    elif has_truth and _pos(H) and not _pos(T):
        lab = "SCORE ONLY"
    elif _pos(row.get("rerun")) and has_held and H and not _pos(H) and H["ci"][1] < row["rerun"]["diff"]:
        lab = "FITS SELECTION"   # held-out gain is credibly smaller than the re-run gain
    elif _pos(row.get("seen")) and row.get("rerun") and not _pos(row["rerun"]) and row["rerun"]["ci"][1] < row["seen"]["diff"] and not _pos(H):
        lab = "LUCK"             # re-runs are credibly below what the loop saw
    elif not H and not row.get("rerun") and _pos(row.get("step_vs_parent") or row.get("seen")):
        lab = "UNCHECKED GAIN"   # beyond task noise on the selection tasks, but never re-run or tested on new tasks
    elif any(row.get(k) for k in ("seen", "rerun", "heldout", "truth_heldout", "step_vs_parent")):
        lab = "NOT SHOWN"
    else:
        lab = "NO DATA"
    for k, name in [("seen", "seen by loop"), ("rerun", "re-run"), ("heldout", "held-out score"),
                    ("truth_heldout", "held-out truth")]:
        p = row.get(k)
        if p: why.append(f"{name} {p['diff']:+.3g} [{p['ci'][0]:+.3g},{p['ci'][1]:+.3g}] (n={p['n_tasks']})")
    return lab, why


# --------------------------------------------------------------------------- markdown
def _f(p):
    return "–" if not p else f"{p['diff']:+.3f} [{p['ci'][0]:+.3f}, {p['ci'][1]:+.3f}] n={p['n_tasks']}"


def _e(e):
    return "–" if not e else f"{e['expected']:+.3f} ± {e['sd']:.3f}"


def to_markdown(rep, title=None):
    L = [f"# realgain report{': ' + title if title else ''}", "",
         f"{rep['n_records']} records · starting version `{rep['root']}` · "
         f"{'held-out tasks: yes' if rep['has_heldout'] else 'held-out tasks: NO (gains cannot be checked on new tasks)'} · "
         f"{'ground truth: yes' if rep['has_truth'] else 'ground truth: no'}", ""]
    n = rep.get("noise")
    if n:
        s = f"**Noise.** Starting version: mean {n['root_mean']:.3f} over {n['n_tasks']} tasks; task-sampling SE of a mean {n['task_se_of_mean']:.3f}"
        if n.get("run_sd_of_mean") is not None: s += f"; run-to-run SE of a mean {n['run_sd_of_mean']:.3f}"
        L += [s + ".", ""]
    acc = {v: r for v, r in rep["versions"].items() if r["accepted"]}
    show = acc if acc else rep["versions"]
    L += ["## Accepted versions" if acc else "## Versions", "",
          "| version | gen | verdict | step vs parent | seen by loop (vs start) | expected on new tasks | re-run | held-out score | held-out truth | detectable | p, Holm-adjusted |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for v, r in sorted(show.items(), key=lambda x: (x[1]["generation"] if x[1]["generation"] is not None else 0, x[0])):
        md = r.get("min_detectable_heldout")
        L.append(f"| `{v}` | {r['generation']} | **{r['verdict']}** | {_f(r.get('step_vs_parent'))} | {_f(r.get('seen'))} | {_e(r.get('expected_new_tasks'))} | {_f(r.get('rerun'))} | "
                 f"{_f(r.get('heldout'))} | {_f(r.get('truth_heldout_honest') or r.get('truth_heldout'))} | "
                 f"{'≥ %.3f' % md if md else '–'} | {('%.3f' % r['p_holm']) if r.get('p_holm') is not None else '–'} |")
    L += ["", "All gains are vs the starting version, averaged over tasks, with 95% bootstrap CIs over tasks. *seen by loop* = "
              "the runs the loop used to accept the version (falls back to the step vs parent). *re-run* = fresh runs on the same "
              "tasks. *detectable* = smallest true change (in ground-truth units when available) these tasks would reveal ~80% of the time. *p* = test of the most "
              "decisive available comparison (held-out truth > held-out score > re-run > step), adjusted for the number of "
              "accepted versions. *expected on new tasks* = the loop's own number corrected for having picked winners "
              "(empirical Bayes over ALL candidates in the log, kept or not; needs no re-runs). In our validation it removes "
              "most of the average over-claim but each single estimate stays noisy; with very few selection tasks it "
              "shrinks every candidate to the average, which means: these tasks cannot tell the candidates apart.", ""]
    dec = [(v, r["decomposition"]) for v, r in show.items() if r.get("decomposition") and any(x is not None for x in r["decomposition"].values())]
    if dec:
        L += ["## Where the claimed gain went", "", "| version | luck (seen − re-run) | fitting selection tasks (re-run − held-out) | survives on held-out |", "|---|---|---|---|"]
        g = lambda x: "–" if x is None else f"{x:+.3f}"
        for v, d in dec:
            L.append(f"| `{v}` | {g(d['luck (seen - re-run)'])} | {g(d['fitting selection tasks (re-run - held-out)'])} | {g(d['survives on held-out'])} |")
        L.append("")
    pt = rep.get("proxy_truth")
    if pt:
        s = f"**Score vs ground truth.** Record-level correlation r = {pt['r_record_level']:+.2f} (n = {pt['n']})."
        if pt.get("versions_compared"):
            s += f" Held-out gains point the same direction for {pt['versions_same_direction']} of {pt['versions_compared']} versions."
        L += [s, ""]
    b = rep.get("best_overall")
    if b:
        L += [f"**Best version.** `{b['best']}` beats the average of {b['k']} versions by {b['observed_best_minus_mean']:+.3f}; "
              f"if all were equally good, picking the best would give {b['chance_best_minus_mean']:+.3f} by chance "
              f"(p = {b['p_value']:.2f}, {b['n_tasks']} shared selection tasks).", ""]
    ga = rep["grader_access"]
    if ga["runs"]:
        s = f"**Grader access.** {ga['runs']} runs in {len(ga['versions'])} versions touched grader files."
        if ga["mean_score_gain_when_accessed"] is not None:
            s += f" On the same task, those runs scored {ga['mean_score_gain_when_accessed']:+.3f} higher than honest runs of the same version."
        L += [s, ""]
    return "\n".join(L)
