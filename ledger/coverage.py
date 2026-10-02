"""Read-only coverage/discharge query tool over a ledger directory.

Spec: docs/pre-registration-coverage-tool.md (wave-4 candidate 2, SEALED).
The blindness-again class ("discharge requires a reason" — but a FILE can
carry an unreasoned discharge) made QUERYABLE, not just preventable.

    python3 -m ledger.coverage <ledger-dir> <query> [args...]

Queries: unreasoned | due <event> | covers <needle> | chain <entry-id>

Load-bearing promises (pinned by tests/pins_coverage.py, CV1-CV4):
- Read-only: the ledger file is opened "r" and never written (CV3 pins
  bytes AND per-line checksums unchanged).
- Reports what the file says: rows are parsed as raw JSON, NOT through
  Entry — the file can carry rows the runtime would refuse (that is the
  class this tool exists to name).
- Substring semantics (limit #5) are inherited from the store, not
  upgraded: covers/chain matches are over-match-capable and every match
  line is LABELED as a substring match.
"""
import json
import os
import sys

USAGE = ("usage: python3 -m ledger.coverage <ledger-dir> "
         "<unreasoned|due|covers|chain> [args...]")


def _load(ledger_dir):
    """Read raw records (id, sum, entry) without Store/Entry validation."""
    path = os.path.join(ledger_dir, "ledger.jsonl")
    recs = []
    if not os.path.exists(path):
        return path, recs
    with open(path, "r") as f:  # read-only is the promise (CV3)
        for line in f.read().splitlines():
            if not line.strip():
                continue
            recs.append(json.loads(line))
    return path, recs


def _unreasoned(recs):
    for rec in recs:
        e = rec.get("entry", {})
        if e.get("status") == "discharged":
            reason = e.get("discharge_reason")
            if reason is None or not str(reason).strip():
                print(rec.get("id"))


def _due(recs, event):
    for rec in recs:
        e = rec.get("entry", {})
        if e.get("status") == "open" and (
                e.get("revisit_trigger") == event or
                (e.get("kind") == "condition" and e.get("expr") == event)):
            print(rec.get("id"))


def _covers(recs, needle):
    for rec in recs:
        e = rec.get("entry", {})
        if e.get("status") in ("open", "due") and \
                needle in (e.get("covered_by") or ""):
            print(f"{rec.get('id')} covered_by="
                  f"{e.get('covered_by')!r} [substring match]")


def _chain(recs, entry_id):
    target = None
    for rec in recs:
        if rec.get("id") == entry_id:
            target = rec.get("entry", {})
            break
    if target is None:
        print(f"chain: no entry with id {entry_id}", file=sys.stderr)
        return 2
    covered_by = target.get("covered_by") or ""
    tokens = covered_by.split()
    for rec in recs:
        stopped = rec.get("entry", {}).get("stopped_checking") or ""
        for tok in tokens:
            if tok and tok in stopped:
                print(f"{rec.get('id')} stopped_checking={stopped!r} "
                      f"token={tok!r} [substring match]")
                break
    return 0


def main(argv):
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 2
    ledger_dir, query = argv[1], argv[2]
    _, recs = _load(ledger_dir)
    if query == "unreasoned":
        _unreasoned(recs)
        return 0
    if query == "due":
        if len(argv) < 4:
            print(USAGE, file=sys.stderr)
            return 2
        _due(recs, argv[3])
        return 0
    if query == "covers":
        if len(argv) < 4:
            print(USAGE, file=sys.stderr)
            return 2
        _covers(recs, argv[3])
        return 0
    if query == "chain":
        if len(argv) < 4:
            print(USAGE, file=sys.stderr)
            return 2
        return _chain(recs, argv[3])
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
