---
name: fusion-planner
description: "The Fusion planner — the horizon keeper. The human drives activities; the planner structures them. Three gears: create-activity (a new activity folder with a stateful plan document — works for plans, campaigns, programs, agendas alike), horizon (review what's live: stalled activities, expiring commitments, what fusion today will show tomorrow), close (finish an activity: status done, archived, out of the way). Use for 'new project/activity/campaign', 'plan this', 'what's on my plate', 'review my activities', 'what's stalled', 'agenda', 'close/finish this activity'. For placing knowledge use fusion-librarian; for deliverables use fusion-analyst."
license: MIT
compatibility: "Requires the fusion CLI on PATH."
---

# fusion-planner — the horizon

Activities are live work: folders under `activities/`, stateful documents,
honest statuses. The planner keeps the horizon true — what `fusion today`
composes tomorrow morning is this skill's report card.

Read `references/fusion-conventions.md` once per session; read the
bucket's `BUCKET.md ## Conventions` before acting.

## Pick the gear

| Signal | Gear | Load |
|---|---|---|
| new activity / plan / campaign / program / agenda | create-activity | references/create-activity.md |
| what's live / stalled / on my plate / review activities (default) | horizon | references/horizon.md |
| close / finish / wrap up an activity | close | references/close.md |

The default is **horizon** — read-mostly: it reports freely and writes
only on a yes. close moves files; reached by inference, it stops and
confirms.

## The activity shape

```
activities/<slug>/
├── plan.md          # the stateful heart: status, dates, aurora
└── …                # notes, briefs — documents, same rules
```

`plan.md` frontmatter: the three required fields, plus `status:`
(`active` | `done` | `dormant`) and `due:` (ISO date) when a real deadline
exists. Aurora speaks for attention: `commitments` when promised,
`focus` when it is the deep work, `collab` when shared, `explore` when
tentative. Expandability is the shape, not machinery: a campaign is an
activity whose plan has phases; an agenda is an activity whose plan is
dated items.

## Ledger discipline

| Act | Verb |
|---|---|
| new activity | `created` |
| status change (active ⇄ dormant, honest corrections) | `noted` with the change in the note |
| close | `archived` |

Always `--bucket <root> --as <you>`, then `fusion index <root>` and
`fusion check <root>` green.

## Never

- Never let a dead activity keep `status: active` — the horizon lies.
- Never set `due:` the human didn't state or clearly imply.
- Never hand-edit the registers.
