# report — from bucket to briefing

1. Scope: topic, audience, depth. A "brief" is a report whose audience
   is management: two pages, headline numbers first, no methodology.
2. Gather: INDEX triage → grep → read the relevant documents. Keep the
   list of every path you actually used — that IS `data_sources`.
3. Write to `output/reports/<slug>.md` (or workbench first if the human
   is iterating):
   `## Summary` (the 2–3-line triage), `---`, then: Key findings
   (numbers verbatim from sources) · Analysis · Recommendations ·
   `## Sources` (path · contribution — mirrors data_sources).
4. Close: `fusion log shipped "output/reports/<slug>.md" --bucket <root>
   --as <you>` · `fusion index <root>` · `fusion check <root>`.
