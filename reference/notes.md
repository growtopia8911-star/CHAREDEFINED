# Competitor design reference

Screenshots in [reference/competitors/](competitors/). Full-page, 390px (mobile) and
1440px (desktop), captured 2026-08-26.

**Rule for using this file:** take structure and ideas, never assets or code. What is
worth mining here is arrangement — where the order button lives, how the menu is
chunked, how big the photos are. The look itself should come out different.

---

## URL corrections

Two of the four requested domains are dead, one needed `www`. Substitutions made:

| Requested | Status | Captured instead |
| --- | --- | --- |
| `bobaguys.com` | Apex fails TLS (`ERR_CERT_COMMON_NAME_INVALID`) | `www.bobaguys.com` |
| `chichasanchen.us` | Does not resolve (`ERR_NAME_NOT_RESOLVED`) | `www.chichasanchentx.com` |
| `sunrighttea.com` | Parked GoDaddy lander, no site | `www.snrtea.com` |
| `fengchateahouse.com` | 404, "Reconnect Your Domain \| Wix.com" | `fengchausa.com` |

Chicha San Chen has no single US site — each region runs its own. I took the Texas
one (Dallas / Austin / Houston) as the closest market.

> **Two of these are neighbours, not abstract competitors.**
> Feng Cha's Bellaire store is **9889 Bellaire Blvd Ste C316** — the same building as
> Cha Redefine at **Suite C318**, one suite over. Chicha San Chen Houston is
> **9750 Bellaire Blvd Ste 180**, a few doors down the same street. Whatever gets
> built has to look deliberately unlike the two sites above.

---

## Boba Guys — `www.bobaguys.com`

`bobaguys-mobile.png` (390x2797) · `bobaguys-desktop.png` (1440x1643)

**Menu structure.** There isn't one on the site. `/menu` is a near-empty page with one
line of copy and two links — "ENGLISH MENU" and "SPANISH MENU" — pointing off-site. No
item names, no categories, no prices in HTML anywhere. The homepage carries no menu
content at all; it is four promo tiles and two press pull-quotes.

**Order button on mobile.** Buried. The header is logo + hamburger only — no visible
order affordance. "Order Ahead" is the third item inside the drawer, below "Shop" and
above "Menu", as a 55px-tall plain text row with no button styling. Nothing sticky, no
persistent CTA. You must open a menu to find out you can order.

**Drink photography.** Light — 6 images on the whole homepage. One full-bleed hero
(370x208 mobile) of eight cups lined up on coral blocks, then three 370x370 square promo
tiles, two of which are product-packaging flat-lays rather than drinks. Below the tiles
the page is entirely type.

**Palette.** White `#FFFFFF` ground, near-black text `#343434`, and a dusty seafoam
`#83B3BE` used sparingly. Most of the colour on screen comes from the photographs, not
the CSS — the tiles are yellow and mint because the photo backdrops are.

**Type.** Poppins for everything, headings and body. Headings are uppercase with 1px
letter-spacing at small sizes; body sits around 13px. Geometric sans, single family, no
pairing.

---

## Chicha San Chen (TX) — `www.chichasanchentx.com`

`chichasanchen-mobile.png` (1039x4744) · `chichasanchen-desktop.png` (1440x4744)

> **Caveat on the mobile file.** This is a Wix site with no responsive breakpoints for a
> desktop user-agent — at a 390px viewport it still lays out at 1039px, so the "mobile"
> screenshot is a squeezed desktop page. A real phone gets Wix's separate UA-switched
> mobile view, which Playwright can't reach here. Treat the file as evidence the site
> isn't fluid, not as a picture of their phone experience.

**Menu structure.** None on their own site. The nav is HOME / LOCATIONS / CATERING /
CONTACT, and "ORDER ONLINE" routes to the Locations page, where each of the three stores
has its own "ORDER ONLINE" link into Chowbus. Every drink name, photo and price lives on
the ordering platform. This is the same shape as Cha Redefine's Toast setup — and it is
the reason a real on-site menu is the easiest way to beat them.

**Order button on mobile.** Top-right of the header, a 156x40 dark rectangle reading
"ORDER ONLINE". Because the layout is fixed-width, on a phone it sits off toward the
edge of a page you have to pinch-zoom. A second "ORDER NOW" appears mid-page as a
hairline outlined box. Neither is sticky.

**Drink photography.** High volume, low consistency — 31 images. Large lifestyle shots
(a tea plantation at 980x778, a 980x844 interior), one strong product shot of a mango
drink with real fruit staged beside it, and a gallery carousel of wooden-tray flat-lays.
Quality is uneven: one section renders as a solid black box, another as a solid pink
block, and there's a tall empty white gap before the footer.

**Palette.** Pale pistachio `#EAF6CE` as the dominant field, near-black `#2F2E2E` for
text and buttons, an olive-lime accent `#9DBA1B`, dusty pink `#EEC3CA`, and full-black
section blocks. Reads agricultural and tea-farm-ish, but the black blocks fight it.

**Type.** A genuine pairing, and the most distinctive of the four: **Lulo Clean One Bold**
for the H1 — a wide, all-caps geometric display face with heavy tracking — over
**DIN Neuzeit Grotesk Light** for headings and body. H1 runs 75px, body 23px, both in
`#2F2E2E`. Licensed Wix fonts, so not directly reproducible; the *idea* (wide tracked
display over a narrow grotesque) is.

---

## Sunright Tea Studio — `www.snrtea.com`

`sunrighttea-mobile.png` (390x4128) · `sunrighttea-desktop.png` (1440x4911)

The only one of the four with a real, structured, on-site menu.

**Menu structure.** `/menu/` opens with a **Best Sellers** row of 9 drinks, then eleven
named categories: Milk Tea · Fruit Tea · Sunright Brown Sugar Boba Milk · Frosties ·
Matcha Series · Yakult Series · Cheese Foam · Original Tea · Coffee · Kid's Menu. Every
item is a 272x272 square photo, name, and an "EXPLORE +" control that opens detail.
**No prices anywhere on the site.** Ordering is a store-locator hop first, then an
external platform.

**Order button on mobile.** The strongest of the four. A fixed 92px header pinned for the
whole scroll, carrying a pill "ORDER NOW" next to a hamburger — always one tap away. It
repeats as a solid yellow pill in the hero and again as "VIEW MENU" mid-page. Pills are
fully rounded (44px radius on a 44px-tall button).

**Drink photography.** Moderate on the homepage (9 images), heavy on the menu. The
homepage leans on one hero of four customers holding cups, one big yellow-background
product shot with a diagonal "SHAKE 17 TIMES" ribbon across it, and circular press logos.
The menu page is where the photography does the work — a uniform square grid, one shot
per drink, consistent lighting and framing throughout.

**Palette.** Black `#000000` and a single saturated yellow `#FFF200`, plus white and two
near-blacks (`#212121`, `#1C1C1C`). Effectively two colours. Loud, high-contrast, very
committed — and the clearest identity of the four.

**Type.** **Jost** for absolutely everything — the only family on the page. Display
headings run to 60px semibold in yellow; body 18px bold white. Big, tight, uppercase for
emphasis. A Google font, so directly available.

---

## Feng Cha — `fengchausa.com`

`fengcha-mobile.png` (390x8618) · `fengcha-desktop.png` (1440x6729)

The most modern build of the four, and the direct next-door neighbour.

**Menu structure.** Two levels, photo-first. The homepage carries a **category card**
block — Dirty Series, Milk Tea, Blended Series, Coffee Series — each a coloured card with
a "View Products" button, followed by a **Best Sellers** row of four drinks (Creme Brulee
Dirty Boba, Mango Fantasy, Matcha Latte, Strawberry Overload) with a 2-3 line tasting
description under each. `/menu/` is nine category cards at 422x281 — Dirty Series, Milk
Tea, Blended Series, Fruit Drinks, Matcha Series, Coffee Series, Au Lait Series, Milk
Foam Cake, Original Tea & Milk Foam Tea. **No item names and no prices on the menu index**
— you click a category to go deeper. Nine categories is a lot of taps to a drink.

**Order button on mobile.** A sticky 72px header runs the whole page, but on mobile it
holds only the wordmark and a hamburger — "Menu" and "Order" are drawer items. The
visible CTA is a cobalt "Order Now" pill (140x44, 32px radius) sitting in the hero at
~390px down, and it repeats near the footer at ~6120px. So: sticky bar, but the actual
order button is not in it, and there's a ~5700px stretch of page with no CTA on screen.

**Drink photography.** The heaviest of the four — 29 images on the homepage alone. Hero
is a hand holding a dirty-boba in a cafe; category cards use full-bleed product shots;
best-sellers are four cups shot on soft pastel gradient backgrounds; plus a lifestyle
grid, a story photo, app-store badges and a mascot penguin illustration. The page runs
8618px on mobile — very long.

**Palette.** Warm cream ground `#F7F7EF`, one strong cobalt-blue accent `#4069E0` used for
headings, buttons, links and full-bleed panels, a pale blue tint `#E9EEFB`, and grey body
text `#595959` / `#969696`. Cream + single saturated accent is exactly the structure the
Cha Redefine direction calls for — which is precisely why the accent must not be blue and
the shapes must not be pills.

**Type.** **Funnel Display** for headings (36px, weight 500) over **Funnel Sans** for body
(17px). Both are Google fonts, both recent, and the pairing is the freshest of the four —
a friendly geometric display over a neutral text sans.

---

## Patterns common to all four

1. **Nobody publishes prices.** Not one of the four shows a dollar figure anywhere on
   its marketing site. Prices live on Toast / Chowbus / the in-store board.
2. **The site never takes the order.** Every one of them hands off — Chowbus, an app, a
   store locator, a PDF. No carts, no checkout. Cha Redefine linking out to Toast is the
   normal shape, not a compromise.
3. **Category-chunked menus, 4–11 groups.** Where a menu exists it is grouped by drink
   family (Milk Tea / Fruit Tea / Matcha / Coffee / Brown Sugar), and a "Best Sellers"
   or "Signature" row is pulled out above the categories. Both sites that do this put
   best-sellers first.
4. **One square photo per drink.** Sunright at 272x272, Feng Cha at 422x281 for
   categories and ~171x181 for best-seller tiles. Uniform crop, one drink per frame,
   plain or gradient backdrop. Never a photoless list.
5. **A hero shot of cups in a row, or a hand holding one.** All four open on either a
   lineup of drinks on a coloured surface or a hand-held cup in a real space.
6. **One accent colour, carried hard.** Sunright yellow on black, Feng Cha cobalt on
   cream, Chicha lime on pistachio. None of them use a second accent. The discipline is
   worth copying; the specific hues are all taken.
7. **Fully rounded pill buttons everywhere.** 32px and 44px radii on 44px-tall buttons —
   three of the four. This is the single most templated thing about the set, and the
   cheapest place to look different.
8. **Sticky headers, weak sticky CTAs.** Three have a pinned header; only Sunright keeps
   an order button inside it. Feng Cha's sticky bar has a hamburger where the CTA should
   be, and Boba Guys hides ordering in a drawer entirely.
9. **Uppercase micro-labels as section markers.** "/ SIP-SATION", "/ MEDIA",
   "BEYOND THE BOBA", "GOOGLE MAPS REVIEWS" — small, tracked, all-caps eyebrow text above
   each section instead of ordinary headings.
10. **Social proof sits low.** Press logos and pull-quotes (Boba Guys: NPR, NYT;
    Sunright: KTLA, NBC, LA Times; Feng Cha: Google Maps reviews) always land in the
    bottom third, after the product.
11. **Sans-serif only, no serifs at all.** Poppins, Jost, DIN Neuzeit, Funnel Sans,
    Lulo Clean. Not one serif or humanist face in the set. A serif — or a serif display
    over a clean sans — would read as premium against every one of these immediately.

### Where the openings are

- **Show prices.** Trivially easy, and nobody does it.
- **One-tap ordering that persists.** A genuine sticky order bar beats all four.
- **A flat menu, not a category maze.** Feng Cha costs two taps and nine choices to reach
  a drink name.
- **Serif display type and non-pill geometry.** The fastest way to not look like the
  neighbours.
- **Say what's in the cup.** Ceremonial-grade matcha, ONYX espresso, house-made taro
  paste and rice mochi, fresh coconut water — Chicha gestures at sourcing and Feng Cha
  writes tasting notes, but none of them make ingredients the argument.
