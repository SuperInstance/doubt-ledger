# Janus hedge — evidence-before-effect sagas (arXiv 2609.38266)

Date: 2026-10-02. Source: Janus (Arslan et al., v1 2026-09-29) — read from
the abstract + submission record; full text not yet ingested. Status:
CITE/DIFFERENTIATE per doctrine. This note books the vocabulary before it
can drift into our receipts culture unexamined.

## Their claim set (as advertised)

1. **Record on the effect path**: proposal, verdict, and validator/person
   answers are durable in a signed hash-chained log BEFORE the step may run
   or its effect be released. Gates are pure functions of the log; an
   auditor re-derives every verdict offline from log + one public key.
2. Effect held at the MCP edge until evidence is durable.
3. Evaluation honesty: crash injection (144 in-process + 81 daemon kills),
   100M-event offline re-derivation (254.5s), governed-vs-plain lending
   comparison, and a self-reported **post-approval substitution** bug
   (approval keyed to an attempt counted for a different proposal;
   approval moved 100→1,000,000) with first fix + five routes around it.
4. Mandate placement result: mandate-in-prompt → 0 violations/0 paid;
   mandate-in-policy-only → 6 declared violations, plain agent paid all 6,
   Janus paid none; an always-approve oracle scored 20/21 declared — the
   *policy layer* was doing the real governance, not the prompt.

## CLAIM-THEIRS / CLAIM-OURS / VERDICT

| # | Claim (theirs) | Ours | Verdict |
|---|---|---|---|
| 1 | Record must be ON the effect path | Our WALs are emitted beside effects (algorithmic engines, cheap replays). EXCEPT: backward-holdem decisions exist ONLY as WAL ticks — no tick, no decision. The record IS the effect path there, by construction, not retrofit. Receipt: master `da241a0`, wal seed 20261002 ref `0809402a13c37d70`. | **DIFFERENTIATE WITH PRIDE** — labs with decision≡tick are ahead of their retrofit; tool-effect repos (theirs: money movement) genuinely need their gate. Both true. |
| 2 | Gates = pure functions of the log | pong-quilt's franken-save guard is exactly a pure function of state+receipts (PR #99 lineage). Cross-end pins (quilt-overhead snapshot wal_ref ↔ backward-holdem WAL) are gate-at-a-distance. | **ADOPT the name.** "Gate = pure function of the receipt log" is now our gloss for guards/pins. |
| 3 | Offline auditor re-derivation | Fresh-clone pin reruns are our offline re-derivation (doubt-ledger 19/19 cold PASS, PR #8 receipt). | **SAME** — no action, vocabulary aligned. |
| 4 | Post-approval substitution is a real class | Our name: **wal_ref substitution** — a receipt consumed for an event it didn't witness. Defense already live: content-sig receipts (nb engine) + cross-end pins (snapshot↔WAL) bind evidence to identity+position, not to "an attempt". | **ADOPT the risk class.** Add "keyed-to-attempt?" to cross-pin review checklist. |
| 5 | Mandate placement (policy ≫ prompt) | Our prereg practice: H1 sits in backward-holdem LEDGER.md (policy layer, outside any run's prompt). exp002 tests it without touching the prereg line. | **REINFORCED.** Prereg-in-LEDGER is the fleet's policy layer; do not move hypotheses into run prompts. |
| 6 | Signed (PKI) hash chains everywhere | fnv1a-64 content chains by design (non-crypto), Ed25519 only at export roots (doubt-ledger wave-2). | **DIFFERENTIATE** (same as IETF-AAT note): weight class differs — our threat model is drift/accident, not adversarial forgery. Cite, don't conform. |

## What Janus does not guarantee (their own honesty, adopted)

- Understated declarations slipped 4+3 payments through (amount unit dropped
  from the prompt). Fleet analogue: a receipt with a hole in its declared
  inputs passes re-derivation while the *semantics* leaked. Our counter:
  nb's `mutant` op grades spec strength; receipts-over-claims doctrine.
- Their fix closed one substitution route; five remain documented. Same
  posture here: pins catch named classes; the ledger records which classes
  are still open (doubt-ledger divergence-watch grammar).

## Kill switch

If a full-text read contradicts any CLAIM-THEIRS row above, this note gets
a correction entry appended (not silently edited) and the REFERRAL_GRAPH
hedge edge stays PENDING.
