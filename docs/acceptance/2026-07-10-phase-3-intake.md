# Phase 3 acceptance — fusion-intake, real formats

ROADMAP gate line 3: "Intake gate proven on real legacy formats (xlsx,
docx, pdf, csv)." Two halves: a scripted integration test and a played
acceptance run on a scratch bucket, following `skills/fusion-intake/SKILL.md`
and its references exactly, no shortcuts, no reading the scripts' source.

## Part A — integration test

`skills/fusion-intake/tests/test_integration.py` — deterministic pipeline
(gate → admit → prepare → link) over real xlsx/csv/pdf/eml/docx fixtures,
with the `fusion` CLI as the conformance oracle.

`uv run --project cli fusion check examples/crazy-ones --json` was run
first to verify the real top-level keys (`bucket`, `ok`, `errors`,
`warnings`) — the brief's two assertion lines (`report["errors"] == []`
and `report["warnings"] == []`) already matched; no adaptation needed.

One adaptation was required beyond the JSON-key note: the brief's final
block (`for name in drops: (bucket / "inbox" / name).unlink()`) assumes
inbox files still exist after the per-file loop. They don't —
`convert.admit()` **moves** (not copies) each file straight from `inbox/`
to `sources/` as its own first act, so by the time that block runs, every
drop is already gone from `inbox/` and `unlink()` raises
`FileNotFoundError`. Rewritten to assert the already-empty state instead
of re-deleting it (see Frictions, #1).

```
uv run --with pytest --with pyyaml --with openpyxl --with pymupdf \
    pytest skills/fusion-intake/tests/test_integration.py -v
```

Result: **1 passed** (docx leg included — `soffice` 26.2.4.2 present on
PATH). Full skill suite (`test_gate.py` + `test_convert.py` +
`test_integration.py`): **29 passed**.

## Part B — acceptance run (agent-in-the-loop)

Sandbox, before any `fusion` call:

```
export FUSION_HUB=/tmp/fusion-accept/hub.md FUSION_ACTOR=claude
mkdir -p /tmp/fusion-accept
cd <fusion repo root>
uv run --project cli fusion new /tmp/fusion-accept/intake-demo --kind personal \
    --description "Intake acceptance bucket."
uv run skills/fusion-intake/tests/make_fixtures.py
# moved scores.xlsx, inventory.csv, audit.pdf, procedure.docx, mail.eml
# into /tmp/fusion-accept/intake-demo/inbox/
```

`fusion new` scaffolded the bucket and registered it in
`/tmp/fusion-accept/hub.md`. Read `references/fusion-conventions.md` and
the fresh `BUCKET.md` (no Rules/Delegations yet) before touching anything,
per SKILL.md's opening instruction.

---

### Scenario 1 — clean new xlsx + csv + pdf + docx + eml

**Gate (Stage 1):**
```
uv run skills/fusion-intake/scripts/gate.py --bucket /tmp/fusion-accept/intake-demo
→ gate: {'exact_dups': 0, 'near_dups': 0, 'update_candidates': 0, 'clean_new': 5}
```
All five `clean_new`. Topic match against `library/INDEX.md` (empty,
fresh bucket) found nothing — no overlap, no reclassification.

**Intake report:**

| Incoming | Class | Matches | Action |
|---|---|---|---|
| scores.xlsx | new | — | converting |
| inventory.csv | new | — | converting |
| audit.pdf | new | — | converting |
| procedure.docx | new | — | converting |
| mail.eml | new | — | converting |

**Admit + prepare + close**, per file (category = short plural noun,
BUCKET.md has no filing Rules):

- `scores.xlsx` → `reports/scores.xlsx` (extractive, `done: true`).
  Refined title/summary from the table (Acme Corp 78.5, Northwind 91 —
  verbatim, pipe-escaped notes cell, all-empty column pruned).
- `inventory.csv` → `gear/inventory.csv` (extractive, `done: true`).
  Jazzmaster 1962 12500.50, Pedalboard 2300 — verbatim, BOM consumed.
- `audit.pdf` → `reports/audit.pdf` (`pdf_text`, 2 pages, both
  `needs_vision: false` — text layer sufficient, matches the fixture's
  single-line `insert_text` content exactly; see Frictions #2 for why the
  page text is naturally truncated mid-word). Both pages transcribed
  verbatim into the document; no image read required by the manifest.
- `procedure.docx` → `procedures/procedure.docx` (`libreoffice` route via
  `soffice`, 1 page, `needs_vision: false` at text_chars=102, just above
  the 100-char floor). **Read `page-001.png` anyway as a spot-check** —
  image matches the extracted text exactly ("Onboarding procedure for the
  studio bucket. / Step one: read the conventions. Step two: sign the
  ledger.").
- `mail.eml` → `mails/mail.eml` (`mail` route). Body: "Rehearsal moves to
  Thursday. Bring the Jazzmaster." `created:` set from the Date header
  (2026-07-09). One attachment extracted, `setlist.csv`. Per
  `references/convert.md`'s mail note, the protocol here is to *tell the
  user and offer to move the attachment into inbox/* for its own gate
  pass — **a real stop-and-ask point not covered by the six numbered
  scenarios**. Noted the offer in the document's summary and declined it
  for this run's scope (the attachment's content is preserved
  byte-identical inside the admitted `.eml` original either way — nothing
  is lost, see Frictions #3).

Each file closed: `link` → `fusion log converted "sources/<cat>/<file> →
<doc>" --as claude` → `fusion index /tmp/fusion-accept/intake-demo --as
claude` → `fusion check ... --json`.

`fusion check /tmp/fusion-accept/intake-demo --json`:
```json
{"bucket": "intake-demo", "ok": true, "errors": [], "warnings": []}
```
(First check attempt returned a `W2` "INDEX.md stale" warning because
`fusion index` was called without a path argument and errored —
`index` and `check` take a positional `path`, not `--bucket` like `log`;
a CLI-surface inconsistency, see Frictions #4. Re-run with the correct
positional form was green.)

Ledger tail (5 `converted` + 1 `indexed`), MANIFEST (5 rows, full
sha256, all `library` columns filled), `library/INDEX.md` regenerated
with 5 documents across `gear/`, `mails/`, `procedures/`, `reports/`.
Inbox empty. Gate run file `gate-873d1b6fcfff.json` deleted per
`references/gate.md`'s end-of-run instruction.

---

### Scenario 2 — exact duplicate

Re-dropped `scores.xlsx` (copied byte-identical from `sources/reports/`,
sha256 confirmed matching: `cfddf2115bd5a2...`).

```
uv run skills/fusion-intake/scripts/gate.py --bucket /tmp/fusion-accept/intake-demo
→ gate: {'exact_dups': 1, ...}
```
`exact_dups: [{"incoming": "scores.xlsx", "matched_source":
"reports/scores.xlsx", "auto_skip": true}]`.

Per `references/gate.md`: recorded in the report, **no prompt, no
convert** — an exact re-drop carries no new information.

| Incoming | Class | Matches | Action |
|---|---|---|---|
| scores.xlsx | duplicate (exact) | sources/reports/scores.xlsx | auto-skipped (exact) |

Nothing in `SKILL.md`/`references/gate.md` specifies whether the
auto-skipped duplicate should be cleared from `inbox/` — the fidelity
contract ties inbox deletion to "MANIFEST link + ledger + green check,"
none of which an exact-dup ever goes through. `fusion check` doesn't
flag files left in `inbox/` either. Judgment call: removed the
now-confirmed-redundant copy from inbox (its content is provably already
preserved, byte-identical, in `sources/`) — see Frictions #5. MANIFEST,
ledger, library untouched (still 5/5/5 from Scenario 1). `fusion check`
stayed green.

---

### Scenario 3 — near duplicate

Dropped `gear-export.csv`: same rows as `sources/gear/inventory.csv`,
header re-cased, BOM dropped, one trailing blank line (a plausible
"re-export").

```
uv run skills/fusion-intake/scripts/gate.py --bucket /tmp/fusion-accept/intake-demo
→ gate: {'near_dups': 1, ...}
```
`near_dups: [{"incoming": "gear-export.csv", "matched_source":
"gear/inventory.csv", "similarity": 1.0, "auto_skip": false}]`.

| Incoming | Class | Matches | Action |
|---|---|---|---|
| gear-export.csv | duplicate (near) | sources/gear/inventory.csv | ASK (skip / update / new) |

**STOP — would ask the user:** "`gear-export.csv` is a near-duplicate
(similarity 1.00) of `sources/gear/inventory.csv` — same data, different
formatting (no BOM, re-cased header, trailing blank line). Skip it, treat
it as an update to the existing document, or admit it as new?"

Per the acceptance protocol, picked the stated default: **skip**. No
admit, no convert. Removed the file from inbox (same judgment as
Scenario 2 — a confirmed skip of content proven identical). `fusion
check` stayed green; MANIFEST/ledger/library unchanged.

---

### Scenario 4 — update

Dropped `2026-07-09_inventory.csv` (normalizes to `inventory`, matching
`sources/gear/inventory.csv`): Jazzmaster row unchanged, Pedalboard
qty/price changed (1→2, 2300→4600), one new row (Cables, 3, 45).

```
uv run skills/fusion-intake/scripts/gate.py --bucket /tmp/fusion-accept/intake-demo
→ gate: {'update_candidates': 1, ...}
```
`update_candidates: [{"incoming": "2026-07-09_inventory.csv",
"matched_source": "gear/inventory.csv", "similarity": 0.5, "history": []}]`
— inside `[UPDATE_SIM_FLOOR, NEAR_DUP_THRESHOLD)` with a name match, as
designed.

| Incoming | Class | Matches | Action |
|---|---|---|---|
| 2026-07-09_inventory.csv | updated | sources/gear/inventory.csv | supersede + reconcile (confirm) |

Read both — same logical identity (the gear inventory), one candidate,
unambiguous → class `updated`. Report states the confirmed-update plan
verbatim per `references/gate.md`: admit the new file as its own source
(no name collision, no rename needed), reconcile
`library/gear/inventory.md` in place, `updated:` bumped, `source:`
repointed, new MANIFEST row added, old row untouched.

Played the confirmed path:
```
convert.py admit --file 2026-07-09_inventory.csv --category gear --actor claude
convert.py prepare --source gear/2026-07-09_inventory.csv \
    --dest library/gear --slug inventory --aurora library
```
`prepare` overwrote `library/gear/inventory.md` in place (same path) with
the reconverted table (Jazzmaster 12500.50, Pedalboard now 4600, new
Cables row). Refined title/summary and **added `updated: '2026-07-10'`**
by hand (the extractive writer's seed only carries `created:` — bumping
`updated:` on reconcile is the operator's job, not scripted). Then
`link` → `fusion log converted ... --note "supersede + reconcile: ..."`
→ `fusion index` → `fusion check --json` → green.

Verified: **one** library document (`library/` still 5 files, not 6);
`updated:` present and bumped; **two** MANIFEST rows for `gear/`
(`inventory.csv` and `2026-07-09_inventory.csv`), both sources present on
disk under `sources/gear/`, old row's `library` column still points at
the same reconciled doc.

---

### Scenario 5 — conflict

Dropped `acme-score-revision.csv`: `Acme Corp,82,revised after Q2
review` — restates Scenario 1's Acme Corp score (78.5 in
`library/reports/scores.md`) with a different value (82).

```
uv run skills/fusion-intake/scripts/gate.py --bucket /tmp/fusion-accept/intake-demo
→ gate: {'clean_new': 1, ...}   (acme-score-revision.csv)
```
Stage 1 saw `clean_new` — expected, since gate.py's text-similarity index
compares against `sources/`, where the matching figure lives in
`sources/reports/scores.xlsx` (binary; decodes to noise, near-zero
similarity — Stage-1's own documented limitation, "full content
comparison is Stage 2's judgment work").

Stage 2 topic match: grepped `library/` for "Acme" →
`library/reports/scores.md` claims Acme Corp 78.5; the incoming file
claims 82 for the same supplier, same metric. **Contradiction** →
reclassified `conflicting` per `references/gate.md`.

| Incoming | Class | Matches | Action |
|---|---|---|---|
| acme-score-revision.csv | conflicting | library/reports/scores.md | hold — score 78.5 vs 82 |

Presented both claims, **converted nothing**: no admit, no prepare, no
ledger entry. File left in `inbox/` pending human resolution (accept as
correction / reject / keep both with a note) — the brief specifies no
default for this scenario, only that nothing converts, so the run stops
here by design. `fusion check` stayed green even with the file still
sitting in `inbox/` (see Frictions #5 — `check` never inspects `inbox/`
contents).

---

### Scenario 6 — unsupported format

Dropped `mystery.xyz` (plain text, unrecognized extension — not in
SKILL.md's supported list: xlsx, csv, docx, pptx, pdf, images, .eml,
markdown/text).

```
uv run skills/fusion-intake/scripts/gate.py --bucket /tmp/fusion-accept/intake-demo
→ gate: {'clean_new': 2, ...}   (acme-score-revision.csv still pending + mystery.xyz)
```
Stage 1 has no format awareness — `mystery.xyz` classifies `clean_new`
same as any other new file.

**Original run (2026-07-10, superseded — preserved for the record).**
Followed the documented pipeline literally (no scripts read beyond what
SKILL.md/references direct): Stage 2 offered no explicit guard for
unrecognized extensions, so per the pipeline order — Classify → **Admit**
→ Prepare — admitted it:
```
convert.py admit --file mystery.xyz --category misc --actor claude
→ {"source": "misc/mystery.xyz", "sha256": "255cb233...", "manifest_row": true}
```
This **moved** `mystery.xyz` out of `inbox/` into `sources/misc/` —
`admit` performed no extension check at the time. Only then did
`prepare` refuse:
```
convert.py prepare --source misc/mystery.xyz --aurora explore
→ intake: unsupported format: .xyz — the gate refuses what it cannot preserve
(exit 1)
```
The refusal itself fired loudly and correctly — but the file did **not**
stay in `inbox/` as the brief's scenario expects. `sources/` is
immutable (`Never modify, rename, or delete anything in sources/`), so
this could not be undone: `mystery.xyz` ended up permanently in
`sources/misc/` with a MANIFEST row whose `library` column is `—`
forever, no document, no way to retry through the normal close path.
`fusion check` did not flag this dangling row either — confirmed green
with no warnings. A `noted` ledger entry was logged to leave an audit
trail since none of the eleven verbs fit "refused":
```
fusion log noted "mystery.xyz: admitted to sources/misc/ then prepare \
refused (unsupported format .xyz) — no library doc created, MANIFEST \
row dangling; friction — see acceptance transcript" --as claude
```
This was the acceptance run's most significant finding.

**Re-run, post-fix (2026-07-10, same day).** `convert.py`'s `admit()`
now checks the extension against `SUPPORTED_EXTS` and refuses **before**
moving anything — closing the gap above. Verified in a minimal scratch
bucket built like `test_convert.py`'s `bucket` fixture
(`/tmp/fusion-accept6/bucket`, empty `sources/MANIFEST.md` seeded with
just the header row):
```
$ uv run skills/fusion-intake/scripts/convert.py admit \
    --bucket /tmp/fusion-accept6/bucket --file mystery.xyz \
    --category records --actor claude
intake: unsupported format: .xyz — the gate refuses what it cannot
preserve; the file stays in inbox/
(exit code 1)
```
Confirmed after the run: `inbox/mystery.xyz` still present;
`sources/records/` was never created; `sources/MANIFEST.md` unchanged
(header only — no `mystery.xyz` row, nothing to dangle). The refusal now
fires before anything leaves `inbox/`, matching SKILL.md's fidelity
contract ("the gate refuses what it cannot preserve; file stays in
inbox") exactly. `_route`'s own refusal inside `prepare()` is kept as
defense-in-depth for direct `prepare` calls that bypass `admit`. See
Frictions #6, now RESOLVED.

---

## Final state

`fusion check /tmp/fusion-accept/intake-demo --json`:
```json
{"bucket": "intake-demo", "ok": true, "errors": [], "warnings": []}
```

Ledger tail:
```
- 10:52 · claude · converted · sources/mails/mail.eml → library/mails/mail.md
- 10:52 · claude · indexed · library/ (5 documents)
- 10:55 · claude · converted · sources/gear/2026-07-09_inventory.csv → library/gear/inventory.md — "supersede + reconcile: qty/price update on pedalboard, new cables row"
- 10:55 · claude · indexed · library/ (5 documents)
- 10:57 · claude · noted · mystery.xyz: admitted to sources/misc/ then prepare refused (unsupported format .xyz) — no library doc created, MANIFEST row dangling; friction — see acceptance transcript
```

MANIFEST tail (7 rows total — 5 from Scenario 1, +1 update source from
Scenario 4, +1 dangling from Scenario 6):
```
| gear/2026-07-09_inventory.csv | 2026-07-10 | claude | eabbe35b... | library/gear/inventory.md |
| misc/mystery.xyz              | 2026-07-10 | claude | 255cb233... | — |
```

`library/` — 5 documents (`gear/inventory.md`, `mails/mail.md`,
`procedures/procedure.md`, `reports/audit.md`, `reports/scores.md`).
`inbox/` — 1 file remaining (`acme-score-revision.csv`, Scenario 5's
unresolved conflict, correctly held pending human resolution).

## Verdict

**DONE_WITH_CONCERNS.** The gate is sound on its happy paths — all five
real formats (xlsx, csv, pdf, docx, eml) converted losslessly and
verbatim (numbers, pipe-escapes, empty-column pruning, vision spot-check
all checked out); exact-dup, near-dup, and update-with-supersede all
behaved exactly as `references/gate.md` describes, including the
identity guard and the `updated:` bump. `fusion check` was green at
every close point. But the acceptance run surfaced real gaps — most
importantly #6, a data-integrity-adjacent one — that should feed the
Phase 4 list before this gate is exercised on a live bucket.

## Frictions (feed the Phase-4 list)

1. **Integration-test assumption bug (fixed in the test, not the
   scripts).** The brief's `test_integration.py` assumed inbox files
   persist until an explicit `unlink()` at the end; `convert.admit()`
   actually *moves* each file out of `inbox/` as its first act, so the
   assumption was false regardless of the `check --json` key question.
   Adapted the test to assert the already-empty state.
2. **Fixture PDF text is naturally truncated, not a bug.** `make_text_pdf`
   calls `page.insert_text((72,72), text, fontsize=11)` with no wrap
   rectangle; at that fontsize/margin the text runs off the page's right
   edge partway through, so the actual extractable text layer really is
   ~111 chars per page, cut mid-word ("...the supplie"). `probe_pdf_text_layer`
   and the resulting document are faithful to what's actually on the
   page — flagged here only so a future reader doesn't mistake the
   truncation for an extraction bug.
3. **No stop-and-ask default for mail attachments.** `references/convert.md`'s
   mail section says to "tell the user, and offer to move [attachments]
   to `inbox/`" but, unlike near-dup/updated/conflicting, this isn't one
   of the four locked classes and has no default. A real operator would
   need to actually ask; this run declined the offer for scope and noted
   it in the document instead. Consider giving this a stated default too.
4. **CLI flag inconsistency: `log` takes `--bucket`, `index`/`check` take
   a positional path.** Cost one failed command
   (`fusion index --bucket ...` → `unrecognized arguments: --bucket`)
   before falling back to the positional form. Minor, but worth
   standardizing or documenting explicitly in the conventions card's CLI
   crib.
5. **No documented disposition for skipped/resolved-pending inbox
   files.** Neither `gate.md` nor the fidelity contract says what happens
   to the physical file in `inbox/` after an exact-dup auto-skip or a
   confirmed near-dup skip — and `fusion check` never inspects `inbox/`
   contents at all, so a bucket can accumulate stale, already-resolved
   files indefinitely with the check staying green throughout. This run
   made the judgment call to delete confirmed-redundant copies; that call
   isn't backed by the docs.
6. **Highest-severity: unsupported-format files are not guaranteed to
   "stay in inbox."** `admit()` performed no extension/format validation —
   it would happily move *any* file from `inbox/` into the immutable
   `sources/` tree, registering a MANIFEST row, before `prepare()` ever
   got a chance to raise `IntakeError: unsupported format`. Following
   the documented pipeline order (Classify → Admit → Prepare) exactly as
   written, `mystery.xyz` ended up permanently exiled to
   `sources/misc/mystery.xyz` with a dangling, never-linkable MANIFEST
   row — not "refused loudly with the file staying in inbox" as
   SKILL.md's fidelity contract implies. None of SKILL.md, `gate.md`, or
   `convert.md` told the operator to check the extension against the
   supported list *before* calling `admit`.

   **RESOLVED**, same day (2026-07-10), commit `fusion-intake: the gate
   refuses at admit, not after — unsupported formats never reach
   sources/ (acceptance finding)`. Option (b) from the original
   recommendation was implemented: extension validation moved into
   `admit()` itself, checked against a new `SUPPORTED_EXTS` set right
   after the `src.is_file()` guard, so the refusal now fires before the
   file ever leaves `inbox/`. `_route`'s refusal inside `prepare()` is
   kept as defense-in-depth for direct `prepare` calls. Covered by a new
   test, `test_admit_refuses_unsupported_format` in
   `skills/fusion-intake/tests/test_convert.py`, and re-verified live —
   see the Scenario 6 re-run above. Frictions #1–#5 remain open as
   recorded; only this one was in scope for the fix.
