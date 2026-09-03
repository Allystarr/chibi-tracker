---
name: chibi-update
description: Check for newly revealed/released Yu-Gi-Oh chibi alternate-art cards and add them to the master list + Google Sheets feed. Use when the user asks to update the chibi tracker, check for new chibi cards, or sync the sheet.
---

# Update the Yu-Gi-Oh Chibi Card Tracker

The master list lives in `chibi-cards.csv` at the project root. This project is the
git repo `Allystarr/chibi-tracker` (public); the user's Google Sheet reads the split
feeds via `=IMPORTDATA()` from
`https://raw.githubusercontent.com/Allystarr/chibi-tracker/main/chibi-cards-tcg.csv`
(and `...-ocg.csv`). This skill also runs unattended as a daily cloud routine, which
clones the repo fresh — the procedure must work from repo contents alone.

## Scope — what counts as a chibi card

- Printed OCG / TCG cards (including Korean and Japanese promos) whose artwork is a
  chibi-style alternate art. Most use Yu-Gi-Oh! Duel Arena sprites; newer OCG
  "Limit Over Collection" / TCG "Magnificent Monsters" waves use newly drawn chibi art.
- Chibi Token cards (e.g. Legendary 5D's Decks L5DD-ENS04–06) count.
- One row **per print**: a TCG reprint of an OCG chibi art is its own row.
- **Excluded:** Yu-Gi-Oh! Rush Duel prints, video-game-only art, merch
  (sleeves, badges, playmats), and non-chibi "extended art" / "new artwork" variants
  that happen to share a set with chibi cards.

## Cloud-run note

When running as the scheduled cloud routine, the sandbox's egress proxy may block
some domains (observed 2026-09-03: yugipedia.com, db.yugioh-card.com,
ygorganization.com, tcgcsv.com — while WebSearch works fine). Handle gracefully:
lean on WebSearch for discovery, skip the price refresh if tcgcsv.com is
unreachable (note it in the commit message), and still publish any new cards found.
If the user has since allowed those domains in the environment's network settings,
the full procedure applies.

## Procedure

1. **Read** `chibi-cards.csv`. Build the set of known (Card Name, Set Code) pairs.

2. **Discover new chibi prints.** Check these sources (Yugipedia's MediaWiki API works
   with `curl -A "ChibiCollectionTracker/1.0"`; regular page fetches return 403, so use
   `https://yugipedia.com/api.php` with `action=query&prop=revisions&rvprop=content&titles=...&redirects&format=json`):

   a. **Set Card Lists tagged chibi** — search API:
      `action=query&list=search&srsearch=chibi&srwhat=text&srnamespace=3006&srlimit=50`
      (ns 3006 = Set Card Lists). Fetch any set list not already fully represented in
      the CSV and pull rows whose description says `(chibi artwork)`.

   b. **Card Artworks pages** — same search with `srnamespace=3012` (Card Artworks).
      Any card name that isn't in the CSV is a lead: read its page content and find
      which set/promo printed the chibi art. Watch for phrases like "chibi",
      "Duel Arena". Ignore Rush Duel and merch mentions.

   c. **Official catalog deck** — WebFetch
      `https://www.db.yugioh-card.com/yugiohdb/member_deck.action?cgid=cb093d6b89d7eba5c2dc4cd3006841e6&dno=204&request_locale=en`
      (a community-maintained "Chibi cards list" on the official DB). Any card name
      there but not in the CSV needs investigating.

   d. **News sweep** — WebSearch for recent reveals, e.g.
      `Yu-Gi-Oh chibi cards <current year> new set` and check ygorganization.com /
      yugiohmeta.com results. New Battles-of-Legend-style TCG sets and OCG
      collection sets are the usual sources of new chibi waves. Note: LOCH/LOCR-style
      set lists on Yugipedia mark chibi rows only as "New artwork" — cross-check with
      the Card Artworks pages or news articles to tell chibi apart from other
      alternate arts in the same set.

3. **Verify each candidate** before adding: confirm set code, rarity/rarities, and
   release date (use the earliest regional release date, format YYYY-MM-DD) from the
   Yugipedia set page or set list. If a card is announced but the set code is unknown,
   still add it with the set name, `TBA` as the set code, and the expected release
   date — a later run should replace `TBA` rows with real codes when known.

4. **Append** new rows to the END of `chibi-cards.csv` — never reorder, resort, or
   delete existing rows (the Google Sheet's owned-checkboxes align by row position).
   Columns: `Card Name,Set,Set Code,Game,Region,Release Date,Rarities,Notes,Market Price (USD),Price Updated`.
   Leave the two price columns empty on new rows — step 5 fills them.
   Quote any field containing a comma. Updating a field in-place on an existing row
   (e.g. filling in a TBA set code) is fine.

5. **Refresh prices**: run `python scripts/fetch_prices.py` from the project root.
   It fills the `Market Price (USD)` / `Price Updated` columns for TCG prints from
   tcgcsv.com (TCGplayer market prices, per rarity). OCG/promo prints stay `n/a`.
   If it warns about a set with no TCGplayer group (e.g. a set that just released),
   note that in the report — those rows keep blank prices until a later run.

6. **Regenerate the per-game feeds**: run `python scripts/split_csv.py` from the
   project root. It rebuilds `chibi-cards-tcg.csv` and `chibi-cards-ocg.csv` from the
   master (the user's sheet has one tab per game, each importing its own file).

7. **Publish** so the Google Sheet picks it up: commit all changed CSVs and push.
   `git add chibi-cards.csv chibi-cards-tcg.csv chibi-cards-ocg.csv`
   `git commit -m "chibi-update: <N new cards | price refresh> <date>"`
   `git push origin main`
   If nothing changed at all (no new cards AND no price movement), skip the commit.

8. **Report** to the user: which new cards were added (name, set, code, date), or
   "no new chibi cards found" with the sources checked. Remind them the Google Sheet
   refreshes IMPORTDATA within ~1 hour (or immediately if they delete and re-enter
   the formula in A1).
