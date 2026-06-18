import json
countries = json.loads(open('data/partners/global/countries.json', encoding='utf-8').read())
print(f'Total: {len(countries)}')
for c in countries[:15]:
    print(f"  {c['name']:30} {c['slug']}")
print('...')
for c in countries[-5:]:
    print(f"  {c['name']:30} {c['slug']}")
