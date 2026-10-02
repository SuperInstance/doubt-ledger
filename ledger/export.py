"""Selective-disclosure export + root hash.

Motivation (edge-watch 10/2): arXiv 2605.11032-style portable agent memory
and the MajorLabs finding (0/6 production memory systems sign memory) both
point the same way — a ledger you can show a slice of, with the slice
carrying its own integrity proof, and a root you can sign.

Honest boundary, stated up front: an export proves the included entries are
byte-intact. It does NOT prove the filter was complete — selective disclosure
hides by construction. Completeness is the verifier's question, not ours.
"""
import hashlib
import hmac as hmac_mod
import json
import os
import sys
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


# --- qmr1-compatible receipt export (wave-3 naming-alignment hedge) --------
#
# Consumes, doesn't rival: SuperInstance/quilt-mcp-receipts (Casey, spike v1)
# minted dialect `qmr1` — the fleet receipt chain as a signed append-only
# MCP organ. Our wave-2 export carries the same discipline with different
# names; rather than fork the dialect, export_qmr1() emits byte-compatible
# qmr1 lines so any qmr1 reader/verifier can consume doubt-ledger exports.
# Cheap naming alignment, the same hedge direction as IETF
# draft-sharif-agent-audit-trail-05 (JCS-canonical SHA-256 chain) — one
# dialect family, not three.
#
# Spec (re-derived from quilt-mcp-receipts DESIGN.md §2, not from its code):
#   id  = SHA-256("qmr1:" + seq + ":" + prev + ":" + canonicalJSON(body))
#   sig = HMAC-SHA256(secret, "qmr1:sig:" + id)
# canonicalJSON = recursive key-sorted, no-whitespace; arrays keep order.

GENESIS_PREV_QMR1 = "0" * 64


def _canonical(body):
    # ensure_ascii=False: JS JSON.stringify (the qmr1 reference
    # canonicalJSON) emits raw UTF-8, not \uXXXX escapes — match it.
    # Honest limit (README): ASCII string/int bodies are byte-exact
    # dialect-compatible; non-ASCII text and floats are the divergence
    # class (escape policy / float repr), kept out of qmr1 bodies here.
    return json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def qmr1_id(seq, prev, body):
    return hashlib.sha256(
        ("qmr1:%d:%s:%s" % (seq, prev, _canonical(body))).encode()
    ).hexdigest()


def qmr1_sign(secret, rid):
    return hmac_mod.new(secret.encode(), ("qmr1:sig:" + rid).encode(),
                        hashlib.sha256).hexdigest()


def _qmr1_secret(secret):
    """Resolve the HMAC secret. Explicit arg wins; else env
    DOUBT_QMR1_SECRET / MCP_RECEIPT_SECRET (same variable the qmr1
    organ reads). The empty-key fallback keeps the export runnable but
    is honestly flagged in the README — an unsigned-looking sig is a
    documented dev mode, never presented as seal."""
    if secret is not None:
        return secret
    env = os.environ.get("DOUBT_QMR1_SECRET") or \
        os.environ.get("MCP_RECEIPT_SECRET")
    if env:
        return env
    sys.stderr.write(
        "doubt-ledger: qmr1 export with EMPTY dev secret — "
        "set DOUBT_QMR1_SECRET (or MCP_RECEIPT_SECRET) for a real seal\n")
    return ""


def export_qmr1(store, predicate, out_path, secret=None):
    """Write entries matching predicate as a qmr1-compatible receipt chain.

    Each line is exactly the five qmr1 fields (seq, prev, body, id, sig);
    body = our entry record, so every byte of the export owes nothing to
    the source file. Returns the number of receipts written. Re-serialized
    or key-reordered lines still verify — only value edits break the id."""
    picked = [e for e in store.entries if predicate(e)]
    secret = _qmr1_secret(secret)
    prev = GENESIS_PREV_QMR1
    with open(out_path, "w") as f:
        for seq, e in enumerate(picked, start=1):
            body = _entry_record(e)
            rid = qmr1_id(seq, prev, body)
            row = {"seq": seq, "prev": prev, "body": body,
                   "id": rid, "sig": qmr1_sign(secret, rid)}
            f.write(_canonical(row) + "\n")
            prev = rid
    return len(picked)


def verify_qmr1(path, secret=None):
    """Re-derive every qmr1 id/sig from genesis. Raises ValueError naming
    the offending line on any mismatch; returns the receipt count."""
    secret = _qmr1_secret(secret)
    prev = GENESIS_PREV_QMR1
    n = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            row = json.loads(line)
            if set(row) != {"seq", "prev", "body", "id", "sig"}:
                raise ValueError("line %d: not exactly the five qmr1 fields" % n)
            if row["seq"] != n:
                raise ValueError("line %d: seq %s != expected %d" % (n, row["seq"], n))
            if row["prev"] != prev:
                raise ValueError("line %d: prev does not match chain tip" % n)
            want_id = qmr1_id(n, prev, row["body"])
            if row["id"] != want_id:
                raise ValueError("line %d: id mismatch (body or linkage edited)" % n)
            if row["sig"] != qmr1_sign(secret, row["id"]):
                raise ValueError("line %d: sig mismatch (wrong secret or edited id)" % n)
            prev = row["id"]
    return n


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
