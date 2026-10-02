"""Q2A pins — optional qmr2-§8 attribution rows on export_qmr1.

FAIL-first: these pins existed before ledger/export.py learned the optional
`signer=` keyword. Cross-repo law is deliberately exercised against the real
SuperInstance/quilt-mcp-receipts v3 verifier, not a local reimplementation.
Set QMR_RECEIPTS_DIR to a checkout of that repo to run this file.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ledger.entry import Entry
from ledger.store import Store
from ledger.export import export_qmr1, qmr1_id, qmr1_sign, _entry_record  # noqa: E402
from ledger.sign import HAVE_CRYPTO  # noqa: E402

SECRET = "qmr2-attribution-pin-secret"
ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tests" / "qmr2_v3_helper.mjs"
QMR_DIR = os.environ.get("QMR_RECEIPTS_DIR")


def _keypair():
    if not HAVE_CRYPTO:
        raise RuntimeError("cryptography package required for Q2A pins")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return private_pem, public


def _store(tmp):
    store = Store(os.path.join(tmp, "ledger-dir"))
    store.add(Entry(stopped_checking="qmr2 attribution build",
                    because="sealed spec names cross-repo verification as load-bearing",
                    covered_by="docs/pre-registration-qmr2-attribution.md",
                    revisit_trigger="casey merges wave-4 build"))
    store.add(Entry(stopped_checking="body envelope drift",
                    because="qmr1 verifier requires body.kind and body.ts",
                    covered_by="README qmr1 naming alignment + qmr2-design §8",
                    revisit_trigger="quilt-mcp-receipts drifts §8",
                    kind="condition", expr="qmr2-dialect-drift"))
    return store


def _rows(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _fp(public_pem):
    return hashlib.sha256(public_pem).hexdigest()


def _run_qmr(rows_path, keyring=None):
    if not QMR_DIR:
        raise RuntimeError("set QMR_RECEIPTS_DIR to a quilt-mcp-receipts checkout")
    client = Path(QMR_DIR) / "test" / "mcp-client.mjs"
    if not client.exists():
        raise RuntimeError(f"mcp-client.mjs not found under {QMR_DIR}")
    cmd = ["node", str(HELPER), str(rows_path),
           json.dumps(keyring) if keyring is not None else "-", str(client)]
    proc = subprocess.run(cmd, cwd=QMR_DIR, text=True, capture_output=True,
                          timeout=30)
    if proc.returncode != 0:
        raise RuntimeError("qmr helper failed:\n" + proc.stderr[-2000:])
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _export_signed(tmp, signer):
    store = _store(tmp)
    out = os.path.join(tmp, "qmr2.jsonl")
    n = export_qmr1(store, lambda e: True, out, secret=SECRET, signer=signer)
    assert n == 2
    return store, out


def _qmr2_body(entry):
    rec = _entry_record(entry)
    return {"kind": entry.kind or "event", "ts": str(entry.ts),
            "id": rec["id"], "sum": rec["sum"], "entry": rec["entry"]}


def pin_q2a1_cross_repo_verification():
    private_pem, public_pem = _keypair()
    with tempfile.TemporaryDirectory() as tmp:
        store, out = _export_signed(tmp, private_pem)
        rows = _rows(out)
        fp = _fp(public_pem)
        assert all(r["sigAlg"] == "ed25519" for r in rows)
        assert all(r["sigKeyFp"] == fp for r in rows)
        assert all(len(r["sig"]) == 128 for r in rows)
        assert all(r["body"]["kind"] and r["body"]["ts"] for r in rows)
        assert rows[0]["body"]["entry"] == store.entries[0].to_dict()

        good = _run_qmr(out, {fp: public_pem.decode()})
        assert good["chain"]["ok"] is True, good
        assert good["attribution"]["ok"] is True, good
        report = good["attribution"]["attribution"]
        assert all(a["sigAlg"] == "ed25519" and a["signedBy"]["verified"] is True
                   and a["signedBy"]["source"] == "keyring"
                   and a["signedBy"]["fingerprint"] == fp
                   for a in report), report

        # No keyring: attribution is fail-closed, never anonymous-success.
        missing = _run_qmr(out)
        assert missing["chain"].get("error") == "E_UNKNOWN_SIGNER", missing

        # A forged sig behind the exported signer fingerprint is a signature
        # failure, not an unknown-signer escape hatch.
        forged_path = os.path.join(tmp, "forged.jsonl")
        forged = rows[:]
        forged[-1]["sig"] = forged[-1]["sig"][:-1] + (
            "0" if forged[-1]["sig"].endswith("1") else "1")
        with open(forged_path, "w") as f:
            for row in forged:
                f.write(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False) + "\n")
        forged_result = _run_qmr(forged_path, {fp: public_pem.decode()})
        assert forged_result["chain"].get("error") == "E_BAD_SIGNATURE", forged_result
    return "real verify_chain/verify_attribution GREEN; missing keyring E_UNKNOWN_SIGNER; forged sig E_BAD_SIGNATURE"


def pin_q2a2_fingerprint_law():
    private_pem, public_pem = _keypair()
    with tempfile.TemporaryDirectory() as tmp:
        _, out = _export_signed(tmp, private_pem)
        rows = _rows(out)
        want_fp = hashlib.sha256(public_pem).hexdigest()
        assert all(r["sigKeyFp"] == want_fp for r in rows)
        blob = Path(out).read_text()
        assert private_pem.decode().splitlines()[0] not in blob
    return "sigKeyFp = sha256(SPKI PEM), private key material absent"


def pin_q2a3_v1_regression():
    with tempfile.TemporaryDirectory() as tmp:
        store = _store(tmp)
        out = os.path.join(tmp, "v1.jsonl")
        n = export_qmr1(store, lambda e: True, out, secret=SECRET)
        assert n == 2
        rows = _rows(out)
        assert all(set(r) == {"seq", "prev", "body", "id", "sig"} for r in rows)
        assert all("sigAlg" not in r and "sigKeyFp" not in r for r in rows)
        prev = "0" * 64
        for seq, (row, entry) in enumerate(zip(rows, store.entries), start=1):
            body = _entry_record(entry)
            rid = qmr1_id(seq, prev, body)
            assert row["body"] == body
            assert row["id"] == rid
            assert row["sig"] == qmr1_sign(SECRET, rid)
            prev = rid
    return "signer=None remains byte-law qmr1 five-field HMAC rows"


def pin_q2a4_tamper_and_dev_secret():
    private_pem, public_pem = _keypair()
    fp = _fp(public_pem)
    with tempfile.TemporaryDirectory() as tmp:
        _, out = _export_signed(tmp, private_pem)
        rows = _rows(out)
        rows[0]["body"]["entry"]["because"] = "tampered after signing"
        tampered = os.path.join(tmp, "tampered.jsonl")
        with open(tampered, "w") as f:
            for row in rows:
                f.write(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False) + "\n")
        result = _run_qmr(tampered, {fp: public_pem.decode()})
        assert result["chain"].get("error") == "E_HASH_MISMATCH", result

        old_doubt = os.environ.pop("DOUBT_QMR1_SECRET", None)
        old_mcp = os.environ.pop("MCP_RECEIPT_SECRET", None)
        try:
            store = _store(tmp)
            try:
                export_qmr1(store, lambda e: True, os.path.join(tmp, "bad.jsonl"),
                            signer=private_pem)
            except ValueError:
                pass
            else:
                raise AssertionError("attribution export accepted the empty dev secret")
        finally:
            if old_doubt is not None:
                os.environ["DOUBT_QMR1_SECRET"] = old_doubt
            if old_mcp is not None:
                os.environ["MCP_RECEIPT_SECRET"] = old_mcp
    return "body tamper E_HASH_MISMATCH; empty dev secret refused"


PINS = [
    ("Q2A1", pin_q2a1_cross_repo_verification),
    ("Q2A2", pin_q2a2_fingerprint_law),
    ("Q2A3", pin_q2a3_v1_regression),
    ("Q2A4", pin_q2a4_tamper_and_dev_secret),
]

if __name__ == "__main__":
    failures = 0
    for name, pin in PINS:
        try:
            detail = pin()
        except Exception as e:  # noqa: BLE001 — pins must name their refusal
            failures += 1
            print(f"FAIL {name} — {type(e).__name__}: {e}")
        else:
            print(f"PASS {name} — {detail}")
    sys.exit(1 if failures else 0)
