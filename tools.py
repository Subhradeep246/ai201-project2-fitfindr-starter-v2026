"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings

_LETTER_SIZES = ("XXS", "XS", "XXL", "XL", "S", "M", "L")
_STOPWORDS = {
    "a", "an", "the", "in", "for", "of", "and", "or", "with", "to", "on",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SHOE_RE = re.compile(r"\bus\s+(\d+(?:\.\d+)?)\b", re.IGNORECASE)
_WAIST_RE = re.compile(r"\bw(\d+)\b", re.IGNORECASE)
_ONE_SIZE_RE = re.compile(r"\bone\s*size\b", re.IGNORECASE)
_LETTER_TOKEN_RE = re.compile(r"[A-Z0-9.]+")


def _letter_tokens(size_str: str) -> set[str]:
    """
    Clothing letter sizes as whole tokens, never substrings.

    "S/M" → {S, M}; "XL (oversized)" → {XL}; "US 9" → {}; "W30 L30" → {}.
    That last one matters: a naive `"l" in "w30 l30"` would treat jeans as L.
    """
    tokens = set()
    for part in _LETTER_TOKEN_RE.findall(size_str.upper()):
        if part in _LETTER_SIZES:
            tokens.add(part)
    return tokens


def _size_matches(listing_size: str, query_size: str) -> bool:
    """
    True when the listing can count as the requested size.

    - Letter sizes match themselves and slash ranges: M matches M, S/M, M/L.
    - They do not match as substrings: S does not match US 9; L does not match XL.
    - A numeric query matches a US shoe size or a W-waist of that number.
    - "One Size" matches a letter-size request (cardigans, belts, bags), not shoes.
    """
    wanted = query_size.strip()
    if not wanted:
        return True

    listing = listing_size or ""

    if re.fullmatch(r"\d+(?:\.\d+)?", wanted):
        shoe = _SHOE_RE.search(listing)
        if shoe and float(shoe.group(1)) == float(wanted):
            return True
        waist = _WAIST_RE.search(listing)
        if waist and "." not in wanted and waist.group(1) == wanted:
            return True
        return False

    wanted_letters = _letter_tokens(wanted)
    if wanted_letters and wanted_letters & _letter_tokens(listing):
        return True
    if wanted_letters and _ONE_SIZE_RE.search(listing):
        return True
    return listing.strip().casefold() == wanted.casefold()


def _tokens(text: str) -> list[str]:
    return [
        t
        for t in _TOKEN_RE.findall(text.lower())
        if t not in _STOPWORDS and len(t) > 1
    ]


def _tokens_close(query_token: str, listing_token: str) -> bool:
    if query_token == listing_token:
        return True
    return query_token + "s" == listing_token or listing_token + "s" == query_token


def _keyword_score(listing: dict, description: str) -> int:
    keywords = _tokens(description)
    if not keywords:
        return 0

    # Title/tags/category are the real match signal. The prose description
    # often says things like "layer under a graphic tee", which is not the
    # item being a graphic tee.
    primary_text = " ".join(
        [
            listing.get("title") or "",
            listing.get("category") or "",
            " ".join(listing.get("style_tags") or []),
            " ".join(listing.get("colors") or []),
            listing.get("brand") or "",
        ]
    )
    primary = _tokens(primary_text)
    secondary = _tokens(listing.get("description") or "")

    score = 0
    for kw in keywords:
        if any(_tokens_close(kw, t) for t in primary):
            score += 2
        elif any(_tokens_close(kw, t) for t in secondary):
            score += 1

    phrase = " ".join(keywords)
    if phrase and phrase in primary_text.lower():
        score += 2
    return score


def _format_listing(item: dict) -> str:
    tags = ", ".join(item.get("style_tags") or []) or "none"
    colors = ", ".join(item.get("colors") or []) or "unlisted"
    brand = item.get("brand") or "unbranded"
    return (
        f"{item.get('title')} — ${item.get('price')} on {item.get('platform')}, "
        f"size {item.get('size')}, {item.get('condition')} condition, "
        f"colors: {colors}, tags: {tags}, brand: {brand}"
    )


def _format_wardrobe(items: list) -> str:
    lines = []
    for piece in items:
        notes = piece.get("notes")
        extra = f" — {notes}" if notes else ""
        colors = ", ".join(piece.get("colors") or [])
        tags = ", ".join(piece.get("style_tags") or [])
        lines.append(
            f"- {piece.get('name')} ({piece.get('category')}; "
            f"colors: {colors}; tags: {tags}{extra})"
        )
    return "\n".join(lines)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()
    scored: list[tuple[int, dict]] = []

    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(listing.get("size") or "", size):
            continue
        score = _keyword_score(listing, description)
        if score <= 0:
            continue
        scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = (wardrobe or {}).get("items") or []
    item_blurb = _format_listing(new_item)

    if not items:
        prompt = (
            "A shopper has no saved wardrobe yet. Give general styling ideas "
            "for this thrifted piece — silhouettes, colors, and shoes that "
            "would work with it. One or two outfits. Be specific, not generic.\n\n"
            f"Item:\n{item_blurb}"
        )
    else:
        prompt = (
            "Suggest one or two outfits that pair this thrifted find with "
            "pieces the shopper already owns. Name those wardrobe pieces "
            "explicitly. Keep it wearable and specific.\n\n"
            f"New item:\n{item_blurb}\n\n"
            f"Wardrobe:\n{_format_wardrobe(items)}"
        )

    return generate(
        prompt,
        system=(
            "You style secondhand clothes. Reply with outfit suggestions only — "
            "no preamble, no bullet-point inventory dump."
        ),
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not (outfit or "").strip():
        title = new_item.get("title") or "this piece"
        price = new_item.get("price")
        platform = new_item.get("platform") or "the listing site"
        price_bit = (
            f"${price:g}" if isinstance(price, (int, float)) else "an unknown price"
        )
        return (
            f"No outfit suggestion to caption. The find is {title} "
            f"({price_bit} on {platform})."
        )

    prompt = (
        "Write a 2–4 sentence social caption about this thrift find. "
        "Sound like a real post, not a product listing. Mention the item, "
        "its price, and the platform exactly once each. Be specific about "
        "the vibe, using the outfit suggestion.\n\n"
        f"Item:\n{_format_listing(new_item)}\n\n"
        f"Outfit suggestion:\n{outfit.strip()}"
    )
    return generate(
        prompt,
        system=(
            "You write short thrift-haul captions. Two to four sentences. "
            "No hashtag walls, no 'link in bio'."
        ),
    )
