# query — answer from the bucket, cited

Read-only. Changes nothing, logs nothing.

1. Parse the question: entities, concepts, constraints (type, aurora,
   dates, status).
2. Triage via `library/INDEX.md` + `activities/INDEX.md` — titles and
   summary lines first. `fusion status` helps scope what exists.
3. Grep frontmatter for structured hits (`type:`, `aurora:`, `tags:`),
   then content for the rest.
4. Read the most relevant documents — summaries first, bodies only for
   the finalists (keep it under ~10 full reads).
5. Answer with a `## Sources` table: document path · what it contributed.
   Every claim cites a path. If the bucket is silent on part of the
   question, say what is known and what is missing — never fill gaps
   from your own general knowledge without labelling it as outside the
   bucket.
