# Getting started

Fusion is two moves: install a small CLI, copy four skills. Then you make
your first bucket and start living in it. Ten minutes, no wizard.

## What you need

- [uv](https://docs.astral.sh/uv/) — installs and runs the CLI.
- `git` — every bucket is its own repo; `fusion new` runs `git init` and
  the first commit for you (and only warns if git is missing).
- An agent that reads [Agent Skills](https://agentskills.io) — Claude Code,
  Pi, Goose, or whatever comes next.
- Optional: LibreOffice (`soffice` on PATH) — only fusion-intake's
  docx/pptx/legacy-office/html route needs it.

## Move one — the CLI

From a clone (or once published on PyPI: `uv tool install fusion-cli`):

```bash
git clone https://github.com/bluewaves-creations/fusion.git
uv tool install ./fusion/cli
fusion --version
```

The CLI is the notary: it records (ledger), registers (hub, manifest,
indexes), checks (the convention), and composes your day. It never judges —
that's the skills' job.

## Move two — the skills

```bash
cp -r fusion/skills/fusion-* ~/.agents/skills/
```

(Or your agent's skills directory. The skills are standard-compliant and
self-contained — copying them **is** installing them.)

Four skills, four accountabilities: **fusion-intake** guards what enters,
**fusion-librarian** owns the library, **fusion-planner** runs activities,
**fusion-analyst** builds reports and exports.

## Your first bucket

A bucket is a life-domain — personal, your studio, one per company. Few and
bold. Each is its own git repo, private by construction.

```bash
fusion new ~/buckets/personal --kind personal \
  --description "Home base: admin, health, house, money."
```

That scaffolds six zones (`inbox/ sources/ library/ activities/ workbench/
output/`), writes `BUCKET.md`, opens the ledger, and registers the bucket in
the hub (`~/.fusion/hub.md`) — the one-file map your agent reads to know
your world.

```bash
fusion hub          # your buckets
fusion status       # this bucket at a glance
fusion check        # audit against the convention — 0 errors, carry on
```

## Live in it

**You never file.** Drop anything — a PDF, a spreadsheet, a mail export —
into `inbox/` and tell your agent to run intake. The gate classifies it
(new, updated, duplicate, conflicting), preserves the original byte-for-byte
under `sources/`, converts it losslessly to markdown in the library, and
signs the ledger. You judge; it operates; the files remember.

It looks like this:

```
You:    process the inbox
Agent:  Intake report — 3 files.
        contract.pdf     → new        converting
        brochure.pdf     → duplicate  auto-skipped (exact)
        q1-report.xlsx   → updated    supersede q1-report.xlsx — confirm?
You:    yes
Agent:  Admitted, converted, ledger signed, fusion check green.
```

"Process the inbox", "run intake", "archive this", "what's on my plate",
"report on X" — plain words; the skills know their triggers.

Each morning:

```bash
fusion today        # commitments and active work, across every bucket
fusion agenda       # the wider horizon: dated things first
```

And once a week, ask the librarian to **reflect**: it reads the ledger,
proposes prunes and conventions, you judge, it signs `reflected`. That's the
metabolism — the bucket learns.

## When something goes wrong

- `fusion: command not found` — install from the clone
  (`uv tool install ./fusion/cli`); PyPI publication lands with Phase 4.
- `fusion check` is red — every code (E1–E8 errors, W1–W5 warnings) is
  defined in [SPEC.md §11](../SPEC.md#11-conformance); the message names
  the file. And a bucket is a git repo: `git diff` shows what changed,
  `git checkout` undoes it. Nothing is unrecoverable.
- `git` was missing when you ran `fusion new` — the bucket scaffolded
  without a repo; install git, then `git init && git add -A && git commit`
  inside the bucket.

## Where to go next

- [A finished bucket to wander](../examples/README.md) — see the
  convention instantiated before you read it abstract.
- [The convention itself](../SPEC.md) — SPEC.md is the actual product.
- [The CLI, command by command](../cli/README.md).
- [The four skills](../skills/README.md).
