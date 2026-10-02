"""Wave-2 pins: selective-disclosure export + root signing.

FAIL-first culture: run this on a tree WITHOUT ledger/export.py /
ledger/sign.py and every pin must be RED. pins/failfirst-wave2.log holds
that receipt.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

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


def _mk(path, **kw):
    base = dict(stopped_checking="s", because="b", covered_by="c",
                revisit_trigger="r")
    base.update(kw)
    return Entry(**base)


def _seed(tmp):
    s = Store(tmp)
    s.add(_mk(tmp, stopped_checking="pr-93 review", covered_by="builder pins"))
    s.add(_mk(tmp, stopped_checking="ci green run", covered_by="ci log 88"))
    s.add(_mk(tmp, stopped_checking="deps audit", covered_by="builder pins"))
    return s


def p_export_selective():
    from ledger.export import export_store
    tmp = tempfile.mkdtemp()
    try:
        s = _seed(tmp)
        out = os.path.join(tmp, "exp.jsonl")
        n = export_store(s, lambda e: "builder pins" in e.covered_by, out)
        lines = [json.loads(l) for l in open(out) if l.strip()]
        hdr = lines[0]
        got = [l["entry"]["stopped_checking"] for l in lines[1:]]
        assert hdr["type"] == "doubt-export", f"bad header {hdr.get('type')}"
        assert n == 2 and len(got) == 2, f"want 2 got n={n} entries={got}"
        assert all("builder pins" in l["entry"]["covered_by"] for l in lines[1:]), \
            "non-matching entry leaked into export"
        assert not any("ci green" in g for g in got), "filter did not select"
        return f"n={n} tip={hdr['source_tip'][:12]}…"
    finally:
        shutil.rmtree(tmp)


def p_export_verify():
    from ledger.export import export_store, verify_export, root_hash
    tmp = tempfile.mkdtemp()
    try:
        s = _seed(tmp)
        out = os.path.join(tmp, "exp.jsonl")
        export_store(s, lambda e: True, out)
        tip = verify_export(out)
        want = root_hash(s)
        assert tip == want, f"export tip {tip} != live root {want}"
        return f"tip={tip[:12]}…"
    finally:
        shutil.rmtree(tmp)


def p_export_tamper():
    from ledger.export import export_store, verify_export
    tmp = tempfile.mkdtemp()
    try:
        s = _seed(tmp)
        out = os.path.join(tmp, "exp.jsonl")
        export_store(s, lambda e: True, out)
        lines = open(out).read().splitlines()
        rec = json.loads(lines[1])
        rec["entry"]["because"] = "rewritten after export"
        lines[1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        open(out, "w").write("\n".join(lines) + "\n")
        try:
            verify_export(out)
        except ValueError as e:
            assert "line 1" in str(e), f"tamper error must name the line: {e}"
            return f"refused: {e}"
        raise AssertionError("tampered export verified clean — canary cannot fail")
    finally:
        shutil.rmtree(tmp)


def p_root_covers_all():
    from ledger.export import root_hash
    tmp = tempfile.mkdtemp()
    try:
        s = _seed(tmp)
        before = root_hash(s)
        s.add(_mk(tmp, stopped_checking="new doubt", covered_by="x"))
        after = root_hash(s)
        assert before != after, "root did not move on append — root is decorative"
        tmp2 = tempfile.mkdtemp()
        try:
            s2 = Store(tmp2)
            s2.add(_mk(tmp2))
            assert root_hash(s2) != before, "different ledger, same root"
        finally:
            shutil.rmtree(tmp2)
        return f"append moved root {before[:8]}…→{after[:8]}…"
    finally:
        shutil.rmtree(tmp)


def p_sign_roundtrip():
    from ledger.export import root_hash
    from ledger.sign import generate_keypair, sign_root, verify_root
    tmp = tempfile.mkdtemp()
    try:
        s = _seed(tmp)
        root = root_hash(s)
        priv, pub = generate_keypair()
        sig = sign_root(root, priv)
        assert verify_root(root, pub, sig), "good signature refused"
        other = Store(tmp)  # noqa: F841 — same dir, reuse root
        s.add(_mk(tmp, stopped_checking="another", covered_by="y"))
        root2 = root_hash(s)
        if verify_root(root2, pub, sig):
            raise AssertionError("stale signature accepted on moved root")
        return "good=accepted stale=refused"
    finally:
        shutil.rmtree(tmp)


pins = [("E1 export-selective", p_export_selective),
        ("E2 export-verify", p_export_verify),
        ("E3 export-tamper-refused", p_export_tamper),
        ("E4 root-covers-all", p_root_covers_all),
        ("E5 sign-roundtrip", p_sign_roundtrip)]

for name, fn in pins:
    pin(name, fn)

for status, name, detail in results:
    print(f"{status} {name} — {detail}")

log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "pins", "failfirst-wave2.log")
with open(log, "w") as f:
    for status, name, detail in results:
        f.write(f"{status} {name} — {detail}\n")

n_fail = sum(1 for s, _, _ in results if s == "FAIL")
print(f"\n{len(results) - n_fail}/{len(results)} pass")
sys.exit(1 if n_fail else 0)
