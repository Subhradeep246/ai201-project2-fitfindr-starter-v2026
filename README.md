# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user types what they want in plain language — for example a vintage graphic
tee under $30. FitFindr parses that into keywords, an optional size, and an
optional price ceiling, then searches `data/listings.json`. If something
matches, it picks the best hit, suggests one or two outfits against the user's
wardrobe, and writes a short caption for the find. If nothing matches, it
stops and says what to change (keywords, size, or price) instead of inventing
an outfit for an item that does not exist.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Loads every listing, drops anything over `max_price` when a ceiling is given, drops anything that fails the size rule when a size is given, scores the rest by keyword overlap with `description` (title, tags, and category count more than the prose description), and returns the best matches first.
- **Inputs:** `description` (str), `size` (str or None), `max_price` (float or None, inclusive). Size match is case-insensitive whole tokens, not substrings: `M` matches `M`, `S/M`, and `M/L`; `S` does not match `US 9`; `L` does not match `XL` or `W30 L30`. A numeric size matches a `US` shoe size or a `W` waist of that number. `One Size` matches a letter-size request, not a shoe size.
- **Returns:** A list of listing dicts, highest score first, at most `config.SEARCH_RESULT_LIMIT` (10). Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`.
- **When it has nothing:** An empty list `[]` — not None, not an exception. That is what the loop branches on.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits that use the thrifted item. If the wardrobe has pieces, the prompt names them and the model is told to combine those pieces with the new item. If the wardrobe is empty, the prompt asks for general styling (silhouettes, colors, shoes) instead of named closet items.
- **Inputs:** `new_item` (dict — one listing), `wardrobe` (dict with an `items` key holding a list of wardrobe-item dicts; `items` may be empty).
- **Returns:** A non-empty string of outfit suggestions.
- **When it has nothing:** An empty wardrobe still returns a non-empty string of general styling advice. It does not raise and it does not return `""`.

### `create_fit_card`

- **What it does:** Asks the model for a 2–4 sentence caption that sounds like a real post, mentions the item, its price, and its platform once each, and uses the outfit for the vibe.
- **Inputs:** `outfit` (str — the text from `suggest_outfit`), `new_item` (dict — the same listing).
- **Returns:** A two-to-four sentence caption string.
- **When it has nothing:** If `outfit` is empty or whitespace, it does not call the model. It returns a short descriptive message that names the item, price, and platform.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:**
If `search_listings` returns an empty list, put a message in `session["error"]`
that names the parsed keywords, size, and price and what the user could change,
then stop. Do not call `suggest_outfit` or `create_fit_card`. Otherwise take
`search_results[0]`, store it as `selected_item`, and continue to
`suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex in `parse_query` — no model call. It pulls
`size` from `size M` / `in size M` / `size 8` / `size XXS`, `max_price` from
`under $30` / `below` / `less than`, and treats the leftover words as
`description` after dropping filler like "looking for".

**What moves through the session:**
`query` → `parsed` (`description`, `size`, `max_price`) → `search_results` →
`selected_item` (first hit) → `outfit_suggestion` → `fit_card`.
`wardrobe` is stored at the start and read by `suggest_outfit`. `error` is
set only when the search branch stops the run.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the butterfly baby tee with the baggy straight-leg jeans, cinched at the waist with the brown leather belt. Layer the oversized grey crewneck sweatshirt on top, letting it slouch off one shoulder while the graphic hem peeks out below. Finish the look with chunky white sneakers and the black crossbody bag.

Tuck the baby tee into the wide-leg khaki trousers and top it with the slightly cropped vintage black denim jacket. Add the black combat boots to ground the pastel Y2K print with a touch of grunge, and sling the black crossbody bag over your shoulder.

  Fit card: Scored this pastel butterfly baby tee on depop for just eighteen dollars and I'm obsessed. The Y2K print gives major early-2000s mall-rat energy, especially styled with wide-leg khaki trousers and a cropped black denim jacket. Throwing on some combat boots grounds the sweetness with a little bit of grunge.

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, ...]
```

The same command also returned the graphic hoodie, a mesh top (description mentions "graphic tee"), cargo pants ("long tee"), and a navy crewneck ("graphics"). First three hits are actual graphic tees under $30.

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Tuck the white ribbed tank top into the vintage Levi's 501 jeans, cinch the waist with the brown leather belt, and layer the slightly cropped vintage black denim jacket on top. Finish the look with the chunky white sneakers and the black crossbody bag.

Slip into the oversized grey crewneck sweatshirt over the Levi's 501 jeans, letting the hem fall loosely over the hips. Ground the relaxed silhouette with the black combat boots and accessorize with the black crossbody bag.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501s on Depop for just $38, and the medium wash is honestly perfection. They have that exact broken-in indigo fade you can't fake. Throwing them on with some crisp white sneakers for that ultimate effortless look.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* Build the planning loop in `agent.py` so it is a real loop with the empty-search branch, not three function calls in a row.
- *What came back:* A `next_step` while-loop that parses the query, searches, and only continues if results came back. The first version still sat on top of stub tools, so both example queries in `python agent.py` printed the empty-search message and looked identical.
- *What I changed:* I left the branch as written (`if not results: set error and stop`) and built the three tools next so the two paths could actually differ. I did not add `trace.step()` or a `ModelUnavailable` handler — those stay for unit 4.

**Moment 2**

- *What I asked for:* Implement `search_listings` / `suggest_outfit` / `create_fit_card` against the listings data, including a size filter that would not treat `"s" in "us 9"` as a match.
- *What came back:* A first scorer that treated the listing's prose description the same as the title. A mesh top ranked like a graphic tee because its description said "layering under a graphic tee". Size matching used whole tokens, which was the part I wanted to keep.
- *What I changed:* Keyword hits in the title, tags, and category now score higher than hits that only appear in the description. `One Size` still matches a letter-size request; a numeric query only matches a `US` shoe size or a `W` waist.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
