# The Fusion skill family

Four skills, four accountabilities. The CLI keeps the facts; these keep
the judgment.

| Skill | Accountability |
|---|---|
| [fusion-intake](fusion-intake/) | The gate — everything that enters, enters through it, losslessly. |
| [fusion-librarian](fusion-librarian/) | The owner — order, placement, curation, restructuring, reflection. |
| [fusion-planner](fusion-planner/) | The horizon — activities, agendas, an honest today. |
| [fusion-analyst](fusion-analyst/) | The output — deliverables that cite their sources and ship signed. |

## Install

Standard-compliant skills need no installer:

```bash
cp -r skills/fusion-* ~/.agents/skills/   # or your agent's skills directory
```

Requirements: the `fusion` CLI on PATH (from a clone: `uv tool install
./fusion/cli`), `uv` for the bundled scripts. fusion-intake additionally
wants LibreOffice (`soffice` on PATH) for docx/pptx/legacy office
formats — it fails fast and loud when missing, never silently degrades.

## The contract all four obey

1. Self-contained — agentskills.io standard, PEP 723 scripts via `uv run`,
   no harness-specific anything.
2. Judgment proposes, code records — every ledger/register write goes
   through its single writer (`fusion log`, `fusion index`, intake's
   register script).
3. The convention travels — each skill carries a byte-identical
   `references/fusion-conventions.md`.
4. One skill, one accountability — the ledger says which hat was worn.
