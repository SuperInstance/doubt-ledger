# ONBOARDING — doubt-ledger

> Seed doc (fleet handoff 2026-10-06). Read with `README.md` (entry grammar +
> pins P1–P5) and `docs/WAVE4-IDEATION.md` (ranked candidates with kill
> switches). Mesh context: `SuperInstance/fleet-seeds` →
> `docs/handoff-2026-10-06/ORG-MESH.md`.

## 1. What this repo is now

**Trust relocates blindness; it does not delete it.** doubt-ledger is an
append-only, git-backed record of what you *stopped checking*, why, what
covers it, and what event brings it back. Every entry carries all five
grammar fields (empty field = rejected and named), every discharge requires a
written reason — an unreasoned discharge is just blindness again.

State at handoff: waves 1–3 merged (`poc` branch is the default — note:
**default branch is `poc`, not `main`**; main = poc tip). Wave-4 shipped so
far: candidate-1 qmr2-§8 attribution export (#12 merged), candidate-2
coverage/discharge query tool (#14 merged), candidate-3 adjudication-client
spec docs + build in flight. **Open PRs:** #16 (adjudication-client — wave-4
candidate-3 BUILD), #18 (receiptd collision hedge — cite/differentiate +
wave-4 lane re-rank), #19 (consistency review #16 × #18), #20 (bone-registry
reuse-metric adoption note). All four are one review family.

## 2. How it got here (the momentum)

- **Real origin, kept honest.** Born 2026-10-02 from a 21-hour live run whose
  every output passed independent verification — while the checkers
  themselves stopped being audited. The doubt was relocated, not deleted;
  this repo is the surface that makes the relocation legible.
- **Wave discipline.** Each wave ships smallest-first with FAIL-first pins
  and a kill switch: wave-1 poc (grammar, P1–P5), wave-2 export + Ed25519
  root signing, wave-3 qmr1-compatible receipt export (naming-alignment
  hedge), wave-4 ranked candidates from live org pulses.
- **Hedge doctrine.** Each wave checks the neighboring lanes (PAM, IETF AAT,
  capsule anchoring, Janus evidence-before-effect, receiptd) and either
  cites-and-differentiates or adopts — consume-don't-rival is the standing
  rule. The #18/#19 pair exists because a *new* neighbor (receiptd) appeared
  mid-wave and the ledger re-ranked itself rather than colliding.
- **Pins as the immune system.** P1 grammar-enforcement, P2 append-only
  (per-line checksum refuses rewrites), P3 fire-and-due (triggers mark
  entries `due`, discharge demands a reason), P4 git-resume (byte-identical
  across process restarts), P5 coverage-query (substring semantics — an
  honest limit, carried loudly).

## 3. The vision

Verification stacks relocate doubt upward: the checker trusts the builder,
the reviewer trusts the checker, the human trusts the review. At the top of
every stack is a *relocation event* nobody wrote down. doubt-ledger's thesis:
**the relocation is data.** Written down, it becomes queryable ("what is
trust letting through HERE?" — P5), dischargeable only with reasons, and
fireable by named triggers. This is the introspection half of the fleet's
honesty law — the receipts say what was proven; the doubt ledger says what
stopped being checked.

## 4. Roadmaps (several directions)

**Going now:** the wave-4 PR family #16/#18/#19/#20 (review together);
candidate-4 items are docs-level adoptions.

**Sketched futures:**
- **Adjudication-client completion.** The wave-4 candidate-3 build (#16)
  makes pre-registration entries adjudicable by an external party — the
  bridge from "recorded doubt" to "resolved doubt with a receipt."
- **qmr2 dialect watch.** The export dialect rides quilt-mcp-receipts' §8;
  kill switch is byte-level drift → revert to v1 export + WATCH entry. A
  standing watch lane (post-cron era) would evaluate this on each qmr release.
- **Coverage calculus.** Substring semantics (limit #5) is deliberately
  cheap; a structured `covered_by` graph would enable transitive coverage
  ("this stop is covered by a chain of three discharges") — genuinely new,
  ranked below adjudication.
- **Cross-ledger discharge.** A discharge in doubt-ledger could anchor as a
  receipt in quilt-mcp-receipts / quilt-jev-toolkit format — the identity
  keypair material is already shared (wave-2 Ed25519).

## 5. How it meshes

- **Neighbors cited, not rivaled:** quilt-mcp-receipts (qmr1/qmr2 dialects —
  our export target), quilt-jev-toolkit (Ed25519 identity + organ custody —
  shared byte-for-byte key semantics), receiptd (the hedge in #18), Janus /
  PAM / IETF AAT (docs hedges in `docs/`).
- **Doctrine siblings:** fleet-witness (deletion evidence) and this repo
  (stopped-checking evidence) are the two halves of *what trust lets through*.
  The referral graph tracks the edges; quilt-tools#40 booked the wave-1/2/3
  follow-through edges (#26/#27 VERIFIED).
- Org state: `fleet-seeds` → `docs/handoff-2026-10-06/HANDOFF.md`.
