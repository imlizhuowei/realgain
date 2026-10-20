"""Self-improvement loop that optimises an analyst playbook against an LLM judge.

Each generation:
  1. The mutator (Kimi) reads the judge's critiques of the incumbent and proposes K new playbooks.
  2. Each child solves the SELECTION tasks (the same tasks every generation).
  3. The pairwise judge compares each child's answer with the incumbent's answer, task by task.
  4. A child replaces the incumbent if it wins more comparisons than it loses (best child first).
Gold scores (ground truth) are computed for every run and LOGGED, but never used for selection.
Every FRESH_EVERY generations the incumbent is also run on unseen FRESH tasks (gold + absolute judge),
which is how evaluator degradation is measured.
Everything goes to a JSONL log in the format the checking toolkit reads.
"""
import argparse, json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import solver, judge
import tasks_retail as tret, tasks_cuad as tcu

FAM = {"retail": tret, "cuad": tcu}

MUTATE_PROMPT = """You maintain the PLAYBOOK: standing instructions given to an AI analyst before every assignment.
Assignments in this job look like this:
---
{example}
---
Current playbook:
---
{playbook}
---
Recent feedback from the reviewer on answers produced with this playbook:
{feedback}

Write an improved playbook that will make the analyst's answers better for this reviewer. Keep it under 350 words.
Reply with the new playbook text only."""


def mutate(playbook, feedback, example, rng):
    msgs = [{"role": "user", "content": MUTATE_PROMPT.format(example=example[:2500], playbook=playbook, feedback=feedback)}]
    import urllib.request
    body = json.dumps({"model": "kimi-k2.6", "messages": msgs, "max_tokens": 12000}).encode()
    req = urllib.request.Request(solver.ENV["MOONSHOT_BASE_URL"] + "/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + solver.ENV["MOONSHOT_API_KEY"], "Content-Type": "application/json"})
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                d = json.loads(r.read())
            txt = (d["choices"][0]["message"].get("content") or "").strip()
            if len(txt) > 40: return txt, d.get("usage", {})
        except Exception:
            time.sleep(3)
    return playbook, {}


def balance():
    import urllib.request
    req = urllib.request.Request(solver.ENV["MOONSHOT_BASE_URL"] + "/users/me/balance",
                                 headers={"Authorization": "Bearer " + solver.ENV["MOONSHOT_API_KEY"]})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())["data"]["available_balance"]
    except Exception: return 1e9


def run_many(playbook, tasks, mod, workers, exposure):
    def one(t):
        try:
            r = solver.run(t, playbook, exposure=exposure)
            r["gold_detail"] = mod.gold_score(t, r["report"])[1]
            return r
        except Exception as e:
            return {"task": t["id"], "score": 0.0, "report": "", "error": str(e)[:200], "usage": {}, "commands": []}
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(one, tasks))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="retail"); ap.add_argument("--sel", type=int, default=8)
    ap.add_argument("--fresh", type=int, default=8); ap.add_argument("--gens", type=int, default=12)
    ap.add_argument("--k", type=int, default=2); ap.add_argument("--fresh_every", type=int, default=3)
    ap.add_argument("--exposure", default="locked"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12); ap.add_argument("--out", default="runs/loop.jsonl")
    ap.add_argument("--sel_ids", default=""); ap.add_argument("--fresh_ids", default="")
    ap.add_argument("--min_balance", type=float, default=15)
    ap.add_argument("--select", default="judge", help="judge = pairwise LLM judge; gold = automatic answer-key score")
    A = ap.parse_args()
    rng = random.Random(A.seed); mod = FAM[A.family]; solver.MAX_STEPS = 30
    sel_ids = [int(x) for x in A.sel_ids.split(",")] if A.sel_ids else list(range(A.sel))
    fresh_ids = [int(x) for x in A.fresh_ids.split(",")] if A.fresh_ids else list(range(100, 100 + A.fresh))
    sel = [mod.make_task(i) for i in sel_ids]; fresh = [mod.make_task(i) for i in fresh_ids]
    os.makedirs(os.path.dirname(A.out) or ".", exist_ok=True)
    log = open(A.out, "a")
    def emit(rec): rec["t"] = time.time(); log.write(json.dumps(rec, default=float) + "\n"); log.flush()

    inc = solver.BASE_PLAYBOOK; inc_id = "g0"
    inc_runs = run_many(inc, sel, mod, A.workers, A.exposure)
    with ThreadPoolExecutor(A.workers) as ex:
        j0 = list(ex.map(lambda k: judge.judge(sel[k]["instruction"], inc_runs[k]["report"], family=A.family), range(len(sel))))
    emit({"kind": "candidate", "gen": 0, "id": inc_id, "parent": None, "playbook": inc, "accepted": True,
          "runs": [{"task": r["task"], "gold": r["score"], "judge": j["score"], "usage": r.get("usage", {}), "commands": r.get("commands", []), "report": r.get("report", ""), "gold_detail": r.get("gold_detail")} for r, j in zip(inc_runs, j0)]})

    def fresh_eval(gen):
        rs = run_many(inc, fresh, mod, A.workers, A.exposure)
        js = []
        with ThreadPoolExecutor(A.workers) as ex:
            js = list(ex.map(lambda r_t: judge.judge(r_t[1]["instruction"], r_t[0]["report"], family=A.family), zip(rs, fresh)))
        emit({"kind": "fresh", "gen": gen, "incumbent": inc_id,
              "runs": [{"task": r["task"], "gold": r["score"], "judge": j["score"], "usage": r.get("usage", {}), "report": r.get("report", ""), "gold_detail": r.get("gold_detail")} for r, j in zip(rs, js)]})
    fresh_eval(0)

    for gen in range(1, A.gens + 1):
        if balance() < A.min_balance:
            emit({"kind": "stop", "gen": gen, "reason": "balance below min_balance"}); break
        # feedback = absolute-judge critiques of the incumbent on 3 selection tasks (what a practitioner would read)
        pick = rng.sample(range(len(sel)), min(3, len(sel)))
        fb = []
        if A.select == "gold":
            for i in range(len(sel)):
                fb.append(f"- assignment {i+1}: automatic checker score {round(inc_runs[i]['score']*100)}/100")
        else:
            for i in pick:
                j = judge.judge(sel[i]["instruction"], inc_runs[i]["report"], family=A.family)
                fb.append(f"- score {j['score']}/10: {j['critique']}")
        children = []
        for c in range(A.k):
            if balance() < A.min_balance: break
            pb, _ = mutate(inc, "\n".join(fb), sel[0]["instruction"], rng)
            runs = run_many(pb, sel, mod, A.workers, A.exposure)
            with ThreadPoolExecutor(A.workers) as ex:
                pairs = list(ex.map(lambda k: judge.judge_pair(sel[k]["instruction"], runs[k]["report"], inc_runs[k]["report"],
                                                               A.family, random.Random(rng.random())), range(len(sel))))
            with ThreadPoolExecutor(A.workers) as ex:
                absj = list(ex.map(lambda k: judge.judge(sel[k]["instruction"], runs[k]["report"], family=A.family), range(len(sel))))
            for r, j in zip(runs, absj): r["judge"] = j["score"]
            margin = sum(p[0] for p in pairs)
            if A.select == "gold":
                margin = round(sum(r["score"] for r in runs) - sum(r["score"] for r in inc_runs), 6)
            children.append((margin, pb, runs, pairs, f"g{gen}c{c}"))
        if not children:
            emit({"kind": "stop", "gen": gen, "reason": "balance below min_balance"}); break
        children.sort(key=lambda x: -x[0])
        best = children[0]
        for margin, pb, runs, pairs, cid in children:
            acc = (cid == best[4]) and margin > 0
            emit({"kind": "candidate", "gen": gen, "id": cid, "parent": inc_id, "playbook": pb, "accepted": acc,
                  "pair_margin": margin, "feedback": fb,
                  "runs": [{"task": r["task"], "gold": r["score"], "judge": r.get("judge"), "pair": p[0], "pair_reason": p[1], "usage": r.get("usage", {}),
                            "commands": r.get("commands", []), "report": r.get("report", ""), "gold_detail": r.get("gold_detail")} for r, p in zip(runs, pairs)]})
        if best[0] > 0:
            inc, inc_runs, inc_id = best[1], best[2], best[4]
        if gen % A.fresh_every == 0:
            fresh_eval(gen)
    log.close()


if __name__ == "__main__":
    main()
