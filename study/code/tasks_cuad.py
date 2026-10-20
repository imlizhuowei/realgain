"""Scenario D on REAL contracts: CUAD (510 commercial contracts from SEC filings, labelled by lawyers).

Task: contract intake review for the General Counsel. For each of ten risk-relevant
provisions, say whether the contract contains it. Gold = the CUAD expert labels
(a category is present if lawyers highlighted at least one span for it).
"""
import json, os, random, re

CUAD = os.environ.get("CUAD_JSON", "data/CUADv1.json")
CATS = ["Uncapped Liability", "Cap On Liability", "Change Of Control", "Anti-Assignment", "Non-Compete",
        "Exclusivity", "Termination For Convenience", "Most Favored Nation", "Liquidated Damages", "Audit Rights"]
KEYNAME = {c: re.sub(r"[^a-z]+", "_", c.lower()).strip("_") for c in CATS}

_contracts = None


def contracts():
    global _contracts
    if _contracts is None:
        out = []
        for x in json.load(open(CUAD))["data"]:
            p = x["paragraphs"][0]; text = p["context"]
            n = len(text.split())
            if not (1500 <= n <= 9000): continue
            labels = {}
            for q in p["qas"]:
                cat = q["question"].split('"')[1]
                if cat in CATS: labels[cat] = len(q["answers"]) > 0
            if len(labels) == len(CATS): out.append((x["title"], text, labels))
        out.sort(key=lambda t: t[0])
        _contracts = out
    return _contracts


SPEC = """You are in-house counsel doing intake review of a signed commercial contract (`contract.txt`) that our
company has just acquired through an acquisition. Write `review.md` (at most 400 words) for the General Counsel:
the main obligations and risks for us, anything unusual, and what to monitor.

Then, for each provision below, state whether the contract contains it. End the review with exactly these lines,
each filled in with yes or no:
""" + "\n".join(f"KEY {KEYNAME[c]} = <yes or no>" for c in CATS) + """

Meanings: uncapped_liability = a party's liability is uncapped or a carve-out from the cap; cap_on_liability = a cap
or limit on liability or damages; change_of_control = rights triggered by a change of control, merger or sale;
anti_assignment = assignment requires consent or notice; non_compete = restriction on competing; exclusivity =
exclusive dealing or exclusivity commitment; termination_for_convenience = a party may terminate without cause;
most_favored_nation = most-favoured terms or pricing; liquidated_damages = pre-set damages or termination fees;
audit_rights = a right to audit books, records or premises.
"""


def make_task(i):
    title, text, labels = contracts()[i % len(contracts())]
    return {"id": f"cuad-{i:03d}", "family": "cuad", "instruction": SPEC, "inputs": {"contract.txt": text},
            "gold": {KEYNAME[c]: ("yes" if labels[c] else "no") for c in CATS}, "meta": {"title": title}}


def parse_keys(text):
    return {m.group(1): m.group(2).strip().strip("`*.").lower() for m in re.finditer(r"^\s*KEY\s+(\w+)\s*=\s*(.+?)\s*$", text, re.M)}


def gold_score(task, text):
    k = parse_keys(text); det = {f: k.get(f) == v for f, v in task["gold"].items()}
    return sum(det.values()) / len(det), det


if __name__ == "__main__":
    from collections import Counter
    cs = contracts(); print("usable contracts", len(cs))
    prev = Counter()
    for _, _, l in cs:
        for c, v in l.items(): prev[c] += v
    print({c: round(prev[c] / len(cs), 2) for c in CATS})
    t = make_task(0); print(t["meta"], t["gold"])
    assert gold_score(t, "\n".join(f"KEY {k} = {v}" for k, v in t["gold"].items()))[0] == 1
