#!/usr/bin/env python3
"""
run_context.py — shared provenance + concurrency-lock helpers for the report-generator
pipeline.

Two problems this exists to fix (see plugin issues #2 and #6 raised in review):

1. **No provenance on tracker entries.** guidance_history.json, fundraise_history.json,
   rating_history.json, litigation_history.json, and source_manifest.json previously
   stored flat arrays with no marker for *which run* wrote each entry. When two agents
   ran concurrently against the same company slug, there was no way to mechanically
   tell "is this entry from my run or a concurrent/stale one" — it required a human
   judgment call and manual cross-verification. Every entry now gets a `run_id` field
   stamped automatically via get_run_id() below.

2. **No lock against concurrent runs on the same company slug.** Nothing stopped two
   agents from processing `bhartiya_international` at the same time, each unaware of
   the other, writing to the same tracker files. acquire_lock()/release_lock() below
   implement a simple PID+timestamp lock file at
   ~/.report-generator/research_cache/<slug>/.lock — Step 0 of the pipeline (see
   SKILL.md) now acquires this before any fetching starts and releases it at the end
   (or on failure). A stale lock (holder process no longer running, or older than
   --stale-after-minutes) is auto-reclaimed rather than blocking forever.

Usage (as a script, for SKILL.md Step 0):
    python3 run_context.py acquire <company_slug>          # prints {"run_id": "...", "acquired": true}
    python3 run_context.py release <company_slug> <run_id>
    python3 run_context.py status <company_slug>

Usage (as a module, from other pipeline scripts):
    from run_context import get_run_id
    entry["run_id"] = get_run_id()
"""
import argparse
import json
import os
import time
import uuid


def _base(company_slug: str) -> str:
    base = os.path.join(os.path.expanduser("~/.report-generator"), "research_cache", company_slug)
    os.makedirs(base, exist_ok=True)
    return base


def _lock_path(company_slug: str) -> str:
    return os.path.join(_base(company_slug), ".lock")


def get_run_id() -> str:
    """Stable run identifier for the current pipeline invocation.

    Prefers REPORT_GEN_RUN_ID if a caller (typically acquire_lock, or an agent that
    exported it after calling `run_context.py acquire`) has set it in the environment,
    so every tracker write within one run shares the same id. Falls back to a
    per-process id so a script called standalone (outside the lock flow) still stamps
    something better than nothing.
    """
    env_id = os.environ.get("REPORT_GEN_RUN_ID")
    if env_id:
        return env_id
    return f"unmanaged-{os.getpid()}-{int(time.time())}"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    except PermissionError:
        return True  # exists, just not ours
    return True


def acquire_lock(company_slug: str, stale_after_minutes: int = 120) -> dict:
    path = _lock_path(company_slug)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                holder = json.load(f)
            except json.JSONDecodeError:
                holder = {}
        held_pid = holder.get("pid")
        acquired_at = holder.get("acquired_at", 0)
        age_minutes = (time.time() - acquired_at) / 60.0 if acquired_at else 999999
        still_alive = held_pid is not None and _pid_alive(held_pid)
        if still_alive and age_minutes < stale_after_minutes:
            return {
                "acquired": False,
                "reason": "locked_by_another_run",
                "holder_run_id": holder.get("run_id"),
                "holder_pid": held_pid,
                "held_since": holder.get("acquired_at_iso"),
                "age_minutes": round(age_minutes, 1),
                "note": (
                    "Another agent appears to be actively processing this company slug. "
                    "Do not proceed with a second concurrent run — either wait, or if you "
                    "are certain the other run is dead (crashed/orphaned), re-run with "
                    "`release --force` first."
                ),
            }
        # stale (dead pid or too old) — reclaim
    run_id = uuid.uuid4().hex[:12]
    payload = {
        "run_id": run_id,
        "pid": os.getpid(),
        "acquired_at": time.time(),
        "acquired_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return {"acquired": True, "run_id": run_id, "note": "export REPORT_GEN_RUN_ID=<run_id> so tracker scripts stamp entries consistently for this run."}


def release_lock(company_slug: str, run_id: str = None, force: bool = False) -> dict:
    path = _lock_path(company_slug)
    if not os.path.exists(path):
        return {"released": True, "note": "no lock was held"}
    with open(path, "r", encoding="utf-8") as f:
        try:
            holder = json.load(f)
        except json.JSONDecodeError:
            holder = {}
    if not force and run_id and holder.get("run_id") != run_id:
        return {
            "released": False,
            "reason": "run_id_mismatch",
            "note": "This lock is held by a different run_id than the one you passed. "
                    "Pass --force only if you're certain the holder is dead/orphaned.",
        }
    os.remove(path)
    return {"released": True}


def status(company_slug: str) -> dict:
    path = _lock_path(company_slug)
    if not os.path.exists(path):
        return {"locked": False}
    with open(path, "r", encoding="utf-8") as f:
        try:
            holder = json.load(f)
        except json.JSONDecodeError:
            return {"locked": True, "corrupt_lock_file": True}
    alive = _pid_alive(holder.get("pid", -1))
    return {"locked": True, "holder": holder, "holder_process_alive": alive}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["acquire", "release", "status"])
    parser.add_argument("company_slug")
    parser.add_argument("run_id", nargs="?", default=None, help="required for release unless --force")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--stale-after-minutes", type=int, default=120)
    args = parser.parse_args()

    if args.action == "acquire":
        print(json.dumps(acquire_lock(args.company_slug, args.stale_after_minutes), indent=2))
    elif args.action == "release":
        print(json.dumps(release_lock(args.company_slug, args.run_id, args.force), indent=2))
    else:
        print(json.dumps(status(args.company_slug), indent=2))


if __name__ == "__main__":
    main()
