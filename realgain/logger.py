"""Write realgain records from inside your own loop:

    from realgain import Logger
    log = Logger("evals.jsonl")
    log.record(version="v3", parent="v1", task="q17", score=0.8, truth=1.0, split="selection",
               repeat=0, accepted=True, generation=3, commands=agent_commands)
"""
import json, threading

class Logger:
    def __init__(self, path):
        self.path = path; self._lock = threading.Lock()

    def record(self, version, task, score=None, **fields):
        rec = {"version": version, "task": task, "score": score, **fields}
        with self._lock, open(self.path, "a") as f:
            f.write(json.dumps(rec, default=float) + "\n")
