# The example bucket — a tour

[`crazy-ones/`](crazy-ones/) is a complete, conformant Fusion bucket for a
fictional music studio. It is also the project's normative test fixture —
`fusion check` holds it at zero errors, zero warnings, and the golden tests
freeze its INDEX files byte-for-byte. Wander it; don't edit it — the freeze
is this fixture's, not a rule of Fusion (your own buckets are yours to
edit, INDEX.md aside).

Read it in this order:

1. **[BUCKET.md](crazy-ones/BUCKET.md)** — the identity card: name, kind,
   description, and the § Conventions section where the bucket's own rules
   and standing delegations accumulate as it learns.
2. **[LEDGER.md](crazy-ones/LEDGER.md)** — the trust record. Every act the
   librarian took, signed and dated, in eleven closed verbs. The story of
   the bucket is readable here alone.
3. **[library/](crazy-ones/library/)** — curated knowledge. Every document
   opens with three required fields (`title`, `type`, `aurora`) and a
   summary before anything else. `INDEX.md` is generated — never edited.
4. **[activities/](crazy-ones/activities/)** — work with a beginning and an
   end; `status: active` is what `fusion today` composes your morning from.
5. **[sources/](crazy-ones/sources/)** — originals, byte-for-byte, each with
   a MANIFEST row (sha256, provenance, converted twin). Immutable.
6. **[workbench/](crazy-ones/workbench/)** — the one ruleless zone; drafts
   live here without frontmatter until they're promoted.
7. **[output/](crazy-ones/output/)** — what the bucket ships: documents and
   exported deliverables.

The eight `aurora` values (commitments · focus · ops · collab · life ·
explore · archive · library) are an attention system, not a taxonomy — they
say what a thing means for your attention, and they are the same eight in
every bucket, forever.
