#!/usr/bin/env python3
"""PINS AC1-AC4 for ledger/adjudication.py (wave-4 candidate 3 build).

Spec: docs/pre-registration-adjudication-client.md (PR #15, SEALED). These
pins are defined in that doc and are not movable. FAIL-first: run against a
tree with no ledger/adjudication.py -> RED 4/4, receipt in
pins/failfirst-adjudication.log.

Also exercises the two sealed kill switches (KS1 schema drift, KS2 judge
landed) — required behavior sealed in the spec's Kill switches section,
labeled below as KS1/KS2 (not new ACs).
"""
import os, sys, json, tempfile, shutil, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

results = []
def pin(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))

try:
    import ledger.adjudication  # noqa: F401
    ADJ = True
except ModuleNotFoundError as e:
    ADJ = False
    os.makedirs(os.path.join(ROOT, "pins"), exist_ok=True)
    with open(os.path.join(ROOT, "pins", "failfirst-adjudication.log"), "w") as f:
        f.write(f"FAIL-first: ledger/adjudication.py absent — {e}\n")

from ledger.store import _checksum

NO_JUDGE = "none — no model is in this loop, by design"

RECORD = {
    "kind": "adjudication",
    "refused": "commit",
    "named_by": "merge commit",
    "short": "177f885",
    "tree": "abc1234",
    "head_before": "1111111",
    "merge_head": "2222222",
    "ts": 1727900000,
    "adjudication": "mechanical",
    "judge": NO_JUDGE,
    "rule": "winner is the claim that arrived on the side being merged; "
            "this is an ordering, not a judgment about truth",
    "conflicts": [
        {
            "key": "inbound_edges",
            "cell": "cells/inbox/body",
            "winner": {"value": "21", "by": "quilt-tools#33 0101409",
                       "side": "incoming",
                       "line": "claim: inbound_edges = 21  by quilt-tools#33 0101409"},
            "losers": [
                {"value": "19", "by": "quilt-tools#32 fb2e041", "side": "base",
                 "line": "claim: inbound_edges = 19  by quilt-tools#32 fb2e041"}
            ],
            "reason": "two attributed claims for key inbound_edges carry "
                      "different values; the record names the incoming claim "
                      "as winner so the merge has one surviving line, and "
                      "keeps the other verbatim. No judge was consulted and "
                      "no model ran.",
            "to_accept_the_loser": "git checkout HEAD -- cells/inbox/body && git commit",
        }
    ],
}


def write_record(dirpath, rec):
    os.makedirs(dirpath, exist_ok=True)
    path = os.path.join(dirpath, rec["short"] + ".json")
    with open(path, "w") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    return path


def run_adj(path, *args):
    return subprocess.run(
        [sys.executable, "-m", "ledger.adjudication", path, *args],
        capture_output=True, text=True, cwd=ROOT)


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def entry_texts(e):
    return {k: str(e.get(k) or "") for k in
            ("stopped_checking", "because", "revisit_trigger", "discharge_reason")}


def main():
    if not ADJ:
        for p in ["AC1", "AC2", "AC3", "AC4"]:
            pin(p, False, "ledger.adjudication not importable")
        return 1

    tmp = tempfile.mkdtemp(prefix="adj-pins-")
    try:
        recdir = os.path.join(tmp, "adjudications")
        recpath = write_record(recdir, RECORD)

        # AC1: planted-record round-trip.
        r = run_adj(recpath, "--emit-only")
        try:
            entries = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
        except json.JSONDecodeError:
            entries = []
        pin("AC1", r.returncode == 0 and len(entries) == 1,
            f"exit={r.returncode} entries={len(entries)}")
        if entries:
            e = entries[0]
            pin("AC1 stopped_checking names key + claimant count, no value "
                "as true",
                e.get("stopped_checking") ==
                "which claim is true for key inbound_edges (2 claimants)",
                repr(e.get("stopped_checking")))
            txt = entry_texts(e)
            pin("AC1 no claimant value appears in any entry field "
                "(cited-never-adopted)",
                all("21" not in v and "19" not in v for v in txt.values()))
            pin("AC1 covered_by cites the record file first + advisory query",
                ".quilt/adjudications/177f885.json" in str(e.get("covered_by") or "")
                and "quilt-query divergence 1111111 2222222 (advisory)"
                in str(e.get("covered_by") or ""),
                repr(e.get("covered_by")))
            pin("AC1 because quotes the record's own reason",
                "mechanical ordering, no judge ran" in txt["because"]
                and "No judge was consulted and no model ran."
                in txt["because"])
            pin("AC1 revisit_trigger carries the reversal command verbatim",
                "git checkout HEAD -- cells/inbox/body && git commit"
                in txt["revisit_trigger"]
                and "OR new evidence for a losing claim"
                in txt["revisit_trigger"])
            pin("AC1 kind=discharge, discharge_reason non-empty",
                e.get("kind") == "discharge"
                and bool(str(e.get("discharge_reason") or "").strip()),
                f"kind={e.get('kind')!r}")

        # AC2: winner != truth (load-bearing).
        swapped = json.loads(json.dumps(RECORD))
        c = swapped["conflicts"][0]
        c["winner"], c["losers"] = (
            {"value": "19", "by": "quilt-tools#32 fb2e041", "side": "incoming",
             "line": "claim: inbound_edges = 19  by quilt-tools#32 fb2e041"},
            [{"value": "21", "by": "quilt-tools#33 0101409", "side": "base",
              "line": "claim: inbound_edges = 21  by quilt-tools#33 0101409"}])
        swapped_path = write_record(recdir, swapped)
        r2 = run_adj(swapped_path, "--emit-only")
        entries2 = [json.loads(l) for l in r2.stdout.splitlines() if l.strip()]
        pin("AC2 swapped-winner record emits", r2.returncode == 0
            and len(entries2) == 1, f"exit={r2.returncode}")
        if entries2:
            e2 = entries2[0]
            txt2 = entry_texts(e2)
            pin("AC2 new winner's value NOWHERE outside the record citation "
                "(cited, never adopted)",
                all("19" not in v for v in txt2.values()))
            pin("AC2 record file still cited in covered_by",
                ".quilt/adjudications/177f885.json"
                in str(e2.get("covered_by") or ""))
            pin("AC2 question unchanged by who won (ordering is not judgment)",
                e2.get("stopped_checking") ==
                "which claim is true for key inbound_edges (2 claimants)",
                repr(e2.get("stopped_checking")))

        # AC3: byte-identity (read-only is the promise).
        before = sha256(recpath)
        r3a = run_adj(recpath, "--emit-only")
        r3b = run_adj(recpath, "--emit-only")
        after = sha256(recpath)
        out_a, out_b = r3a.stdout.strip(), r3b.stdout.strip()
        pin("AC3 record file bytes unchanged across re-runs", before == after,
            f"sha256 before={before[:12]} after={after[:12]}")
        pin("AC3 emitted entry byte-identical across re-runs",
            out_a == out_b and out_a != "",
            f"run1={len(out_a)}B run2={len(out_b)}B")
        if out_a:
            ea = json.loads(out_a)
            body_a = json.dumps(ea, sort_keys=True, separators=(",", ":"))
            eb = json.loads(out_b)
            body_b = json.dumps(eb, sort_keys=True, separators=(",", ":"))
            pin("AC3 emitted entry fnv1a-64 line checksum unchanged across "
                "re-run", _checksum(ea["id"], body_a) ==
                _checksum(eb["id"], body_b), _checksum(ea["id"], body_a))
            pin("AC3 entry is a pure function of the record (deterministic "
                "id, record ts)", ea.get("id") == eb.get("id")
                and ea.get("ts") == 1727900000, f"id={ea.get('id')}")

        # AC4: zero-disputes healthy answer.
        emptydir = os.path.join(tmp, "empty")
        os.makedirs(emptydir)
        r4a = run_adj(emptydir, "--emit-only")
        r4b = run_adj(os.path.join(tmp, "no-such-dir"), "--emit-only")
        pin("AC4 empty adjudications dir -> exit 0, zero entries, message",
            r4a.returncode == 0 and r4a.stdout.strip() != ""
            and "healthy" in r4a.stdout.lower(),
            f"exit={r4a.returncode} out={r4a.stdout.strip()!r}"[:120])
        pin("AC4 absent adjudications dir -> exit 0, healthy answer not error",
            r4b.returncode == 0 and "healthy" in r4b.stdout.lower(),
            f"exit={r4b.returncode} out={r4b.stdout.strip()!r}"[:120])

        # KS1: schema drift -> E_SCHEMA_DRIFT, emit nothing, name the field.
        for kill_field in ("judge", "conflicts",
                           "conflicts[0].to_accept_the_loser"):
            drifted = json.loads(json.dumps(RECORD))
            if kill_field == "conflicts":
                drifted["conflicts"] = []
            elif kill_field == "judge":
                del drifted["judge"]
            else:
                del drifted["conflicts"][0]["to_accept_the_loser"]
            dp = write_record(recdir, drifted)
            rd = run_adj(dp, "--emit-only")
            short = kill_field.split(".")[-1]
            pin(f"KS1 missing '{kill_field}' -> E_SCHEMA_DRIFT, nothing "
                "emitted, field named",
                rd.returncode != 0 and "E_SCHEMA_DRIFT" in rd.stderr
                and rd.stdout.strip() == "" and short in rd.stderr,
                f"exit={rd.returncode} err={rd.stderr.strip()[:80]!r}")

        # KS2: judge landed -> emit nothing.
        judged = json.loads(json.dumps(RECORD))
        judged["judge"] = "gpt-5"
        jp = write_record(recdir, judged)
        rj = run_adj(jp, "--emit-only")
        pin("KS2 judge names a model -> emit nothing",
            rj.returncode != 0 and rj.stdout.strip() == ""
            and "judge" in rj.stderr.lower(),
            f"exit={rj.returncode} err={rj.stderr.strip()[:80]!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print(f"{sum(results)}/{len(results)} pins "
          f"{'PASS' if all(results) else 'FAIL'}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
