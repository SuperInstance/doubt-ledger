# Pre-registration: export dialect v2 — optional qmr2-§8 attribution rows

Sealed: 2026-10-03 (snowball pulse, Asia/Shanghai). BEFORE any code.
Lane: wave-4 candidate 1 from docs/WAVE4-IDEATION.md (ranked smallest, recommended).
Status law: this document is byte-frozen. The build that follows must implement
exactly this spec; if reality disagrees with the spec at build time, the spec
FAILS (R8) — the spec is never edited mid-lane to fit the implementation.

## Grounding (all verified live, 2026-10-03 02:5x CST)

- quilt-mcp-receipts tip `c8ad04e` (2026-10-02 18:43Z): qmr2 §8 v3 attribution
  (`d3ab7bf` spec, `c8ad04e` conformance §9). Read directly from
  `docs/qmr2-design.md` §8.1–§8.5, NOT from code. Zero commits since landing —
  no dialect drift as of seal.
- Wave-3 `export_qmr1()` on poc emits byte-compatible qmr1 (five fields:
  seq, prev, body, id, sig; sig = HMAC-SHA256(secret, "qmr1:sig:"+id)).
- Wave-2 `ledger/sign.py` already carries optional Ed25519 (dependency:
  `cryptography`, pip; pins skip-never-pass when absent — established pattern).

## The delta (byte-frozen spec)

`export_qmr1(store, predicate, out_path, secret=None, signer=None)` — one new
optional kwarg. Everything else untouched.

1. **Default path unchanged.** `signer=None` emits exactly the wave-3 v1 rows.
   No `sigAlg`/`sigKeyFp` field may leak into hmac rows (their §8.3 law:
   `sigKeyFp` FORBIDDEN on hmac rows — `E_SIGNER_MALFORMED`). v1 exports already
   in the wild keep verifying byte-for-byte.
2. **Attribution path.** `signer=private_pem_bytes` (our wave-2 keypair
   material, reused — no new key machinery) makes each row:
   - `sigAlg: "ed25519"` (registered value, their §8.1)
   - `sigKeyFp: sha256(normalized SPKI PEM of the public key)` → 64 lowercase
     hex (their §8.2 fingerprint law, byte-identical to quilt-jev-toolkit
     organ v3 `publicKeyFingerprint` — one identity across repos by name)
   - `sig: Ed25519 over the SAME preimage the HMAC covers, "qmr1:sig:"+id` →
     128-hex (their §8.1: id unchanged, hash slot and sig slot orthogonal)
   - `prev` chaining unchanged; `id` derivation unchanged.
3. **Mutual exclusion with dev mode.** The empty-dev-secret fallback
   (`_qmr1_secret` stderr warning path) refuses attribution: calling
   `export_qmr1(..., signer=...)` with the empty dev secret raises
   ValueError. An attribution row minted under a documented unsigned dev mode
   would be a candor violation in dialect form.
4. **Capability gate mirrors theirs.** Their `--v3` versioned-capability
   pattern is the adoption gate; our kwarg is the same shape (opt-in, default
   off, consumer-side verification decides).

## Pins (FAIL-first, implemented by the build lane — not this doc)

- **Q2A1 dialect compatibility (load-bearing, cross-repo).** A v2 export
  verifies under quilt-mcp-receipts' own `verify_chain`/`verify_attribution`
  with `keyring = {our_fp: our_public_pem}`; with a keyring missing our fp →
  `E_UNKNOWN_SIGNER`; with the wrong key under our fp → `E_BAD_SIGNATURE`.
  RED first: run all three against a v1 export before the build exists.
- **Q2A2 fingerprint law.** `sigKeyFp` equals an independently recomputed
  sha256 of the SPKI PEM (trailing newline included, per §8.2).
- **Q2A3 v1 regression.** Default (`signer=None`) export on a fixed store is
  byte-identical to the wave-3 output for the same store+secret.
- **Q2A4 attribution ≠ truth.** A body edit in a v2 export still fails id
  re-derivation (names the line, existing verify law); attribution only names
  the signer, never endorses content.

## Honest boundaries (carried, sealed)

- Attribution proves WHO signed, never that the content is TRUE.
- Anchoring ≠ verifying (carried from CAPSULE-ANCHORING-ADAPTER).
- We emit rows; we do NOT build a keyring/registry — the keyring is
  quilt-mcp-receipts' surface. Consume-don't-rival, weight law.
- Selective-disclosure honesty (README limit 5) applies unchanged: a v2
  export proves integrity of included rows, never completeness of the filter.
- Core stays stdlib-only; `cryptography` remains the one optional dependency.
- Hmac shared-secret path is the qmr1 law unchanged; §8.3 keyring refusals
  apply to ed25519 rows only.

## Kill switch

Any byte-level drift in qmr2 §8 (docs/qmr2-design.md §8.1–§8.5) → revert to
v1 emission only, log a WATCH entry, no further attribution work until the
dialect restabilizes. Their versioned-capability pattern (--v3) is the gate.

## Referral edge

None minted by this pre-registration (docs-only). On merge of the build PR:
doubt-ledger → quilt-mcp-receipts CANDIDATE edge (we emit what their
verify_attribution consumes), PENDING at birth per weight law, VERIFIED only
on merge — never self-upgraded.
