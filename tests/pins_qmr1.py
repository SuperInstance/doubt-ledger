"""Wave-3 pins: qmr1-compatible receipt export (naming-alignment hedge).

FAIL-first culture: run this on a tree WITHOUT export_qmr1 and every pin
must be RED. pins/failfirst-wave3.log holds that receipt.

qmr1 dialect (SuperInstance/quilt-mcp-receipts, spike v1):
  id  = SHA-256("qmr1:" + seq + ":" + prev + ":" + canonicalJSON(body))
  sig = HMAC-SHA256(secret, "qmr1:sig:" + id)
canonicalJSON = recursive key-sorted, no-whitespace (arrays keep order).
"""
import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

results = []


def pin(name, fn):
    try:
        detail = fn()
        results.append(("PASS", name, detail))
    except Exception as e:  # noqa: BLE001 — a pin failure is a receipt, not a crash
        results.append(("FAIL", name, f"{type(e).__name__}: {e}"))


from ledger.entry import Entry  # noqa: E402
from ledger.store import Store  # noqa: E402
from ledger.export import export_qmr1, verify_qmr1, qmr1_id  # noqa: E402


def canon(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def independent_id(seq, prev, body):
    return hashlib.sha256(
        ("qmr1:%d:%s:%s" % (seq, prev, canon(body))).encode()).hexdigest()


def independent_sig(secret, rid):
    return hmac.new(secret.encode(), ("qmr1:sig:" + rid).encode(),
                    hashlib.sha256).hexdigest()


SECRET = "pin-secret-not-for-production"


def build_store(tmp):
    path = os.path.join(tmp, "doubt.jsonl")
    s = Store(path)
    e1 = Entry(stopped_checking="nightly-ci", because="migrated to guardian lane",
               covered_by="guardian receipts", revisit_trigger="guardian silent 3d")
    e2 = Entry(stopped_checking="manual audit", because="low churn",
               covered_by="pinned suite", revisit_trigger="suite red")
    s.add(e1)
    s.add(e2)
    return s, e1, e2


def Q1_id_derivation():
    body = {"kind": "test.body", "n": 1}
    got = qmr1_id(1, "0" * 64, body)
    want = independent_id(1, "0" * 64, body)
    assert got == want, "own id %s != independent %s" % (got, want)
    # canonical binding: key ORDER in the input dict must not matter
    body2 = {"n": 1, "kind": "test.body"}
    assert qmr1_id(1, "0" * 64, body2) == want, "key order changed the id"
    return "independent recompute matches; key-order invariant"


def Q2_chain_roundtrip():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        s, _, _ = build_store(tmp)
        out = os.path.join(tmp, "export.qmr1.jsonl")
        n = export_qmr1(s, lambda e: True, out, secret=SECRET)
        assert n == 2
        assert verify_qmr1(out, secret=SECRET) == 2
        rows = [json.loads(l) for l in open(out)]
        assert rows[0]["prev"] == "0" * 64 and rows[0]["seq"] == 1
        assert rows[1]["prev"] == rows[0]["id"] and rows[1]["seq"] == 2
        for r in rows:
            assert r["sig"] == independent_sig(SECRET, r["id"]), "sig mismatch"
        return "2 rows, linkage ok, sigs independently recomputed"


def Q3_tamper_refused():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        s, _, _ = build_store(tmp)
        out = os.path.join(tmp, "export.qmr1.jsonl")
        export_qmr1(s, lambda e: True, out, secret=SECRET)
        lines = open(out).read().splitlines()
        row = json.loads(lines[1])
        row["body"]["entry"]["because"] = "quietly edited"  # value edit
        lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
        open(out, "w").write("\n".join(lines) + "\n")
        try:
            verify_qmr1(out, secret=SECRET)
        except ValueError as e:
            assert "2" in str(e), "tamper must be named by line: %s" % e
            return "value edit caught, named by line"
        raise AssertionError("tampered qmr1 chain verified clean")


def Q4_wrong_secret_refused():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        s, _, _ = build_store(tmp)
        out = os.path.join(tmp, "export.qmr1.jsonl")
        export_qmr1(s, lambda e: True, out, secret=SECRET)
        try:
            verify_qmr1(out, secret="attacker-secret")
        except ValueError:
            return "HMAC mismatch refused"
        raise AssertionError("wrong secret verified clean")


for p in (Q1_id_derivation, Q2_chain_roundtrip, Q3_tamper_refused,
          Q4_wrong_secret_refused):
    pin(p.__name__, p)

for status, name, detail in results:
    print("%s %s — %s" % (status, name, detail))
sys.exit(0 if all(r[0] == "PASS" for r in results) else 1)
