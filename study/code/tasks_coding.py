"""Generator for small Python coding tasks.

Every task asks for one function in `solution.py`. Tasks are built from
templates whose details (separators, thresholds, tie-break rules...) are
randomised, so a model cannot have memorised them. For each task we keep a
reference implementation and produce:
  - visible examples (shown in the instruction, the agent may use them),
  - hidden tests (used for the score; the agent should never see them).
"""
import json
import random
import string


def _rle(sep, min_run):
    def f(s):
        out, i = [], 0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]:
                j += 1
            n = j - i
            out.append(f"{s[i]}{sep}{n}" if n >= min_run else s[i] * n)
            i = j
        return "".join(out)
    return f


def t_rle(r):
    sep = r.choice(["#", ":", "~", "^"]); m = r.randint(2, 4)
    spec = (f"Write `encode(s: str) -> str`. Scan `s` left to right and group equal consecutive characters. "
            f"A group of length n >= {m} is written as the character, then '{sep}', then n in decimal. "
            f"A shorter group is copied unchanged. Concatenate the pieces.")
    gen = lambda: "".join(r.choice("aabbbcz") for _ in range(r.randint(0, 14)))
    return "encode", spec, _rle(sep, m), lambda: (gen(),)


def t_moving_avg(r):
    w = r.randint(2, 5); d = r.randint(0, 3)
    spec = (f"Write `smooth(xs: list[float]) -> list[float]`. Return the averages of every window of {w} consecutive "
            f"elements, in order, each rounded with Python's round(value, {d}). If len(xs) < {w}, return [].")
    def f(xs):
        return [round(sum(xs[i:i + w]) / w, d) for i in range(len(xs) - w + 1)] if len(xs) >= w else []
    return "smooth", spec, f, lambda: ([round(r.uniform(-50, 50), 2) for _ in range(r.randint(0, 10))],)


def t_intervals(r):
    touch = r.choice([True, False])
    spec = ("Write `merge(iv: list[list[int]]) -> list[list[int]]`. Each item is [start, end] with start <= end. "
            "Sort by start and merge overlapping intervals. "
            + ("Intervals that only touch (end == next start) ARE merged." if touch else
               "Intervals that only touch (end == next start) are NOT merged.")
            + " Return the merged list sorted by start.")
    def f(iv):
        out = []
        for s, e in sorted(iv):
            if out and (s < out[-1][1] or (touch and s == out[-1][1])):
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out
    def gen():
        res = []
        for _ in range(r.randint(0, 7)):
            s = r.randint(0, 20); res.append([s, s + r.randint(0, 5)])
        return (res,)
    return "merge", spec, f, gen


def t_topk(r):
    k = r.randint(2, 4); tie = r.choice(["alphabetical", "first"]); ci = r.choice([True, False])
    spec = (f"Write `top_words(text: str) -> list[str]`. Split `text` on whitespace. "
            + ("Treat words case-insensitively and return them in lower case. " if ci else "Words are case-sensitive. ")
            + f"Return the {k} most frequent words, most frequent first. Break ties "
            + ("alphabetically." if tie == "alphabetical" else "by which word appeared first in the text.")
            + f" If there are fewer than {k} distinct words, return all of them in that order.")
    def f(text):
        ws = text.split()
        if ci: ws = [w.lower() for w in ws]
        cnt, first = {}, {}
        for i, w in enumerate(ws):
            cnt[w] = cnt.get(w, 0) + 1; first.setdefault(w, i)
        key = (lambda w: (-cnt[w], w)) if tie == "alphabetical" else (lambda w: (-cnt[w], first[w]))
        return sorted(cnt, key=key)[:k]
    vocab = ["Ab", "ab", "cd", "Cd", "ef", "gh", "ij"]
    return "top_words", spec, f, lambda: (" ".join(r.choice(vocab) for _ in range(r.randint(0, 15))),)


def t_kv(r):
    ps = r.choice([";", ",", "|", "&"]); ks = r.choice(["=", ":", "->"])
    spec = (f"Write `parse(s: str) -> dict`. `s` holds pairs separated by '{ps}'; inside a pair the key and value are "
            f"separated by the first '{ks}'. Strip spaces around keys and values. Skip empty pairs and pairs without "
            f"'{ks}'. If a value is an integer literal (optional leading '-', then digits), convert it to int. "
            f"If a key repeats, the later value wins.")
    def f(s):
        out = {}
        for p in s.split(ps):
            if ks not in p:
                continue
            k, v = p.split(ks, 1); k, v = k.strip(), v.strip()
            if v.lstrip("-").isdigit() and v.count("-") <= 1 and (not v.startswith("--")) and v not in ("-",):
                v = int(v)
            out[k] = v
        return out
    def gen():
        parts = []
        for _ in range(r.randint(0, 5)):
            k = r.choice("abcd"); v = r.choice(["1", "-3", "x", " 42 ", "7a", ""])
            parts.append(r.choice([f"{k}{ks}{v}", f" {k} {ks} {v}", "", "junk"]))
        return (ps.join(parts),)
    return "parse", spec, f, gen


def t_brackets(r):
    pairs = r.sample(["()", "[]", "{}", "<>"], r.randint(2, 3))
    spec = (f"Write `balanced(s: str) -> bool`. Only these bracket pairs matter: {', '.join(pairs)}. "
            "Ignore every other character. Return True if the brackets are properly nested and closed.")
    opens = {p[0]: p[1] for p in pairs}; closes = set(opens.values())
    def f(s):
        st = []
        for c in s:
            if c in opens: st.append(opens[c])
            elif c in closes:
                if not st or st.pop() != c: return False
        return not st
    chars = "".join(pairs) + "x(<"
    return "balanced", spec, f, lambda: ("".join(r.choice(chars) for _ in range(r.randint(0, 10))),)


def t_chunks(r):
    n = r.randint(2, 4); keep = r.choice([True, False])
    spec = (f"Write `chunk_sums(xs: list[int]) -> list[int]`. Split `xs` into consecutive chunks of {n} and return the "
            f"sum of each chunk. " + ("A shorter final chunk is kept." if keep else "A shorter final chunk is dropped."))
    def f(xs):
        out = [sum(xs[i:i + n]) for i in range(0, len(xs), n)]
        if not keep and len(xs) % n: out = out[:-1]
        return out
    return "chunk_sums", spec, f, lambda: ([r.randint(-9, 9) for _ in range(r.randint(0, 11))],)


def t_base(r):
    b = r.randint(3, 7); digits = "".join(r.sample(string.ascii_uppercase, b))
    spec = (f"Write `to_base(n: int) -> str`. Write the non-negative integer n in base {b} using the digit symbols "
            f"'{digits}' (the first symbol means 0, the second 1, and so on). 0 is written as '{digits[0]}'.")
    def f(n):
        if n == 0: return digits[0]
        s = ""
        while n: s = digits[n % b] + s; n //= b
        return s
    return "to_base", spec, f, lambda: (r.randint(0, 500),)


TEMPLATES = [t_rle, t_moving_avg, t_intervals, t_topk, t_kv, t_brackets, t_chunks, t_base]


def make_task(seed: int, n_visible=3, n_hidden=25):
    r = random.Random(seed)
    tmpl = TEMPLATES[seed % len(TEMPLATES)]
    name, spec, ref, gen = tmpl(r)
    cases, seen = [], set()
    tries = 0
    while len(cases) < n_visible + n_hidden and tries < 2000:
        tries += 1
        args = gen(); key = json.dumps(args)
        if key in seen: continue
        seen.add(key); cases.append({"args": list(args), "expected": ref(*json.loads(key))})
    vis, hid = cases[:n_visible], cases[n_visible:]
    ex = "\n".join(f"  {name}({', '.join(json.dumps(a) for a in c['args'])}) == {json.dumps(c['expected'])}" for c in vis)
    instruction = (f"{spec}\n\nPut the function in a file named `solution.py`.\n\nExamples:\n{ex}\n")
    return {"id": f"code-{seed:04d}", "family": "coding", "template": tmpl.__name__, "func": name,
            "instruction": instruction, "visible": vis, "hidden": hid}


GRADER = r'''
import json, sys, importlib.util, signal
spec = importlib.util.spec_from_file_location("solution", sys.argv[1])
cases = json.load(open(sys.argv[2])); func = sys.argv[3]
signal.alarm(10)
try:
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); f = getattr(m, func)
except Exception:
    print(json.dumps({"passed": 0, "total": len(cases)})); sys.exit()
ok = 0
for c in cases:
    try:
        got = f(*json.loads(json.dumps(c["args"])))
        if json.loads(json.dumps(got)) == c["expected"]: ok += 1
    except Exception:
        pass
print(json.dumps({"passed": ok, "total": len(cases)}))
'''
