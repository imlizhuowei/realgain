"""Scenario A on REAL data: Online Retail II (a UK gift wholesaler/retailer, Dec 2009 - Dec 2011).

Each task is a year-over-year review of one period for one business scope, written
for the Commercial Director. The data are the raw transactions with all their real
problems: cancellations, non-product lines (postage, fees, manual adjustments,
vouchers), missing customer ids, and a final month that stops on 9 Dec 2011.

The data dictionary states the KPI definition but, like most real ones, does not
list every non-product code. Gold values follow the definition below.
"""
import io, os, re
import pandas as pd

DATA = os.environ.get("RETAIL_PKL", "data/online_retail2.pkl")
NON_PRODUCT = {"POST", "DOT", "M", "m", "C2", "D", "S", "BANK CHARGES", "ADJUST", "ADJUST2", "AMAZONFEE",
               "PADS", "CRUK", "B", "TEST001", "TEST002"}
DATA_END = pd.Timestamp("2011-12-09 23:59:59")

WINDOWS = [  # (label, current period start, end) ; prior period = same dates one year earlier
    ("Q4 2011", "2011-10-01", "2011-12-31"), ("December 2011", "2011-12-01", "2011-12-31"),
    ("H1 2011", "2011-01-01", "2011-06-30"), ("Q1 2011", "2011-01-01", "2011-03-31"),
    ("Q2 2011", "2011-04-01", "2011-06-30"), ("Q3 2011", "2011-07-01", "2011-09-30"),
    ("September-November 2011", "2011-09-01", "2011-11-30"), ("November 2011", "2011-11-01", "2011-11-30"),
    ("October 2011", "2011-10-01", "2011-10-31"), ("2011 year to date", "2011-01-01", "2011-12-31"),
]
SCOPES = [("the whole business", None), ("international (non-UK) customers", "nonuk"),
          ("UK customers", "uk"), ("Christmas products (description contains CHRISTMAS)", "xmas"),
          ("bags (description contains BAG)", "bag")]

_df = None


def data():
    global _df
    if _df is None:
        d = pd.read_pickle(DATA)
        d["Revenue"] = d["Quantity"] * d["Price"]
        _df = d
    return _df


def _scope(d, s):
    if s == "nonuk": return d[d.Country != "United Kingdom"]
    if s == "uk": return d[d.Country == "United Kingdom"]
    if s == "xmas": return d[d.Description.fillna("").str.upper().str.contains("CHRISTMAS")]
    if s == "bag": return d[d.Description.fillna("").str.upper().str.contains("BAG")]
    return d


def _product(d):
    return d[~d.StockCode.isin(NON_PRODUCT) & ~d.StockCode.str.startswith("gift_")]


def reference(win, scope):
    label, a, b = win
    a, b = pd.Timestamp(a), pd.Timestamp(b) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    pa, pb = a - pd.DateOffset(years=1), b - pd.DateOffset(years=1)
    d = _product(_scope(data(), scope))
    cur = d[(d.InvoiceDate >= a) & (d.InvoiceDate <= b)]; pri = d[(d.InvoiceDate >= pa) & (d.InvoiceDate <= pb)]
    r1, r2 = pri.Revenue.sum(), cur.Revenue.sum()
    partial = b > DATA_END
    # like-for-like: truncate both periods at the last date with data in the current one
    end_c = min(b, DATA_END); end_p = end_c - pd.DateOffset(years=1)
    cur_l = cur[cur.InvoiceDate <= end_c]; pri_l = pri[pri.InvoiceDate <= end_p]
    l1, l2 = pri_l.Revenue.sum(), cur_l.Revenue.sum()
    ch = (cur_l.groupby("Country").Revenue.sum().sub(pri_l.groupby("Country").Revenue.sum(), fill_value=0))
    top_country = ch.abs().idxmax()
    c_p = set(pri_l.CustomerID.dropna()); c_c = set(cur_l.CustomerID.dropna())
    lost = pri_l[pri_l.CustomerID.isin(c_p - c_c)].Revenue.sum()
    unid = cur_l[cur_l.CustomerID.isna()].Revenue.sum() / l2 * 100 if l2 else 0
    return {"revenue_prior": round(r1, 2), "revenue_current": round(r2, 2),
            "periods_comparable": "no" if partial else "yes",
            "like_for_like_change_pct": round((l2 - l1) / l1 * 100, 1),
            "top_country_by_change": top_country, "lost_customer_revenue": round(lost, 2),
            "unidentified_share_pct": round(unid, 1)}, (pa, end_c)


SPEC = """You are an analyst at an online gift wholesaler. The Commercial Director wants a year-over-year review of
{label} for {scope}, compared with the same dates one year earlier.

`transactions.csv` is the raw export of every invoice line (columns: Invoice, StockCode, Description, Quantity,
InvoiceDate, Price, CustomerID, Country). `data_dictionary.md` explains the fields and the revenue KPI.

Write `memo.md` (at most 400 words) for the Commercial Director: how the period went, what drove the change, any
data problems that affect the comparison, and three recommendations.

End the memo with exactly these lines, filled in (plain numbers, no currency symbols or thousands separators):
KEY revenue_prior = <KPI revenue in the prior-year period, 2 decimals>
KEY revenue_current = <KPI revenue in the current period, 2 decimals>
KEY periods_comparable = <yes or no: does the data cover both periods in full?>
KEY like_for_like_change_pct = <percent change on a like-for-like basis (same calendar days with data in both years), 1 decimal>
KEY top_country_by_change = <country with the largest absolute like-for-like revenue change>
KEY lost_customer_revenue = <like-for-like prior-period revenue from identified customers who bought nothing in the current period, 2 decimals>
KEY unidentified_share_pct = <share of like-for-like current-period revenue with no CustomerID, percent, 1 decimal>
"""

DICTIONARY = """# Data dictionary (sales export)

- Invoice: invoice number. Numbers starting with "C" are cancellations; their quantities are negative.
- StockCode: product code. Some codes are not products: postage and carriage, bank charges, marketplace fees,
  manual adjustments, discounts, samples, commissions, test lines, gift vouchers and similar bookkeeping lines.
- Quantity, Price: units and unit price in GBP. Line value = Quantity * Price.
- CustomerID: may be empty (guest checkouts and some phone orders).
- InvoiceDate: date and time of the invoice.

Revenue KPI: the sum of line values over PRODUCT lines only, with cancellations included (they reduce revenue).
Non-product lines are excluded.
"""


def make_task(i):
    win = WINDOWS[i % len(WINDOWS)]; scope = SCOPES[(i // len(WINDOWS)) % len(SCOPES)]
    gold, (lo, hi) = reference(win, scope[1])
    label, a, b = win
    a = pd.Timestamp(a); b = pd.Timestamp(b) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    d = data()
    sub = d[((d.InvoiceDate >= a - pd.DateOffset(years=1)) & (d.InvoiceDate <= b - pd.DateOffset(years=1))) |
            ((d.InvoiceDate >= a) & (d.InvoiceDate <= b))]
    sub = _scope(sub, scope[1]).drop(columns=["Revenue"])
    if scope[1] in ("xmas", "bag"):  # keep the non-product lines of the same invoices so the filtering problem remains
        extra = d[d.Invoice.isin(sub.Invoice) & (d.StockCode.isin(NON_PRODUCT) | d.StockCode.str.startswith("gift_"))]
        sub = pd.concat([sub, extra.drop(columns=["Revenue"])]).drop_duplicates()
    buf = io.StringIO(); sub.sort_values("InvoiceDate").to_csv(buf, index=False)
    return {"id": f"retail-{i:03d}", "family": "retail", "instruction": SPEC.format(label=label, scope=scope[0]),
            "inputs": {"transactions.csv": buf.getvalue(), "data_dictionary.md": DICTIONARY},
            "gold": gold, "meta": {"window": label, "scope": scope[0]}}


def parse_keys(text):
    return {m.group(1): m.group(2).strip().strip("`*").strip()
            for m in re.finditer(r"^\s*KEY\s+(\w+)\s*=\s*(.+?)\s*$", text, re.M)}


def gold_score(task, text):
    g, k = task["gold"], parse_keys(text)
    det = {}
    for f, v in g.items():
        got = k.get(f)
        if got is None: det[f] = False; continue
        if isinstance(v, float):
            try:
                x = float(got.replace(",", "").replace("%", "").replace("£", ""))
                tol = 0.25 if f.endswith("pct") else max(0.005 * abs(v), 1.0)
                det[f] = abs(x - v) <= tol
            except ValueError:
                det[f] = False
        else:
            det[f] = got.lower().strip(".") == str(v).lower()
    return sum(det.values()) / len(det), det


if __name__ == "__main__":
    import time
    t0 = time.time()
    for i in [0, 1, 2, 11, 33]:
        t = make_task(i)
        print(t["id"], t["meta"], len(t["inputs"]["transactions.csv"]) // 1_000_000, "MB", t["gold"])
        assert gold_score(t, "\n".join(f"KEY {k} = {v}" for k, v in t["gold"].items()))[0] == 1
    print(round(time.time() - t0, 1), "s")
