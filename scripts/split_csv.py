"""Regenerate chibi-cards-tcg.csv and chibi-cards-ocg.csv from chibi-cards.csv.

Preserves row order (append-only master -> append-only splits) so the
Google Sheet checkbox columns stay aligned. Run from the project root.
"""
import csv
from pathlib import Path

root = Path(__file__).resolve().parent.parent
with open(root / "chibi-cards.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

header, body = rows[0], rows[1:]
game_idx = header.index("Game")

for game in ("TCG", "OCG"):
    out = root / f"chibi-cards-{game.lower()}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(r for r in body if r[game_idx] == game)
    print(out.name, sum(1 for r in body if r[game_idx] == game), "cards")
