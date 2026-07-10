# The Fusion Convention

**Version 1.0**

Fusion is a file-based working environment for Human + AI collaboration —
knowledge, activities, and their shared record — living entirely in markdown
on a filesystem. It is operable by any capable agent and by any human with a
text editor. It is not a document-management system, not a PKM, not a note
app. It refuses the category.

The contract the whole convention serves:

> **The human judges, the AI operates, the files remember.**

This document is the product. Everything else — the `fusion` CLI, the skill
family — is a reference implementation. Rewrite the tools in any language;
buckets that follow this convention are Fusion.

## 0. Conformance

The key words MUST, MUST NOT, SHOULD, and MAY are to be interpreted as in
RFC 2119.

**Liberal reader, strict writer:**

- A **consumer** (anything reading a bucket) MUST NOT reject a bucket or a
  document because of missing optional fields, unknown `type` values, unknown
  frontmatter keys, broken links, or missing INDEX files. A half-migrated
  bucket is still a bucket.
- A **producer** (anything writing to `library/`, `activities/`, `output/`,
  or any register) MUST satisfy every applicable MUST in this convention
  before writing. Validation happens before damage, not after.

## 1. The hub

The hub registers a machine's buckets so any agent can discover the user's
world. It lives at `~/.fusion/hub.md` and is maintained by `fusion hub`;
hand edits MUST be tolerated by consumers.

```markdown
# Fusion Hub

- **personal** · personal · ~/Fusion/personal — life, training, the wide-open days
- **studio** · studio · ~/Fusion/studio — music, photography, instruments
- **acme** · company · ~/Work/acme-fusion — the Acme engagement
```

Entry grammar, one line per bucket:

    - **<name>** · <kind> · <path> — <description>

- `name` MUST be unique in the hub and MUST equal the bucket's
  `BUCKET.md` `name`.
- `kind` SHOULD be one of `personal`, `company`, `studio`, `club` — but the
  vocabulary is open (liberal reader).
- `path` is absolute or `~`-relative.
- The hub is per-machine and never synced; buckets are the durable objects.

## 2. Bucket anatomy

A bucket is a directory — its own git repository — with this exact shape.
All zones MUST exist from creation; an empty zone carries a `.gitkeep`.

```
<bucket>/
├── BUCKET.md        # identity card + learned conventions (§3)
├── LEDGER.md        # append-only collaboration record (§6)
├── inbox/           # drop zone — things arrive here, nothing lives here
├── sources/         # immutable originals + MANIFEST.md (§7)
├── library/         # settled knowledge — documents per §4
├── activities/      # live work — documents per §4, plus status
├── workbench/       # ephemeral human+AI space — NO format rules
└── output/          # finished deliverables — documents per §4
```

Zone rules:

- `inbox/` — ephemeral by contract. Files older than `inbox_max_age_days`
  (§3) are a conformance warning.
- `sources/` — immutable. Files here MUST NOT be modified, renamed, or
  deleted after registration in `MANIFEST.md`. Organized in subdirectories
  by category.
- `library/`, `activities/`, `output/` — every `.md` file MUST conform to
  the document format (§4). `INDEX.md` files (§8) are generated and exempt.
- `workbench/` — no rules. Half-baked work belongs here. Leaving workbench
  (promotion) is a deliberate, ledger-logged act.
- Fusion holds knowledge and work, never media or code. Big binaries and
  repositories stay in their native homes; documents point to them
  (`resource:`, §4).

## 3. BUCKET.md

The bucket's identity card and its long-term memory of how it works.

```markdown
---
name: studio
kind: studio
description: Music, photography, instruments — the creative domain.
fusion_version: "1.0"
created: 2026-07-10
inbox_max_age_days: 7
reflection_cadence: weekly
---

Free-form introduction: what this bucket is for, what lives here,
anything a new collaborator (human or AI) should know first.

## Conventions

### Rules

- Instruments are filed one document per instrument, by slug of make-model-year.
- Session notes are weekly, never daily.

### Delegations

- The librarian may archive dormant explore-aurora documents without asking.
```

- Frontmatter `name`, `kind`, `description`, `fusion_version`, `created`
  are REQUIRED. `inbox_max_age_days` (default 7) and `reflection_cadence`
  (free text) are optional.
- `## Conventions` holds what the bucket has learned (§10): `### Rules` are
  operating rules discovered through use; `### Delegations` are standing
  grants of autonomy to the AI colleague. Both are maintained by the
  librarian; every change MUST be ledger-logged.
- Skills MUST read `## Conventions` before acting on the bucket.
