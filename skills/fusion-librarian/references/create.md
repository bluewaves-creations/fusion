# create — a document born conformant

1. Establish title, type, aurora, and destination zone/folder. Infer type
   and folder from the bucket's existing taxonomy and BUCKET.md Rules;
   ask only when genuinely ambiguous. Aurora is the human-attention call —
   propose, and let an explicit instruction override. Before writing,
   triage `library/INDEX.md` for an existing document on the same
   subject — extending or reconciling one beats creating a twin; when a
   candidate exists, propose the edit instead and let the human choose.
2. Write the document: the three required fields (plus `created:` today,
   `tags:` when useful), `## Summary` (2–3 lines), `---`, then the body.
   Filename: lowercase-hyphen slug, ≤60 chars.
3. `fusion log created "<zone>/<path>" --bucket <root> --as <you>` ·
   `fusion index <root>` · `fusion check <root>` green.
