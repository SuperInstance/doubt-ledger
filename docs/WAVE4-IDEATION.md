# Wave-4 Ideation — ranked candidates (snowball pulse 2026-10-03 02:14 CST)

Status: IDEATION ONLY. Nothing here is committed work. Each candidate carries its
evidence, its honest boundary, and its kill switch. Smallest-first per standing
backlog doctrine. wave-1 (poc) / wave-2 (export + Ed25519 root signing) /
wave-3 (qmr1-compatible export, capsule adapter sketch) all merged 10/2; the
queue's follow-through edges (#26/#27 VERIFIED) are booked in quilt-tools#40 (open).

## Org pulse inputs (2026-10-02 15:42Z → 18:14Z, all verified live)

- doubt-ledger #5 (PAM hedge), #6 (IETF AAT hedge), #7 (capsule adapter), #8
  (fresh-clone verify of main), #9 (Janus hedge) ALL MERGED ~15:42-15:51Z.
  Main = poc tip 6f202da.
- tidepool#12 (PAM hedge) MERGED 15:42:43Z.
- quilt-mcp-receipts: qmr2 §8 v3 attribution LANDED (sigAlg:'ed25519' +
  sigKeyFp sha256-of-SPKI-PEM fingerprint law, keyring verify, E_UNKNOWN_SIGNER
  fail-closed, verify_attribution under --v3 versioned capability). Cross-repo
  identity shared byte-for-byte with quilt-jev-toolkit organ v3.
- New-to-us activity, zero collisions: fleet-seeds ("Tap Tavern: the fleet
  talks to itself, on the record, stone-v1 sealed"), superinstance-advisor
  ("witnesses every action with a merkle-rooted audit log"), Patchwork-experts
  pushes, slackwater-rust/slackwater-lattice PRs, quilt-organ-workers pushes,
  warp PR (external agentic dev env — WATCH only, not ours).

## Candidate 1 (smallest, recommended next): export dialect v2 = optional qmr2-§8 attribution row

- What: our export (wave-2/3) emits qmr1-compatible receipts per row. qmr2 v3
  now defines per-row attribution: sigAlg:'ed25519' + sigKeyFp, keyring
  verification, append refuses what it cannot attribute. A ~30-line stdlib
  delta could let export_store optionally attach attribution rows compatible
  with qmr2 v3, reusing our existing Ed25519 root keypair material.
- Consume-don't-rival: we do NOT build a keyring/registry; we emit rows that
  THEIR verify_attribution accepts, if and only if the dialect stays stable.
- Honest boundary: anchoring != verifying (carried from CAPSULE-ANCHORING-ADAPTER);
  attribution proves who signed, never that the content is true; a v2 export
  never rewrites v1 rows (qmr2's own never-rewritten law).
- Kill switch: qmr2 dialect drift (any byte-level change to §8) → revert to v1
  export, WATCH entry only. Their versioned-capability pattern (--v3) is the
  adoption gate.

## Candidate 2: coverage/discharge query tool (`ledger/coverage.py`, stdlib)

- What: the ledger's core thesis is "discharge requires a reason." Today
  coverage is only inspectable by reading JSONL. A stdlib tool answering:
  entries with revisit_trigger due (by evalIndex/clock), covered_by chains
  (what covers what), unreasoned-discharge candidates (grammar present, reason
  empty/absent — the blindness-again class guardD found once already).
- Pins: FAIL-first (synthetic ledger with a planted unreasoned discharge must
  be NAMED by id), append-only read (tool never writes), regression vs P1-P5.
- Honest boundary: substring semantics (limit #5) apply to covered_by matching;
  the tool reports what the file says, never completeness of coverage.
- Size: one bounded build, ~fits a 15-min lane only if pins are 3-4; otherwise
  split spec-first (pre-registration doc) / run-second, per R8 culture.

## Candidate 3: adjudication-client spec (docs-first, no code yet)

- What: quilt-adjudication#1+#2 merged ("merge that records its disputes",
  query layer over recorded disputes). Our discharge-reason grammar
  {stopped_checking, because, covered_by, revisit_trigger} is a natural
  ATTEST input to an adjudication query: a discharge is itself a small
  dispute-resolution record. Spec doc only: mapping table doubt-grammar →
  adjudication query layer, divergence notes (we are ledger-of-doubt not
  judge-by-design; receipted != true).
- Referral edge: doubt-ledger → quilt-adjudication CANDIDATE, PENDING at
  birth per weight law; VERIFIED only on merge of BOTH a consumer and this
  doc — never self-upgraded.
- Honest boundary: committed-tree-only reads; we do not become the judge.

## Candidate 4: WATCH-only entries (no build)

- fleet-seeds Tap Tavern / stone-v1: fleet self-talk on the record. Adjacent
  vocabulary ("on the record") but different mechanism (seed channel vs doubt
  ledger). WATCH; if stone-v1 grows a dispute/correction channel, revisit
  candidate 3 as the doubt side of that pair.
- superinstance-advisor merkle-rooted audit log: merkle vs our fnv1a-64
  chain = weight-class difference (PKI-adjacent vs stdlib), same receipts
  culture. WATCH; no hedge needed — vocabulary overlap is healthy, not
  ownership.
- warp (agentic dev env): external product, terminal-agent lane. Zero
  collision with anything we build. No action.

## Standing laws carried (unchanged)

- Receipts over claims; FAIL-first pins where code; honest FAILs stand (R8).
- Weight law: consume-don't-rival; edges PENDING at birth, VERIFIED only on merge.
- Append corrections, never silent edit (Janus-hedge doctrine).
- main (= poc) untouched until Casey merges; sole-contributor force only on
  own branches, on the record.

Next pulse: candidate 1 pre-registration (spec + pins) if queue clears it, else
candidate 2 spec-first.
