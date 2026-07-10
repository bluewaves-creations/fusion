# cross-reference — map what relates to what

Read-only. For a target document or topic:

1. Extract its entities (names, projects, products, periods).
2. Sweep the bucket: direct mentions (grep), shared frontmatter values
   (type, tags, aurora), thematic kinship (summaries that talk about the
   same thing).
3. Report three buckets, every line carrying a path:
   **Direct references** · **Shared attributes** · **Thematic connections**.
4. Offer (don't apply) link edits: "these two documents should point at
   each other" — applying them is a content change the user approves,
   then edit, `fusion index`, `fusion check`.
