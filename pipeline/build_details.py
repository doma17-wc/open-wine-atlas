"""Merge every fact about a place into web/data/details-<cc>.json.

Sources merged, in order (later keys win only where earlier ones are empty):
  build/<src>_details.json   facts straight from the source register
  build/enrich.json          facts computed in enrich.py
  pipeline/notes/editorial.json  short editorial notes (CC BY 4.0)
"""
import json
import os
from collections import defaultdict

from common import BUILD, ROOT, norm

WEB = os.path.join(ROOT, "web", "data")
HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = {"appellation": 0, "region": 1, "subzone": 2, "vineyard": 3}


def build_details():
    merged = defaultdict(dict)
    for name in ["fr_details.json", "eu_details.json", "de_details.json", "ch_details.json", "us_details.json", "world_details.json"]:
        path = os.path.join(BUILD, name)
        if os.path.exists(path):
            for k, v in json.load(open(path, encoding="utf-8")).items():
                merged[k].update(v)
    enrich_path = os.path.join(BUILD, "enrich.json")
    if os.path.exists(enrich_path):
        for k, v in json.load(open(enrich_path, encoding="utf-8")).items():
            for kk, vv in v.items():
                if merged[k].get(kk) in (None, "", []):
                    merged[k][kk] = vv

    # editorial notes, matched by id or by country + name
    index = json.load(open(os.path.join(WEB, "search.json"), encoding="utf-8"))
    by_name = defaultdict(list)
    for r in index:
        by_name[(r[2], norm(r[0]))].append(r)
    notes = json.load(open(os.path.join(HERE, "notes", "editorial.json"), encoding="utf-8"))["notes"]
    missing = []
    for n in notes:
        pid = n.get("id")
        if not pid:
            cands = sorted(by_name.get((n["country"], norm(n["name"])), []), key=lambda r: ORDER.get(r[3], 9))
            pid = cands[0][1] if cands else None
        if pid and pid in merged:
            merged[pid]["atlas_note"] = n["note"]
        else:
            missing.append(n.get("name") or n.get("id"))
    print(f"  notes matched {len(notes) - len(missing)}/{len(notes)}; unmatched: {missing}")

    by_cc = defaultdict(dict)
    for k, v in merged.items():
        by_cc[k[:2]][k] = v
    for cc, d in by_cc.items():
        path = os.path.join(WEB, f"details-{cc}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  details-{cc}.json: {len(d)} places, {os.path.getsize(path) / 1e6:.1f} MB")


if __name__ == "__main__":
    build_details()
