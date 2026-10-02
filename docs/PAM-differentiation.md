# PAM vocabulary hedge — cite/differentiate (2026-10-02)

**Source:** Ravindran, *Portable Agent Memory*, arXiv:2605.11032 (v1, 10 May 2026).
Flagged by edge-watch 09:27 and 15:30 pulses as the nearest external collision on
hash-chained agent memory. This note is filed BEFORE the vocabulary gets owned.

## What PAM is (cited, from the abstract)

An open protocol + reference implementation for *transferring persistent memory
state across heterogeneous AI agents*. Four pillars: (1) five-component
structured memory model with content-addressable entries linked by a
**Merkle-DAG provenance graph** providing tamper-evidence; (2) **capability-based
access control** for selective, scoped disclosure of memory segments;
(3) **injection-resistant rehydration** adapting recalled content to target
models while mitigating indirect prompt injection; (4) JSON-first serialization
with optional CBOR compaction. Python SDK (54 tests), Apache 2.0,
cross-model transfer demonstrated (GPT-4 / Claude / Gemini / Llama).

## What doubt-ledger is (differentiate, not rival)

doubt-ledger is NOT a memory-transfer protocol and must not drift into that
lane. It is a **relocated-trust ledger**: an append-only, git-backed record of
what stopped being checked, why, what covers the blindness, and what event
re-opens it. The axis PAM does not have: **reasoned discharge** — removing an
entry from active doubt requires a written reason, and an unreasoned discharge
is just blindness again.

| axis | PAM | doubt-ledger |
|---|---|---|
| question answered | "what may this target agent see?" | "what did we stop checking, and who covers it?" |
| purpose | portability across vendor runtimes | legibility of relocated trust |
| disclosure | capability-based, privacy-scoped | filtered-slice, audit-scoped (P6, qmr1 export) |
| chain | Merkle-DAG provenance, content-addressed | fnv1a-64 order-sensitive chain, genesis-anchored (integrity mark, not addressing — honest limit 2) |
| integrity upgrade | (not stated in abstract) | optional Ed25519 root signature over tip (P7) |
| trust model | capabilities | written reasons + coverage query (P5) |
| dialect alignment | JSON/CBOR | qmr1 (`quilt-mcp-receipts` dialect, wave-3; IETF draft-sharif-agent-audit-trail-05 hedge) |

## Explicit boundaries (what we do NOT build)

1. **No rehydration.** Injection-resistant adaptation of recalled content to a
   target model is a reader-side problem; doubt-ledger exports are for
   auditors, not for agents about to believe the content. (PAM's hardest
   pillar is precisely the one we leave untouched.)
2. **No content-addressing.** Our checksum chain binds *order and integrity of
   the record as kept*, not the content graph of memories. That is a feature
   for an audit trail (append-only by construction) and a ceiling for
   dedup/merge semantics.
3. **No cross-vendor runtime claims.** The ledger's consumer is a human or
   reviewer with `python3`, not a model runtime.

## Terminology we keep (vocabulary we are NOT yielding)

- **relocated trust / reasoned discharge** — the grammar fields
  (`stopped_checking`, `because`, `covered_by`, `revisit_trigger`).
- **coverage query** — "what is trust letting through HERE" (P5), substring
  answerable, always live.
- **doubt grammar** — the five-field entry shape; "discharge requires a reason"
  as adjudication thesis in one line.

If the fleet later adopts PAM-shaped vocabulary for memory transfer, this repo
consumes it at the export boundary (as it already consumes qmr1); it does not
re-purpose its core ledger as a memory substrate.

## Synergy note (consume-don't-rival)

PAM's capability-scoped selective disclosure and doubt-ledger's audit-scoped
selective disclosure are complementary slices of the same problem: one gates
what an agent may recall, the other records what a team stopped verifying.
A PAM rehydration step that consults a doubt-ledger coverage query before
trusting recalled provenance would be the natural interop seam — filed here as
an idea, not a build commitment.
