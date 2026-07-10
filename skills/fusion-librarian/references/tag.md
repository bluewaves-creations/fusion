# tag — bulk metadata, honestly reported

1. Parse the field and value; `--scope`-like constraints (a folder, a
   type) narrow the set. Value "auto" means you infer per document from
   its content — say so in the report.
2. Edit each document's frontmatter, preserving every existing key and
   the body untouched. `updated:` does NOT bump (metadata, not content).
3. Report a table: file · field · old → new.
4. One ledger entry for the batch:
   `fusion log classified "<scope> — <field>: <value> (<N> documents)" --as <you>`
   then `fusion index` (summaries unchanged, but titles/auroras may have
   moved in the index) and `fusion check`.
