# Fusion Roadmap & QA Gates

Four phases. Each ends at a gate; no phase starts before the previous
gate is green. Each gate closes with an improvement loop: what the phase
taught goes into the next phase's plan (and, where it changes the
convention, into a versioned SPEC amendment).

## Phase 1 — Foundation (the Convention)

**Ships:** SPEC.md 1.0 · examples/crazy-ones fixture · README · this roadmap.

**Gate:**
- [x] Full conformance sweep of the fixture against SPEC §11 — zero
      errors, zero warnings (mechanical, scripted in the phase plan).
- [x] Spec ↔ fixture cross-read — every SPEC §2–9 rule demonstrated.
- [x] Fresh-eyes read of SPEC.md for contradiction and ambiguity.

## Phase 2 — The CLI (the notary)

**Ships:** `fusion` as a uv tool — new, hub, log, index, check, status,
today, agenda; `--json` everywhere; `--since` on status/log.

**Gate:**
- [x] `fusion check examples/crazy-ones` → 0 errors, 0 warnings.
- [x] `fusion index` regenerates the fixture's INDEX files byte-identical
      (golden-file test).
- [x] pytest suite green; every SPEC §11 rule has a failing-fixture test
      proving detection.
- [x] Round-trip: `fusion new` a scratch bucket → log all 11 verbs →
      check green → status/today/agenda sane.
- [x] Docs: `--help` complete for all 8 commands; README Status updated.

## Phase 3 — The skill family (the judgment)

**Ships:** fusion-intake, fusion-librarian, fusion-planner, fusion-analyst
— agentskills.io-compliant, self-contained, byte-identical conventions copy.

**Gate:**
- [x] Duplication check green (conventions copies byte-identical).
- [x] Each skill exercised on a scratch bucket; every scenario leaves
      `fusion check` green and the ledger correctly signed.
- [x] Intake gate proven on real legacy formats (xlsx, docx, pdf, csv).
- [x] Skills reviewed against the writing-skills quality bar.

## Phase 4 — Dogfood + release (the life)

**Ships:** two real buckets (personal + pro), first reflection cycles,
open-source readiness.

**Gate:**
- [ ] `fusion today` composes a real morning correctly across buckets.
- [ ] One full reflection cycle per bucket: proposals → judgment →
      conventions updated → `reflected` signed.
- [ ] A week of real use; frictions recorded and triaged.
- [x] Open-source pass: no personal paths, install-from-clean-machine
      test, README truthful.
      Evidence: sweep clean (test_skill_family + repo audit, 2026-07-10) ·
      docs/acceptance/2026-07-10-phase-4-install.md · README claims
      re-verified against the tree in the Task-7 commit.

## The improvement loop (all phases)

At every gate: run the phase's checks · record what the phase taught ·
fold lessons into the next plan · amend the spec only through a versioned
change. The system that tells its users to reflect, reflects.
