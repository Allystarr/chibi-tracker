# Yu-Gi-Oh! Chibi Card Collection Tracker

Tracks every printed chibi alternate-art card in the Yu-Gi-Oh! OCG/TCG
(Duel Arena-style chibi arts + the newer Limit Over Collection chibi waves).

## How it works

```
chibi-cards.csv  ──gh gist──►  GitHub gist (raw CSV URL)  ──IMPORTDATA──►  Google Sheet
        ▲
   /chibi-update skill appends new releases
```

- `chibi-cards.csv` — master list, one row **per print** (79 prints as of Sept 2026).
  Append-only: new cards go at the bottom so the sheet's checkboxes stay aligned.
- `chibi-cards-tcg.csv` / `chibi-cards-ocg.csv` — per-game feeds regenerated from the
  master by `scripts/split_csv.py`; the sheet has one tab per game, each importing
  its own file.
- `gist-info.txt` — gist ID (line 1) and raw URL (line 2). Created when the gist is
  first published.
- `.claude/skills/chibi-update/SKILL.md` — run `/chibi-update` in Claude Code to
  check Yugipedia + news for new chibi cards, append them, and push to the gist.
  The Google Sheet then refreshes on its own within ~1 hour.

## One-time Google Sheet setup (phone or desktop)

1. Create a new Google Sheet (sheets.new), name it e.g. **Chibi Collection**.
2. Make two tabs: **TCG** and **OCG**. In cell **A1** of each, paste the matching formula:
   - TCG tab: `=IMPORTDATA("https://gist.githubusercontent.com/Allystarr/b7363102526caf9e40122bbc4a7b5516/raw/chibi-cards-tcg.csv")`
   - OCG tab: `=IMPORTDATA("https://gist.githubusercontent.com/Allystarr/b7363102526caf9e40122bbc4a7b5516/raw/chibi-cards-ocg.csv")`
   Columns A–J fill with the card list automatically (I–J are TCGplayer market
   prices per rarity, refreshed by `/chibi-update` via `scripts/fetch_prices.py`;
   OCG promos show `n/a` — no TCGplayer market for them).
3. On each tab: in **L1** type `Owned`. Select L2 down a few hundred rows →
   Insert → Checkbox (or do this step once on desktop). Column K stays empty as a
   buffer in case the feed ever grows.
4. Optional stats in **N1** of each tab:
   `="Owned: " & COUNTIF(L2:L,TRUE) & " / " & (COUNTA(A2:A)-1)`
   Or a combined total on the TCG tab:
   `="Total: " & (COUNTIF(L2:L,TRUE)+COUNTIF(OCG!L2:L,TRUE)) & " / " & (COUNTA(A2:A)+COUNTA(OCG!A2:A)-2)`
5. **Don't sort the tabs** — column A–J order comes from the feed, and your
   checkboxes in column L align by row. Use a filter view if you want to filter/sort
   temporarily.

## Scope

Included: TCG sets (Battles of Legend: Monster Mayhem, Maze of Muertos,
Battles of Legend: Glorious Gallery, Magnificent Monsters, Legendary 5D's Decks
chibi tokens), OCG sets (Limit Over Collection: The Heroes / The Rivals),
Japanese 7-Eleven campaign promos (2023/2024/2025), Korean Hyundai Seoul
Pop-Up Special Pack B.

Excluded: Yu-Gi-Oh! Rush Duel chibi prints (separate game), video-game-only art,
merch (sleeves/badges/playmats). Ask Claude to add Rush Duel as a second list if
you ever want it.
