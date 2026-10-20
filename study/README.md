# The study behind realgain

Do self-improving agents really get better when an LLM judge decides what counts as better? Write-up: [link].

Everything needed to check the numbers is here: the code that ran the experiments, every run's log (including each
report the agent wrote, each judge score, and every shell command the agent ran), the pre-registration, and an
independent re-computation.

## Layout

| path | what |
|---|---|
| `prereg.md` | predictions written before the contract-review loops were run, with outcomes and corrections appended below (the original text is unchanged) |
| `code/solver.py` | the agent: Kimi K2.6 with one `bash` tool in a scratch folder, a "playbook" as its system prompt |
| `code/tasks_retail.py` | scenario A: year-over-year memos on the real Online Retail II transactions; answer key computed from the KPI definition |
| `code/tasks_cuad.py` | scenario D: contract intake reviews on real CUAD contracts; answer key = lawyers' labels for 10 provisions |
| `code/judge.py` | the LLM judges (absolute 1–10 and pairwise), which see the assignment and the report only |
| `code/loop.py` | the self-improvement loop: mutate the playbook from feedback, run candidates, accept by judge or by answer key |
| `code/heldout.py`, `code/decompose.py` | checks: start vs final on unseen tasks; re-runs and held-out runs for every accepted version |
| `code/rejudge_ds.py` | re-scoring every saved report with DeepSeek-V4-Pro |
| `code/judge_with_data.py` | the "let the judge see the data" test (sandboxed shell over the raw data) |
| `code/analyze*.py`, `code/plot*.py` | the numbers and figures in the write-up |
| `code/tasks_coding.py` etc. | early synthetic pilots (too easy: the agent solved ~100%), kept because `solver.py` imports them |
| `runs/` | all logs (JSONL). `cuad_v1` = loop R1 (judge selects), `cuad_R2_gold_locked`, `cuad_R3_gold_open`; `decomp_R*` = re-runs + held-out; `heldout_*` = start-vs-final checks; `rejudge_*`, `judgeB_*` = other judges |
| `public_logs_analysis/` | the first-pass analysis of AFlow's published logs |
| `verify/` | an independent re-computation of the key numbers from the raw logs, written without reading the analysis code |

## Re-running

Needs a Moonshot (Kimi) API key, and a DeepSeek key for the cross-judge checks. Put them in `secrets/kimi.env`
(`MOONSHOT_API_KEY=…`, `MOONSHOT_BASE_URL=https://api.moonshot.cn/v1`) and `secrets/deepseek.env`
(`DEEPSEEK_API_KEY=…`, `DEEPSEEK_BASE_URL=https://api.deepseek.com`), or point `KIMI_ENV` / `DEEPSEEK_ENV` at them.

Data (not redistributed here):
- CUAD v1 (`CUADv1.json`, CC BY 4.0), from the Atticus Project; set `CUAD_JSON`.
- Online Retail II (UCI, CC BY 4.0), loaded into a pandas pickle with columns Invoice, StockCode, Description,
  Quantity, InvoiceDate, Price, CustomerID, Country; set `RETAIL_PKL`.

```bash
cd code
python3 loop.py --family cuad --select judge --sel 5 --fresh 5 --gens 6 --k 2 --out ../runs/my_R1.jsonl
python3 decompose.py --family cuad --log ../runs/my_R1.jsonl --out ../runs/my_decomp_R1.jsonl
python3 analyze_decomp.py ../runs/my_R1.jsonl ../runs/my_decomp_R1.jsonl judge
```

Contract runs cost about ¥0.9 each with Kimi K2.6 (Oct 2026 prices), retail runs about ¥2.

**Sandboxing caveat.** The agent's shell was not isolated from the rest of the machine. An audit of every logged
command found no run that left its own folder to look for a grader (`grep` the `commands` fields to confirm). The
data-access judge, which did wander into other folders in a first test, was re-run inside a mount namespace that
shows it only its own folder.
