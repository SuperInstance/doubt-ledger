# Bone-registry reuse metric — adoption note (2026-10-03)

**Source:** SuperInstance/purpose-loops (org repo, created 07:16Z 2026-10-03), flagged by
edge-watch 2026-10-03B pulse as SYNERGY CANDIDATE #3. Read is org-internal and direct.

## What they built (cited, from their receipted evidence)

purpose-loops runs the **deadband law** (second org repo after erised-exocortex): a
bone-registry that records compiled strategy fragments ("bones") and measures their
**reuse** — same bone invoked again costs less than re-deriving it. Their proof is
receipted, not claimed: bones under the law compress 99 → 67 → 38 ops across passes
while the deadband-disabled control stays flat at 99. The metric they mint is
**costSaved**: per-bone accounting of operations not spent because the bone existed.

## What we do today (the gap)

The doubt-ledger tool surface *mints bones and never measures reuse*: every pin
suite, hedge note, and receipt-grammar doc is a compiled artifact that sibling lanes
re-derive by hand from scratch. We seal FAIL-first pins (`pins/failfirst-*.log`)
but keep no count of how often a sealed artifact is *consumed* rather than rebuilt.

## Adoption (one paragraph, commitment-free)

Adopt their **costSaved metric as a legibility question, not a runtime**: whenever a
doubt-ledger artifact (grammar doc, pin suite, export/signature adapter) is consumed
by another lane — cited instead of re-derived — that event deserves a row. The
natural home is the existing **coverage query** surface (P5, PR #14): a consumption
is structurally identical to a `covered_by` entry, except the covering thing is *our
own prior work* instead of someone else's blind spot. Differentiator we keep: their
metric optimizes *operations saved*; ours would record *reasons not re-litigated* —
reuse as discharged doubt. Explicit boundary: no new runtime, no dependency on
purpose-loops, one paragraph of vocabulary alignment only.

## Honest limits

- This note is vocabulary adoption on the strength of one org read; their
  99→67→38 numbers are theirs, not independently re-run here.
- If costSaved ever becomes contested, the receipts-over-claims rule applies to
  OUR use of their metric before it applies to anyone else.
