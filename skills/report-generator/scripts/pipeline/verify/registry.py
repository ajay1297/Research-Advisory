"""Check registry — lets each check declare its own CLI surface next to its code.

Why this exists: main() used to carry a subparser block and an elif branch for
every check, so adding one meant three edits in three places (the function, the
parser, the dispatch) and forgetting the third failed silently as "invalid
choice". Here a check declares its arguments in a decorator directly above
itself, and main() is a loop.

The CLI surface is unchanged from the pre-registry version — same subcommand
names, same argument names, same defaults and help strings. verify_report.py's
ORDER tuple fixes the order they appear in `--help`, which insertion order alone
would not guarantee once checks are spread across modules.
"""
import os

# Path anchors, computed once here rather than re-derived with a chain of
# dirname() calls in each check that needs them. This file lives at
# scripts/pipeline/verify/registry.py, so the skill root is three levels up —
# a check that recomputed this locally would silently point one level off if it
# were ever moved between modules.
_HERE = os.path.dirname(os.path.abspath(__file__))          # .../scripts/pipeline/verify
PIPELINE_DIR = os.path.dirname(_HERE)                        # .../scripts/pipeline
SCRIPTS_DIR = os.path.dirname(PIPELINE_DIR)                  # .../scripts
HELPERS_DIR = os.path.join(SCRIPTS_DIR, "helpers")           # .../scripts/helpers
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)                     # .../report-generator

# name -> (function, tuple of Arg)
CHECKS = {}


class Arg:
    """One argparse argument, declared inline on the check it belongs to.

    Takes exactly what parser.add_argument() takes; it is only a deferred call.
    """

    def __init__(self, *names, **kwargs):
        self.names = names
        self.kwargs = kwargs

    def add_to(self, parser):
        parser.add_argument(*self.names, **self.kwargs)


def check(name, *args):
    """Register a check under its CLI subcommand name.

    The decorated function's keyword parameters must match the argument dests,
    since main() calls it as fn(**vars(args)). A mismatch raises TypeError at
    call time rather than passing the wrong value silently.
    """

    def deco(fn):
        if name in CHECKS:
            raise ValueError(f"duplicate check name: {name!r}")
        CHECKS[name] = (fn, args)
        return fn

    return deco
