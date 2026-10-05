# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
`search_listings` is a keyword-overlap score, not a semantic search. A query
that a person would treat as the same request — "graphic t-shirt" instead of
"graphic tee" — can score zero and take the empty-search branch. 4 of 5 leaves
room for one phrasing miss without pretending the search understands synonyms.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never calls the model. `search_listings` returns `[]`, and
`run_agent` writes `session["error"]` from the parsed size and price, then
returns. There is no temperature and no synonym problem, so 5 of 5 is the
right bar — if this misses, the branch is broken, not "unlucky."

---

## 3. Something about state

On a matching query, `session["selected_item"]["id"]` equals
`session["search_results"][0]["id"]`, and `session["outfit_suggestion"]` is a
non-empty string produced after that selection — 5 of 5 tries.

**Why this target:**
The loop is supposed to pass the first hit through the session, not ask the
user to type the item again. If `selected_item` is a different listing than
`search_results[0]`, or the outfit is filled in while `selected_item` is still
`None`, the tools can look fine and the wiring is still wrong. 5 of 5 is
fair because this is an assignment in `run_agent`, not a model judgment.



---

## 4. Something about the fit card

On a matching query, the fit card is 2–4 sentences and, case-insensitively,
contains the listing's platform (`depop`, `thredup`, or `poshmark`) and a
price cue (a digit from `selected_item["price"]`, or the word `dollar`) —
in at least 4 of 5 tries.

**Why this target:**
I would actually be unhappy with a caption that reads like a vibe paragraph
and never says what it cost or where it was listed. Word-for-word sameness is
the wrong target: `TEMPERATURE` is 0.9 and the cache is off during eval, so
the sentences will move. 4 of 5 leaves room for one run that spells the price
in a way I didn't count, or drops the platform.



---

## 5. Your choice

When the parsed query has a `max_price` and search returns at least one hit,
every listing in `session["search_results"]` has `price <= max_price` —
5 of 5 tries.

**Why this target:**
A price ceiling that is quietly ignored looks like a successful search. The
filter is an inclusive numeric comparison with no model in the middle, so 5
of 5 is the right target. If this misses, `search_listings` dropped the
ceiling or `parse_query` never pulled the dollar amount out of the text.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
