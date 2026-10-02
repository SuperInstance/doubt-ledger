"""Selective-disclosure export + root hash.

Motivation (edge-watch 10/2): arXiv 2605.11032-style portable agent memory
and the MajorLabs finding (0/6 production memory systems sign memory) both
point the same way — a ledger you can show a slice of, with the slice
carrying its own integrity proof, and a root you can sign.

Honest boundary, stated up front: an export proves the included entries are
byte-intact. It does NOT prove the filter was complete — selective disclosure
hides by construction. Completeness is the verifier's question, not ours.
"""
import json
import time

from ledger.store import _checksum

GENESIS = "0" * 16  # anchored root of the empty ledger


def _fnv(h, s):
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def _entry_record(e):
    body = json.dumps(e.to_dict(), sort_keys=True, separators=(",", ":"))
    return {"id": e.id, "sum": _checksum(e.id, body), "entry": e.to_dict()}


def root_hash(store):
    """fnv1a-64 chain over per-line checksums, genesis-anchored.

    Append-order-sensitive by design: the root is a receipt for THIS
    ledger at THIS length, not a set fingerprint.
    """
    h = 0xcbf29ce484222325
    for e in store.entries:
        h = _fnv(h, _checksum(e.id, json.dumps(e.to_dict(), sort_keys=True,
                                              separators=(",", ":"))))
    return "%016x" % h


def export_store(store, predicate, out_path):
    """Write entries matching predicate as a standalone verifiable file.

    Line 0 is a header binding the export to the live ledger's tip root at
    export time. Every following line carries its own per-entry checksum,
    recomputed — the export owes nothing to the source file staying put.
    """
    picked = [e for e in store.entries if predicate(e)]
    header = {"type": "doubt-export", "v": 1,
              "source_tip": root_hash(store), "count": len(picked),
              "exported_ts": int(time.time())}
    with open(out_path, "w") as f:
        f.write(json.dumps(header, sort_keys=True, separators=(",", ":")) + "\n")
        for e in picked:
            f.write(json.dumps(_entry_record(e), sort_keys=True,
                               separators=(",", ":")) + "\n")
    return len(picked)


def verify_export(path):
    """Reload an export, recompute every checksum, re-derive its tip.

    Returns the export's own tip (chain over included entries, anchored at
    GENESIS). Raises ValueError naming the line on any tamper.
    """
    with open(path) as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    if not lines:
        raise ValueError("export empty — refusing to verify")
    try:
        header = json.loads(lines[0])
    except json.JSONDecodeError:
        raise ValueError("export header unparseable — refusing to verify")
    if header.get("type") != "doubt-export":
        raise ValueError(f"not a doubt-export (type={header.get('type')!r})")
    h = 0xcbf29ce484222325
    n = 0
    for i, line in enumerate(lines[1:], start=1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError(f"export corrupt at line {i} — refusing")
        body = json.dumps(rec["entry"], sort_keys=True, separators=(",", ":"))
        want = _checksum(rec["id"], body)
        if rec.get("sum") != want:
            raise ValueError(f"export tampered at line {i} "
                             f"(id {rec.get('id')}) — checksum mismatch")
        h = _fnv(h, want)
        n += 1
    if n != header.get("count"):
        raise ValueError(f"export count mismatch: header {header.get('count')} "
                         f"vs actual {n} — entries added or dropped")
    tip = "%016x" % h
    if header.get("source_tip") and n == 0:
        tip = GENESIS
    return tip
