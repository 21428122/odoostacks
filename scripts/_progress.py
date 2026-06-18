import csv, json
from collections import Counter
from pathlib import Path

BASE = Path("data/partners/global")

# Phase 2 progress
partners_file = BASE / "partners_raw.csv"
state_file    = BASE / "state.json"
refs_file     = BASE / "references_raw.csv"
enriched_file = BASE / "partners_enriched.csv"

if partners_file.exists():
    with open(partners_file, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
else:
    rows = []

state = json.loads(state_file.read_text()) if state_file.exists() else {}
n_countries = 167

done_countries  = len(state.get("crawled_country_slugs", []))
done_partner_ids = len(state.get("crawled_partner_ids", []))
partners_done    = state.get("partners_done", False)

print(f"Partners:       {len(rows):,} rows")
print(f"Countries done: {done_countries}/{n_countries}  {'[PHASE 2 COMPLETE]' if partners_done else '(crawling...)'}")
print(f"Partners done:  {done_partner_ids}  {'(Phase 3 running)' if done_partner_ids > 0 else ''}")
if enriched_file.exists():
    with open(enriched_file, encoding="utf-8") as f:
        n_enriched = sum(1 for _ in csv.DictReader(f))
    print(f"Enriched:       {n_enriched:,} rows")
if refs_file.exists():
    with open(refs_file, encoding="utf-8") as f:
        n_refs = sum(1 for _ in csv.DictReader(f))
    print(f"References:     {n_refs:,} rows")
print()

# Grade distribution
if rows:
    grades = Counter(r['grade'] for r in rows)
    print("Grade breakdown:")
    for g in ("Gold", "Silver", "Ready", "Unknown"):
        n = grades.get(g, 0)
        bar = "#" * (n // 50)
        print(f"  {g:<8} {n:>5,}  {bar}")
    print()

print("Top 10 countries by partner count:")
top = Counter(r['country'] for r in rows).most_common(10)
for c, n in top:
    print(f"  {c:<30} {n}")
