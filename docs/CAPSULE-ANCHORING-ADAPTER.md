# Capsule-Hash Anchoring Adapter — wave-3 sketch (consume-don't-rival)

Status: SKETCH ONLY. No code in this branch. Build the adapter only when an
actual capsule-producing consumer appears. This note exists so the design is
pinned *before* vocabulary gets owned elsewhere.

## Motivation

External evidence systems are starting to seal agent-run artifacts with
heavyweight stacks (NovaFabric Run Capsules — arXiv 2609.12582: DSSE signature
+ RFC 3161 timestamp + Merkle log; see `memory/study/2026-10-02-nova-fabric-evidence-capsules.md`).
doubt-ledger will not re-implement any of that. But a ledger whose job is
"what are we trusting, and what covers it" needs a **way to point at** such a
sealed artifact without swallowing it.

## Proposed shape

An *anchor* is a pointer, not a copy:

```json
{
  "id": "…", "ts": …,
  "stopped_checking": "re-verifying run 42 evidence by hand",
  "because": "run 42 sealed as NovaFabric capsule, third-party verifiable",
  "covered_by": "capsule:sha256:9f2c…e1@novafabric://runs/42",
  "revisit_trigger": "capsule-revocation-list-update",
  "kind": "anchor",
  "status": "open",
  "anchors": [{"scheme": "capsule-sha256", "hash": "9f2c…e1", "locator": "novafabric://runs/42"}]
}
```

Mechanics (all already exist on `poc`):

1. `anchors` rides the entry grammar as an OPTIONAL field — grammar-enforcement
   pin P1 pattern: present-but-empty is rejected, absent is fine (backwards
   compatible with every existing entry).
2. The per-line checksum (`store._checksum`) and the export chains
   (`export.root_hash`, `export.qmr1_id`) hash the canonical line, so an
   anchored entry inherits tamper-evidence automatically. No new chain logic.
3. `export_qmr1` / `verify_qmr1` need no changes: the anchor is inside the
   body they already chain and HMAC.
4. Minimal adapter surface if built later: `entry.py` accepts `anchors`,
   plus one convenience constructor. ~20 lines, stdlib-only.

## Honest boundaries (sealed now, defended later)

1. **Anchoring ≠ verifying.** The ledger records *that we anchored a hash*.
   Whether the capsule verifies is the external tool's job (their Evidence
   Bundle with stock tooling). Receipts over claims applies to us too.
2. **Provenance-only, not replay** — same doctrine as limit #1. The fnv1a-64
   chain is non-cryptographic by design; the capsule's sha256 carries the
   cryptographic weight. The `scheme` field keeps hash agility explicit.
3. **Shared gap shape.** NovaFabric replays only 2/10 tool-using workloads;
   tidepool's moat note ("local receipt proves what was emitted, not that the
   pool accepted it") is the same emitted≠accepted shape. The adapter does
   not close that gap and must not claim to.
4. **Completeness honesty.** Their declared-stream completeness is 0.652, not
   1.0. If this adapter ever lands, any coverage claim must be measured the
   same way — never assumed.
5. **No conformance claim.** We cite/differentiate, we do not claim
   compatibility with NovaFabric, DSSE, or RFC 3161. If a quilt lane ever
   ingests OTel traces, cite their capsule format rather than inventing one.

## Why not build it now

No consumer exists. A sketch without a consumer is cheap; a module without a
consumer is a maintenance surface and a vocabulary land-grab. WATCH trigger:
first time a fleet lane actually produces or ingests a sealed external
artifact, this note becomes the spec.
