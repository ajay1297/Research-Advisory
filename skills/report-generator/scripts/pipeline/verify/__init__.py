"""The verify_report checks, split by guardrail tier.

Importing this package is what registers every check: each module's @check
decorators run at import time and populate registry.CHECKS, which verify_report.py
then turns into the CLI. A module that isn't imported here has its checks silently
missing from `--help`, so every module belongs in the list below.
"""
from . import core, inputs, execution, output, recency  # noqa: F401  (import = register)
from .registry import CHECKS, Arg, check  # noqa: F401
