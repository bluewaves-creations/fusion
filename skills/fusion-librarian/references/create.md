# create — a document born conformant

1. Establish title, type, aurora, and destination zone/folder. Infer type
   and folder from the bucket's existing taxonomy and BUCKET.md Rules;
   ask only when genuinely ambiguous. Aurora is the human-attention call —
   propose, and let an explicit instruction override.
2. Write the document: the three required fields (plus `created:` today,
   `tags:` when useful), `## Summary` (2–3 lines), `---`, then the body.
   Filename: lowercase-hyphen slug, ≤60 chars.
3. `fusion log created "<zone>/<path>" --as <you>` · `fusion index` ·
   `fusion check` green.
