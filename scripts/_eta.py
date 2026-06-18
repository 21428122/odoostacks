import csv, json
from datetime import datetime, timedelta

state = json.loads(open('data/partners/global/state.json').read())
done  = len(state.get('crawled_partner_ids', []))
total = 11850

rows = list(csv.DictReader(open('data/partners/global/partners_enriched.csv', encoding='utf-8')))
refs = list(csv.DictReader(open('data/partners/global/references_raw.csv', encoding='utf-8')))

t_start  = datetime.fromisoformat(rows[0]['crawled_at'])
t_now    = datetime.now()
elapsed  = (t_now - t_start).total_seconds()
rate     = done / elapsed          # partners per second (true average)
remaining = total - done
eta_sec  = remaining / rate
finish   = t_now + timedelta(seconds=eta_sec)

print(f"Started:   {t_start.strftime('%H:%M:%S')}")
print(f"Now:       {t_now.strftime('%H:%M:%S')}")
print(f"Elapsed:   {elapsed/60:.0f} min")
print(f"Done:      {done}/{total}  ({done/total*100:.1f}%)")
print(f"Refs:      {len(refs):,}")
print(f"Rate:      {rate*60:.1f} partners/min")
print(f"ETA:       {eta_sec/60:.0f} min")
print(f"Finishes:  {finish.strftime('%H:%M:%S')}")
