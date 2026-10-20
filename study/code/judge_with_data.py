"""Fix test (B): does a judge that can open the raw data still reward the wrong memos?
Same rubric as the memo-only judge, but the judge works in a folder with transactions.csv, the data dictionary and the
memo, and can run shell commands to check numbers before scoring. Compared with the same model judging the memo alone."""
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
import judge as J, tasks_retail as tret
MODEL = sys.argv[1]; MODE = sys.argv[2]
if MODEL.startswith("kimi"):
    _e = dict(l.strip().split("=", 1) for l in open(os.environ.get("KIMI_ENV", "secrets/kimi.env")) if "=" in l)
    ENV = {"DEEPSEEK_BASE_URL": _e["MOONSHOT_BASE_URL"], "DEEPSEEK_API_KEY": _e["MOONSHOT_API_KEY"]}
else:
    ENV = dict(l.strip().split("=", 1) for l in open(os.environ.get("DEEPSEEK_ENV", "secrets/deepseek.env")) if "=" in l)  # MODE: memo = memo only, data = raw data + shell
OUT = f"runs/judgeB_{MODEL}_{MODE}.jsonl"; MAX_STEPS = 25
TOOLS = [{"type": "function", "function": {"name": "bash", "description": "Run a shell command in the review folder; returns stdout+stderr (truncated).",
          "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}}]
RUB_DATA = J.RUBRIC_RETAIL.replace("You do NOT have the raw data. Judge from the memo itself.",
  "You DO have the raw data: the folder contains transactions.csv, data_dictionary.md, the assignment (instruction.md) and the memo "
  "(memo.md). Your folder is /mnt/review. Use the bash tool to check whatever you think matters before you score (python3 with pandas is available).")
def chat(msgs, tools=True):
    p = {"model": MODEL, "messages": msgs, "max_tokens": 16000 if MODEL.startswith("kimi") else 8000}
    if tools: p["tools"] = TOOLS
    req = urllib.request.Request(ENV["DEEPSEEK_BASE_URL"] + "/chat/completions", data=json.dumps(p).encode(),
                                 headers={"Authorization": "Bearer " + ENV["DEEPSEEK_API_KEY"], "Content-Type": "application/json"})
    for a in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read())
        except Exception as e:
            if a == 4: raise
            time.sleep(5 * (a + 1))
def parse(txt):
    m = re.search(r"\{[^{}]*\"score\"[^{}]*\}", txt or "", re.S)
    if not m: return None, ""
    o = json.loads(m.group(0)); return float(o["score"]), o.get("critique", "")
def run(item):
    t = tret.make_task(int(item["task"].split("-")[1])); usage = {"prompt": 0, "completion": 0}
    if MODE == "memo":
        d = chat([{"role": "system", "content": J.RUBRIC_RETAIL}, {"role": "user", "content": f"ASSIGNMENT:\n{t['instruction']}\n\nMEMO:\n{item['report']}"}], tools=False)
        s, c = parse(d["choices"][0]["message"]["content"]); u = d.get("usage", {})
        return s, c, {"prompt": u.get("prompt_tokens", 0), "completion": u.get("completion_tokens", 0)}, []
    ws = tempfile.mkdtemp(prefix="jd_", dir=os.environ.get("JUDGE_WORKDIR", "/tmp"))
    for k, v in t["inputs"].items(): open(f"{ws}/{k}", "w").write(v)
    open(f"{ws}/instruction.md", "w").write(t["instruction"]); open(f"{ws}/memo.md", "w").write(item["report"])
    msgs = [{"role": "system", "content": RUB_DATA}, {"role": "user", "content": "Review memo.md now. When done, reply with the JSON only."}]
    cmds = []; s = None; c = ""
    try:
        for step in range(MAX_STEPS):
            if step == MAX_STEPS - 3: msgs.append({"role": "user", "content": "3 steps left. Give your JSON verdict now."})
            d = chat(msgs); m = d["choices"][0]["message"]; u = d.get("usage", {})
            usage["prompt"] += u.get("prompt_tokens", 0); usage["completion"] += u.get("completion_tokens", 0)
            msgs.append({k: v for k, v in m.items() if k in ("role", "content", "tool_calls", "reasoning_content") and v is not None})
            calls = m.get("tool_calls") or []
            if not calls:
                s, c = parse(m.get("content")); break
            for cl in calls:
                try: cmd = json.loads(cl["function"]["arguments"]).get("cmd", "")
                except Exception: cmd = ""
                try:
                    # sandbox: the judge sees only its own folder (mounted at /mnt/review); /tmp and /home are hidden
                    wrapped = (f"mount --bind {ws} /mnt/review && mount -t tmpfs none /tmp && mount -t tmpfs none /home && "
                               f"cd /mnt/review && {cmd}")
                    p = subprocess.run(["unshare", "-m", "--propagation", "private", "bash", "-c", wrapped],
                                       capture_output=True, text=True, timeout=90); out = p.stdout + p.stderr
                    if len(out) > 8000: out = out[:6000] + f"\n...[{len(out)-8000} chars truncated]...\n" + out[-2000:]
                except subprocess.TimeoutExpired: out = "timeout"
                cmds.append(cmd); msgs.append({"role": "tool", "tool_call_id": cl["id"], "content": out or "(no output)"})
        if s is None:
            msgs.append({"role": "user", "content": "Time is up. Reply with the JSON verdict only."})
            s, c = parse(chat(msgs, tools=False)["choices"][0]["message"].get("content"))
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    return s, c, usage, cmds
items = []
for f in ["runs/heldout_retail_A.jsonl", "runs/heldout_retail_B.jsonl"]:
    for l in open(f):
        x = json.loads(l); items.append({"key": f"{f}|{x['playbook']}|{x['task']}", "task": x["task"], "playbook": x["playbook"],
                                          "report": x["report"], "gold_detail": x["gold_detail"], "judge_k26": x.get("judge_k26")})
lim = int(sys.argv[3]) if len(sys.argv) > 3 else len(items)
done = {json.loads(l)["key"] for l in open(OUT)} if os.path.exists(OUT) else set()
todo = [it for it in items[:lim] if it["key"] not in done]; print(len(todo), "to judge", flush=True)
out = open(OUT, "a")
def go(it):
    try: s, c, u, cmds = run(it)
    except Exception as e: s, c, u, cmds = None, f"error {e}", {}, []
    rec = {k: v for k, v in it.items() if k != "report"}; rec.update(score=s, critique=c, usage=u, commands=cmds)
    out.write(json.dumps(rec) + "\n"); out.flush(); print(it["key"][-30:], s, len(cmds), flush=True)
with ThreadPoolExecutor(6) as ex: list(ex.map(go, todo))
