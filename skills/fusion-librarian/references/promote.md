# promote — leaving the workbench is a deliberate act

workbench/ has no rules; the zones do. Promotion is the moment the rules
attach.

Pre-flight (all three, before anything moves):
1. Explicit invocation confirmed — arrived here by inference? Stop, ask.
2. Source is in `workbench/`; destination zone/folder named or clearly
   inferable from the document's nature (`library/` knowledge,
   `activities/` live work, `output/` deliverables). Ask if unclear.
3. State the plan in one sentence: "Promoting workbench/<x> to
   <zone>/<folder>/<slug>.md."

Validate BEFORE moving (strict writer — a failed check stops the
promotion, nothing moves):
- frontmatter parses; `title`, `type`, `aurora` present; aurora one of
  the eight; summary-first body; slug filename ≤60.
- activities documents: `status` present. output documents: encourage
  `data_sources`.
Fix what the user wants fixed, or leave it in the workbench.

Then: move the file (Write new + delete old, or `mv`), then
`fusion log promoted "workbench/<x> → <zone>/<path>" --as <you>` ·
`fusion index` · `fusion check` green.
