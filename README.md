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
- **The librarian owns the library.** You never file. The AI colleague
  places, names, curates, restructures — and signs every act in an
  append-only ledger. Ownership with a paper trail.
- **The metabolism** — buckets reflect, prune, and learn. What a bucket
  learns lands in its conventions; trust widens through explicit, recorded
  delegations.

## How it's built

Three layers: a **convention** ([SPEC.md](SPEC.md) — the actual product),
a small **CLI** (`fusion` — the notary: ledger, registers, hub, checks,
your cross-bucket day), and a **skill family** (the judgment: intake,
librarian, planner, analyst) for any agent that reads
[Agent Skills](https://agentskills.io) — Claude Code, Pi, Goose, and
whatever comes next.

See it in motion: [`examples/crazy-ones/`](examples/crazy-ones/) — a
fictional studio bucket, fully conformant, ledger and all.

## Status

| Phase | What | State |
|---|---|---|
| 1 | The Convention + example bucket | ✅ this repo |
| 2 | The `fusion` CLI | ✅ cli + gate |
| 3 | The skill family | in design |
| 4 | Dogfood + release | in design |

Design spec: [docs/specs/2026-07-10-fusion-design.md](docs/specs/2026-07-10-fusion-design.md)
· Roadmap & QA gates: [docs/ROADMAP.md](docs/ROADMAP.md)

## Lineage

Fusion is the deliberate synthesis of four systems — Google's
[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog), and
Bluewaves' Athena, Gizmo, and Shaping Room — keeping from each the one
thing it got right. The full argument lives in the design spec.

## License

[MIT](LICENSE.md). The spec is the contribution; the tools are reference
implementations. Rewrite them in anything — buckets that follow the
convention are Fusion.
