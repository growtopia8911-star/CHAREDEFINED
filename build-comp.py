#!/usr/bin/env python3
"""
Build the Cha Redefine design comp as a single self-contained HTML file.

Reads data/menu.json, resizes the drink photos, inlines everything as data
URIs (the artifact host blocks external image requests), and writes the comp.

Usage:  python3 build-comp.py [output.html]
"""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "comp.html")

DRINK_PX = 440
HERO_PX = 1600

# Hero: prefer the untitled cup-lineup shot if it has been saved, otherwise
# fall back to the Toast banner (which has promo text baked into the left side,
# so it gets shifted with object-position).
HERO_CANDIDATES = ["assets/hero-lineup.jpg", "assets/hero-lineup.png", "assets/hero-toast.jpg"]

# Brand logos, used the moment the files exist. Until then the header falls back
# to the typeset wordmark and the favicon to an inline 茶.
#   logo-mark      - the square CHA REDEFINE badge, used as the browser-tab icon
#   logo-wordmark  - the horizontal CHA REDEFINE lockup, used in the header
# A wordmark drawn in white needs a dark chip behind it on the cream header;
# set LOGO_ON_DARK = True in that case.
MARK_CANDIDATES = [
    "assets/logo-mark.png", "assets/logo-mark.svg", "assets/logo-mark.jpg",
]
WORDMARK_CANDIDATES = [
    "assets/logo-wordmark.svg", "assets/logo-wordmark.png", "assets/logo-wordmark.jpg",
]
LOGO_ON_DARK = False

# One hue per drink family, sampled from the drinks themselves rather than
# invented. Matcha is one of these, not the brand colour - that was the note.
FAMILY_HUES = [
    (r"matcha",                     "#7C9B4E"),
    (r"beet|superfood",             "#C0495F"),
    (r"longan|coconut|coco",        "#D9B57F"),
    (r"lychee|rice",                "#E0A0AC"),
    (r"hojicha",                    "#A8623A"),
    (r"einspanner",                 "#C08A4E"),
    (r"mochi",                      "#B39BC6"),
    (r"milk tea|chappuccino|latte", "#8A6642"),
    (r"fruit",                      "#D9704A"),
    (r"coffee",                     "#6B4526"),
    (r"non caffeinated|kids",       "#CE8A5C"),
    (r"cream foam",                 "#D8B072"),
    (r"^cha$",                      "#7E9E7A"),
    (r"cup|topping",                "#A99684"),
]
DEFAULT_HUE = "#A99684"

# Instagram mark as inline SVG - currentColor so it inherits the text colour.
IG_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
    '<rect x="2.5" y="2.5" width="19" height="19" rx="5.2"/>'
    '<circle cx="12" cy="12" r="4.2"/>'
    '<circle cx="17.6" cy="6.4" r="1.1" fill="currentColor" stroke="none"/>'
    '</svg>'
)

# The six that carry the ingredient argument: matcha, house taro + mochi,
# ONYX espresso, fresh coconut, plus the two signatures.
SIGNATURE_SLUGS = [
    "matcha-latte-ice",
    "mochi-taro-24oz",
    "rice-einspanner-12oz-no-need-straw",
    "matcha-coco-chill-16oz",
    "banana-pudding-matcha-latte-12oz",
    "popping-milk-tea-16oz",
]


def hue_for(category):
    c = (category or "").lower()
    for pat, hue in FAMILY_HUES:
        if re.search(pat, c):
            return hue
    return DEFAULT_HUE


def resize_to_data_uri(path, px, quality=70):
    """Resize with sips (built into macOS) and return a base64 data URI."""
    if not os.path.exists(path):
        return None
    tmpdir = tempfile.mkdtemp()
    try:
        tmp = os.path.join(tmpdir, "out.jpg")
        shutil.copy(path, tmp)
        subprocess.run(
            ["sips", "-Z", str(px), "-s", "format", "jpeg",
             "-s", "formatOptions", str(quality), tmp],
            capture_output=True, check=False,
        )
        with open(tmp, "rb") as fh:
            return "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def load_logo(candidates, px):
    """First existing candidate as a data URI. SVG is passed through untouched."""
    for rel in candidates:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        if path.lower().endswith(".svg"):
            with open(path, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode()
            return f"data:image/svg+xml;base64,{b64}", rel
        return resize_to_data_uri(path, px, quality=88), rel
    return None, None


def esc(s):
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# Copy normalisation
#
# Toast is a point-of-sale system; its item names and descriptions are typed by
# staff between orders and carry typos, inconsistent casing and stuck-together
# sizes. Everything below fixes the DISPLAY copy only - data/menu.json stays a
# faithful record of what Toast actually says, so a re-scrape never silently
# reintroduces a fix we already made.
# ---------------------------------------------------------------------------

# Outright typos, matched case-insensitively as whole words.
TYPO_FIXES = [
    (r"\bCeremonial Grad\b",  "Ceremonial Grade"),
    (r"\bSmotthie\b",         "Smoothie"),
    (r"\bFerminated\b",       "Fermented"),
    (r"\bSir Lanka\b",        "Sri Lanka"),
    (r"\bChewBlis\b",         "Chew Bliss"),
    (r"\bwater-\s*chestnut\b", "Water Chestnut"),
    (r"\bslush(?=\d)",         "Slush "),
]

# Phrases replaced wholesale.
PHRASE_FIXES = [
    (r"[,\s]*\(?\s*this drink is not able to adjust anything\s*\)?",
     " \u2014 served as-is, no modifications"),
    (r"\(\s*no need straw\s*\)", ""),
]

# Words that keep their own casing rather than being title-cased.
ACRONYMS = {"onyx": "ONYX", "bom": "BOM", "diy": "DIY"}

# Connectors that stay lowercase unless they open a phrase.
SMALL_WORDS = {"and", "or", "with", "of", "in", "on", "at", "to", "a", "an", "the", "by"}


def _fix_typos(text):
    for pat, rep in TYPO_FIXES:
        text = re.sub(pat, rep, text, flags=re.I)
    return text


def _apply_phrases(text):
    """Run LAST. These replacements carry their own punctuation and casing,
    so they must not be fed through the spacing or title-case passes."""
    for pat, rep in PHRASE_FIXES:
        text = re.sub(pat, rep, text, flags=re.I)
    return re.sub(r"\s{2,}", " ", text).strip(" ,;")


def _fix_spacing(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;])", r"\1", text)      # " ," -> ","
    text = re.sub(r"([,;])(?=\S)", r"\1 ", text)   # ",x" -> ", x"
    text = re.sub(r"\s*-\s*", " - ", text)         # spaced en-dash style
    return text.strip(" ,;-")


def _size_format(text):
    """12oz / 24 OZ / slush24oz -> 12 oz, 24 oz - always spaced and lowercase."""
    return re.sub(r"(\d+)\s*oz\b", r"\1 oz", text, flags=re.I)


def smart_title(text):
    """Title-case an ingredient list without wrecking brand casing.

    A token that already carries an internal capital (CocoLongan, DaHongPao)
    is left exactly as typed - those are deliberate, not mistakes.
    """
    def cap_token(tok, first):
        if not tok:
            return tok
        low = tok.lower()
        if low.strip(".,") in ACRONYMS:
            return tok.replace(tok.strip(".,"), ACRONYMS[low.strip(".,")])
        if re.search(r"[a-z][A-Z]", tok):   # CocoLongan, ChewBliss
            return tok
        if tok.isupper() and len(tok) > 1:  # already an acronym
            return tok
        if low in SMALL_WORDS and not first:
            return low
        m = re.search(r"[a-z]", low)
        if not m:
            return low
        i = m.start()
        return low[:i] + low[i].upper() + low[i + 1:]

    out = []
    for segment in re.split(r"(,\s*)", text):
        if not segment or segment.startswith(","):
            out.append(segment)
            continue
        words = segment.split(" ")
        out.append(" ".join(
            cap_token(w, i == 0) for i, w in enumerate(words)
        ))
    return "".join(out)


def clean_name(name):
    """Display name: typos fixed, casing normalised, sizes spaced last."""
    s = _fix_typos(name)
    s = _fix_spacing(s)
    s = smart_title(s)
    s = _size_format(s)      # before phrases, so casing cannot produce "Oz"
    return _apply_phrases(s)


def clean_desc(desc):
    """Description: same treatment, kept as a Title Case ingredient list."""
    if not desc:
        return ""
    s = _fix_typos(desc)
    s = _fix_spacing(s)
    s = smart_title(s)
    s = _size_format(s)
    return _apply_phrases(s)


# Toast's category names are typed by staff and carry casing and spacing
# quirks. Fix them for display without touching the source data.
CATEGORY_OVERRIDES = {
    "superfood-Beet & Coconut": "Superfood — Beet & Coconut",
    "Longan& coconut": "Longan & Coconut",
    "Signature Milk Tea (Chappuccino & Cha Latte)": "Signature Milk Tea",
    "Non Caffeinated & Kids Menu": "Non-Caffeinated & Kids",
    "cups": "Cups",
    "Topping": "Toppings",
    "Cha X Fruits": "Cha × Fruits",
}


def category_id(name):
    """Stable anchor id for a menu category."""
    slug = re.sub(r"[^a-z0-9]+", "-", tidy_category(name).lower()).strip("-")
    return f"cat-{slug}"


def tidy_category(name):
    if name in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[name]
    s = re.sub(r"\s*&\s*", " & ", name)
    s = re.sub(r"\s+", " ", s).strip()
    # capitalise a leading lowercase word, leave the rest as typed
    return s[:1].upper() + s[1:] if s else s


def main():
    data = json.load(open(os.path.join(ROOT, "data", "menu.json")))
    menu = data["menu"]

    by_slug = {i["slug"]: (s, i) for s in menu for i in s["items"]}

    print("encoding images...")
    images = {}
    for sec in menu:
        for item in sec["items"]:
            if item.get("image"):
                uri = resize_to_data_uri(os.path.join(ROOT, item["image"]), DRINK_PX)
                if uri:
                    images[item["slug"]] = uri
    print(f"  {len(images)} drink photos encoded")

    hero_uri, hero_src = None, None
    for cand in HERO_CANDIDATES:
        p = os.path.join(ROOT, cand)
        if os.path.exists(p):
            hero_uri = resize_to_data_uri(p, HERO_PX, quality=68)
            hero_src = cand
            break
    print(f"  hero: {hero_src}")

    mark_uri, mark_src = load_logo(MARK_CANDIDATES, 180)
    word_uri, word_src = load_logo(WORDMARK_CANDIDATES, 720)
    print(f"  tab mark: {mark_src or 'none - falling back to inline 茶'}")
    print(f"  wordmark: {word_src or 'none - falling back to typeset text'}")

    if word_uri:
        brand_html = (
            f'<a class="mark mark--img{" mark--dark" if LOGO_ON_DARK else ""}" href="#top">'
            f'<img src="{word_uri}" alt="Cha Redefine" width="220" height="44">'
            f'</a>'
        )
    else:
        brand_html = '<a class="mark" href="#top">Cha Redefine</a>'

    # The Toast banner has "LONGAN & COCONUT" set across its upper left. In a
    # tall band the full image width shows, so the crop has to bias downward
    # instead of sideways to keep the promo type out of frame and the cups in.
    # A photo without baked-in type (assets/hero-lineup.jpg) needs none of this.
    hero_pos = "center 78%" if hero_src == "assets/hero-toast.jpg" else "center"

    # ---- signature cards -------------------------------------------------
    sig_html = []
    for slug in SIGNATURE_SLUGS:
        if slug not in by_slug:
            print(f"  ! signature missing: {slug}")
            continue
        sec, item = by_slug[slug]
        hue = hue_for(sec["category"])
        img = images.get(slug)
        media = (f'<img class="sig__img" src="{img}" alt="{esc(clean_name(item["name"]))}" '
                 f'loading="lazy" decoding="async" width="440" height="440">'
                 if img else '<div class="sig__img sig__img--none"></div>')
        sig_html.append(f"""
        <article class="sig">
          <div class="sig__media" style="--hue:{hue}">{media}</div>
          <div class="sig__text">
            <h3 class="sig__name">{esc(clean_name(item['name']))}</h3>
            <p class="sig__desc">{esc(clean_desc(clean_desc(item["description"])))}</p>
            <p class="sig__price">{esc(item['price'])}</p>
          </div>
        </article>""")

    # ---- full menu -------------------------------------------------------
    drink_secs = [s for s in menu if s["kind"] == "drink"]
    topping_secs = [s for s in menu if s["kind"] == "topping"]

    menu_html = []
    for sec in drink_secs:
        hue = hue_for(sec["category"])
        rows = []
        for item in sec["items"]:
            img = images.get(item["slug"])
            alt = esc(clean_name(item["name"]))
            thumb = (f'<span class="row__thumbwrap"><img class="row__thumb" src="{img}" '
                     f'alt="{alt}" loading="lazy" decoding="async" width="440" height="440">'
                     f'</span>'
                     if img else '<span class="row__thumbwrap row__thumbwrap--none" aria-hidden="true"></span>')
            desc = (f'<p class="row__desc">{esc(clean_desc(item["description"]))}</p>'
                    if item["description"] else "")
            rows.append(f"""
            <li class="row">
              {thumb}
              <div class="row__text">
                <h4 class="row__name">{esc(clean_name(item['name']))}</h4>
                {desc}
              </div>
              <span class="row__price">{esc(item['price'])}</span>
            </li>""")
        menu_html.append(f"""
        <section class="group" id="{category_id(sec['category'])}" style="--hue:{hue}">
          <h3 class="group__name"><span class="group__dot" aria-hidden="true"></span>{esc(tidy_category(sec["category"]))}</h3>
          <ul class="rows">{''.join(rows)}</ul>
        </section>""")

    top_html = []
    for sec in topping_secs:
        chips = "".join(
            f'<li class="chip"><span>{esc(clean_name(i["name"]))}</span><b>{esc(i["price"])}</b></li>'
            for i in sec["items"]
        )
        top_html.append(f"""
        <section class="group group--chips" id="{category_id(sec['category'])}">
          <h3 class="group__name"><span class="group__dot" style="--hue:#A99684" aria-hidden="true"></span>{esc(tidy_category(sec["category"]))}</h3>
          <ul class="chips">{chips}</ul>
        </section>""")

    jump_html = "".join(
        f'<li><a class="jump__link" href="#{category_id(sec["category"])}" '
        f'style="--hue:{hue_for(sec["category"])}">'
        f'<span class="jump__dot" aria-hidden="true"></span>'
        f'{esc(tidy_category(sec["category"]))}</a></li>'
        for sec in drink_secs + topping_secs
    )

    n_drinks = sum(len(s["items"]) for s in drink_secs)

    hero_media = (f'<img src="{hero_uri}" alt="Cha Redefine drinks lined up" '
                  f'style="object-position:{hero_pos}">' if hero_uri else "")

    html = TEMPLATE.format(
        ig_svg=IG_SVG,
        brand=brand_html,
        hero_media=hero_media,
        signatures="".join(sig_html),
        menu="".join(menu_html),
        jump=jump_html,
        toppings="".join(top_html),
        n_drinks=n_drinks,
        n_cats=len(drink_secs),
        hero_note=("" if hero_src != "assets/hero-toast.jpg" else
                   " The header photo is the Toast banner as a stand-in — save the cup-lineup "
                   "shot as <b>assets/hero-lineup.jpg</b> and rebuild to swap it in."),
    )

    # The artifact host wraps the fragment in its own document shell. Pass
    # --standalone for a file that opens on its own by double-clicking, which
    # is what you want when sending it to someone directly.
    if "--standalone" in sys.argv:
        head, rest = html.split('<header class="masthead">', 1)
        # A 茶 on the site's cream ground, drawn inline so there is no icon file.
        favicon = mark_uri or (
            "data:image/svg+xml,"
            "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
            "%3Crect width='64' height='64' fill='%23F4EBDD'/%3E"
            "%3Ctext x='32' y='47' font-family='Georgia,serif' font-size='44' "
            "text-anchor='middle' fill='%2315120F'%3E%E8%8C%B6%3C/text%3E%3C/svg%3E"
        )
        description = (
            "Ceremonial grade matcha, handmade rice mochi and house-made taro paste. "
            "Craft boba on Bellaire Blvd in Houston Chinatown \u2014 order pickup online."
        )
        # bare & is invalid inside an attribute value
        og_title = "Cha Redefine \u2014 Ceremonial Matcha &amp; Handmade Mochi | Houston, TX"
        html = (
            '<!doctype html>\n<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<meta name="description" content="{description}">\n'
            f'<link rel="icon" href="{favicon}">\n'
            '<meta property="og:type" content="website">\n'
            f'<meta property="og:title" content="{og_title}">\n'
            f'<meta property="og:description" content="{description}">\n'
            '<meta property="og:locale" content="en_US">\n'
            '<!-- REPLACE WITH A REAL HOSTED IMAGE URL, 1200x630, BEFORE LAUNCH -->\n'
            '<meta property="og:image" content="https://example.com/cha-redefine-og.jpg">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            + head
            + '</head>\n<body>\n<header class="masthead">'
            + rest
            + '\n</body>\n</html>\n'
        )

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote {OUT}  ({os.path.getsize(OUT)/1_000_000:.1f} MB)")


TEMPLATE = """<title>Cha Redefine \u2014 Ceremonial Matcha &amp; Handmade Mochi | Houston, TX</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Instrument+Sans:wght@400;500;600&display=swap">

<style>
/* ─────────────────────────────────────────────
   Cha Redefine — design comp
   Palette and type follow the shop's own brand
   assets: warm sand ground, black CHA wordmark,
   high-contrast serif set in small caps.
   Colour comes from the drinks, not the chrome —
   matcha is one family hue among several.
   ───────────────────────────────────────────── */
:root{{
  --paper:#F4EBDD;
  --paper-2:#EDE0CE;
  --card:#FBF5EC;
  --sand:#D9C3A2;
  --ink:#15120F;
  --ink-2:#6B5D4E;
  --ink-3:#9C8B78;
  --rule:#DFCFB8;
  --rule-soft:#E8DBC7;

  --s-1:.8125rem;
  --s0:1rem;
  --s1:1.125rem;
  --s2:1.5rem;
  --s3:2.125rem;
  --s4:3rem;
  --s5:4.25rem;

  --gut:clamp(1.25rem,5vw,4rem);
  --stack:clamp(3.5rem,8vw,6.5rem);

  --serif:"Cormorant Garamond",Georgia,"Times New Roman",serif;
  --sans:"Instrument Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}}

*,*::before,*::after{{box-sizing:border-box}}

html{{scroll-behavior:smooth}}

body{{
  margin:0;
  background:var(--paper);
  color:var(--ink);
  font-family:var(--sans);
  font-size:var(--s0);
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
  overflow-x:hidden;
}}

h1,h2,h3,h4{{margin:0;font-weight:500;line-height:1.1;text-wrap:balance}}
p{{margin:0}}
ul{{margin:0;padding:0;list-style:none}}
/* figure carries a 40px UA margin that breaks the full-bleed hero */
figure{{margin:0}}
table{{margin:0}}
img{{max-width:100%;display:block}}
a{{color:inherit}}

:focus-visible{{outline:2px solid var(--ink);outline-offset:3px;border-radius:2px}}

.wrap{{width:100%;max-width:76rem;margin-inline:auto;padding-inline:var(--gut)}}

/* in-page links must clear the sticky masthead */
[id]{{scroll-margin-top:76px}}

/* display type — their brand sets it in small caps with wide tracking */
.display{{
  font-family:var(--serif);
  font-variant:small-caps;
  letter-spacing:.06em;
  font-weight:500;
}}

.eyebrow{{
  font-size:.6875rem;
  font-weight:600;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:var(--ink-3);
  display:flex;
  align-items:center;
  gap:.75rem;
  margin-bottom:1.25rem;
}}
.eyebrow::after{{content:"";flex:1;height:1px;background:var(--rule)}}

/* ── masthead ───────────────────────────────── */
.masthead{{
  position:sticky;top:0;z-index:40;
  /* anchor for the mobile nav drop panel */
  background:color-mix(in srgb,var(--paper) 92%,transparent);
  backdrop-filter:blur(12px);
  border-bottom:1px solid var(--rule-soft);
}}
.masthead__in{{display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:62px}}
.mark{{
  font-family:var(--serif);
  font-variant:small-caps;
  letter-spacing:.1em;
  font-size:1.125rem;
  font-weight:600;
  text-decoration:none;
  display:flex;align-items:center;
  min-height:44px;
  white-space:nowrap;
}}
@media(min-width:48rem){{.mark{{font-size:1.375rem}}}}

/* supplied wordmark image, when assets/logo-wordmark.* exists */
.mark--img{{padding-block:.25rem}}
.mark--img img{{
  width:auto;height:26px;display:block;
}}
@media(min-width:48rem){{.mark--img img{{height:30px}}}}
/* a white wordmark needs a dark chip to read on the cream header */
.mark--dark{{
  background:var(--ink);
  padding:.4375rem .75rem;
  border-radius:2px;
}}

.masthead__actions{{display:flex;align-items:center;gap:.5rem}}

/* ── primary nav ────────────────────────────── */
.nav{{display:none;align-items:center;gap:1.75rem}}
.nav__link{{
  font-family:var(--serif);
  font-variant:small-caps;
  letter-spacing:.14em;
  font-size:1rem;
  font-weight:600;
  text-decoration:none;
  color:var(--ink-2);
  min-height:44px;
  display:inline-flex;align-items:center;
  border-bottom:1px solid transparent;
  transition:color .18s ease,border-color .18s ease;
}}
.nav__link:hover{{color:var(--ink);border-bottom-color:var(--ink)}}
.nav__ig{{
  display:inline-flex;align-items:center;justify-content:center;
  width:44px;height:44px;color:var(--ink-2);
  transition:color .18s ease;
}}
.nav__ig:hover{{color:var(--ink)}}
.nav__ig svg{{width:19px;height:19px;display:block}}

/* hamburger — mobile only */
.burger{{
  display:inline-flex;align-items:center;justify-content:center;
  width:44px;height:44px;flex:none;
  background:none;border:1px solid var(--rule);border-radius:2px;
  color:var(--ink);cursor:pointer;padding:0;
}}
.burger span{{
  display:block;width:17px;height:1.5px;background:currentColor;
  position:relative;transition:background-color .18s ease;
}}
.burger span::before,.burger span::after{{
  content:"";position:absolute;left:0;width:17px;height:1.5px;background:currentColor;
  transition:transform .22s ease,top .22s ease;
}}
.burger span::before{{top:-5.5px}}
.burger span::after{{top:5.5px}}
.burger[aria-expanded="true"] span{{background:transparent}}
.burger[aria-expanded="true"] span::before{{top:0;transform:rotate(45deg)}}
.burger[aria-expanded="true"] span::after{{top:0;transform:rotate(-45deg)}}

@media(min-width:48rem){{
  .nav{{display:flex}}
  .burger{{display:none}}
}}

/* mobile drop panel */
@media(max-width:47.99rem){{
  .nav.is-open{{
    display:flex;
    flex-direction:column;
    align-items:flex-start;
    gap:0;
    position:absolute;
    top:100%;left:0;right:0;
    background:var(--paper);
    border-bottom:1px solid var(--rule);
    padding:.5rem var(--gut) 1rem;
  }}
  .nav.is-open .nav__link{{
    width:100%;
    min-height:52px;
    font-size:1.25rem;
    border-bottom:1px solid var(--rule-soft);
  }}
  .nav.is-open .nav__link:hover{{border-bottom-color:var(--rule-soft)}}
  .nav.is-open .nav__ig{{justify-content:flex-start;width:auto;padding-top:.75rem}}
}}

/* ── buttons — black, from the CHA wordmark ─── */
.btn{{
  display:inline-flex;align-items:center;justify-content:center;gap:.5rem;
  min-height:46px;padding:.6875rem 1.5rem;
  font-family:var(--sans);font-size:.9375rem;font-weight:600;
  letter-spacing:.01em;text-decoration:none;
  border-radius:2px;border:1px solid transparent;
  transition:background-color .18s ease,color .18s ease,border-color .18s ease;
}}
.btn--solid{{background:var(--ink);color:var(--paper)}}
.btn--solid:hover{{background:#332A22}}
.btn--ghost{{border-color:var(--ink);color:var(--ink)}}
.btn--ghost:hover{{background:var(--ink);color:var(--paper)}}
.btn--compact{{padding:.5625rem .875rem;font-size:.8125rem;min-height:44px}}
@media(min-width:48rem){{.btn--compact{{padding:.6875rem 1.5rem;font-size:.9375rem}}}}

/* ── hero ───────────────────────────────────── */
.hero{{padding-top:clamp(2rem,4vw,3rem)}}
.hero__type{{max-width:52rem}}
.hero h1{{
  font-family:var(--serif);
  font-variant:small-caps;
  letter-spacing:.04em;
  font-size:clamp(2.375rem,5.5vw,3.75rem);
  line-height:1.05;
}}
.hero__lede{{
  margin-top:1rem;
  font-size:var(--s1);
  color:var(--ink-2);
  max-width:44ch;
  line-height:1.6;
}}
.hero__actions{{margin-top:1.625rem;display:flex;flex-wrap:wrap;gap:.75rem}}
.hero__figure{{
  margin-top:clamp(1.75rem,3.5vw,2.5rem);
  width:100%;
  aspect-ratio:16/9;
  max-height:clamp(300px,62vh,680px);
  overflow:hidden;
  background:var(--sand);
}}
.hero__figure img{{width:100%;height:100%;object-fit:cover}}
.hero__facts{{
  display:flex;flex-wrap:wrap;gap:.5rem 2rem;
  padding-block:1.125rem;
  border-bottom:1px solid var(--rule-soft);
  font-size:var(--s-1);
  color:var(--ink-2);
}}
.hero__facts b{{color:var(--ink);font-weight:600}}

/* ── ingredient claims ──────────────────────── */
.claims{{padding-block:var(--stack)}}
.claims__grid{{display:grid;gap:0;border-top:1px solid var(--rule)}}
@media(min-width:44rem){{.claims__grid{{grid-template-columns:repeat(2,1fr);column-gap:clamp(2rem,5vw,4rem)}}}}
.claim{{padding-block:1.5rem;border-bottom:1px solid var(--rule-soft)}}
.claim__top{{display:flex;align-items:baseline;gap:.75rem}}
.claim__dot{{width:9px;height:9px;border-radius:50%;background:var(--hue);flex:none;position:relative;top:-.15rem}}
.claim__name{{font-family:var(--serif);font-variant:small-caps;letter-spacing:.05em;font-size:1.375rem;font-weight:600}}
.claim__body{{margin-top:.5rem;color:var(--ink-2);font-size:.9375rem;max-width:46ch}}

/* ── signatures ─────────────────────────────── */
.signatures{{padding-block:var(--stack);background:var(--paper-2)}}
.sig__head{{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:1rem;margin-bottom:2.5rem}}
.sig__head h2{{font-family:var(--serif);font-variant:small-caps;letter-spacing:.05em;font-size:var(--s3)}}
.sig__grid{{display:grid;gap:clamp(1.5rem,3vw,2.25rem)}}
@media(min-width:38rem){{.sig__grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(min-width:62rem){{.sig__grid{{grid-template-columns:repeat(3,1fr)}}}}
.sig{{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--rule-soft)}}
.sig__media{{
  position:relative;
  aspect-ratio:1;overflow:hidden;
  background:color-mix(in srgb,var(--hue) 16%,var(--card));
  border-bottom:3px solid var(--hue);
}}
/* Toast shoots these on a tiled "CHA REDEFINE" backdrop. Insetting the image
   past its frame crops the repeating watermark out and centres the cup. */
.sig__img{{
  position:absolute;
  top:-12%;left:-12%;
  width:124%;height:124%;
  object-fit:cover;object-position:center 52%;
}}
.sig__img--none{{width:100%;height:100%}}
.sig__text{{padding:1.25rem 1.25rem 1.5rem;display:flex;flex-direction:column;flex:1;gap:.5rem}}
.sig__name{{font-family:var(--serif);font-variant:small-caps;letter-spacing:.04em;font-size:1.375rem;font-weight:600;line-height:1.15}}
.sig__desc{{font-size:.875rem;color:var(--ink-2);line-height:1.5;flex:1}}
.sig__price{{
  font-size:1rem;font-weight:600;
  font-variant-numeric:tabular-nums;
  padding-top:.625rem;border-top:1px solid var(--rule-soft);
}}

/* ── full menu ──────────────────────────────── */
.menu{{padding-block:var(--stack)}}
.menu__head{{margin-bottom:2.5rem;max-width:44rem}}
.menu__head h2{{font-family:var(--serif);font-variant:small-caps;letter-spacing:.05em;font-size:var(--s3)}}
.menu__head p{{margin-top:.75rem;color:var(--ink-2)}}
/* horizontal category jump list - scrolls sideways on narrow screens */
.jump{{
  margin-bottom:2.5rem;
  border-block:1px solid var(--rule-soft);
  overflow-x:auto;
  scrollbar-width:none;
  -webkit-overflow-scrolling:touch;
}}
.jump::-webkit-scrollbar{{display:none}}
.jump__list{{display:flex;gap:.375rem;padding-block:.5rem;width:max-content;min-width:100%}}
.jump__link{{
  display:inline-flex;align-items:center;gap:.5rem;
  min-height:44px;padding:.375rem .875rem;
  white-space:nowrap;
  font-size:.8125rem;font-weight:500;letter-spacing:.04em;
  color:var(--ink-2);text-decoration:none;
  border:1px solid var(--rule);border-radius:2px;
  background:var(--card);
  transition:color .18s ease,border-color .18s ease;
}}
.jump__link:hover{{color:var(--ink);border-color:var(--ink)}}
.jump__dot{{width:7px;height:7px;border-radius:50%;background:var(--hue);flex:none}}

.menu__cols{{columns:1;column-gap:clamp(2rem,4vw,3.5rem)}}
@media(min-width:56rem){{.menu__cols{{columns:2}}}}
.group{{break-inside:avoid;margin-bottom:2.75rem;display:inline-block;width:100%}}
.group__name{{
  font-family:var(--serif);font-variant:small-caps;letter-spacing:.06em;
  font-size:1.25rem;font-weight:600;
  display:flex;align-items:center;gap:.625rem;
  padding-bottom:.75rem;border-bottom:1px solid var(--ink);
  margin-bottom:.25rem;
}}
.group__dot{{width:8px;height:8px;border-radius:50%;background:var(--hue);flex:none}}
.row{{
  display:grid;
  grid-template-columns:52px 1fr auto;
  gap:.25rem .875rem;
  align-items:center;
  padding-block:.75rem;
  border-bottom:1px solid var(--rule-soft);
}}
.row__thumbwrap{{
  position:relative;
  width:52px;height:52px;flex:none;overflow:hidden;
  border-radius:2px;background:var(--paper-2);
}}
.row__thumb{{
  position:absolute;
  top:-10%;left:-10%;
  width:120%;height:120%;
  object-fit:cover;object-position:center 52%;
}}
.row__thumbwrap--none{{background:color-mix(in srgb,var(--hue) 18%,var(--paper-2))}}
.row__text{{min-width:0}}
.row__name{{font-size:.9375rem;font-weight:500;line-height:1.3}}
.row__desc{{font-size:.8125rem;color:var(--ink-3);line-height:1.45;margin-top:.15rem}}
.row__price{{font-size:.9375rem;font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}}
.group--chips .chips{{display:flex;flex-wrap:wrap;gap:.5rem;padding-top:.875rem}}
.chip{{
  display:inline-flex;align-items:center;gap:.5rem;
  padding:.4375rem .75rem;
  border:1px solid var(--rule);
  border-radius:2px;
  font-size:.8125rem;
  background:var(--card);
}}
.chip b{{font-weight:600;font-variant-numeric:tabular-nums}}

/* ── visit ──────────────────────────────────── */
.visit{{padding-block:var(--stack);background:var(--paper-2)}}
.visit__grid{{display:grid;gap:clamp(2.5rem,5vw,4rem)}}
@media(min-width:52rem){{.visit__grid{{grid-template-columns:1fr 1fr}}}}
.visit h2{{font-family:var(--serif);font-variant:small-caps;letter-spacing:.05em;font-size:var(--s3);margin-bottom:1.5rem}}
.rowlink{{
  display:flex;align-items:center;justify-content:space-between;gap:1rem;
  min-height:56px;padding-block:.5rem;
  border-bottom:1px solid var(--rule);
  text-decoration:none;transition:color .18s ease;
}}
.rowlink:hover{{color:var(--ink-2)}}
.rowlink__k{{font-size:.6875rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3);flex:none}}
.rowlink__v{{text-align:right;font-size:.9375rem;line-height:1.4}}
/* map — thin border matching the divider rules */
.map{{
  margin-top:1.5rem;
  border:1px solid var(--rule);
  background:var(--paper);
  line-height:0;
}}
.map iframe{{display:block;width:100%;height:350px;border:0}}
.map__link{{
  display:inline-flex;align-items:center;gap:.4rem;
  min-height:44px;margin-top:.5rem;
  font-size:.875rem;font-weight:600;
  color:var(--ink);
  border-bottom:1px solid var(--rule);
  text-decoration:none;
  transition:border-color .18s ease;
}}
.map__link:hover{{border-bottom-color:var(--ink)}}

.hours{{width:100%;border-collapse:collapse}}
.hours th,.hours td{{text-align:left;padding-block:.75rem;border-bottom:1px solid var(--rule);font-weight:400;font-size:.9375rem}}
.hours td{{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}}
/* every row is styled identically - no day is highlighted or selected */
.hours tr{{background:none}}
.hours tr:last-child th,.hours tr:last-child td{{border-bottom:none}}

/* ── footer ─────────────────────────────────── */
.foot{{padding-block:2.5rem 6.5rem;font-size:.8125rem;color:var(--ink-3)}}
@media(min-width:48rem){{.foot{{padding-bottom:3rem}}}}
.foot__in{{
  display:grid;gap:2rem;
  padding-bottom:2rem;border-bottom:1px solid var(--rule);
}}
@media(min-width:44rem){{.foot__in{{grid-template-columns:1.2fr 1fr 1fr}}}}
.foot__name{{
  font-family:var(--serif);font-variant:small-caps;letter-spacing:.1em;
  font-size:1.375rem;font-weight:600;color:var(--ink);
}}
.foot__col{{display:flex;flex-direction:column;gap:.375rem}}
.foot__k{{
  font-size:.6875rem;font-weight:600;letter-spacing:.16em;
  text-transform:uppercase;color:var(--ink-3);margin-bottom:.25rem;
}}
.foot__col a{{
  color:var(--ink-2);text-decoration:none;
  min-height:44px;display:inline-flex;align-items:center;
  transition:color .18s ease;
}}
.foot__col a:hover{{color:var(--ink)}}
.foot__social{{
  display:inline-flex;align-items:center;gap:.5rem;
  min-height:44px;color:var(--ink-2);text-decoration:none;
  transition:color .18s ease;
}}
.foot__social:hover{{color:var(--ink)}}
.foot__social svg{{width:19px;height:19px;flex:none}}
.foot__legal{{
  display:flex;flex-wrap:wrap;gap:.75rem 1.5rem;
  justify-content:space-between;padding-top:1.5rem;
}}
.comp-note{{
  margin-top:1.75rem;padding-top:1.25rem;border-top:1px solid var(--rule);
  font-size:.75rem;line-height:1.7;max-width:64ch;
}}
.comp-note b{{color:var(--ink-2);font-weight:600}}

/* ── sticky order bar, mobile ───────────────── */
.orderbar{{
  position:fixed;left:0;right:0;bottom:0;z-index:50;
  padding:.75rem var(--gut) calc(.75rem + env(safe-area-inset-bottom));
  background:color-mix(in srgb,var(--paper) 95%,transparent);
  backdrop-filter:blur(12px);
  border-top:1px solid var(--rule);
  display:flex;gap:.625rem;
}}
.orderbar .btn{{flex:1}}
.orderbar .btn--ghost{{flex:0 0 auto;padding-inline:1.125rem}}
@media(min-width:48rem){{.orderbar{{display:none}}}}

@media(prefers-reduced-motion:reduce){{
  html{{scroll-behavior:auto}}
  *{{transition-duration:.01ms !important;animation-duration:.01ms !important}}
}}
</style>

<header class="masthead">
  <div class="wrap masthead__in">
    {brand}

    <nav class="nav" id="site-nav" aria-label="Primary">
      <a class="nav__link" href="#menu">Menu</a>
      <a class="nav__link" href="#visit">Visit</a>
      <!-- GET REAL HANDLE FROM OWNER -->
      <a class="nav__ig" href="https://instagram.com/PLACEHOLDER" target="_blank" rel="noopener" aria-label="Cha Redefine on Instagram">{ig_svg}</a>
    </nav>

    <div class="masthead__actions">
      <a class="btn btn--solid btn--compact" href="https://charedefinearcadia.toast.site/order/cha-redefine-houston" target="_blank" rel="noopener">Order now</a>
      <button class="burger" type="button" id="nav-toggle" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu"><span></span></button>
    </div>
  </div>
</header>

<main id="top">

  <section class="hero">
    <div class="wrap hero__type">
      <h1>Tea, taken seriously.</h1>
      <p class="hero__lede">Ceremonial grade matcha whisked to order. Taro paste and rice mochi made in our kitchen each morning. Espresso by ONYX. Coconut water cracked fresh.</p>
      <div class="hero__actions">
        <a class="btn btn--solid" href="https://charedefinearcadia.toast.site/order/cha-redefine-houston" target="_blank" rel="noopener">Order now</a>
        <a class="btn btn--ghost" href="#menu">See the menu</a>
      </div>
    </div>
    <figure class="hero__figure">{hero_media}</figure>
    <div class="wrap">
      <p class="hero__facts">
        <span><b>Open</b> daily until 11 PM</span>
        <span><b>Bellaire Blvd</b> Suite C318</span>
        <span><b>{n_drinks} drinks</b> across {n_cats} series</span>
      </p>
    </div>
  </section>

  <section class="claims">
    <div class="wrap">
      <p class="eyebrow">What we buy and what we make</p>
      <div class="claims__grid">
        <div class="claim" style="--hue:#7C9B4E">
          <div class="claim__top"><span class="claim__dot"></span><h3 class="claim__name">Ceremonial grade matcha</h3></div>
          <p class="claim__body">The grade you would drink on its own, not the cooking grade most shops sweeten into submission. Whisked to order, which is why it takes a minute longer.</p>
        </div>
        <div class="claim" style="--hue:#6B4526">
          <div class="claim__top"><span class="claim__dot"></span><h3 class="claim__name">Espresso by ONYX</h3></div>
          <p class="claim__body">Pulled from ONYX Coffee Lab beans — a specialty roaster's espresso in a boba shop, which is not a normal thing to find on Bellaire.</p>
        </div>
        <div class="claim" style="--hue:#B39BC6">
          <div class="claim__top"><span class="claim__dot"></span><h3 class="claim__name">Taro paste and rice mochi</h3></div>
          <p class="claim__body">Both made here. Real taro is a soft grey-purple, not the bright lavender of powder — that colour is how you tell. Mochi is cooked fresh daily.</p>
        </div>
        <div class="claim" style="--hue:#D9B57F">
          <div class="claim__top"><span class="claim__dot"></span><h3 class="claim__name">Fresh coconut water</h3></div>
          <p class="claim__body">Cracked from the coconut, never concentrate. It turns cloudy after a day, so we only open what we will use.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="signatures">
    <div class="wrap">
      <div class="sig__head">
        <div>
          <p class="eyebrow">Start here</p>
          <h2>Six worth queueing for</h2>
        </div>
        <a class="btn btn--ghost" href="#menu">Full menu</a>
      </div>
      <div class="sig__grid">{signatures}</div>
    </div>
  </section>

  <section class="menu" id="menu">
    <div class="wrap">
      <div class="menu__head">
        <p class="eyebrow">Everything, with prices</p>
        <h2>The full menu</h2>
        <p>Every drink comes at your sweetness and ice level. These are the prices you pay at the counter — the same ones on our Toast ordering page.</p>
      </div>
      <nav class="jump" aria-label="Jump to a menu section">
        <ul class="jump__list">{jump}</ul>
      </nav>
      <div class="menu__cols">{menu}{toppings}</div>
    </div>
  </section>

  <section class="visit" id="visit">
    <div class="wrap visit__grid">
      <div>
        <p class="eyebrow">When we're open</p>
        <h2>Hours</h2>
        <!--
          Toast publishes only the CLOSING time for each location, never the
          opening time. Every opening time below is a placeholder.
        -->
        <table class="hours">
          <tbody>
            <tr><th scope="row">Monday</th><td>11:00 AM – 11:00 PM</td></tr><!-- CONFIRM OPENING TIME WITH OWNER -->
            <tr><th scope="row">Tuesday</th><td>11:00 AM – 11:00 PM</td></tr><!-- CONFIRM OPENING TIME WITH OWNER -->
            <tr><th scope="row">Wednesday</th><td>11:00 AM – 11:00 PM</td></tr><!-- CONFIRM OPENING TIME WITH OWNER -->
            <tr><th scope="row">Thursday</th><td>11:00 AM – 11:00 PM</td></tr><!-- CONFIRM OPENING TIME WITH OWNER -->
            <tr><th scope="row">Friday</th><td>11:00 AM – 11:00 PM</td></tr><!-- CONFIRM OPENING TIME WITH OWNER -->
            <tr><th scope="row">Saturday</th><td>11:00 AM – 11:00 PM</td></tr><!-- CONFIRM OPENING TIME WITH OWNER -->
            <tr><th scope="row">Sunday</th><td>11:00 AM – 11:00 PM</td></tr><!-- CONFIRM OPENING TIME WITH OWNER -->
          </tbody>
        </table>
      </div>
      <div>
        <p class="eyebrow">Where to find us</p>
        <h2>Visit</h2>
        <a class="rowlink" href="https://maps.google.com/?q=9889+Bellaire+Blvd+Suite+C318+Houston+TX+77036" target="_blank" rel="noopener">
          <span class="rowlink__k">Address</span>
          <span class="rowlink__v">9889 Bellaire Blvd, Suite C318<br>Houston, TX 77036</span>
        </a>
        <!-- VERIFY: 678 is an Atlanta area code, confirm this is the shop's real number -->
        <a class="rowlink" href="tel:+16788143557">
          <span class="rowlink__k">Phone</span>
          <span class="rowlink__v">(678) 814-3557</span>
        </a>
        <a class="rowlink" href="https://charedefinearcadia.toast.site/order/cha-redefine-houston" target="_blank" rel="noopener">
          <span class="rowlink__k">Order</span>
          <span class="rowlink__v">Pick up on Toast</span>
        </a>

        <div class="map">
          <iframe
            src="https://maps.google.com/maps?q=9889%20Bellaire%20Blvd%20Suite%20C318%20Houston%20TX%2077036&amp;output=embed"
            title="Map showing Cha Redefine at 9889 Bellaire Blvd Suite C318, Houston, Texas"
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
        <a class="map__link" href="https://www.google.com/maps/dir/?api=1&amp;destination=9889%20Bellaire%20Blvd%20Suite%20C318%20Houston%20TX%2077036" target="_blank" rel="noopener">Get directions &rarr;</a>
      </div>
    </div>
  </section>

  <footer class="foot">
    <div class="wrap">
      <div class="foot__in">
        <div class="foot__col">
          <p class="foot__name">Cha Redefine</p>
          <p>9889 Bellaire Blvd, Suite C318<br>Houston, TX 77036</p>
          <p>Open daily until 11 PM</p>
        </div>

        <div class="foot__col">
          <p class="foot__k">Get in touch</p>
          <!-- VERIFY: 678 is an Atlanta area code, confirm this is the shop's real number -->
          <a href="tel:+16788143557">(678) 814-3557</a>
          <a href="https://maps.google.com/?q=9889+Bellaire+Blvd+Suite+C318+Houston+TX+77036" target="_blank" rel="noopener">Find us on the map</a>
          <!-- GET REAL HANDLE FROM OWNER -->
          <a class="foot__social" href="https://instagram.com/PLACEHOLDER" target="_blank" rel="noopener">{ig_svg}<span>Instagram</span></a>
        </div>

        <div class="foot__col">
          <p class="foot__k">Order</p>
          <a href="https://charedefinearcadia.toast.site/order/cha-redefine-houston" target="_blank" rel="noopener">Order pickup on Toast</a>
          <a href="#menu">See the full menu</a>
        </div>
      </div>

      <div class="foot__legal">
        <span>&copy; 2026 Cha Redefine &middot; Houston, Texas</span>
        <span class="display">茶</span>
      </div>
      <p class="comp-note">
        <b>Design comp — not the finished site.</b> Drink names, descriptions, prices and
        photography are pulled live from the shop's own Toast ordering page on 26 August 2026,
        so the menu is real. Hours are shown as "until 11PM" because Toast publishes only the
        closing time — opening times still need confirming.{hero_note}
      </p>
    </div>
  </footer>

  <!--
    Opening times below are the same placeholders as the Hours table.
    Update both together once the owner confirms.
  -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "CafeOrCoffeeShop",
    "name": "Cha Redefine",
    "description": "Ceremonial grade matcha, handmade rice mochi and house taro paste on Bellaire Blvd in Houston Chinatown.",
    "servesCuisine": "Bubble Tea",
    "priceRange": "$$",
    "address": {{
      "@type": "PostalAddress",
      "streetAddress": "9889 Bellaire Blvd, Suite C318",
      "addressLocality": "Houston",
      "addressRegion": "TX",
      "postalCode": "77036",
      "addressCountry": "US"
    }},
    "telephone": "+1-678-814-3557",
    "menu": "https://charedefinearcadia.toast.site/order/cha-redefine-houston",
    "acceptsReservations": false,
    "openingHoursSpecification": [{{
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
      "opens": "11:00",
      "closes": "23:00"
    }}]
  }}
  </script>

</main>

<script>
(function () {{
  var toggle = document.getElementById('nav-toggle');
  var nav = document.getElementById('site-nav');
  if (!toggle || !nav) return;

  function setOpen(open) {{
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  }}

  toggle.addEventListener('click', function () {{
    setOpen(toggle.getAttribute('aria-expanded') !== 'true');
  }});

  // close after tapping a link, and on Escape
  nav.addEventListener('click', function (e) {{
    if (e.target.closest('a')) setOpen(false);
  }});
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {{
      setOpen(false);
      toggle.focus();
    }}
  }});
}})();
</script>

<nav class="orderbar" aria-label="Order">
  <a class="btn btn--solid" href="https://charedefinearcadia.toast.site/order/cha-redefine-houston" target="_blank" rel="noopener">Order now</a>
  <a class="btn btn--ghost" href="tel:+16788143557">Call</a>
</nav>
"""


if __name__ == "__main__":
    main()
