# reflect — the metabolism (SPEC §10)

The files remember → you reflect → the human judges → the system learns.
Run on the bucket's `reflection_cadence`, or when asked.

## 1. Introspect

```bash
fusion log --since last-reflection      # what happened this window
fusion status --since last-reflection   # counts, auroras, activities
fusion check <root>                     # drift: stale INDEX, W1 inbox age…
```

Read the window's ledger like telemetry: what got converted, promoted,
touched — and what never did.

## 2. Curate & prune — the proposal list

Propose, with paths and evidence, whichever apply:
- workbench items older than the window → promote or expire;
- activities with `status: active` and no ledger touch → `dormant` or
  archive (W5 already names them);
- superseded or stale library documents → `archive/`;
- duplicates to merge, fat documents to split;
- summaries that no longer match their bodies;
- taxonomy that stopped serving → a restructure proposal;
- rules the window taught: "we always filed X under Y — make it a Rule?"
- delegations earned: acts the human approved repeatedly this window.

## 3. Judge

Present the list. Destructive and archival acts need a yes — EXCEPT where
`### Delegations` already grants it (cite the delegation, act, and note
it). Never bundle: the human can take proposal 3 and refuse proposal 4.

## 4. Learn & sign

- Approved rule/delegation changes: edit `BUCKET.md ## Conventions`, one
  `fusion log noted "BUCKET.md — <the change>" --as <you>` per change.
- Execute approved acts via their own gears (archive, restructure…) so
  each carries its own verb.
- Sign the cycle LAST:
  `fusion log reflected "<bucket> — <N> proposals, <M> adopted" --as <you>`
- Episodic reports are ephemeral: the proposal list lives in workbench/
  and can die there; only conventions and ledger entries persist.
