#!/usr/bin/env python3
"""PINS CV1-CV4 for ledger/coverage.py (wave-4 candidate 2 build).

Spec: docs/pre-registration-coverage-tool.md (PR #13, SEALED). These pins are
defined in that doc and are not movable. FAIL-first: run against a tree with
no ledger/coverage.py -> RED, receipt in pins/failfirst-coverage.log.
"""
import os, sys, json, tempfile, shutil, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

results = []
def pin(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))

try:
    import ledger.coverage  # noqa: F401
    COVERAGE = True
except ModuleNotFoundError as e:
    COVERAGE = False
    os.makedirs(os.path.join(ROOT, "pins"), exist_ok=True)
    with open(os.path.join(ROOT, "pins", "failfirst-coverage.log"), "w") as f:
        f.write(f"FAIL-first: ledger/coverage.py absent — {e}\n")

from ledger.store import _checksum


def plant(dirpath, rows):
    """Write ledger.jsonl directly (bypassing Store) with correct checksums."""
    os.makedirs(dirpath, exist_ok=True)
    path = os.path.join(dirpath, "ledger.jsonl")
    with open(path, "w") as f:
        for entry_id, entry in rows:
            body = json.dumps(entry, sort_keys=True, separators=(",", ":"))
            rec = {"id": entry_id, "sum": _checksum(entry_id, body), "entry": entry}
            f.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")
    return path


def run_cov(ledger_dir, *args):
    return subprocess.run(
        [sys.executable, "-m", "ledger.coverage", ledger_dir, *args],
        capture_output=True, text=True, cwd=ROOT)


def entry(**kw):
    base = dict(ts=1, stopped_checking="s", because="b", covered_by="c",
                revisit_trigger="never", kind="event", expr=None,
                status="open", discharge_reason=None)
    base.update(kw)
    return base


def line_checksums_ok(path):
    with open(path) as f:
        for i, line in enumerate(f.read().splitlines()):
            if not line.strip():
                continue
            rec = json.loads(line)
            body = json.dumps(rec["entry"], sort_keys=True, separators=(",", ":"))
            if rec.get("sum") != _checksum(rec["id"], body):
                return False, f"line {i} checksum mismatch"
    return True, ""


def main():
    if not COVERAGE:
        for p in ["CV1", "CV2", "CV3", "CV4"]:
            pin(p, False, "ledger.coverage not importable")
        return 1

    tmp = tempfile.mkdtemp(prefix="pins-coverage-")
    try:
        # CV1: planted file-carried unreasoned discharge NAMED by id.
        d1 = os.path.join(tmp, "cv1")
        plant(d1, [
            ("open-1", entry(id="open-1", stopped_checking="a thing")),
            ("bad-1", entry(id="bad-1", stopped_checking="other",
                            status="discharged", discharge_reason="")),
        ])
        r = run_cov(d1, "unreasoned")
        pin("CV1", r.returncode == 0 and "bad-1" in r.stdout,
            f"rc={r.returncode} out={r.stdout!r}"[:120])

        # CV2: zero unreasoned -> empty output, exit 0 (healthy, not error).
        d2 = os.path.join(tmp, "cv2")
        plant(d2, [
            ("ok-1", entry(id="ok-1", stopped_checking="x",
                           status="discharged", discharge_reason="real reason")),
            ("open-2", entry(id="open-2", stopped_checking="y")),
        ])
        r = run_cov(d2, "unreasoned")
        pin("CV2", r.returncode == 0 and r.stdout.strip() == "",
            f"rc={r.returncode} out={r.stdout!r}"[:120])

        # CV3: due is advisory — bytes AND line checksums unchanged.
        d3 = os.path.join(tmp, "cv3")
        path3 = plant(d3, [
            ("e-1", entry(id="e-1", stopped_checking="z",
                          revisit_trigger="wave4-merge", covered_by="q")),
            ("e-2", entry(id="e-2", stopped_checking="w", kind="condition",
                          expr="wave4-merge", covered_by="q")),
            ("e-3", entry(id="e-3", stopped_checking="v",
                          revisit_trigger="other-event", covered_by="q")),
        ])
        before = open(path3, "rb").read()
        before_sha = hashlib.sha256(before).hexdigest()
        r = run_cov(d3, "due", "wave4-merge")
        after = open(path3, "rb").read()
        same_bytes = after == before
        same_sha = hashlib.sha256(after).hexdigest() == before_sha
        sums_ok, why = line_checksums_ok(path3)
        named = "e-1" in r.stdout and "e-2" in r.stdout and "e-3" not in r.stdout
        pin("CV3", r.returncode == 0 and same_bytes and same_sha and sums_ok and named,
            f"bytes={same_bytes} sha={same_sha} sums={sums_ok} due-named={named} {why}"[:160])

        # CV4: covers is substring, every match line LABELED substring.
        d4 = os.path.join(tmp, "cv4")
        plant(d4, [
            ("m-1", entry(id="m-1", stopped_checking="s1",
                          covered_by="fleet-triage resolver")),
            ("m-2", entry(id="m-2", stopped_checking="s2", status="due",
                          covered_by="unrelated coverage")),
        ])
        r = run_cov(d4, "covers", "triage")
        match_lines = [l for l in r.stdout.splitlines() if "m-1" in l]
        pin("CV4", (r.returncode == 0 and len(match_lines) >= 1
                    and all("substring" in l for l in match_lines)
                    and not any("m-2" in l for l in r.stdout.splitlines())),
            f"rc={r.returncode} lines={match_lines!r}"[:160])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
