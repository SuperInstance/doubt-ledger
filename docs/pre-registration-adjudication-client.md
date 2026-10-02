# Pre-registration — adjudication-client spec (wave 4, candidate 3, SPEC-FIRST lane)

**Status: SEALED spec.** Docs-only. No implementation in this lane; the BUILD
lane implements the FAIL-first pins defined here, byte-frozen otherwise.
**Stacked:** off `poc` `6f202da`. Prior wave-4 lanes: candidate 1
qmr2 attribution (PR #11 spec / #12 build), candidate 2 coverage tool
(PR #13 spec / #14 build), ideation (PR #10) — all OPEN, Casey-gated.
**External surface consumed:** SuperInstance/quilt-adjudication `main`
(merge adjudication fork of quilt-in-git @ `6a1ae48`; PRs #1/#2 MERGED
2026-10-02 04:57Z). Referral edge quilt-in-git wave4-query →
quilt-adjudication already filed in their docs (CANDIDATE per weight law).

## The one-sentence thesis

A refused merge already wrote the dispute down — both claims verbatim, winner
named as ordering-not-judgment, one-command reversal carried. What it cannot
express is **who stopped checking which question because that record exists**.
That second record is exactly this repo's grammar. The adjudication-client is
the adapter that turns `.quilt/adjudications/<short>.json` into one
doubt-ledger entry — and refuses, by construction, to ever write the winner
down as the truth.

"Discharge requires a reason" (this repo) and "the winner rule is an ordering,
not a truth" (quilt-adjudication honest limit #6) are the same law stated at
two layers: **an unreasoned discharge is blindness again**, whether the
discharge is a silent merge or an unquestioned winner.

## The consumed schema (read 2026-10-03 04:1xZ from quilt-adjudication main)

An adjudication record `.quilt/adjudications/<short>.json` carries, verbatim
from their README:

- the contested `key`, and **both** claims with values and attributions;
- `adjudication: "mechanical"` and
  `judge: "none — no model is in this loop, by design"`;
- a winner rule ("the claim that arrived on the side being merged") stated
  explicitly as **an ordering, not a judgment about which is true**;
- a reason, and the command that takes the other number
  (`git checkout HEAD -- cells/... && git merge --abort && git merge <branch>`).

Load-bearing for this spec, in order of fragility:

1. `judge: "none …"` field exists → the client keys its honesty annotation on
   it. If a future judge lands and this field's value changes, the client must
   say so in the emitted entry, never silently inherit the no-judge gloss.
2. Both claims preserved verbatim → `covered_by` can cite the losing claim by
   value, not by paraphrase.
3. The reversal command exists → `revisit_trigger` can carry it verbatim
   instead of inventing its own.

**Schema drift is a kill switch, not a parsing challenge** (see KS1).

## The client protocol (v0, what the BUILD lane implements)

`ledger/adjudication.py`, stdlib-only, mirroring `ledger/coverage.py`'s
read-only contract:

```
usage: adjudication.py RECORD.json [--ledger PATH] [--emit-only]
```

Given one adjudication record, emit exactly one ledger entry:

| entry field | populated from |
|---|---|
| `stopped_checking` | the **question**, not the answer: `"which claim is true for key <key> (N claimants)"` — never the winner's value |
| `because` | `"adjudication record <short> exists — mechanical ordering, no judge ran"` + the record's own reason, quoted |
| `covered_by` | `[".quilt/adjudications/<short>.json", "quilt-query divergence <refA> <refB> (advisory)"]` — record path first, query second |
| `revisit_trigger` | the record's reversal command verbatim + `" OR new evidence for a losing claim"` |
| `kind` | `"discharge"` |
| `discharge_reason` | required non-empty (the grammar's core law; empty → refused, this is the CV1-class wound) |

## FAIL-first pins (AC1–AC4, RED against absent module → GREEN)

- **AC1 planted-record round-trip.** A fixture adjudication record with
  `judge: "none …"` and two claims yields exactly one entry whose
  `stopped_checking` names the key and claimant count but **no value as true**.
  RED first: module absent.
- **AC2 winner≠truth (the load-bearing pin).** Mutate the fixture so one
  claim is marked winner; assert the emitted entry contains the winner's
  *value* nowhere outside the quoted `covered_by` citation of the record file.
  The winner is cited, never adopted. (Same shape as Q2A4 attribution≠truth
  in PR #11: attribution and truth live in different columns.)
- **AC3 byte-identity.** Fixture file bytes AND the emitted entry's
  fnv1a-64 line checksums unchanged across a re-run (read-only is the
  promise, same pin class as CV3).
- **AC4 zero-disputes healthy answer.** Empty/absent adjudications dir →
  exit 0, zero entries, message on stdout (healthy answer, not error —
  same law as CV2).

## Honest boundaries (sealed in-doc)

1. **The client records a discharge of the question; it does not resume the
   adjudication.** No model in the loop here either — the entry says who
   stopped checking and what would reopen it, nothing about which claim is
   right.
2. **Receipted ≠ true, cited ≠ adjudicated.** The emitted entry is a claim
   until this ledger's own chain verifies it (receipts over claims); the
   adjudication record is a claim until re-derived against the tree.
3. **Coverage cross-reference is substring-based and advisory** (limit #5
   carries); the divergence query mention in `covered_by` is a pointer for a
   human, not a verified dependency.
4. **Committed-tree-only.** The record must exist on disk before the client
   runs; uncommitted dispute notes are invisible (receipt first, query
   second — the order is load-bearing, same as the wave4-query referral).
5. **Ordering asymmetry disclosure.** The winner arrived "on the side being
   merged"; the emitted entry must not let a later reader mistake temporal
   order for evidential weight. The `because` field carries the record's own
   ordering language verbatim for this reason.
6. **Synthetic fixtures are constructions** (carried from PR #13): the pins
   prove the client behaves, not that any real dispute was adjudicated.

## Kill switches

- **KS1 schema drift:** any of the three load-bearing fields (judge,
   both-claims-verbatim, reversal command) absent or reshaped in a record →
   exit `E_SCHEMA_DRIFT`, emit nothing, name the missing field. Corrections
   append to this doc, never silent edit.
- **KS2 judge landed:** if the `judge` field ever names a model, v0 emits
   nothing and this spec is re-opened — a judging record is a different
   animal from a mechanical one and the entry grammar must say which it saw.
- **R8 lane kill:** if a BUILD-lane failure traces to this spec being wrong
   (not to implementation), the lane closes at the honest FAIL and the spec
   needs fresh evidence, not new constants.
- Any drift in quilt-adjudication's record schema on their main → v0
  refuses, this doc gets an appendix; we consume their record, never fork it.

## Why this is consume-don't-rival

quilt-adjudication records disputes; quilt-query answers questions about
recorded state; doubt-ledger records who stopped checking. Three verbs, three
layers, zero overlap. This client adds no adjudication logic of its own — it
is a grammar adapter, ~100 lines of stdlib, that only exists because a
dispute record and a discharge entry turned out to be the same shape.

main(poc) untouched. BUILD lane next if cleared: implement AC1–AC4 FAIL-first
per this spec.
