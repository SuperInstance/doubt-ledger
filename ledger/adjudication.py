"""Adjudication-client: .quilt/adjudications/<short>.json -> discharge entries.

Spec: docs/pre-registration-adjudication-client.md (wave-4 candidate 3,
SEALED, PR #15). Grammar adapter only — this client adds no adjudication
logic of its own. It turns a quilt-adjudication refused-merge record into
doubt-ledger discharge entries, and refuses, by construction, to ever write
the winner down as the truth.

    python3 -m ledger.adjudication RECORD-or-DIR [--ledger PATH] [--emit-only]

PATH may be one record JSON or a directory of them (every *.json inside,
sorted). Default ledger dir is ./ledger; --emit-only prints entry JSON
without writing anything.

Load-bearing promises (pinned by tests/pins_adjudication.py, AC1-AC4):
- The winner is cited, never adopted: no claimant VALUE appears in any
  emitted field — stopped_checking names the key and claimant count only.
- Read-only is the promise (AC3): record files are opened "r" and never
  written; each emitted entry is a pure function of the record bytes
  (deterministic id from short|key, ts from the record), so re-runs are
  byte-identical.
- One entry per CONFLICT the record wrote down. The sealed spec table maps
  one record to one entry; the upstream generator allows several conflicts
  (distinct keys, reasons, reversal commands) per record, and folding them
  would mix grammars — so v0 emits one entry per conflict, and the
  single-conflict case (the common one) is exactly the sealed mapping.
- Ordering asymmetry disclosure (honest boundary #5): `because` carries the
  record's own ordering language verbatim ("mechanical ordering, no judge
  ran" + the record's quoted reason), so no later reader can mistake the
  temporal winner for evidential weight.
- Coverage cross-reference is substring-based and advisory (limit #5); the
  quilt-query divergence mention in covered_by is a pointer for a human,
  not a verified dependency (honest boundary #3).
- Receipted != true, cited != adjudicated (honest boundary #2): the entry
  is a claim until this ledger's own chain verifies it.

Kill switches (sealed in the spec):
- KS1 schema drift: a load-bearing field absent or reshaped -> E_SCHEMA_DRIFT,
  nothing emitted, the missing field named. Corrections append to the spec,
  never silent edit.
- KS2 judge landed: the judge field ever names a model -> emit nothing; a
  judging record is a different animal from a mechanical one.
"""
import hashlib
import json
import os
import sys

USAGE = ("usage: python3 -m ledger.adjudication RECORD.json|DIR "
         "[--ledger PATH] [--emit-only]")

NO_JUDGE = "none — no model is in this loop, by design"


def _schema_drift(rec):
    """Return the name of the first missing/reshaped load-bearing field."""
    if not isinstance(rec.get("judge"), str) or not rec["judge"].strip():
        return "judge"
    conflicts = rec.get("conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        return "conflicts"
    for i, c in enumerate(conflicts):
        if not isinstance(c, dict):
            return f"conflicts[{i}]"
        for field in ("key", "reason", "to_accept_the_loser"):
            if not isinstance(c.get(field), str) or not c[field].strip():
                return f"conflicts[{i}].{field}"
        winner = c.get("winner")
        if not isinstance(winner, dict) or \
                not str(winner.get("value", "")).strip() or \
                not str(winner.get("by", "")).strip() or \
                not str(winner.get("line", "")).strip():
            return f"conflicts[{i}].winner"
        losers = c.get("losers")
        if not isinstance(losers, list) or not losers:
            return f"conflicts[{i}].losers"
        for j, l in enumerate(losers):
            if not isinstance(l, dict) or \
                    not str(l.get("value", "")).strip() or \
                    not str(l.get("by", "")).strip() or \
                    not str(l.get("line", "")).strip():
                return f"conflicts[{i}].losers[{j}]"
    for ref in ("head_before", "merge_head"):
        if not str(rec.get(ref, "")).strip():
            return ref
    return None


def _entries_from_record(rec):
    """Pure function of the record: one discharge entry per conflict."""
    short = str(rec.get("short") or "unknown")
    ts = int(rec.get("ts") or 0)
    head = str(rec.get("head_before"))
    merge = str(rec.get("merge_head"))
    out = []
    for c in rec["conflicts"]:
        claimants = 1 + len(c["losers"])
        noun = "claimant" if claimants == 1 else "claimants"
        entry_id = hashlib.sha256(
            f"{short}|{c['key']}".encode()).hexdigest()[:12]
        out.append({
            "id": entry_id,
            "ts": ts,
            "stopped_checking":
                f"which claim is true for key {c['key']} "
                f"({claimants} {noun})",
            "because":
                f"adjudication record {short} exists — mechanical ordering, "
                f"no judge ran: \"{c['reason']}\"",
            "covered_by":
                f".quilt/adjudications/{short}.json; "
                f"quilt-query divergence {head} {merge} (advisory)",
            "revisit_trigger":
                f"{c['to_accept_the_loser']} OR new evidence for a "
                f"losing claim",
            "kind": "discharge",
            "expr": None,
            "status": "discharged",
            "discharge_reason":
                "discharged because the adjudication record exists and is "
                "cited in covered_by; mechanical ordering only — the winner "
                "is cited as an ordering, never adopted as truth",
        })
    return out


def _record_paths(path):
    if os.path.isdir(path):
        try:
            names = sorted(os.listdir(path))
        except OSError:
            return []
        return [os.path.join(path, n) for n in names if n.endswith(".json")
                and os.path.isfile(os.path.join(path, n))]
    if os.path.isfile(path):
        return [path]
    return []


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    emit_only = "--emit-only" in argv[1:]
    ledger_arg = None
    if "--ledger" in argv[1:]:
        i = argv[1:].index("--ledger")
        try:
            ledger_arg = argv[1:][i + 1]
        except IndexError:
            print(USAGE, file=sys.stderr)
            return 2
    if not args:
        print(USAGE, file=sys.stderr)
        return 2

    paths = _record_paths(args[0])
    if not paths:
        print("no adjudication records found — healthy answer "
              "(zero disputes, zero entries)")
        return 0

    emitted = []
    for p in paths:
        with open(p, "r") as f:  # read-only is the promise (AC3)
            rec = json.load(f)
        missing = _schema_drift(rec)
        if missing:
            print(f"E_SCHEMA_DRIFT: record {os.path.basename(p)} missing "
                  f"load-bearing field: {missing}", file=sys.stderr)
            return 3
        if rec["judge"].strip() != NO_JUDGE:
            print(f"E_JUDGE_LANDED: record {os.path.basename(p)} judge field "
                  f"names a judge ({rec['judge']!r}) — a judging record is a "
                  f"different animal; v0 emits nothing for it",
                  file=sys.stderr)
            return 4
        emitted.extend(_entries_from_record(rec))

    if emit_only:
        for e in emitted:
            print(json.dumps(e, sort_keys=True, separators=(",", ":")))
        return 0

    from ledger.store import Store
    store = Store(ledger_arg or "ledger")
    for e in emitted:
        from ledger.entry import Entry
        try:
            store.add(Entry(**e))
            print(f"recorded: {e['id']} — {e['stopped_checking']}")
        except ValueError as ex:
            if "duplicate" in str(ex):
                print(f"already recorded: {e['id']}")
            else:
                raise
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
