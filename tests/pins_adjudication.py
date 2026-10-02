#!/usr/bin/env python3
"""PINS AC1-AC4 for ledger/adjudication.py (wave-4 candidate 3 build).

Spec: docs/pre-registration-adjudication-client.md (PR #15, SEALED).
These pins are defined in that doc and are not movable. FAIL-first: run
against a tree with no ledger/adjudication.py -> RED, receipt in
pins/failfirst-adjudication.log.
"""
import os, sys, json, tempfile, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

results = []
def pin(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))

try:
    import ledger.adjudication as adj
    ADJ = True
except ModuleNotFoundError as e:
    ADJ = False
    os.makedirs(os.path.join(ROOT, "pins"), exist_ok=True)
    with open(os.path.join(ROOT, "pins", "failfirst-adjudication.log"), "w") as f:
        f.write(f"FAIL-first: ledger/adjudication.py absent — {e}\n")

from ledger.store import _checksum


RECORD = {
    "kind": "adjudication",
    "refused": "index",
    "named_by": "merge tree the refusal judged",
    "short": "177f885",
    "tree": "t" * 40,
    "head_before": "a" * 40,
    "merge_head": "b" * 40,
    "ts": 1727000000,
    "adjudication": "mechanical",
    "judge": "none — no model is in this loop, by design",
    "rule": "winner is the claim that arrived on the side being merged; "
            "this is an ordering, not a judgment about truth",
    "conflicts": [{
        "key": "inbound_edges",
        "cell": "cells/inbox/body",
        "winner": {"value": "21", "by": "quilt-tools#33 0101409",
                   "side": "incoming",
                   "line": "claim: inbound_edges = 21  by quilt-tools#33 0101409"},
        "losers": [{"value": "19", "by": "quilt-tools#32 fb2e041",
                    "side": "base",
                    "line": "claim: inbound_edges = 19  by quilt-tools#32 fb2e041"}],
        "reason": "two attributed claims for key inbound_edges carry "
                  "different values; the record names the incoming claim as "
                  "winner so the merge has one surviving line, and keeps the "
                  "other verbatim. No judge was consulted and no model ran.",
        "to_accept_the_loser": "git checkout HEAD -- cells/inbox/body && git commit",
    }],
}


def plant(dirpath, record=RECORD, name="177f885.json"):
    os.makedirs(dirpath, exist_ok=True)
    p = os.path.join(dirpath, name)
    with open(p, "w") as f:
        json.dump(record, f, indent=2)
    return p


def run_adj(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledger.adjudication", *args],
        capture_output=True, text=True, cwd=ROOT)


def entry_line_checksum(entry_id, d):
    body = json.dumps(d, sort_keys=True, separators=(",", ":"))
    return _checksum(entry_id, body)


def main():
    if not ADJ:
        for p in ["AC1", "AC2", "AC3", "AC4"]:
            pin(p, False, "module absent — see pins/failfirst-adjudication.log")
        return 1 if not all(results) else 0

    tmp = tempfile.mkdtemp(prefix="pins-adjudication-")
    try:
        # ---- AC1 planted-record round-trip
        d1 = os.path.join(tmp, "ac1")
        rp = plant(d1)
        r = run_adj(rp, "--emit-only")
        ok = r.returncode == 0
        entry = json.loads(r.stdout.strip().splitlines()[-1]) if ok else {}
        sc = entry.get("stopped_checking", "")
        ok = ok and "inbound_edges" in sc and "2 claimants" in sc \
            and "21" not in sc and "19" not in sc
        pin("AC1 planted-record round-trip", ok,
            f"stopped_checking={sc!r}" if not ok else "")

        # ---- AC2 winner != truth (load-bearing)
        d2 = os.path.join(tmp, "ac2")
        rp2 = plant(d2)
        r2 = run_adj(rp2, "--emit-only")
        ok2 = r2.returncode == 0
        blob = r2.stdout if ok2 else ""
        # winner's VALUE must appear NOWHERE in the emitted entry (the
        # record path citation names the file, not the value)
        ok2 = ok2 and '"21"' not in blob and " 21 " not in blob \
            and "inbound_edges = 21" not in blob
        ok2 = ok2 and "177f885.json" in blob  # record cited by path
        pin("AC2 winner value adopted nowhere (cited, never adopted)", ok2,
            "winner value leaked into entry" if not ok2 else "")

        # ---- AC3 byte-identity across re-run (read-only is the promise)
        d3 = os.path.join(tmp, "ac3")
        rp3 = plant(d3)
        before = open(rp3, "rb").read()
        e1 = adj.build_entry(RECORD, rp3, entry_id="fixedid00001", ts=999)
        e2 = adj.build_entry(RECORD, rp3, entry_id="fixedid00001", ts=999)
        c1 = entry_line_checksum("fixedid00001", e1)
        c2 = entry_line_checksum("fixedid00001", e2)
        r3 = run_adj(rp3, "--emit-only")
        after = open(rp3, "rb").read()
        ok3 = e1 == e2 and c1 == c2 and before == after \
            and not os.path.exists(os.path.join(d3, "ledger.jsonl"))
        pin("AC3 fixture bytes + emitted-entry checksums unchanged re-run",
            ok3, "" if ok3 else
            f"e1==e2:{e1 == e2} sum:{c1 == c2} bytes:{before == after}")

        # ---- AC4 zero-disputes healthy answer
        d4 = os.path.join(tmp, "ac4-empty")
        os.makedirs(d4)
        r4 = run_adj(d4, "--emit-only")
        ok4 = r4.returncode == 0 and r4.stdout.strip() != "" \
            and "zero" in r4.stdout
        r4b = run_adj(os.path.join(tmp, "ac4-absent"), "--emit-only")
        ok4b = r4b.returncode == 0  # absent dir treated as zero records
        pin("AC4 zero-disputes healthy answer (exit 0, message)",
            ok4 and ok4b, f"empty:{ok4} absent:{ok4b}")

        # ---- KS1 schema drift refusal (named field, emit nothing)
        d5 = os.path.join(tmp, "ks1")
        rec_bad = json.loads(json.dumps(RECORD))
        del rec_bad["judge"]
        rp5 = plant(d5, rec_bad)
        r5 = run_adj(rp5, "--emit-only")
        ok5 = r5.returncode == 3 and "judge" in r5.stderr and r5.stdout == ""
        pin("KS1 schema drift -> E_SCHEMA_DRIFT names judge, emits nothing",
            ok5, f"rc={r5.returncode}" if not ok5 else "")

        # ---- KS2 judge landed -> refuse, re-open spec
        d6 = os.path.join(tmp, "ks2")
        rec_j = json.loads(json.dumps(RECORD))
        rec_j["judge"] = "claude-opus-4.7 — judgment requested"
        rp6 = plant(d6, rec_j)
        r6 = run_adj(rp6, "--emit-only")
        ok6 = r6.returncode == 4 and r6.stdout == ""
        pin("KS2 judge landed -> E_JUDGE_LANDED emits nothing", ok6,
            f"rc={r6.returncode}" if not ok6 else "")

        # ---- ledger write path (Store append + coverage-style checksums)
        d7 = os.path.join(tmp, "ac1-ledger")
        rp7 = plant(d7)
        led = os.path.join(tmp, "ledger-ac1")
        r7 = run_adj(rp7, "--ledger", led)
        lf = os.path.join(led, "ledger.jsonl")
        ok7 = r7.returncode == 0 and os.path.exists(lf)
        if ok7:
            line = open(lf).read().strip()
            rec = json.loads(line)
            body = json.dumps(rec["entry"], sort_keys=True,
                              separators=(",", ":"))
            ok7 = rec["sum"] == _checksum(rec["id"], body)
        pin("ledger write path: Store append, checksum verifies", ok7,
            "" if ok7 else f"rc={r7.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
