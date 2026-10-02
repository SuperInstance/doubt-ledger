# Pre-registration — wave-4 candidate 2: coverage/discharge query tool (`ledger/coverage.py`)

Status: SEALED SPEC ONLY. No implementation in this lane. The build lane
implements against this spec FAIL-first; the pins below are defined here and
are not movable after the build lane starts (R8 — an honest FAIL stands, no
goalpost move).

Ground: the ledger's core thesis is "discharge requires a reason"
(`store.discharge` refuses an empty reason at runtime — but a file can still
CARRY an unreasoned discharge: hand-edited rows, pre-fix files from before
guardD closed the silent-failure class, or a future regression). Today the
only way to inspect coverage is to read JSONL by eye. This tool makes the
blindness-again class QUERYABLE, not just preventable.

## What it is

A stdlib-only, read-only query tool over a ledger directory:

    python3 -m ledger.coverage <ledger-dir> <query> [args...]

Queries (exactly four; no flags beyond these in this wave):

- `unreasoned` — list entries with status "discharged" AND
  (discharge_reason absent OR empty OR whitespace-only after strip),
  each NAMED by id, one per line, exit 0 even when the list is empty
  (empty list = the healthy answer, not an error).
- `due <event>` — entries that `Store.fire(event)` would flip to "due":
  status "open" AND (revisit_trigger == event OR
  (kind == "condition" AND expr == event)). Reports, never fires —
  the ledger file must be byte-identical after the run.
- `covers <needle>` — entries with status in ("open", "due") whose
  covered_by contains <needle> as a SUBSTRING (the tool inherits the
  store's own substring semantics verbatim; it does not upgrade them).
- `chain <entry-id>` — the entry's covered_by value plus every entry
  whose stopped_checking contains any whitespace-separated token of that
  value as a substring; output states matches as substring matches.

## Pins (FAIL-first, defined here, sealed)

Run against a SYNTHETIC ledger planted in a temp dir (never a real
ledger). Build lane writes `tests/pins_coverage.py` in the established
pin-suite style.

- **CV1 unreasoned named by id.** Synthetic ledger carries a planted
  discharge with discharge_reason "" (constructed by writing the JSONL
  record directly, bypassing `Store.discharge`). `unreasoned` output MUST
  contain that entry's id. RED first: on a tree with no coverage module,
  the pin fails because the module does not exist.
- **CV2 empty-reason-healthy exit.** Synthetic ledger with zero unreasoned
  discharges: `unreasoned` prints nothing, exits 0.
- **CV3 due is advisory, file untouched.** After `due <event>` on a
  planted ledger, the ledger file's bytes AND its fnv1a-64 line checksums
  are unchanged (hash the file before and after; the tool must open the
  file read-only). RED first on absent module.
- **CV4 substring honesty.** `covers needle` on planted entries matches a
  covered_by of "fleet-triage resolver" given needle "triage", and the
  output line for each match includes the substring marker "substring" —
  the tool reports what the file says, never claiming precise identity.

## Honest boundaries (sealed in-doc)

- The tool reports what the file says. Completeness of coverage is NOT
  asserted anywhere — a discharged doubt covered by nothing is invisible
  to `chain` by design; "unreasoned" catches only reason-emptiness, not
  wrongness of reason.
- Substring semantics (limit #5) are inherited, not upgraded: `covers` and
  `chain` can over-match, and every match line is labeled as substring.
- Read-only is a load-bearing promise: CV3 pins bytes-not-just-semantics;
  a tool that mutates the ledger fails the pin even if the mutation were
  "harmless."
- The synthetic ledger in pins is a construction (planted data), like all
  pinned fixtures; it tests the query layer, not the ledger's load-path
  guarantees (those are P1–P5 + guardian pins).

## Non-goals (this wave)

- No evalIndex/clock-dating of revisit triggers (that is quilt-dba's
  state law, not ours; our triggers are event strings, not counters).
- No cross-ledger aggregation, no export integration, no covered_by
  graph validation (cycle detection) — all future-candidate material.
- No TUI/JSON flag proliferation; four queries, one exit-code contract.

## Kill switch

If any of the four queries turns out to require writing to the ledger, or
if substring matching is found to silently mislead in a named real case,
the lane closes at honest FAIL per R8 and coverage remains eyeball-only
until a fresh spec.

## Standing laws carried

Receipts over claims; FAIL-first pins; append corrections, never silent
edit; main (= poc) untouched until Casey merges; consume-don't-rival (this
is a query layer over our own ledger — nothing external is shadowed).
