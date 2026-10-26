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

- **What it does:** Loads every listing, drops anything over `max_price` when a ceiling is given, drops anything that fails the size rule when a size is given, scores the rest by keyword overlap with `description` (title, tags, and category count more than the prose description), and if the query names an item noun (`jacket`, `tee`, `dress`, …) drops listings that do not carry that noun in the title, category, or tags. Returns the best matches first.
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

From `results/run_2026-10-26_1828_before.md`, produced by `run_eval.py::main`
(caching off). Try cells scored against `criteria.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. session keeps first hit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card names price and platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. price ceiling holds | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try**, pasted as text. Produced by `run_eval.py::run_once`
calling `agent.py::run_agent` on scenario 1, try 1:

```
- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Outfit suggestion:

Pair the Y2K butterfly baby tee with the baggy dark wash straight-leg jeans, cinched at the waist with the brown leather belt. Layer the oversized grey crewneck sweatshirt loosely over your shoulders, and finish the look with the chunky white sneakers and the black crossbody bag.

Tuck the butterfly baby tee into the wide-leg khaki trousers, and layer the black cropped zip hoodie unzipped over top. Add the black combat boots and the black crossbody bag to balance the Y2K and minimal earth-tone mix.

Fit card:

Scored this pastel butterfly baby tee for just $18 on Depop and I am obsessed. It gives major Y2K energy when tucked into baggy dark wash jeans with a chunky brown belt. Throwing a grey crewneck over my shoulders makes it the ultimate lazy-day campus fit.

Trace:

[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee' size=None max_price=30.0
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: hits found, continuing to select
[3] select
      in:  dict with keys: first_result_id
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    selected_item is search_results[0]
[4] suggest_outfit
      in:  dict with keys: item, wardrobe_items
      out: Pair the Y2K butterfly baby tee with the baggy dark wash straight-leg jeans, cinched at the waist with the bro…
[5] create_fit_card
      in:  dict with keys: outfit, item
      out: Scored this pastel butterfly baby tee for just $18 on Depop and I am obsessed. It gives major Y2K energy when …
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
| 1 | matching query completes | 4 of 5 | MET | All five tries ran search + suggest + fit card and returned a non-empty `fit_card`. Traces show five steps, never `session["error"]`. |
| 2 | impossible query stops early | 5 of 5 | MET | All five tries: `search_results` is 0, `selected_item` is none, trace ends at `search_listings (via MCP)` with `branch: empty, stopping before suggest_outfit`. Error names keywords, size XXS, $5, and what to change. |
| 3 | session keeps first hit | 5 of 5 | MET | Every try selected `Denim Jacket — Light Wash, Cropped` and the trace note is `selected_item is search_results[0]`. Outfit text is filled after `[3] select`, never before. |
| 4 | fit card names price and platform | 4 of 5 | MET | All five cards are 2–3 sentences and mention `depop` plus a price cue. Try 2 still counts as a pass under the written rule — see the diagnosis. |
| 5 | price ceiling holds | 5 of 5 | MET | Query parses `max_price=30.0`. `search_listings` returned 10 hits each try; the highest price in that list is $30.0, so the inclusive ceiling held. |

**Diagnoses**

No criterion missed its target, so there is no miss to pin on a broken branch. The one weak mechanism I still saw is in **the model's output inside `create_fit_card`**, not in the loop.

Criterion 4 try 2 (`silk slip dress under $40`) wrote `on depop for thirty bucks` and never used `$30`. It still PASSED because the criterion accepts "a digit from `selected_item['price']`" — price is `30.0`, and the caption already contains `90s`, which has a `0`. That is a pass on the letter of the criterion and a miss on what I actually wanted: a readable price. Same pattern showed up on criterion 1 try 5 (`eighteen dollars` instead of `$18`). The tool ran; the prompt let the model spell the number.

I did not treat that as a reason to lower the target. I used it as the one improvement.



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
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee' size=None max_price=30.0
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: hits found, continuing to select
[3] select
      in:  dict with keys: first_result_id
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    selected_item is search_results[0]
[4] suggest_outfit
      in:  dict with keys: item, wardrobe_items
      out: Tuck the butterfly baby tee into the baggy dark-wash straight-leg jeans, accented with the brown leather belt.…
[5] create_fit_card
      in:  dict with keys: outfit, item
      out: Scored the absolute cutest Y2K butterfly baby tee for just $18.0 on depop. It gives major early-2000s mallrat …

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown' size='XXS' max_price=5.0
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  No listings matched 'designer ballgown' in size XXS under $5. You could try different keywords, drop or change the size, or raise the price ceiling.

0 model calls this session
```

The empty path is two steps. The happy path is five. The branch is doing the stopping.

**The other two failure modes**

Empty wardrobe (`python app.py ask 'denim jacket under $50' --trace --empty-wardrobe`): search still hits, then `suggest_outfit` notes `empty wardrobe: general styling` and returns a non-empty string of silhouettes instead of crashing.

Bad key: `run_agent` catches `ModelUnavailable` after select. Search already finished over MCP (no model). The session gets an error instead of a stack trace:

```
[4] ModelUnavailable
      out: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.goo…
      →    caught in run_agent; suggest_outfit/create_fit_card skipped
```

**On the MCP move:**
I registered `search_listings` in `mcp_server.py` (typed inputs + empty-list contract) and swapped the direct call in `agent.py::run_agent` for `mcp_client.call_tool("search_listings", ...)`. The return value stayed a list of listing dicts — same first hit (`Y2K Baby Tee — Butterfly Print`) as the unit 3 direct call. The only visible change is latency (the client starts the server per call) and the step name `search_listings (via MCP)` in the trace. I also catch `MCPError` the same way as `ModelUnavailable` so a registration miss becomes a session error instead of a traceback.



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**
In `tools.py::create_fit_card` only. The prompt now asks for the price as `$` plus digits (the exact `price_bit`) and the exact platform string, and not a spelled-out number. After `generate()`, `_ensure_price_and_platform` appends a short `Listed $N on platform.` line if either cue is missing, without pushing the caption past four sentences.

**Which failure it was meant to fix:**
The criterion 4 near-miss: captions that say `thirty bucks` / `eighteen dollars` and only pass because a stray digit (the `0` in `90s`) or the word `dollar` satisfies the written check.

### Run Log — After

From `results/run_2026-10-26_1833_after.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. session keeps first hit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card names price and platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. price ceiling holds | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:**
The scoreboard did not move — C4 was already 5/5. The mechanism did. Before, C4 try 2 was `on depop for thirty bucks` with no `$30`. After, every C4 card uses `$30` and `depop` (`just $30 on depop`, five times). Criterion 1 try 5 went from `eighteen dollars` to `on depop for just $18`. I know because I compared those strings in the two run logs, not because the PASS count changed.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

The five numbered criteria already MET. The leftover targets from the first after-run were adjacent, and this redo was those:

- `search_listings` no longer returns jeans for `denim jacket`. An item noun in the query (`jacket`, `tee`, `dress`, …) now has to appear in the listing title, category, or tags. Local check: `denim jacket` under $50 is two jackets only; `vintage graphic tee` under $30 still leads with the butterfly baby tee; the ballgown query is still empty.
- Empty wardrobe prompt now forbids inventing a fake closet. Rechecked with `--empty-wardrobe`.
- Fit cards already used `$` + digits + platform on the after log; that guard stayed.

Still adjacent, not a missed criterion: `denim jacket` can still return the navy track jacket, because that listing really is a jacket. I stopped once jeans were gone. Empty-wardrobe outfits still name generic silhouettes (ribbed tank, loafers) — that is the spec, not a fake closet.



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

       [x] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [x] Run Log — Before, five criteria, five tries each
       [x] Real output pasted underneath, naming file and function
       [x] A verdict on every criterion
       [x] A diagnosis for every miss, naming a place AND a mechanism
       [x] Loop Trace, with the MCP call visible in it
       [x] All three failure modes triggered and handled
       [x] One improvement, with Run Log — After in the same format
       [x] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
