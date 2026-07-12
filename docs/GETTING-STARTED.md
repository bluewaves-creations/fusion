# Getting started

Fusion is one line: the installer brings uv, the CLI, and the four
skills. Then you make your first bucket and start living in it. Ten
minutes, no wizard.

## What you need

- [uv](https://docs.astral.sh/uv/) — installs and runs the CLI.
- `git` — every bucket is its own repo; `fusion new` runs `git init` and
  the first commit for you (and only warns if git is missing).
- An agent that reads [Agent Skills](https://agentskills.io) — Claude Code,
  Pi, Goose, or whatever comes next.
- Optional: LibreOffice (`soffice` on PATH) — only fusion-intake's
  docx/pptx/legacy-office/html route needs it.

## One line

```bash
curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
```

Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.ps1 | iex"
```

One line installs uv (which brings Python), the `fusion` CLI, and the
four skills into every agent on your machine that reads them.

## The manual way

No script between you and the steps it runs:

```bash
git clone https://github.com/bluewaves-creations/fusion.git
uv tool install ./fusion/cli
fusion --version
```

The CLI is the notary: it records (ledger), registers (hub, manifest,
indexes), checks (the convention), and composes your day. It never judges —
that's the skills' job.

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

- `fusion: command not found` — re-run the one-liner, or
  `uv tool install fusion-cli`, or install from a clone
  (`uv tool install ./fusion/cli`).
- `fusion check` is red — every code (E1–E8 errors, W1–W8 warnings) is
  defined in [SPEC.md §11](../SPEC.md#11-conformance); the message names
  the file. And a bucket is a git repo: `git diff` shows what changed,
  `git checkout` undoes it. Nothing is unrecoverable.
- `git` was missing when you ran `fusion new` — the bucket scaffolded
  without a repo; install git, then `git init && git add -A && git commit`
  inside the bucket.
- The installer failed partway — every step prints the manual command it
  was running; finish by hand from there. The three steps are: install
  uv, `uv tool install fusion-cli`, `fusion setup`.

## Staying current

```bash
fusion update
```

One verb: upgrades fusion-cli through uv, then re-runs `fusion setup`
from the new binary so the bundled skills refresh everywhere setup put
them. If you pinned a version at install time (`FUSION_VERSION=…`), uv
respects the pin — upgrade past it with uv directly. If fusion wasn't
installed through uv, `fusion update` says so and tells you what to
run instead.

## Leaving cleanly

`fusion setup --remove` takes the skills back out of every agent it
installed into (it only removes what it can prove it created), then:
`uv tool uninstall fusion-cli`. Buckets are yours — nothing touches them.

## Where to go next

- [A finished bucket to wander](../examples/README.md) — see the
  convention instantiated before you read it abstract.
- [Buckets everywhere](BUCKETS-EVERYWHERE.md) — migrate a messy folder
  in, sync a bucket between machines, rebuild the hub on a new one,
  track a project whose code lives outside.
- [The convention itself](../SPEC.md) — SPEC.md is the actual product.
- [The CLI, command by command](../cli/README.md).
- [The four skills](../skills/README.md).
