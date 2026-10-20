"""realgain: check whether a self-improving system's claimed improvements are real."""
from .checks import load, report, to_markdown, verdict, paired, null_best_of_k, holm
from .logger import Logger
from .shrink import candidate_gains, shrink
from .audit import classical, ppi, label_budget
__version__ = "0.3.0"
