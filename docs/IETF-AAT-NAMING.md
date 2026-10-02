# IETF AAT naming-alignment hedge

Source: `draft-sharif-agent-audit-trail` (R. Sharif, CyberSecAI Ltd, IETF
Internet-Draft, Standards Track). Fetched from the IETF datatracker on
2026-10-02; the fetched text is revision **-00 (2026-03-29)** while a fleet
edge-watch pulse (2026-10-01) reports a renewed **-05** with IPR filed Sep
2026 — the live revision number was NOT re-verified at cite time, so treat the
revision as pending. The vocabulary analysis below is against the fetched
text; field names in this draft family have been stable across its revisions
per the fleet pulse, but that stability claim is itself a pulse claim, not a
primary source.

## What AAT is

A JSON audit-record format for autonomous agents: mandatory fields
(`record_id`, `timestamp`, `agent_id`, `agent_version`, `session_id`,
`action_type`, `outcome`, `trust_level`, `parent_record_id`, `prev_hash`),
tamper-evident chaining `prev_hash(N) = hex(SHA-256(JCS(record(N-1))))` with
JCS (RFC 8785) canonicalization mandatory, optional ECDSA P-256 signatures,
JSONL as the primary export, EU AI Act Art. 12 mapping.

## Why this note exists (vocabulary hedge)

If AAT or a descendant becomes the dominant vocabulary for hash-chained agent
logs, we want our terms already parked adjacent to it — same parking lot,
different vehicle. This is a naming-alignment note, NOT an adoption: no AAT
field becomes load-bearing here, and no claim is made of conformance.

## Free alignments (adopt in speech and docs)

| AAT term | doubt-ledger term already in use | action |
|---|---|---|
| genesis record | GENESIS-anchored chain (`GENESIS`, `GENESIS_PREV_QMR1`) | adopt AAT wording when describing the anchor |
| `prev_hash` chain link | `prev` in qmr1 export rows | already semantically identical; keep short name, gloss as "prev_hash-style link" in docs |
| JSONL primary export | JSONL export + qmr1 JSONL | already aligned; state it |
| session chain | per-store chain, one ledger per repo | gloss "one session per store" |

## Deliberate divergences (state, do not paper over)

1. **Hash function.** AAT mandates SHA-256; our live-chain checksums are
   fnv1a-64 — deliberately non-cryptographic, an order-sensitive *receipt*
   chain (cheap, deterministic across runtimes), not a forgery barrier. This
   is documented in README limit #1. AAT-grade tamper evidence lives at our
   root: one Ed25519 signature over the fnv1a-64 tip root (`ledger/sign.py`).
   Verdict: fnv1a stays; the SHA-256 work in this repo is the qmr1 `id`
   derivation, which uses SHA-256 with an explicit `"qmr1:"` domain-separation
   prefix — a naming choice we keep exactly because un-prefixed SHA-256 over
   canonical JSON is AAT's lane, and domain separation prevents silent
   cross-format confusion of receipts.
2. **Canonicalization.** AAT mandates JCS (RFC 8785). Our qmr1 `_canonical`
   is an in-house deterministic serializer. If an AAT adapter is ever built,
   the correct move is to replace `_canonical` with JCS wholesale (one
   function, one pin re-derivation), not to maintain two canonicalizers.
   Recorded here so the adapter starts from the right seam.
3. **Subject matter.** AAT logs *actions* with an outcome taxonomy. This
   ledger logs *relocated trust* with an entry grammar (`stopped_checking` /
   `because` / `covered_by` / `revisit_trigger`) and the rule that discharge
   requires a reason. `covered_by` — who or what now carries the blindness —
   has no AAT equivalent; that is the differentiator and it stays first-class.

## Mapping table (for a future adapter, not a promise)

| AAT field | doubt-ledger / qmr1 source |
|---|---|
| `record_id` | qmr1 `id` (SHA-256, domain-separated) or entry `id` |
| `parent_record_id` | qmr1 `prev` |
| `prev_hash` | qmr1 `prev` (but SHA-256/JCS semantics differ — divergence 2) |
| `timestamp` | entry `ts` (unix; AAT wants RFC 3339 — mechanical) |
| `agent_id` | repo + signer pubkey (Ed25519 root signer) |
| `outcome` | entry `status` (`open` / `due` / `discharged-with-reason`) |
| `session_id` | store path / git checkpoint ref |
| `trust_level` | **no equivalent** — closest is `covered_by`, which is richer; do not flatten |
| `signature` | qmr1 row `sig` (Ed25519), or `ledger/sign.py` root signature |

## Honest limits of this note

- Fetched revision is -00; the -05 delta was not read. If -05 renamed fields,
  this table is stale and should be corrected, not defended.
- AAT is an Internet-Draft: it can expire, fork, or be replaced (the fleet
  pulse family already includes sahu -00, asqav -07, mvps-logging,
  evidence-action, AGTP-LOG, ISO/IEC FDIS 24970). This hedge buys vocabulary
  adjacency cheaply; it does not bet the repo on AAT.
- No conformance claim, no validator, no adapter is implied. This is
  cite/differentiate, per the standing fleet doctrine.
