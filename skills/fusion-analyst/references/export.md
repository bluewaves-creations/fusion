# export — data that leaves as data

1. Scope the rows: which documents, which frontmatter fields / table
   columns. Collect into JSON: `{"headers": […], "rows": [[…], …]}`.
2. Pipe through the script:

   ```bash
   echo '<json>' | uv run <skill>/scripts/export.py --format xlsx \
     --output output/exports/<slug>.xlsx
   ```

   Formats: csv (default), json, xlsx.
3. Write the companion document `output/exports/<slug>.md` — summary of
   what the export contains + `resource:` naming the binary +
   `data_sources` listing every source path. The binary is data; the
   document is its passport.
4. `fusion log shipped "output/exports/<slug>.xlsx" --bucket <root>
   --as <you>` · `fusion index <root>` · `fusion check <root>`.
