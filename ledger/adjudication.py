"""Adjudication-client: quilt-adjudication record -> doubt-ledger entry.

Spec: docs/pre-registration-adjudication-client.md (wave-4 candidate 3,
SEALED, PR #15). A refused merge already wrote the dispute down; what it
cannot express is who stopped checking which question because that record
exists. This client is the grammar adapter between the two shapes — and
refuses, by construction, to ever write the winner down as the truth.

    python3 -m ledger.adjudication RECORD.json|DIR [--ledger PATH] [--emit-only]

Given one adjudication record, emit exactly one ledger entry. A directory
(.quilt/adjudications/) is scanned for *.json records; absent/empty is a
healthy answer (AC4): exit 0, zero entries, message on stdout.

Load-bearing promises (pinned by tests/pins_adjudication.py, AC1-AC4):
- Read-only: the record file is opened "r" and never written (AC3 pins
  fixture bytes AND emitted-entry line checksums across a re-run).
- The winner is cited, never adopted: no winner VALUE appears anywhere in
  the emitted entry (AC2).
- KS1 schema drift: judge / both-claims-verbatim / reversal command absent
  or reshaped -> E_SCHEMA_DRIFT, emit nothing, name the field.
- KS2 judge landed: a judge field naming a model -> E_JUDGE_LANDED, emit
  nothing, the spec is re-opened — never silently inherit the no-judge gloss.
"""
import json
import os
import sys

E_SCHEMA_DRIFT = 3
E_JUDGE_LANDED = 4
E_MULTI_CONFLICT = 5

USAGE = ("usage: python3 -m ledger.adjudication RECORD.json|DIR "
         "[--ledger PATH] [--emit-only]")


def _fail(code, msg):
    print(msg, file=sys.stderr)
    return code


def _check_schema(record, src):
    """KS1: the three load-bearing fields, named on refusal."""
    if not isinstance(record, dict):
        return f"{src}: not a JSON object"
    judge = record.get("judge")
    if judge is None:
        return f"{src}: missing field judge"
    if not isinstance(judge, str) or not judge.startswith("none"):
        return f"E_JUDGE_LANDED: {src} judge field names a model "
    conflicts = record.get("conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        return f"{src}: missing field conflicts (non-empty list)"
    for i, c in enumerate(conflicts):
        if not isinstance(c, dict):
            return f"{src}: conflicts[{i}] not an object"
        if not isinstance(c.get("winner"), dict) or \
                not c["winner"].get("line"):
            return f"{src}: conflicts[{i}] missing winner.line "
        losers = c.get("losers")
        if not isinstance(losers, list) or not losers or \
                any(not isinstance(l, dict) or not l.get("line")
                    for l in losers):
            return f"{src}: conflicts[{i}] losers not verbatim-carrying"
        if not c.get("to_accept_the_loser"):
            return f"{src}: conflicts[{i}] missing to_accept_the_loser"
    return None


def build_entry(record, record_path, entry_id=None, ts=None):
    """One record -> one entry dict. Winner cited, never adopted (AC2)."""
    from ledger.entry import Entry
    short = record.get("short") or os.path.basename(record_path)
    conflicts = record["conflicts"]
    if len(conflicts) != 1:
        raise ValueError(
            f"E_MULTI_CONFLICT: record {short} carries {len(conflicts)} "
            f"conflicts; v0 emits exactly one entry per record")
    c = conflicts[0]
    n_claimants = 1 + len(c["losers"])
    key = c["key"]
    stopped = (f"which claim is true for key {key} "
               f"({n_claimants} claimants)")
    because = (f"adjudication record {short} exists — mechanical ordering, "
               f"no judge ran; record reason: {c['reason']!r}")
    covered_by = [record_path,
                  f"quilt-query divergence {record.get('head_before', '?')} "
                  f"{record.get('merge_head', '?')} (advisory)"]
    revisit = (f"{c['to_accept_the_loser']} "
               f"OR new evidence for a losing claim")
    reason = (f"question discharged by recorded adjudication {short}; "
              f"pending reversal command or new evidence for a losing claim")
    e = Entry(stopped_checking=stopped, because=because,
              covered_by=covered_by, revisit_trigger=revisit,
              kind="discharge", discharge_reason=reason, id=entry_id, ts=ts)
    return e.to_dict()


def _records(path):
    """Yield (record, record_path). Dir -> sorted *.json; file -> one."""
    if os.path.isdir(path):
        names = sorted(n for n in os.listdir(path) if n.endswith(".json"))
        for n in names:
            p = os.path.join(path, n)
            with open(p, "r") as f:  # read-only is the promise (AC3)
                yield json.load(f), p
    else:
        with open(path, "r") as f:
            yield json.load(f), path


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    emit_only = "--emit-only" in argv[1:]
    ledger_path = None
    if "--ledger" in argv[1:]:
        i = argv[1:].index("--ledger")
        try:
            ledger_path = argv[1:][i + 1]
        except IndexError:
            print(USAGE, file=sys.stderr)
            return 2
    if len(args) < 1:
        print(USAGE, file=sys.stderr)
        return 2
    path = args[0]
    if not os.path.exists(path) or (os.path.isdir(path)
                                    and not os.listdir(path)):
        print(f"adjudication-client: no records under {path} — "
              f"zero entries, nothing to discharge")
        return 0
    store = None
    if ledger_path and not emit_only:
        from ledger.store import Store
        store = Store(ledger_path)
    n = 0
    for record, rp in _records(path):
        err = _check_schema(record, rp)
        if err:
            return _fail(E_JUDGE_LANDED if err.startswith("E_JUDGE_LANDED")
                         else E_SCHEMA_DRIFT, err)
        try:
            d = build_entry(record, rp)
        except ValueError as e:
            if str(e).startswith("E_MULTI_CONFLICT"):
                return _fail(E_MULTI_CONFLICT, str(e))
            raise
        if store is not None:
            from ledger.entry import Entry
            store.add(Entry(**d))
        print(json.dumps(d, sort_keys=True))
        n += 1
    if n == 0:
        print(f"adjudication-client: zero records — zero entries")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
