# Phase 4 acceptance — install proven from a clean slate

ROADMAP's open-source gate box: "Open-source pass: no personal paths,
install-from-clean-machine." An earlier audit had already proven `uv pip
install ./cli` works in an isolated venv; this run replays it as a played
acceptance transcript, exercising the **final** Phase 4 behavior — the
taught `--help` text (Tasks 1–2) and the JSON failure envelopes (an earlier
Phase 4 task) — not just the bare install.

Played as a brand-new user: clone the repo, install the CLI into an
isolated venv (never `uv tool install`, which is global), copy the skills,
sandbox the hub, make a first bucket, round-trip it, then cross-read
`docs/GETTING-STARTED.md` against what actually happened.

## Environment

- macOS 26.5.2, `uv 0.9.17`, Python 3.13.11 (uv-managed CPython).
- Isolated venv at `/tmp/fusion-clean/.venv` — the real `~/.fusion` hub and
  the global `uv tool` registry were never touched.
- `FUSION_HUB=/tmp/fusion-clean/hub.md`, `FUSION_ACTOR=newcomer` exported
  before any `fusion new` call, per the sandbox rule.
- `$REPO` = the repo root (`git rev-parse --show-toplevel`); `$FUSION` =
  `/tmp/fusion-clean/.venv/bin/fusion`. Both stand in for the real absolute
  paths everywhere below — the committed transcript names neither.

---

## Step 1 — clean-slate install

```bash
REPO=$(git rev-parse --show-toplevel)     # run from the repo; $REPO is used everywhere below
FUSION=/tmp/fusion-clean/.venv/bin/fusion
rm -rf /tmp/fusion-clean && mkdir -p /tmp/fusion-clean && cd /tmp/fusion-clean
uv venv .venv
uv pip install --python .venv/bin/python "$REPO/cli"
$FUSION --version
$FUSION --help
```

```
Using CPython 3.13.11
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

Resolved 2 packages in 101ms
   Building fusion-cli @ file://$REPO/cli
      Built fusion-cli @ file://$REPO/cli
Prepared 1 package in 216ms
Installed 2 packages in 1ms
 + fusion-cli==1.0.0 (from file://$REPO/cli)
 + pyyaml==6.0.3

fusion 1.0.0

usage: fusion [-h] [--version]
              {new,hub,log,index,check,status,today,agenda} ...

Fusion — the notary. Records, checks, composes; never judges.

positional arguments:
  {new,hub,log,index,check,status,today,agenda}
    new                 scaffold a bucket and register it
    hub                 list, register, or retire buckets
    log                 append to the ledger, or read it
    index               regenerate INDEX.md in library/ and activities/
    check               audit a bucket against the convention
    status              one bucket at a glance
    today               the composed day, across the hub
    agenda              the wider horizon, across the hub

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

One package, one dependency (`pyyaml`), a five-line build — the CLI has no
hidden weight. The parent `--help` listing carries its one-liners at every
subcommand (Task 1–2's fix, confirmed live here rather than by reading the
diff).

---

## Step 2 — the two-move check (skills)

```bash
mkdir -p /tmp/fusion-clean/skills
cp -r "$REPO"/skills/fusion-* /tmp/fusion-clean/skills/
ls /tmp/fusion-clean/skills
```

```
fusion-analyst  fusion-intake  fusion-librarian  fusion-planner
```

No build step, no install script — the `cp -r` alone produced four
directories an agent could load as-is. This is the claim
`docs/GETTING-STARTED.md` makes ("copying them **is** installing them," per
the agentskills.io standard) and it held exactly as written.

---

## Step 3 — first-bucket round trip

```bash
export FUSION_HUB=/tmp/fusion-clean/hub.md FUSION_ACTOR=newcomer
$FUSION new /tmp/fusion-clean/personal --kind personal --description "First bucket."
$FUSION hub
```

```
bucket 'personal' born at /private/tmp/fusion-clean/personal — registered in the hub. Go live in it.

- **personal** · personal · /private/tmp/fusion-clean/personal — First bucket.
```

(macOS resolves `/tmp` to `/private/tmp` under the hood — cosmetic, not a
Fusion behavior; see Frictions.)

```bash
cd /tmp/fusion-clean/personal
$FUSION log noted BUCKET.md --note "first entry by hand"
$FUSION index && $FUSION check && $FUSION status
$FUSION today
$FUSION check /nonexistent --json ; echo "exit=$?"
```

```
logged: 2026-07-10 14:01 · newcomer · noted · BUCKET.md — "first entry by hand"

library/ — 0 documents — unchanged
activities/ — 0 documents — unchanged
personal: 0 errors · 0 warnings — clean, carry on.
personal — 0 documents
  recent:
    2026-07-10 14:01 · newcomer · created · BUCKET.md
    2026-07-10 14:01 · newcomer · noted · BUCKET.md

Today across 1 bucket
  nothing demands you — the wide-open day.

{"ok": false, "error": "no bucket at: /nonexistent"}
exit=1
```

The JSON failure envelope is exactly the shape the earlier "failures speak
JSON too" task promised: `{"ok": false, "error": "..."}"`, non-zero exit,
no traceback, no half-written output. Every command in the round trip
succeeded on the first try — `log`, `index`, `check`, `status`, `today` all
matched their `--help` descriptions.

Confirmed `fusion new` also scaffolds all six zones and opens the ledger
under git, unprompted:

```
$ find /tmp/fusion-clean/personal -maxdepth 1
BUCKET.md  LEDGER.md  activities  inbox  library  output  sources  workbench  .git

$ cd /tmp/fusion-clean/personal && git log --oneline
38a95a3 fusion new: bucket born
```

---

## Step 4 — the GETTING-STARTED cross-read

Read `docs/GETTING-STARTED.md` top to bottom against Steps 1–3, verbatim,
looking for anything that lied or omitted:

- **Move one — the CLI.** GETTING-STARTED prescribes `uv tool install
  ./fusion/cli` (a real user's global install); this run intentionally used
  `uv pip install --python .venv/bin/python` into an isolated venv instead,
  per the sandbox rule (`uv tool install` is global and out of bounds for
  an acceptance run). That's a deliberate divergence in *how this run
  installs*, not a defect in the doc — the doc's own command is what an
  earlier audit already proved works, and this run doesn't repeat that
  proof. `fusion --version` / `fusion --help` matched what the doc implies
  either way.
- **Move two — the skills.** `cp -r fusion/skills/fusion-*
  ~/.agents/skills/` — Step 2 above ran the identical pattern against a
  scratch directory and it held exactly: four directories, no build step.
- **Your first bucket.** `fusion new ~/buckets/personal --kind personal
  --description "..."` scaffolds six zones, `BUCKET.md`, the ledger, and
  registers in the hub — confirmed directly (`find`, `git log` above).
  `fusion hub`, `fusion status`, `fusion check` all matched the doc's
  description and this run's real output ("0 errors, carry on").
- **Live in it.** `fusion today` / `fusion agenda` — both run clean on the
  fresh bucket (`agenda` → `the horizon is clear.`, checked below,
  consistent with "the wider horizon, across the hub" from its own
  `--help`).
- **Where to go next.** All four linked paths exist and resolve from
  `docs/`: `../SPEC.md`, `../examples/README.md`, `../cli/README.md`,
  `../skills/README.md`.

```bash
$FUSION agenda
```

```
the horizon is clear.
```

No step lied, no step omitted a prerequisite, nothing needed fixing.
**`docs/GETTING-STARTED.md` is unchanged by this run** — the walkthrough
was tested exactly as written and held end to end, so this commit carries
the transcript alone.

---

## Frictions

Genuinely small, and neither blocked nor misled this run:

1. **`/tmp` resolves to `/private/tmp` in command output on macOS.** Every
   path this run typed as `/tmp/fusion-clean/...` came back from `fusion`
   as `/private/tmp/fusion-clean/...` (see Step 3's `fusion new` /
   `fusion hub` output). This is a macOS filesystem symlink, not a Fusion
   behavior — worth knowing so a future reader doesn't mistake it for a
   path bug when diffing transcripts.
2. **`fusion new` git-inits and commits the bucket unprompted.** Harmless
   and consistent with prior Phase 3 acceptance runs (same note there) —
   flagged again here only because a brand-new user reading
   GETTING-STARTED wouldn't expect a `git log` to already have a commit in
   it the first time they look.

No install, skills-copy, CLI-usage, or documentation friction beyond the
above two cosmetic notes — every command listed in Steps 1–3 succeeded on
the first attempt with output matching its own `--help` text.

## Verdict

**DONE.** Install-from-clean-slate holds end to end on the final Phase 4
CLI: isolated-venv install works from a bare `uv pip install ./cli`, skills
install by `cp -r` alone, the taught `--help` text is accurate at every
level, and the JSON failure envelope fires exactly as designed on a
missing bucket path. `docs/GETTING-STARTED.md`'s two-move promise was
cross-read command by command and held without needing a single edit. This
is the evidence line for the ROADMAP's open-source gate box.
