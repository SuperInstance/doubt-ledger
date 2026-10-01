# doubt-ledger

**Trust relocates blindness; it does not delete it.** This ledger is where the
relocation gets written down — an append-only, git-backed record of what you
stopped checking, why, what covers it, and what event brings it back for a look.

Origin (real, 2026-10-02): a 21-hour live run of sub-agent lanes whose every
output passed independent verification — and whose checkers (the verifying
pulse, the reading human) stopped being audited somewhere along the way.
The doubt was relocated, not deleted. This repo is the surface that makes the
relocation legible.

## Entry grammar (all five required — no field may be empty)

```json
{
  "id": "a1b2c3d4e5f6",
  "ts": 1762051200,
  "stopped_checking": "pr-93 review",
  "because": "builder sealed 4 pins independently verified",
  "covered_by": "builder RESULT.md + pins/failfirst.log",
  "revisit_trigger": "casey-merged-pr-93",
  "kind": "event",
  "status": "open"
}
```

`kind: condition` entries carry `expr` instead of a single trigger.
Discharge requires a written reason — an unreasoned discharge is just
blindness again.

## What it proves (pins P1–P5)

| pin | claim |
|-----|-------|
| P1 | grammar-enforced — an incomplete entry is rejected and names the missing field |
| P2 | append-only — any rewritten stored line is refused on load (per-line checksum) |
| P3 | fire-and-due — a trigger fires exactly its entries, marks them `due`, discharge demands a reason |
| P4 | git-resume — checkpoints commit the ledger; a fresh process over the same dir resumes byte-identical |
| P5 | coverage-query — "what is trust letting through HERE" is always answerable by substring |

Run: `python3 tests/pins_ledger.py` (stdlib only; FAIL-first log in
`pins/failfirst.log`).

## Honest limits

1. The ledger records doubt, it doesn't rank it — a cheap doubt and an
   existential one take the same five fields. Severity is unbuilt.
2. The checksum is fnv1a-64 (integrity mark, not a signature).
3. Condition expressions are exact-string matches, not a real expression
   language.
4. Nobody audits the ledger-keeper. A doubt-ledger that lies about its own
   entries is just a diary. (Pins prove the store refuses tampering *on load*
   — but the keeper chooses when to load.)
