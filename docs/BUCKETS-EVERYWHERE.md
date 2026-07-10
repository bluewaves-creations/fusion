# Buckets everywhere

A bucket is a directory and a git repository — which means everything
git can do, a bucket can do: absorb an old mess, travel to a new
machine, live on two at once, stand beside a code repo it describes.
This page holds the recipes. The ten-minute basics are in
[GETTING-STARTED.md](GETTING-STARTED.md).

## Moving in — a messy folder becomes a bucket

`fusion new` refuses a non-empty target on purpose: it never builds on
top of something it might damage. So the move is scaffold-beside, then
feed the mess through the gate:

```bash
fusion new ~/buckets/studio --kind studio --description "…"
mv ~/old-mess/* ~/buckets/studio/inbox/
```

Then tell your agent to **process the inbox**. The intake gate handles
a folder of dozens to hundreds of files as one delivery: byte-identical
duplicates are swept, folder structure becomes filing categories,
originals land immutable under `sources/`, and every document comes out
summary-first and conformant. You confirm the judgment calls (updates,
conflicts); the ledger records the lot.

Two placements the gate will not make for you:

- Half-formed personal notes with no original worth preserving can go
  straight to `workbench/` — no rules apply there.
- Things that are neither knowledge nor work (installers, media
  libraries, code) do not belong in a bucket at all. Leave them where
  they live; documents can point at them (see the last section).

Finish with `fusion check` — green means the mess is now a library.

## Handoffs — an archive arrives

`.zip` and `.athena` packages are delivery vehicles, not originals: drop
one in `inbox/` and the gate unpacks it, treats the members as the
originals, and walks the same delivery pipeline. A retiring workspace —
a shaping room, an export from another tool — hands off the same way:
export, drop, process the inbox.

## One bucket, two machines

Every bucket is born a git repository with a `.gitattributes` that makes
parallel work merge safely:

```gitattributes
# written by fusion new — multi-machine merges stay safe (SPEC §6)
* text=auto eol=lf
sources/** -text
LEDGER.md merge=union
sources/MANIFEST.md merge=union
```

Give the bucket a private remote and it travels like any repo:

```bash
cd ~/buckets/studio
git remote add origin git@github.com:you/studio-bucket.git
git push -u origin main
```

Work on both machines, push and pull as you go. When both sides
appended to the ledger, git's union driver keeps both sets of entries —
the merged ledger may hold two headings for the same date,
which every Fusion reader tolerates; it is the honest record of
parallel work. After any merge, settle the registers:

```bash
fusion index && fusion check
```

A bucket born before this page (no `.gitattributes` at its root) gets
one by copying the five lines above into `<bucket>/.gitattributes` and
committing.

Two things deliberately do not sync: the hub (`~/.fusion/hub.md` is
per-machine — see the next section) and anything `resource:` points at
(the bucket carries the pointer, not the thing).

## A new machine

Fusion's install is one line; your buckets are git clones; the hub is
rebuilt by registration, not by copying:

```bash
curl -fsSL https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.sh | sh
git clone git@github.com:you/studio-bucket.git ~/buckets/studio
fusion hub add ~/buckets/studio        # once per bucket
fusion check --hub                     # every entry answers at its path
fusion today                           # the composed morning is back
```

`fusion hub add` reads the bucket's own BUCKET.md, so the path can
differ from the old machine's — buckets are the durable objects, the
hub is just this machine's map. If `fusion today` ever goes quiet about
a bucket you expected, `fusion check --hub` names what is missing and
how to fix it.

## The project that lives outside

An app, a site, a tool — the code belongs in its own repository, never
inside a bucket. The bucket keeps what the code cannot remember:

```markdown
---
title: Band Site
type: plan
aurora: focus
status: active
resource: ~/Code/band-site
---
```

`resource:` points at the repo; the activity holds the plan, the
decisions, and the progress; `fusion today` surfaces it every morning
like any other live work. The worked example is
[band-site in the example bucket](../examples/crazy-ones/activities/band-site/plan.md)
— wander it before you build your own.
