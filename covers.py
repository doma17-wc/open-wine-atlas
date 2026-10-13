"""Resolve cover items (names -> atlas ids + bbox). usage: covers.py items.json list.json"""
import json, sys, unicodedata, re
S = json.load(open('/home/claude/open-wine-atlas/web/data/search.json'))
def norm(x): return unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower().replace('-', ' ').replace("'", ' ').strip()
IDX = {}
for r in S: IDX.setdefault(norm(r[0]), []).append(r)
def find(name, cc=None):
    c = IDX.get(norm(name), [])
    if c: return c[0]
    n = norm(re.sub(r'\s*\(.*\)', '', name))
    c = IDX.get(n, [])
    h = re.search(r'\((.*)\)', name)
    if h: c = [r for r in c if norm(h.group(1)) in norm(r[7] or '')] or c
    if cc: c = [r for r in c if r[2] == cc] or c
    if not c: return None
    if len(c) > 1:  # prefer appellation/vineyard over region
        c.sort(key=lambda r: {'vineyard': 0, 'appellation': 1}.get(r[3], 2))
    return c[0]
CCN = {'FR':'France','IT':'Italy','DE':'Germany','ES':'Spain','US':'California · United States','AU':'Australia','NZ':'New Zealand','ZA':'South Africa','CL':'Chile','AR':'Argentina','CH':'Switzerland','PT':'Portugal','AT':'Austria'}
items = json.load(open(sys.argv[1])); out = []
for it in items:
    rs = [find(n, it.get('cc')) for n in it['places']]
    miss = [n for n, r in zip(it['places'], rs) if r is None]
    if miss: print('MISSING', it['key'], miss)
    rs = [r for r in rs if r]
    if not rs: continue
    if not it.get('kicker'): it['kicker'] = CCN.get(rs[0][2], rs[0][2])
    bb = [min(r[6][0] for r in rs), min(r[6][1] for r in rs), max(r[6][2] for r in rs), max(r[6][3] for r in rs)]
    out.append({**it, 'ids': [r[1] for r in rs], 'bbox': bb})
    print(it['key'], [r[1] for r in rs])
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
