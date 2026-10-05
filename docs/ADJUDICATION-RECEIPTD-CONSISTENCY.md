# Adjudication-client (wave-4 c3) × receiptd hedge — consistency review

Date: 2026-10-03 (13:10 pulse). Scope: PR #16 (branch
`wave4-adjudication-build`, build of the SEALED spec in PR #15) reviewed
against `docs/RECEIPTD-COLLISION-HEDGE.md` (PR #18) — the 10:56 pulse's
queued follow-on "check doubt-ledger#16 vs receiptd consume-don't-rival
consistency". Verdict: **CONSISTENT on every load-bearing axis; one
non-blocking citation gap named below.**

## What was checked (diff read directly, base 6f202da)

Files: `ledger/adjudication.py` (+159), `tests/pins_adjudication.py`
(+184), `pins/failfirst-adjudication.log`. Module reviewed line-level;
pins reviewed for AC1–AC4 + KS1/KS2 semantics.

## Axis table

| # | Hedge rule (RECEIPTD-COLLISION-HEDGE.md) | #16 build | Verdict |
|---|---|---|---|
| 1 | Do NOT rebuild a generic claim-chain — receiptd owns execution receipts | The client emits **doubt-grammar entries** only: {stopped_checking, because, covered_by, revisit_trigger, kind=discharge}. Zero claim/assert rows, zero hash-chain construction, zero execution-receipt surface. | **CONSISTENT** (gap-we-keep preserved) |
| 2 | Same chain shape, different question — we answer "what stopped being checked" | Entry text: "which claim is true for key <key> (N claimants)" — a *blindness* record, not a *truth* record. | **CONSISTENT** |
| 3 | Winner cited, never adopted (AC2 pinned, load-bearing) | `build_entry` carries no winner VALUE anywhere; record cited by path in covered_by, never adopted. Mirrors coverage-tool column-law. | **CONSISTENT** |
| 4 | Row-3 ADOPT: "a gate that can't say UNKNOWN will lie to you" — INCONCLUSIVE first-class | AC4: absent/empty adjudications dir = exit 0, zero entries, message on stdout ("healthy answer", not an error). KS1 schema drift = E_SCHEMA_DRIFT, emit nothing, name the field. KS2 judge landed = E_JUDGE_LANDED, emit nothing, re-open spec. Three distinct honest answers instead of a binary that would launder. | **CONSISTENT in shape — but see gap** |
| 5 | record read-only (AC3 pins fixture bytes + emitted line checksums across re-run) | Records opened `"r"` only; AC3 pins both fixture bytes and fnv1a-64 line checksums stable across re-run. | **CONSISTENT** |

## Gap named (non-blocking, post-merge follow-up)

The build's three-valued refusal vocabulary (healthy-answer / schema-drift /
judge-landed) is structurally the receiptd row-3 INCONCLUSIVE adoption, but
neither `ledger/adjudication.py` nor PR #16's body cites
`SuperInstance/receiptd` or `RECEIPTD-COLLISION-HEDGE.md`. The hedge exists
precisely to stop this vocabulary drifting untracked. Suggested post-merge
one-liner: module docstring line "Three honest answers (empty / drift /
judge) per receiptd INCONCLUSIVE adoption (RECEIPTD-COLLISION-HEDGE row 3)"
+ PR-body mention on any follow-up. Not a #16 blocker — the spec (PR #15)
predates the hedge and the behavior is correct; only the citation is absent.

## Non-issues observed

- Build branch base (6f202da) predates the #14/#15 merges on poc — cosmetic;
  GitHub resolves; spec doc and coverage tool land independently.
- E_MULTI_CONFLICT v0 restriction (one conflict per record) is a scope
  limit, pinned-adjacent, and honestly documented in the module docstring —
  not a hedge violation.

## Boundary of this note

Review of an unmerged PR's diff; if #16 changes before merge, this note's
axis rows re-check at next doubt-ledger touch. Corrections append, never
silent edit.
