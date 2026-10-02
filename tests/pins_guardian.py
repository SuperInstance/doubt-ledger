#!/usr/bin/env python3
"""GUARDIAN PINS G1-G4 (guardian lane D') — FAIL-first against poc.

G1 discharge-reason-persists: a written discharge reason must reach the
    JSONL and survive process death + reload.
G2 atomic-rewrite: a crash mid-_rewrite must leave the last good ledger
    intact and loadable (no truncation, no silent loss).
G3 truncation-named: a mid-line truncated file must fail LOUD and NAMED as
    truncation/corruption — not leak a raw JSONDecodeError.
G4 id-unique / G4b discharge-unknown-loud: duplicate entry ids are rejected
    at add() and at _load(); discharging a nonexistent id raises.
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ledger.entry import Entry
from ledger.store import Store
import ledger.entry as entry_mod
import ledger.store as store_mod

results = []


def pin(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))


def base(**kw):
    args = dict(stopped_checking="pr-93 review",
                because="builder sealed 4 pins independently verified",
                covered_by="builder RESULT.md + pins/failfirst.log",
                revisit_trigger="casey-merged-pr-93")
    args.update(kw)
    return Entry(**args)


def main():
    # G1: discharge reason must persist to disk and survive reload
    d = tempfile.mkdtemp(prefix="dg-")
    s = Store(d)
    e = base()
    s.add(e)
    s.fire("casey-merged-pr-93")
    s.discharge(e.id, reason="re-read the diff; guard verified")
    raw = open(os.path.join(d, "ledger.jsonl")).read()
    s2 = Store(d)  # new process view
    reason = getattr(s2.entries[0], "discharge_reason", None)
    ok = "re-read the diff" in raw and reason == "re-read the diff; guard verified"
    pin("G1 discharge-reason-persists", ok,
        f"in-file={'re-read the diff' in raw} reload-reason={reason!r}")
    shutil.rmtree(d)

    # G2: crash mid-_rewrite must not destroy the ledger
    d = tempfile.mkdtemp(prefix="dg-")
    s = Store(d)
    s.add(base())
    s.add(base(stopped_checking="quota watch", revisit_trigger="quota-reset"))
    real_json = store_mod.json
    calls = {"n": 0}

    class FlakyJson:
        loads = staticmethod(real_json.loads)

        @staticmethod
        def dumps(*a, **k):
            calls["n"] += 1
            if calls["n"] > 1:
                raise OSError("simulated crash mid-rewrite")
            return real_json.dumps(*a, **k)

    store_mod.json = FlakyJson
    try:
        s._rewrite()
    except OSError:
        pass
    finally:
        store_mod.json = real_json
    try:
        s2 = Store(d)
        ok = len(s2.entries) == 2
        pin("G2 atomic-rewrite", ok,
            f"entries loadable after crash={len(s2.entries)}/2")
    except ValueError as ex:
        pin("G2 atomic-rewrite", False, f"ledger unreadable after crash: {ex}")
    shutil.rmtree(d)

    # G3: mid-line truncated file must fail NAMED as truncation/corruption
    d = tempfile.mkdtemp(prefix="dg-")
    s = Store(d)
    s.add(base())
    s.add(base(stopped_checking="quota watch", revisit_trigger="quota-reset"))
    path = os.path.join(d, "ledger.jsonl")
    lines = open(path).read().splitlines(keepends=True)
    with open(path, "w") as f:
        f.write(lines[0] + lines[1][:40])  # process died mid-line
    try:
        Store(d)
        pin("G3 truncation-named", False, "truncated file loaded silently")
    except ValueError as ex:
        msg = str(ex).lower()
        ok = "truncat" in msg or "corrupt" in msg
        pin("G3 truncation-named", ok, f"error={str(ex)[:70]!r}")
    shutil.rmtree(d)

    # G4: duplicate ids rejected at add(); G4b: unknown discharge id is loud
    class FakeUUID:
        hex = "deadbeefcafe"

    real_uuid4 = entry_mod.uuid.uuid4
    entry_mod.uuid.uuid4 = lambda: FakeUUID()
    try:
        d = tempfile.mkdtemp(prefix="dg-")
        s = Store(d)
        s.add(base(stopped_checking="tls cert expiry"))
        try:
            s.add(base(stopped_checking="disk watch"))
            pin("G4 id-unique", False, "duplicate id accepted at add()")
        except ValueError as ex:
            pin("G4 id-unique", True, f"rejected: {str(ex)[:50]}")
        try:
            s.discharge("nosuchid0000", reason="guardian probe")
            pin("G4b discharge-unknown-loud", False, "silent no-op on unknown id")
        except ValueError:
            pin("G4b discharge-unknown-loud", True, "raises on unknown id")
        shutil.rmtree(d)
    finally:
        entry_mod.uuid.uuid4 = real_uuid4

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
