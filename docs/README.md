# The docs tree — a map

Start at the repository [README](../README.md); the convention itself is
[SPEC.md](../SPEC.md). This folder holds everything else:

| Where | What | Read it when |
|---|---|---|
| [GETTING-STARTED.md](GETTING-STARTED.md) | The ten-minute walkthrough | You're new |
| [BUCKETS-EVERYWHERE.md](BUCKETS-EVERYWHERE.md) | Moving in, syncing, new machines, code repos | Your buckets meet the world |
| [ROADMAP.md](ROADMAP.md) | Phases and their QA gates | You want the state of things |
| [specs/](specs/) | Dated design rationale — the argument behind SPEC.md | You want the *why* |
| [plans/](plans/) | Implementation plans, task by task | You're archaeologizing a change |
| [acceptance/](acceptance/) | Signed phase-gate evidence | You want proof, not claims |
| [dogfood/](dogfood/) | The live-use protocol + frictions log | You want to see the loop run |

`plans/`, `acceptance/`, and `dogfood/` are the engineering record — dated
(`YYYY-MM-DD-…`), append-mostly, never guides. They show how the thing was
built and verified; nothing in them is needed to *use* Fusion.
