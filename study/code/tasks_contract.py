"""Contract-review tasks (scenario D).

Each task is a synthetic services agreement that our company (the Customer) is
about to sign. A few clauses are replaced by versions that are unfavourable to the
Customer ("planted issues"); the rest are standard, balanced wording. The agent
writes `review.md` for the General Counsel and ends it with one ISSUE line per
problem it found. Gold = precision / recall against the planted clauses.
"""
import random, re

# each topic: (balanced clause, problematic clause, issue label)
TOPICS = {
    "liability": ("Each party's total liability under this Agreement is capped at the fees paid in the twelve months before the claim, except for breaches of confidentiality.",
                  "The Customer's liability under this Agreement is unlimited, while the Supplier's total liability is capped at the fees paid in the one month before the claim.",
                  "one-sided liability cap"),
    "renewal": ("This Agreement runs for twelve months and renews only if both parties agree in writing.",
                "This Agreement renews automatically for successive three-year terms unless the Customer gives notice at least 180 days before the end of the current term.",
                "aggressive auto-renewal"),
    "pricing": ("Fees are fixed for the initial term. Any later change requires a written amendment signed by both parties.",
                "The Supplier may increase fees at any time by notice to the Customer; continued use of the services after notice is acceptance of the new fees.",
                "unilateral price increase"),
    "ip": ("Each party keeps its pre-existing intellectual property. Deliverables created specifically for the Customer belong to the Customer once paid for.",
           "All intellectual property created or used in connection with the services, including the Customer's pre-existing materials provided to the Supplier, is assigned to the Supplier.",
           "IP grab"),
    "termination": ("Either party may terminate for convenience on 60 days' written notice.",
                    "The Supplier may terminate for convenience on 7 days' notice. The Customer may terminate only for the Supplier's uncured material breach.",
                    "asymmetric termination"),
    "payment": ("Invoices are payable within 30 days of receipt. Disputed amounts may be withheld in good faith while the dispute is resolved.",
                "Invoices are payable within 5 days of issue, disputed or not. Late amounts carry interest of 4% per month and the Supplier may suspend services immediately.",
                "harsh payment terms"),
    "indemnity": ("Each party indemnifies the other against third-party claims caused by its own negligence or breach.",
                  "The Customer indemnifies the Supplier against all claims of any kind arising from the services, including claims caused by the Supplier's own negligence.",
                  "one-sided indemnity"),
    "data": ("The Supplier processes Customer data only to provide the services and deletes it within 30 days after termination.",
             "The Supplier may use Customer data, including personal data, for any purpose, including training its products and sharing with affiliates, and may keep it indefinitely.",
             "unrestricted data use"),
    "governing_law": ("This Agreement is governed by the laws of the Customer's home jurisdiction, and disputes go to its courts.",
                      "This Agreement is governed by the laws of a jurisdiction chosen by the Supplier at the time of any dispute, and the Customer waives any right to a jury or class action.",
                      "supplier-chosen governing law"),
    "audit": ("The Customer may audit the Supplier's compliance once a year on 30 days' notice.",
              "The Customer has no right to audit or inspect the Supplier's compliance, security practices or subcontractors.",
              "no audit rights"),
    "sla": ("The Supplier guarantees 99.9% monthly availability; below that the Customer receives service credits of 10% of monthly fees per 0.1% shortfall.",
            "The Supplier will use reasonable efforts to keep the services available but gives no availability commitment and owes no credits or remedies for downtime.",
            "no service level commitment"),
    "assignment": ("Neither party may assign this Agreement without the other's written consent, which may not be unreasonably withheld.",
                   "The Supplier may assign or subcontract any part of this Agreement to anyone without notice; the Customer may not assign it at all.",
                   "one-sided assignment"),
}
FILLER = [
    "Notices must be in writing and are effective on delivery to the addresses in the order form.",
    "Each party shall comply with applicable anti-bribery and export control laws.",
    "Headings are for convenience only and do not affect interpretation.",
    "If any provision is held invalid, the remainder of this Agreement remains in effect.",
    "This Agreement, with its order forms, is the entire agreement between the parties on its subject.",
    "Neither party is liable for delays caused by events beyond its reasonable control.",
    "The parties are independent contractors; nothing here creates a partnership or agency.",
]
TITLES = {"liability": "Limitation of Liability", "renewal": "Term and Renewal", "pricing": "Fees", "ip": "Intellectual Property",
          "termination": "Termination", "payment": "Payment", "indemnity": "Indemnification", "data": "Data Protection",
          "governing_law": "Governing Law", "audit": "Audit", "sla": "Service Levels", "assignment": "Assignment"}

SPEC = """You are reviewing a supplier's services agreement before our company (the Customer) signs it.
The agreement is in `contract.md`. Write `review.md` for our General Counsel (at most 400 words): which clauses
are unfavourable or risky for the Customer and why, and what to ask the Supplier to change. Do not flag clauses
that are standard and balanced.

End the review with one line per problematic clause, exactly in this form (clause number as it appears in the contract):
ISSUE <clause number> | <short label of the problem>
If you find no problems, write: ISSUE none
"""


def make_task(seed):
    r = random.Random(500_000 + seed)
    topics = r.sample(sorted(TOPICS), 9)
    bad = set(r.sample(topics, r.randint(2, 4)))
    clauses = [(TITLES[t], TOPICS[t][1] if t in bad else TOPICS[t][0], t) for t in topics]
    clauses += [("General", f, None) for f in r.sample(FILLER, 3)]
    r.shuffle(clauses)
    lines = [f"# Master Services Agreement\n\nBetween Northwind Analytics Ltd (\"Supplier\") and the Customer.\n"]
    gold = {}
    for i, (title, text, t) in enumerate(clauses, 1):
        lines.append(f"## {i}. {title}\n{text}\n")
        if t in bad: gold[i] = TOPICS[t][2]
    return {"id": f"contract-{seed:04d}", "family": "contract", "instruction": SPEC,
            "inputs": {"contract.md": "\n".join(lines)}, "gold": gold}


def parse_issues(text):
    found = set()
    for m in re.finditer(r"^\s*ISSUE\s+(\d+)\s*\|", text, re.M):
        found.add(int(m.group(1)))
    return found


def gold_score(task, review_text):
    """F1 of flagged clause numbers against planted ones (0 if nothing parseable)."""
    gold = set(task["gold"]); got = parse_issues(review_text)
    tp = len(gold & got)
    prec = tp / len(got) if got else 0.0; rec = tp / len(gold)
    f1 = 2 * prec * rec / (prec + rec) if tp else 0.0
    return f1, {"tp": tp, "fp": len(got - gold), "fn": len(gold - got)}


if __name__ == "__main__":
    t = make_task(0); print(t["inputs"]["contract.md"][:900]); print(t["gold"])
    fake = "\n".join(f"ISSUE {k} | x" for k in t["gold"]); assert gold_score(t, fake)[0] == 1.0
    print("ok")
