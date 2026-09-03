"""Refresh the price columns in chibi-cards.csv from tcgcsv.com (TCGplayer market prices).

- TCG prints get per-rarity market prices, e.g. "Secret: $13.69 | Starlight: $166.21".
- OCG/promo prints have no TCGplayer listings and get "n/a".
- Only the two price columns are touched; row order never changes.

Run from the project root, then run scripts/split_csv.py and push the gist.
"""
import csv
import json
import urllib.request
from datetime import date
from pathlib import Path

CATEGORY = 2  # TCGplayer category: YuGiOh
SHORT_RARITY = {
    "Secret Rare": "Secret",
    "Starlight Rare": "Starlight",
    "Ultra Rare": "Ultra",
    "Prismatic Secret Rare": "Prismatic",
    "Quarter Century Secret Rare": "QCSR",
    "Common": "Common",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ChibiCollectionTracker/1.0"})
    return json.load(urllib.request.urlopen(req))

root = Path(__file__).resolve().parent.parent
with open(root / "chibi-cards.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
header, body = rows[0], rows[1:]

# ensure price columns exist
for col in ("Market Price (USD)", "Price Updated"):
    if col not in header:
        header.append(col)
        for r in body:
            r.append("")
n_cols = len(header)
for r in body:
    while len(r) < n_cols:
        r.append("")
i_set, i_code, i_game = header.index("Set"), header.index("Set Code"), header.index("Game")
i_price, i_updated = header.index("Market Price (USD)"), header.index("Price Updated")

# resolve TCGplayer group ids for the sets we need
wanted_sets = {r[i_set] for r in body if r[i_game] == "TCG"}
groups = {g["name"]: g["groupId"] for g in fetch(f"https://tcgcsv.com/tcgplayer/{CATEGORY}/groups")["results"]}
group_ids = {name: groups[name] for name in wanted_sets if name in groups}
missing = wanted_sets - set(group_ids)
if missing:
    print("WARNING: no TCGplayer group found for:", ", ".join(sorted(missing)))

# build set_code -> [(rarity, market_price)] from products + prices per group
by_code = {}
for name, gid in group_ids.items():
    products = fetch(f"https://tcgcsv.com/tcgplayer/{CATEGORY}/{gid}/products")["results"]
    price_rows = fetch(f"https://tcgcsv.com/tcgplayer/{CATEGORY}/{gid}/prices")["results"]
    prices = {}  # productId -> marketPrice, preferring 1st Edition
    for p in price_rows:
        pid, mp = p["productId"], p.get("marketPrice")
        if mp is None:
            continue
        if pid not in prices or p.get("subTypeName") == "1st Edition":
            prices[pid] = mp
    for p in products:
        ext = {e["name"]: e["value"] for e in p.get("extendedData", [])}
        code, rarity = ext.get("Number"), ext.get("Rarity")
        mp = prices.get(p["productId"])
        if code and mp is not None:
            by_code.setdefault(code, []).append((rarity or "?", mp))

today = date.today().isoformat()
priced = 0
for r in body:
    if r[i_game] != "TCG":
        r[i_price], r[i_updated] = "n/a", ""
        continue
    entries = by_code.get(r[i_code])
    if not entries:
        r[i_price], r[i_updated] = "", ""
        continue
    parts = [f"{SHORT_RARITY.get(rar, rar)}: ${mp:,.2f}" for rar, mp in sorted(entries, key=lambda e: e[1])]
    r[i_price], r[i_updated] = " | ".join(parts), today
    priced += 1

with open(root / "chibi-cards.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(header)
    w.writerows(body)
print(f"priced {priced} TCG prints; {sum(1 for r in body if r[i_game]=='TCG' and not r[i_price])} TCG prints had no listing")
