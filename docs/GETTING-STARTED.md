# Getting started

Fusion is two moves: install a small CLI, copy four skills. Then you make
your first bucket and start living in it. Ten minutes, no wizard.

## What you need

- [uv](https://docs.astral.sh/uv/) — installs and runs the CLI.
- An agent that reads [Agent Skills](https://agentskills.io) — Claude Code,
  Pi, Goose, or whatever comes next.
- Optional: LibreOffice (`soffice` on PATH) — only fusion-intake's
  docx/pptx/legacy-office route needs it.

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
(new, update, duplicate, conflicting), preserves the original byte-for-byte
under `sources/`, converts it losslessly to markdown in the library, and
signs the ledger. You judge; it operates; the files remember.

Each morning:

```bash
fusion today        # commitments and active work, across every bucket
fusion agenda       # the wider horizon: dated things first
```

And once a week, ask the librarian to **reflect**: it reads the ledger,
proposes prunes and conventions, you judge, it signs `reflected`. That's the
metabolism — the bucket learns.

## Where to go next

- [The convention itself](../SPEC.md) — SPEC.md is the actual product.
- [A finished bucket to wander](../examples/README.md) — the crazy-ones tour.
- [The CLI, command by command](../cli/README.md).
- [The four skills](../skills/README.md).
