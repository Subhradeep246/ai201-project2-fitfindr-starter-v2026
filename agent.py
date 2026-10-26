"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import trace
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError
from tools import suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_SIZE_RE = re.compile(
    r"(?:in\s+)?size\s+(XXS|XS|XXL|XL|S|M|L|\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(
    r"(?:under|below|less than)\s*\$?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_FILLER_RE = re.compile(
    r"\b(looking for|i(?:'m| am)? (?:looking for|want|need)|"
    r"find me|please|want|need|a|an|the)\b",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """
    Pull a description, optional size, and optional max_price out of the
    user's query with regex — no model call.

    "vintage graphic tee under $30"      → description, max_price=30
    "90s track jacket in size M"         → description, size="M"
    "designer ballgown size XXS under $5" → all three
    """
    remainder = query.strip()

    size = None
    size_match = _SIZE_RE.search(remainder)
    if size_match:
        raw = size_match.group(1)
        size = raw.upper() if raw.isalpha() else raw
        remainder = remainder[: size_match.start()] + " " + remainder[size_match.end() :]

    max_price = None
    price_match = _PRICE_RE.search(remainder)
    if price_match:
        max_price = float(price_match.group(1))
        remainder = remainder[: price_match.start()] + " " + remainder[price_match.end() :]

    description = _FILLER_RE.sub(" ", remainder)
    description = re.sub(r"[,.]+", " ", description)
    description = re.sub(r"\s+", " ", description).strip()
    if not description:
        description = query.strip()

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


def _empty_search_message(parsed: dict) -> str:
    """What the user could change — not just 'No results'."""
    bits = [f"No listings matched '{parsed['description']}'"]
    if parsed.get("size"):
        bits.append(f"in size {parsed['size']}")
    if parsed.get("max_price") is not None:
        bits.append(f"under ${parsed['max_price']:g}")

    hints = ["try different keywords"]
    if parsed.get("size"):
        hints.append("drop or change the size")
    if parsed.get("max_price") is not None:
        hints.append("raise the price ceiling")

    if len(hints) == 1:
        hint = hints[0]
    else:
        hint = ", ".join(hints[:-1]) + ", or " + hints[-1]
    return f"{' '.join(bits)}. You could {hint}."


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # The next tool is chosen from what the last step put in the session —
    # not a fixed list of three calls.
    count = 0
    next_step = "parse"

    try:
        while next_step is not None:
            count += 1
            trace.check_iterations(count)

            if next_step == "parse":
                parsed = parse_query(query)
                session["parsed"] = parsed
                trace.step(
                    "parse_query",
                    inputs=query,
                    returned=(
                        f"description={parsed['description']!r} "
                        f"size={parsed.get('size')!r} "
                        f"max_price={parsed.get('max_price')!r}"
                    ),
                )
                next_step = "search"

            elif next_step == "search":
                parsed = session["parsed"]
                mcp_args = {
                    "description": parsed["description"],
                    "size": parsed.get("size"),
                    "max_price": parsed.get("max_price"),
                }
                results = call_tool("search_listings", mcp_args)
                session["search_results"] = results
                if not results:
                    session["error"] = _empty_search_message(parsed)
                    trace.step(
                        "search_listings (via MCP)",
                        inputs=mcp_args,
                        returned=results,
                        note="branch: empty, stopping before suggest_outfit",
                    )
                    next_step = None
                else:
                    trace.step(
                        "search_listings (via MCP)",
                        inputs=mcp_args,
                        returned=results,
                        note="branch: hits found, continuing to select",
                    )
                    next_step = "select"

            elif next_step == "select":
                session["selected_item"] = session["search_results"][0]
                trace.step(
                    "select",
                    inputs={"first_result_id": session["search_results"][0].get("id")},
                    returned=session["selected_item"],
                    note="selected_item is search_results[0]",
                )
                next_step = "suggest"

            elif next_step == "suggest":
                wardrobe = session["wardrobe"] or {}
                empty_closet = not (wardrobe.get("items") or [])
                outfit = suggest_outfit(
                    session["selected_item"],
                    session["wardrobe"],
                )
                session["outfit_suggestion"] = outfit
                trace.step(
                    "suggest_outfit",
                    inputs={
                        "item": session["selected_item"],
                        "wardrobe_items": len(wardrobe.get("items") or []),
                    },
                    returned=outfit,
                    note="empty wardrobe: general styling" if empty_closet else "",
                )
                next_step = "fit_card"

            elif next_step == "fit_card":
                card = create_fit_card(
                    session["outfit_suggestion"],
                    session["selected_item"],
                )
                session["fit_card"] = card
                trace.step(
                    "create_fit_card",
                    inputs={
                        "outfit": session["outfit_suggestion"],
                        "item": session["selected_item"],
                    },
                    returned=card,
                )
                next_step = None

            else:
                session["error"] = f"Unknown planning step: {next_step}"
                trace.step("unknown_step", note=session["error"])
                next_step = None

    except ModelUnavailable as exc:
        session["error"] = (
            "The model could not be reached, so FitFindr stopped after search "
            f"instead of inventing an outfit. {exc}"
        )
        trace.step(
            "ModelUnavailable",
            note="caught in run_agent; suggest_outfit/create_fit_card skipped",
            returned=str(exc),
        )
    except MCPError as exc:
        session["error"] = (
            "Search over MCP failed, so the run stopped before styling. "
            f"{exc}"
        )
        trace.step("MCPError", note="search_listings via MCP failed", returned=str(exc))

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
