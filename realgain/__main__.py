import argparse, json, os
from .checks import report, to_markdown, DEFAULT_TAMPER

def main():
    ap = argparse.ArgumentParser(prog="realgain", description="Check whether a self-improving loop's claimed gains are real.")
    ap.add_argument("log", nargs="?", help="JSONL evaluation log (see FORMAT.md); omit with --demo")
    ap.add_argument("--json", help="write the full report as JSON")
    ap.add_argument("--plot", help="write a PNG summary figure (needs matplotlib)")
    ap.add_argument("--title", default=None)
    ap.add_argument("--tamper", nargs="*", help="regexes that mark grader access in commands (default: %s)" % " ".join(DEFAULT_TAMPER))
    ap.add_argument("--demo", action="store_true", help="run on a bundled example (our contract-review loop R1)")
    A = ap.parse_args()
    path = A.log
    if A.demo: path = os.path.join(os.path.dirname(__file__), "data", "demo_contracts_R1.jsonl")
    if not path: ap.error("give a log file or --demo")
    rep = report(path, A.tamper if A.tamper is not None else DEFAULT_TAMPER)
    print(to_markdown(rep, A.title or os.path.basename(path)))
    if A.json: json.dump(rep, open(A.json, "w"), indent=1, default=float)
    if A.plot:
        from .plot import plot; plot(rep, A.plot, A.title or os.path.basename(path))

if __name__ == "__main__":
    main()
