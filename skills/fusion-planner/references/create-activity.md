# create-activity — structure the human's intent

1. Get the essentials from the conversation: name (→ slug), what done
   looks like, deadline (if promised), who else is involved. Ask only
   what the human hasn't said.
2. Choose aurora: promised-with-deadline → `commitments`; the current
   deep work → `focus`; shared → `collab`; tentative → `explore`. Say
   which and why in one line.
3. Create `activities/<slug>/plan.md`:

   ```markdown
   ---
   title: <name>
   type: plan
   aurora: <chosen>
   status: active
   created: <today>
   due: <date, only if real>
   ---

   ## Summary

   <what this activity is and what done looks like, 2–3 lines>

   ---

   ## Steps

   - [ ] <the first concrete steps, from the conversation>

   ## Log

   - <today> — created.
   ```

4. `fusion log created "activities/<slug>/plan.md" --bucket <root>
   --as <you>` · `fusion index <root>` · `fusion check <root>` green.
   Then show the human what `fusion today` now includes.
