"""Generator for small data-processing tasks.

Each task gives one or two CSV files and a written spec. The agent must write
`output.csv`. A reference implementation produces the expected output, which is
kept hidden. A small worked example (different data, same spec) is visible.
Score = fraction of expected rows reproduced exactly, with a penalty for extra rows.
"""
import csv
import io
import random
from collections import defaultdict
from datetime import date, timedelta

REGIONS = ["north", "south", "east", "west"]
PRODUCTS = ["apple", "bolt", "cable", "drum", "easel"]


def _orders(r, n):
    rows, d0 = [], date(2026, 1, 1)
    for i in range(n):
        d = d0 + timedelta(days=r.randint(0, 120))
        fmt = r.choice(["%Y-%m-%d", "%d/%m/%Y", "%Y.%m.%d"])
        rows.append({"order_id": f"O{1000 + i}", "customer": f"C{r.randint(1, 8)}",
                     "region": r.choice(REGIONS) if r.random() > 0.08 else r.choice(REGIONS).upper(),
                     "product": r.choice(PRODUCTS), "date": d.strftime(fmt),
                     "qty": str(r.randint(0, 12)), "price": f"{r.uniform(1, 40):.2f}"})
    return rows


def _parse_date(s):
    for sep in "-/.":
        if sep in s:
            a, b, c = s.split(sep)
            return date(int(c), int(b), int(a)) if sep == "/" else date(int(a), int(b), int(c))


def _csv(rows, cols):
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader(); [w.writerow({c: row[c] for c in cols}) for row in rows]
    return buf.getvalue()


def d_filter(r):
    regs = sorted(r.sample(REGIONS, 2)); t = r.randint(3, 7); key = r.choice(["order_id", "qty"])
    spec = (f"From orders.csv keep rows whose region is one of {regs} (compare case-insensitively) and whose qty "
            f">= {t}. Write output.csv with columns order_id,region,qty where region is lower case. Sort by "
            + ("order_id ascending." if key == "order_id" else "qty descending, then order_id ascending."))
    def ref(files):
        rows = [x for x in files["orders"] if x["region"].lower() in regs and int(x["qty"]) >= t]
        out = [{"order_id": x["order_id"], "region": x["region"].lower(), "qty": x["qty"]} for x in rows]
        out.sort(key=(lambda x: x["order_id"]) if key == "order_id" else (lambda x: (-int(x["qty"]), x["order_id"])))
        return out, ["order_id", "region", "qty"]
    return spec, ref


def d_groupby(r):
    by = r.choice(["region", "product", "customer"]); dp = r.choice([0, 2])
    spec = (f"From orders.csv compute revenue = qty * price for each row, then total revenue per {by} "
            f"({'lower-case the region first' if by == 'region' else 'as written'}). Write output.csv with columns "
            f"{by},revenue, revenue formatted with exactly {dp} decimal places (Python f'{{x:.{dp}f}}'), "
            f"sorted by revenue descending then {by} ascending. Skip groups whose total is 0.")
    def ref(files):
        tot = defaultdict(float)
        for x in files["orders"]:
            k = x[by].lower() if by == "region" else x[by]
            tot[k] += int(x["qty"]) * float(x["price"])
        items = sorted(((k, v) for k, v in tot.items() if round(v, 9) != 0), key=lambda kv: (-round(kv[1], 6), kv[0]))
        return [{by: k, "revenue": f"{v:.{dp}f}"} for k, v in items], [by, "revenue"]
    return spec, ref


def d_dates(r):
    month = r.randint(1, 4)
    spec = (f"Dates in orders.csv use three formats: YYYY-MM-DD, DD/MM/YYYY and YYYY.MM.DD. Keep only orders placed in "
            f"month {month} of 2026. Write output.csv with columns order_id,date where date is ISO YYYY-MM-DD, sorted by "
            f"date then order_id.")
    def ref(files):
        out = []
        for x in files["orders"]:
            d = _parse_date(x["date"])
            if d.year == 2026 and d.month == month:
                out.append({"order_id": x["order_id"], "date": d.isoformat()})
        out.sort(key=lambda x: (x["date"], x["order_id"]))
        return out, ["order_id", "date"]
    return spec, ref


def d_join(r):
    spec = ("customers.csv maps customer to tier. Join it with orders.csv on customer (orders whose customer is missing "
            "from customers.csv get tier 'unknown'). Write output.csv with columns tier,orders,units: number of orders and "
            "sum of qty per tier, sorted by tier ascending.")
    def ref(files):
        tier = {c["customer"]: c["tier"] for c in files["customers"]}
        agg = defaultdict(lambda: [0, 0])
        for x in files["orders"]:
            t = tier.get(x["customer"], "unknown"); agg[t][0] += 1; agg[t][1] += int(x["qty"])
        return [{"tier": t, "orders": str(a), "units": str(b)} for t, (a, b) in sorted(agg.items())], ["tier", "orders", "units"]
    return spec, ref


def d_latest(r):
    spec = ("For each customer in orders.csv keep only their most recent order (dates use YYYY-MM-DD, DD/MM/YYYY or "
            "YYYY.MM.DD; if two orders share the latest date keep the larger order_id). Write output.csv with columns "
            "customer,order_id,date (date as YYYY-MM-DD), sorted by customer.")
    def ref(files):
        best = {}
        for x in files["orders"]:
            k = (_parse_date(x["date"]), x["order_id"])
            if x["customer"] not in best or k > best[x["customer"]][0]:
                best[x["customer"]] = (k, x)
        return ([{"customer": c, "order_id": v[1]["order_id"], "date": v[0][0].isoformat()} for c, v in sorted(best.items())],
                ["customer", "order_id", "date"])
    return spec, ref


TEMPLATES = [d_filter, d_groupby, d_dates, d_join, d_latest]


def _files(r, n):
    files = {"orders": _orders(r, n)}
    custs = [f"C{i}" for i in range(1, 9)]
    files["customers"] = [{"customer": c, "tier": r.choice(["gold", "silver", "bronze"])} for c in custs if r.random() > 0.2]
    return files


def _render(files):
    return {"orders.csv": _csv(files["orders"], list(files["orders"][0])),
            "customers.csv": _csv(files["customers"], ["customer", "tier"])}


def make_task(seed: int):
    r = random.Random(10_000 + seed)
    tmpl = TEMPLATES[seed % len(TEMPLATES)]
    spec, ref = tmpl(r)
    ex_files = _files(r, 8); ex_out, cols = ref(ex_files)
    files = _files(r, r.randint(30, 50)); out, cols = ref(files)
    instruction = (f"{spec}\n\nThe input files are in the current directory. Write the result to `output.csv` "
                   f"(comma-separated, header row first).\n\nA worked example with different data is in `example/`: "
                   f"`example/orders.csv`, `example/customers.csv` and the correct `example/output.csv`.\n")
    return {"id": f"data-{seed:04d}", "family": "data", "template": tmpl.__name__, "instruction": instruction,
            "inputs": _render(files), "example": {**_render(ex_files), "output.csv": _csv(ex_out, cols)},
            "expected": _csv(out, cols)}


def score_output(expected_csv: str, got_csv: str) -> float:
    """Fraction of expected rows matched in order-insensitive multiset sense, minus extra rows; header must match.
    Row order is checked separately: full credit only if order also matches."""
    exp = list(csv.reader(io.StringIO(expected_csv.strip())))
    try:
        got = list(csv.reader(io.StringIO(got_csv.strip())))
    except Exception:
        return 0.0
    if not got or [h.strip() for h in got[0]] != exp[0]:
        return 0.0
    e_rows, g_rows = exp[1:], [[c.strip() for c in row] for row in got[1:]]
    if not e_rows:
        return 1.0 if not g_rows else 0.0
    if g_rows == e_rows:
        return 1.0
    pool = list(map(tuple, g_rows)); hit = 0
    for row in map(tuple, e_rows):
        if row in pool: pool.remove(row); hit += 1
    s = max(0.0, (hit - len(pool)) / len(e_rows))
    return round(0.9 * s, 4)   # right rows but wrong order (or partial) caps at 0.9
