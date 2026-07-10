# assess — scored, scaled, evidenced

1. Subject + criteria + scale. No scale given → 1–5 integers
   (1 very poor … 5 excellent) and SAY SO at the top of the document.
2. Evidence per criterion from the bucket (paths kept for data_sources).
   A criterion without evidence scores nothing — mark it "no evidence
   in bucket" instead of guessing.
3. Write `output/assessments/<slug>.md`: summary + `---` + scores table
   (criterion · score · evidence path) + per-criterion rationale +
   `## Sources`.
4. `fusion log shipped … --bucket <root> --as <you>` · `fusion index <root>`
   · `fusion check <root>`.
