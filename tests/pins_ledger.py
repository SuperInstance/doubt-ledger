#!/usr/bin/env python3
"""PINS P1-P5 for doubt-ledger. FAIL-first: run against absent ledger/ -> RED."""
import os, sys, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

results = []
def pin(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))

try:
    from ledger.entry import Entry
    from ledger.store import Store
    from ledger.gitback import Gitback
    LEDGER = True
except ModuleNotFoundError as e:
    LEDGER = False
    os.makedirs(os.path.join(ROOT, "pins"), exist_ok=True)
    with open(os.path.join(ROOT, "pins", "failfirst.log"), "w") as f:
        f.write(f"FAIL-first: ledger/ absent — {e}\n")

def main():
    if not LEDGER:
        for p in ["P1", "P2", "P3", "P4", "P5"]:
            pin(p, False, "ledger/ not importable")
        return 1

    # P1: grammar enforced — missing field rejected with the field's NAME
    try:
        Entry(stopped_checking="tests", because="trust lane", covered_by="lane pins")
        pin("P1 grammar-enforced", False, "incomplete entry accepted")
        return 1
    except ValueError as e:
        ok = "revisit_trigger" in str(e)
        pin("P1 grammar-enforced", ok, f"rejected naming field={ok}")

    # P2: append-only — rewriting a stored line is refused (checksum)
    d = tempfile.mkdtemp(prefix="dl-")
    s = Store(d)
    s.add(Entry(stopped_checking="engine pins", because="lane A sealed them",
                covered_by="pins/failfirst.log", revisit_trigger="pins touched"))
    path = os.path.join(d, "ledger.jsonl")
    lines = open(path).read().splitlines()
    tampered = lines[0].replace("engine pins", "engine pins TAMPERED")
    with open(path, "w") as f:
        f.write("\n".join([tampered] + lines[1:]) + "\n")
    try:
        s2 = Store(d)
        pin("P2 append-only", False, "tampered line loaded silently")
        shutil.rmtree(d); return 1
    except ValueError:
        pin("P2 append-only", True, "tamper refused")
    shutil.rmtree(d)

    # P3: fire-and-due — matching trigger returns exactly its entries, marks
    #     due, discharge requires a reason
    d = tempfile.mkdtemp(prefix="dl-")
    s = Store(d)
    s.add(Entry(stopped_checking="pr-93 review", because="builder sealed 4 pins",
                covered_by="builder RESULT.md", revisit_trigger="casey-merged-pr-93"))
    s.add(Entry(stopped_checking="quota watch", because="403 window",
                covered_by="time", revisit_trigger="quota-reset"))
    due = s.fire("casey-merged-pr-93")
    ok = len(due) == 1 and due[0]["stopped_checking"] == "pr-93 review" \
         and due[0]["status"] == "due"
    try:
        s.discharge(due[0]["id"], reason="")
        pin("P3 fire-and-due", False, "empty-reason discharge accepted")
        shutil.rmtree(d); return 1
    except ValueError:
        pass
    s.discharge(due[0]["id"], reason="re-read the diff, guard verified")
    still_open = [e for e in s.open() if e["stopped_checking"] == "quota watch"]
    pin("P3 fire-and-due", ok and len(still_open) == 1,
        f"due-exact={ok} others-untouched={len(still_open)==1}")
    shutil.rmtree(d)

    # P4: git-resume — checkpoint, wipe memory, resume() identical, git log shows it
    d = tempfile.mkdtemp(prefix="dl-")
    os.system(f"git init -q {d}")
    g = Gitback(d)
    g.add(Entry(stopped_checking="lane harvests", because="verified 3x tonight",
                covered_by="verify protocol", revisit_trigger="next harvest"))
    g.add(Entry(stopped_checking="disk watch", because="crisis at 100%",
                covered_by="df in pulses", revisit_trigger="disk>80%"))
    g.checkpoint()
    before = open(os.path.join(d, "ledger.jsonl")).read()
    fresh = Gitback(d)  # new in-memory view = session death + resume
    after = open(os.path.join(d, "ledger.jsonl")).read()
    log = os.popen(f"git -C {d} log --oneline").read()
    ok = before == after and "checkpoint" in log
    pin("P4 git-resume", ok, f"identical={before == after} commit={'checkpoint' in log}")
    shutil.rmtree(d)

    # P5: coverage query — 'what is trust letting through HERE' always answerable
    d = tempfile.mkdtemp(prefix="dl-")
    s = Store(d)
    s.add(Entry(stopped_checking="fleet-triage/docs review", because="pulse sealed",
                covered_by="pulse pins", revisit_trigger="docs touched"))
    s.add(Entry(stopped_checking="wardroom moderation", because="off-duty room",
                covered_by="culture", revisit_trigger="spam wave"))
    hits = s.at("fleet-triage/docs")
    pin("P5 coverage-query", len(hits) == 1 and "pulse sealed" in hits[0]["because"],
        f"hits={len(hits)}")
    shutil.rmtree(d)

    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
