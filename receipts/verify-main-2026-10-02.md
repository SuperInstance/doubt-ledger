# Post-merge verification receipt — main @ wave-3 (#4 merged 2026-10-02T08:51Z)

Harvest-protocol re-run on a FRESH shallow clone of `main` (no local state,
pins re-derived by the suite itself, not by the merge narrative).

| suite | pins | result |
|---|---|---|
| tests/pins_ledger.py | P1–P5 | 5/5 PASS |
| tests/pins_export.py | E1–E5 | 5/5 PASS |
| tests/pins_qmr1.py | Q1–Q4 | 4/4 PASS |
| tests/pins_guardian.py | G1–G4b | 5/5 PASS |

Total: 19/19 PASS, zero skips.

Notable receipts observed live during the re-run:
- E3 named the tampered export line by id (`fc954b431d75`) — legibility
  promise holds post-merge, not just in the PR branch.
- Q3/Q4 refused both a value edit and a wrong-secret HMAC by line.
- G3 truncation refusal message names the corruption class verbatim.

Honest boundary: this verifies the pin suite as it exists on main; it does
not re-audit the diff of #4 itself (guardian lane D' covered #1's class of
silent failures; the qmr1 dialect was reviewed at PR time against the
`quilt-mcp-receipts` spike-v1 README, which remains Casey-side and
unversioned — dialect drift is a standing WATCH, not closed by this receipt).
