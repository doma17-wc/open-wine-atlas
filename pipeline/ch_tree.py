"""Hang the Swiss wine areas and communal appellations (ch_regions.py) under their cantonal AOC in tree.json.

Patches only the Switzerland branch of web/data/tree.json, so it needs none of the raw files that build_tree.py
reads for other countries. Run after ch_regions.py.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web", "data")


def main():
    tree = json.load(open(os.path.join(WEB, "tree.json"), encoding="utf-8"))
    rows = json.load(open(os.path.join(WEB, "search.json"), encoding="utf-8"))
    nodes = tree["nodes"]
    spec = json.load(open(os.path.join(ROOT, "pipeline", "lists", "ch_regions.json"), encoding="utf-8"))
    spec_order = {pl["id"]: i for i, pl in enumerate(spec["places"])}
    ch = [r for r in rows if r[2] == "CH"]
    by_name = {r[0]: r[1] for r in ch}

    # drop earlier regional nodes and children, keep the groups and cantons
    for k in [k for k in nodes if k.startswith("ch-")]:
        del nodes[k]
    kids = {}
    for r in ch:
        if not r[1].startswith("ch-reg-"):
            continue
        pid = by_name.get(r[5])
        assert pid, f"parent not found for {r[0]}: {r[5]}"
        kids.setdefault(pid, []).append(r[1])
    # cantons added by ch_regions.py (Bern, Fribourg...) join their wine region group
    for cid, nc in spec.get("new_cantons", {}).items():
        g = "g:CH/" + nc["region"].lower().replace(" ", "-")
        assert g in nodes, f"no group {g} for {cid}"
        nodes[g][3] = [k for k in nodes[g][3] if k != cid] + [cid]
    rank = {r[1]: r[4] for r in ch}
    for pid, ks in kids.items():
        # grands crus first, then the order of pipeline/lists/ch_regions.json (wider places, then communes)
        ks.sort(key=lambda k: (rank[k] != "grand_cru", spec_order.get(k, 999)))
        nodes[pid] = [None, "place", None, ks, 0]

    def total(k):
        n = nodes.get(k)
        if not n:
            return 0
        s = 0
        for c in n[3]:
            s += (total(c) if c.startswith("g:") else 1 + total(c))
        n[4] = s
        return s
    # the outline box of each Swiss wine region group follows its places (new cantons widen it)
    box = {r[1]: r[6] for r in ch}
    for g in nodes["g:CH"][3]:
        bs = [box[k] for k in nodes[g][3] if k in box]
        if bs:
            nodes[g][2] = [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]
    total("g:CH")
    json.dump(tree, open(os.path.join(WEB, "tree.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"  tree.json: Switzerland {nodes['g:CH'][4]} places")


if __name__ == "__main__":
    main()
