"""Business-analysis report tasks (scenario A).

Each task: half a year of messy sales data for one company, with ONE planted
event (a stockout, a returns spike, or a price cut in one region/product during
Q2). The agent writes `report.md` for the head of sales and ends it with a block
of KEY lines in a fixed format.

Gold (true quality, never shown to the judge or the loop):
  - the KEY numbers and labels, computed from the data by the reference code;
  - whether the planted cause was found.
Proxy (what a loop optimises): an LLM judge's score of the whole report.
"""
import csv, io, random, re
from collections import defaultdict
from datetime import date

REGIONS = ["north", "south", "east", "west", "central"]
PRODUCTS = ["alpha", "bravo", "cobalt", "delta", "ember", "flint"]
EVENTS = ["volume", "returns", "price"]


def _fmt_date(r, d):
    return d.strftime(r.choice(["%Y-%m-%d", "%d/%m/%Y", "%Y.%m.%d"]))


def _fmt_price(r, p):
    k = r.random()
    return f"${p:,.2f}" if k < 0.15 else (f"USD {p:.2f}" if k < 0.25 else f"{p:.2f}")


def _parse_date(s):
    for sep in "-/.":
        if sep in s:
            a, b, c = s.split(sep)
            return date(int(c), int(b), int(a)) if sep == "/" else date(int(a), int(b), int(c))


def _parse_price(s):
    return float(s.replace("USD", "").replace("$", "").replace(",", "").strip())


def generate(seed):
    r = random.Random(900_000 + seed)
    event = EVENTS[(seed // 100) % 3]
    er, ep = r.choice(REGIONS), r.choice(PRODUCTS)
    base_price = {p: r.uniform(8, 60) for p in PRODUCTS}
    growth = {g: r.uniform(-0.04, 0.10) for g in REGIONS}      # mild organic trend per region
    rows, oid = [], 10000
    for m in range(1, 7):
        for g in REGIONS:
            for p in PRODUCTS:
                n = max(0, int(r.gauss(9, 2) * (1 + growth[g]) ** (m - 1)))
                q2, hit = m >= 4, (g == er and p == ep)
                if q2 and hit and event == "volume": n = r.randint(0, 1)
                for _ in range(n):
                    qty = r.randint(1, 10); price = base_price[p] * r.uniform(0.95, 1.05)
                    if q2 and hit and event == "price": price *= 0.5
                    ret = 0
                    if r.random() < 0.04: ret = r.randint(1, qty)
                    if q2 and hit and event == "returns" and r.random() < 0.7: ret = qty if r.random() < 0.6 else r.randint(1, qty)
                    oid += 1
                    rows.append({"order_id": f"S{oid}", "date": _fmt_date(r, date(2026, m, r.randint(1, 28))),
                                 "region": g.upper() if r.random() < 0.1 else g, "product": p, "qty": str(qty),
                                 "unit_price": _fmt_price(r, round(price, 2)), "returned_qty": str(ret)})
    rows += [dict(x) for x in r.sample(rows, len(rows) // 20)]      # exact duplicate rows
    r.shuffle(rows)
    return rows, {"event": event, "region": er, "product": ep}


def reference(rows):
    seen, clean = set(), []
    for x in rows:
        if x["order_id"] in seen: continue
        seen.add(x["order_id"])
        d = _parse_date(x["date"]); price = _parse_price(x["unit_price"])
        clean.append((d.month, x["region"].lower(), x["product"], int(x["qty"]), price, int(x["returned_qty"])))
    net = lambda rows_: sum((q - rt) * pr for _, _, _, q, pr, rt in rows_)
    q1 = [c for c in clean if c[0] <= 3]; q2 = [c for c in clean if c[0] >= 4]
    n1, n2 = net(q1), net(q2)
    drop = {g: net([c for c in q2 if c[1] == g]) - net([c for c in q1 if c[1] == g]) for g in REGIONS}
    reg = min(drop, key=drop.get)
    pdrop = {p: net([c for c in q2 if c[1] == reg and c[2] == p]) - net([c for c in q1 if c[1] == reg and c[2] == p]) for p in PRODUCTS}
    prod = min(pdrop, key=pdrop.get)
    rr = {}
    for p in PRODUCTS:
        sold = sum(c[3] for c in q2 if c[2] == p); ret = sum(c[5] for c in q2 if c[2] == p)
        rr[p] = ret / sold if sold else 0
    out_extra = {"region_change": round(drop[reg], 2)}
    return {**out_extra, "net_revenue_q1": round(n1, 2), "net_revenue_q2": round(n2, 2),
            "change_pct": round((n2 - n1) / n1 * 100, 1), "biggest_decline_region": reg,
            "driver_product": prod, "highest_return_rate_product": max(rr, key=rr.get)}


SPEC = """You are preparing a short analysis memo for the Head of Sales.

Data: `sales.csv` holds every order from January to June 2026 (columns: order_id, date, region, product, qty,
unit_price, returned_qty). The export is messy: dates use YYYY-MM-DD, DD/MM/YYYY or YYYY.MM.DD; unit_price may
look like `12.50`, `$1,234.50` or `USD 12.50`; region names may be upper case; some rows are exact duplicates of
another row with the same order_id (count each order_id once).

Definitions: net revenue = sum over orders of (qty - returned_qty) * unit_price. Q1 = January-March, Q2 = April-June.

Write `report.md` (at most 400 words) that tells the Head of Sales how Q2 compared with Q1, which region declined
the most and WHY (what happened, in which product, and whether it was a volume, returns or pricing problem), and
three concrete recommendations.

End the report with exactly these lines, filled in (numbers without currency symbols or thousands separators):
KEY net_revenue_q1 = <number, 2 decimals>
KEY net_revenue_q2 = <number, 2 decimals>
KEY change_pct = <percent change from Q1 to Q2, 1 decimal>
KEY biggest_decline_region = <region with the largest drop in net revenue, lower case>
KEY driver_product = <product with the largest net revenue drop inside that region>
KEY driver_cause = <one of: volume (far fewer units sold), returns (many units returned), price (lower unit prices)>
KEY highest_return_rate_product = <product with the highest Q2 returned_qty / qty across all regions>
"""


def make_task(seed):
    for k in range(50):                       # regenerate until the planted event is the true biggest driver
        rows, planted = generate(seed * 100 + k)
        planted["event"] = EVENTS[seed % 3]
        g0 = reference(rows)
        if (g0["biggest_decline_region"] == planted["region"] and g0["driver_product"] == planted["product"]
                and g0["region_change"] < 0):
            break
    else:
        raise RuntimeError("could not plant event")
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader(); [w.writerow(x) for x in rows]
    gold = reference(rows); gold.pop("region_change"); gold["driver_cause"] = planted["event"]
    return {"id": f"report-{seed:04d}", "family": "report", "instruction": SPEC, "inputs": {"sales.csv": buf.getvalue()},
            "gold": gold, "planted": planted}


def parse_keys(text):
    keys = {}
    for m in re.finditer(r"^\s*KEY\s+(\w+)\s*=\s*(.+?)\s*$", text, re.M):
        keys[m.group(1)] = m.group(2).strip().strip("`*").strip()
    return keys


def gold_score(task, report_text):
    """Fraction of the 7 KEY facts that are correct, plus per-field detail."""
    g, k = task["gold"], parse_keys(report_text)
    detail = {}
    for f, v in g.items():
        got = k.get(f)
        if got is None: detail[f] = False; continue
        if isinstance(v, float):
            try:
                x = float(got.replace(",", "").replace("%", "").replace("$", ""))
                tol = 0.15 if f == "change_pct" else max(0.005 * abs(v), 0.01)
                detail[f] = abs(x - v) <= tol
            except ValueError:
                detail[f] = False
        else:
            detail[f] = got.lower().strip(".") == str(v).lower()
    return sum(detail.values()) / len(detail), detail


if __name__ == "__main__":
    from collections import Counter
    c = Counter()
    for s in range(30):
        t = make_task(s)
        ok = (t["gold"]["biggest_decline_region"] == t["planted"]["region"] and t["gold"]["driver_product"] == t["planted"]["product"])
        c[(t["planted"]["event"], ok)] += 1
        fake = "\n".join(f"KEY {k} = {v}" for k, v in t["gold"].items())
        assert gold_score(t, fake)[0] == 1.0
    print(c); print(make_task(0)["gold"], len(make_task(0)["inputs"]["sales.csv"].splitlines()))
