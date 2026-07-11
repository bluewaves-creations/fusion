# Fusion

**A file-based working environment for humans and their AI colleagues.**

Here's to the ones who drown in legacy documents — the spreadsheets, the
PDFs, the decks, the mail threads — and decided the filing cabinet was the
problem, not them. Fusion is not a document-management system, not a PKM,
not another note app. It refuses the category.

> **The human judges, the AI operates, the files remember.**

## What it is

- **Buckets** — your life-domains (personal, studio, each company) as
  separate git repos. Private by construction. A tiny hub registers them.
- **Markdown + frontmatter, everywhere** — three required fields (`title`,
  `type`, `aurora`), summary-first, plain relative links. Readable by any
  human, any agent, forever.
- **Aurora** — eight words for what a thing means for your attention:
  commitments, focus, ops, collab, life, explore, archive, library. An
  attention system, not a taxonomy. It's what makes this calm instead of a
  hoard.
- **The librarian — your AI colleague wearing its curator hat — owns the
  library.** You never file. It places, names, curates, restructures — and
  signs every act in an append-only ledger.
- **The metabolism** — buckets reflect, prune, and learn. What a bucket
  learns lands in its conventions; trust widens through explicit, recorded
  delegations.

## The shape of a bucket

```
<bucket>/
├── BUCKET.md        # identity card + learned conventions
├── LEDGER.md        # append-only collaboration record
├── inbox/           # drop zone — things arrive, nothing lives here
├── sources/         # immutable originals + MANIFEST.md
├── library/         # settled knowledge — documents
├── activities/      # live work — documents + status
├── workbench/       # ephemeral human+AI space — NO format rules
└── output/          # finished deliverables — documents
```

Six zones, two root files, one shape in every bucket forever. The full
anatomy: [SPEC.md §2](SPEC.md).

## How it's built

Three layers: a **convention** ([SPEC.md](SPEC.md) — the actual product),
a small **[CLI](cli/README.md)** (`fusion` — the notary: ledger, registers,
hub, checks, your cross-bucket day), and a
**[skill family](skills/README.md)** (the judgment: intake, librarian,
planner, analyst) for any agent that reads
[Agent Skills](https://agentskills.io) — Claude Code, Pi, Goose, and
whatever comes next.

See it in motion: [`examples/crazy-ones/`](examples/crazy-ones/) — a
fictional studio bucket, fully conformant, ledger and all.

## Get started

```bash
curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
```

Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.ps1 | iex"
```

One line installs uv (which brings Python), the `fusion` CLI, and the
four skills into every agent on your machine that reads them. Later,
`fusion update` brings the whole system — CLI and skills — current in
one verb. Then:

```bash
fusion new ~/buckets/personal --kind personal \
  --description "Home base: admin, health, house, money."
fusion today
```

Ten minutes, no wizard. The walkthrough:
[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).

## Status

| Phase | What | State |
|---|---|---|
| 1 | The Convention + example bucket | ✅ this repo |
| 2 | The `fusion` CLI | ✅ cli + gate |
| 3 | The skill family | ✅ skills + gate |
| 4 | Dogfood + release | in progress |

Design spec: [docs/specs/2026-07-10-fusion-design.md](docs/specs/2026-07-10-fusion-design.md)
· Roadmap & QA gates: [docs/ROADMAP.md](docs/ROADMAP.md)

## Lineage

Fusion is the deliberate synthesis of four systems — Google's
[Knowledge Catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog) open format ("OKF" in our design spec), and
Bluewaves' Athena, Gizmo, and Shaping Room — keeping from each the one
thing it got right. The full argument lives in the design spec.

## Docs map

| Doc | What |
|---|---|
| [SPEC.md](SPEC.md) | The convention — normative, versioned, the actual product |
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | Ten-minute walkthrough |
| [docs/BUCKETS-EVERYWHERE.md](docs/BUCKETS-EVERYWHERE.md) | Migration, git sync, new machines, external projects |
| [examples/README.md](examples/README.md) | A finished bucket to wander |
| [cli/README.md](cli/README.md) | The CLI, command by command |
| [skills/README.md](skills/README.md) | The four skills |
| [docs/README.md](docs/README.md) | The rest: design rationale, roadmap, build records |
| [CONTRIBUTING.md](CONTRIBUTING.md) | The spec is the contribution |

`SPEC.md` is the contract — root, stable name, changes rarely and only
versioned. `docs/specs/` holds the dated design rationale behind it — the
argument, not the contract.

## License

[MIT](LICENSE.md). The spec is the contribution; the tools are reference
implementations. Rewrite them in anything — buckets that follow the
convention are Fusion.
