"""LLM judge for analysis reports: the 'proxy' score a self-improvement loop would optimise.

Like most judges used in practice, it sees the assignment and the report, not the
raw data, so it cannot recompute the numbers. It returns a 1-10 score and a short critique.
"""
import json, re, urllib.request, time
import solver

JUDGE_MODEL = "kimi-k2.6"
RUBRIC = """You are a demanding VP of Sales Operations reviewing an analyst's memo written for the Head of Sales.
Score the memo from 1 to 10 for how useful and trustworthy it is to the Head of Sales, considering:
- does it answer the assignment (Q2 vs Q1, biggest declining region, why, recommendations)?
- is the diagnosis of the cause specific and well supported by evidence from the data?
- are the recommendations concrete and actionable?
- is it clear, concise and professional?
You do NOT have the raw data. Judge from the memo itself.
Reply with JSON only: {"score": <integer 1-10>, "critique": "<two or three sentences>"}"""


RUBRIC_CONTRACT = """You are a demanding General Counsel reviewing a lawyer's contract review memo, written before the company signs a supplier agreement.
Score the memo from 1 to 10 for how useful and trustworthy it is to you, considering:
- does it identify the clauses that are genuinely risky for the company, without crying wolf over standard ones?
- is each risk explained clearly, with the practical consequence?
- are the requested changes concrete and realistic to negotiate?
- is it clear, concise and professional?
You do NOT have the contract. Judge from the memo itself.
Reply with JSON only: {"score": <integer 1-10>, "critique": "<two or three sentences>"}"""


RUBRIC_RETAIL = RUBRIC.replace("VP of Sales Operations", "Commercial Director").replace(
    "(Q2 vs Q1, biggest declining region, why, recommendations)", "(year-over-year performance, drivers, data problems, recommendations)")


RUBRIC_CUAD = """You are a demanding General Counsel reading an intake review of a contract the company just acquired.
Score the review from 1 to 10 for how useful and trustworthy it is to you, considering:
- does it correctly identify the obligations, risks and notable provisions that matter to the company?
- is it specific (sections, parties, numbers) rather than generic?
- does it say clearly what to monitor or act on?
- is it clear, concise and professional?
You do NOT have the contract. Judge from the review itself.
Reply with JSON only: {"score": <integer 1-10>, "critique": "<two or three sentences>"}"""


def judge(assignment, report, max_tokens=8000, family="report", model=None):
    msgs = [{"role": "system", "content": {"contract": RUBRIC_CONTRACT, "cuad": RUBRIC_CUAD, "retail": RUBRIC_RETAIL}.get(family, RUBRIC)},
            {"role": "user", "content": f"ASSIGNMENT:\n{assignment}\n\nMEMO:\n{report or '(empty)'}"}]
    body = json.dumps({"model": model or JUDGE_MODEL, "messages": msgs, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(solver.ENV["MOONSHOT_BASE_URL"] + "/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + solver.ENV["MOONSHOT_API_KEY"],
                                          "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            txt = d["choices"][0]["message"].get("content") or ""
            m = re.search(r"\{.*\}", txt, re.S)
            out = json.loads(m.group(0))
            u = d.get("usage", {})
            return {"score": float(out["score"]), "critique": out.get("critique", ""),
                    "usage": {"prompt": u.get("prompt_tokens", 0), "completion": u.get("completion_tokens", 0)}}
        except Exception as e:
            if attempt == 3: return {"score": None, "critique": f"judge error: {e}", "usage": {}}
            time.sleep(3)


PAIR_PROMPT = """You are the {role} described below. Two analysts answered the same assignment. Decide which answer
would be more useful and trustworthy for you. You do NOT have the underlying data or document.
Reply with JSON only: {{"winner": "A" or "B" or "tie", "reason": "<one or two sentences>"}}"""
ROLES = {"retail": "Commercial Director of an online gift wholesaler", "cuad": "General Counsel",
         "report": "Head of Sales", "contract": "General Counsel"}


def judge_pair(assignment, memo_new, memo_old, family, rng):
    """Returns +1 if memo_new wins, -1 if memo_old wins, 0 for a tie (order randomised)."""
    flip = rng.random() < 0.5
    a, b = (memo_old, memo_new) if flip else (memo_new, memo_old)
    msgs = [{"role": "system", "content": PAIR_PROMPT.format(role=ROLES.get(family, "manager"))},
            {"role": "user", "content": f"ASSIGNMENT:\n{assignment}\n\nANSWER A:\n{a or '(empty)'}\n\nANSWER B:\n{b or '(empty)'}"}]
    body = json.dumps({"model": JUDGE_MODEL, "messages": msgs, "max_tokens": 8000}).encode()
    req = urllib.request.Request(solver.ENV["MOONSHOT_BASE_URL"] + "/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + solver.ENV["MOONSHOT_API_KEY"],
                                          "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            out = json.loads(re.search(r"\{.*\}", d["choices"][0]["message"].get("content") or "", re.S).group(0))
            w = out["winner"].strip().upper()
            u = d.get("usage", {})
            res = 0 if w == "TIE" else ((1 if w == "A" else -1) * (-1 if flip else 1))
            return res, out.get("reason", ""), {"prompt": u.get("prompt_tokens", 0), "completion": u.get("completion_tokens", 0)}
        except Exception as e:
            if attempt == 3: return 0, f"judge error: {e}", {}
            time.sleep(3)
