# receiptd collision note — cite/differentiate (org-side trust layer)

Date: 2026-10-03. Source: SuperInstance/receiptd (org repo, created 18:46Z
2026-10-02, first push 00:53Z). Read directly: README, SKILL.md, receiptd.py
(SHA-256 chain, daemon+CLI twin, unix socket), tipnotary.py (external
anchoring). Status: CITE/DIFFERENTIATE per doctrine. This note books the
collision before vocabulary drifts: receiptd is the fleet's *execution-trust*
layer; doubt-ledger is the *doubt* layer. Same append-only hash-chain shape,
different question.

## Their claim set (as shipped and pinned)

1. **One append-only JSONL, SHA-256 chain**: `h = sha256(h_prev + "\n" +
   canonical(rec))`, canonical = sorted keys, compact separators. Genesis
   64 zeros. Verify re-derives from disk O(n): tamper names the line,
   deletion names the gap, rewrite breaks prev-links. rc=2 on tamper.
2. **Daemon + CLI twin** over a unix socket (0600, per-user): any agent
   that can `write()` NDJSON can append. The daemon's index is a VIEW;
   `verify` never lies (re-derives).
3. **Three-valued or nothing**: `v ∈ {-1, 0, +1}`; INCONCLUSIVE is
   first-class — "a gate that can't say UNKNOWN will lie to you."
4. **tipnotary (slice 1.5)**: `verify` proves self-consistency only — a
   full-file rewrite with recomputed hashes passes. Notarized KV anchors
   close that: check is MATCH / STALE / FORGED, rc=0/3/2. `hash_spec`
   field anchors the SPELLING (sha256/utf-8/bytes vs fnv1a64 UTF-16
   charCodeAt cousins) — machine-checkable per the wardroom byte-mandate.
5. **Trust = re-execution**: slice 2 road is `receipt verify-exec <hash>`
   spawning champion_audit in a sandbox lane, DERIVATIVE receipts with
   `re: <parent>` — never mutate the parent.

## CLAIM-THEIRS / CLAIM-OURS / VERDICT

| # | Claim (theirs) | Ours | Verdict |
|---|---|---|---|
| 1 | Append-only hash chain over agent claims (execution receipts) | doubt-ledger: append-only JSONL + git checkpoints, fnv1a-64 receipt chain — but entries are **doubt grammar**: {stopped_checking, because, covered_by, revisit_trigger}; discharge requires a reason. | **DIFFERENTIATE WITH PRIDE** — same chain shape, different question. receiptd answers "did the claimed act happen?" (re-execution); doubt-ledger answers "what did we decide to stop checking, and why is that safe?" (trust relocation). Complementary, not rival. |
| 2 | SHA-256, PKI-grade | fnv1a-64 by design (non-crypto); Ed25519 only at export roots (wave-2). | **DIFFERENTIATE** (same as IETF-AAT + Janus rows): weight class differs — our threat model is drift/accident, not adversarial forgery. Their tipnotary FORGED class is the adversarial answer; we cite it instead of building it. |
| 3 | INCONCLUSIVE first-class, three-valued gates | doubt-ledger discharge requires reason vocabulary; fire-and-due never asserts coverage beyond its rows; doubt grammar admits "superseded". | **ADOPT the name at fleet level.** "A gate that can't say UNKNOWN will lie to you" is the receipts-culture gloss for our INCONCLUSIVE pins (canon-rotation H1, E-CF-1 cross-colo). |
| 4 | `hash_spec` anchors spelling (fn/encoding/unit/rule) | Our chains carry implicit spelling (fnv1a-64, UTF-8). Cross-repo cousins (quilt-dba UTF-16 charCodeAt) silently differ. | **ADOPT the field.** Any future ledger/export adapter carries hash_spec verbatim; without it, "same names, different bytes" forgery-by-transcoding walks. Cheap, load-bearing. |
| 5 | verify re-derives from disk; index is a view | doubt-ledger loads refuse tampered entries on load; export_store recomputes checksums; pins re-run from fresh clone (19/19 cold PASS, PR #8). | **SAME** — no action. Two independent implementations of receipts-over-claims; convergence is evidence, not redundancy. |
| 6 | DERIVATIVE receipts (`re: <parent>`), never mutate the parent | Our referral-edge / superseded-by grammar (quilt-in-git merge-order note) is the same law in doc form; wave-4 attest rows are derivative rows. | **ADOPT the verb.** `re:` parent links as first-class ledger field for attest/derivative rows. |

## What receiptd does not cover (the gap we keep)

- **No doubt grammar.** receiptd receipts assert; nothing records *why
  checking stopped*, *what covers the blind spot*, or *when to revisit*.
  That is doubt-ledger's entire thesis ("trust relocates blindness; it does
  not delete it"). If the fleet adopts receiptd as the execution layer, our
  ledger sits beside it as the blindness layer — the two chains can even
  cross-anchor (their tipnotary KV as our external anchor for doubt tips;
  our covered_by rows as evidence in their corr threads).
- **No coverage semantics.** Their `by-corr` threads are replay, not
  coverage. Our coverage/discharge query tool (PR #14) answers "what is
  still unchecked?" — receiptd cannot.

## Wave-4 lane re-rank (collision consequence)

receiptd now owns org-side *execution receipts* (daemon, socket, re-execution
road). Wave-4 lanes therefore:
- **do NOT** rebuild a generic claim-chain tool (that lane is receiptd's now);
- **DO** consume it where an execution-receipt surface is needed
  (adjudication record rows, attest rows) and cite this note;
- **DO** keep doubt-ledger focused on doubt grammar + coverage queries —
  the layer receiptd explicitly does not build.

## Kill switch

If a deeper read of receiptd.py/tipnotary.py contradicts any CLAIM-THEIRS
row above, a correction entry is appended here (never silently edited) and
the collision verdict re-opens.
