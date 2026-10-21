"""Write web/data/game-wines.json: the wines of the "Where is it from?" game (web/study.js).

From the LWIN database (Liv-ex, CC BY 4.0) as placed by pipeline/lwin.py: wines whose record names an atlas
appellation, sub-region or vineyard, whose name does not already say where they come from, from producers with a
real range (so the names mean something to a student). A few per place, so famous places do not crowd the game.

  python3 pipeline/game_wines.py
"""
import collections
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web", "data")
PER_PLACE = 6
MIN_RANGE = 25  # producer has at least this many wines in the database: houses a student may know
LIMIT = 6000


def plain(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def main():
    idx = {r[1]: r for r in json.load(open(os.path.join(WEB, "search.json"), encoding="utf-8"))}
    prod = json.load(open(os.path.join(WEB, "producers.json"), encoding="utf-8"))
    wines = json.load(open(os.path.join(WEB, "wines.json"), encoding="utf-8"))["w"]
    places = prod["places"]
    by_place = collections.defaultdict(list)
    for name, pi, li, kind, lwin in wines:
        if li < 0 or kind not in ("r", "w", "p", "s", "f", "d"):
            continue
        pid = places[li]
        r = idx.get(pid)
        if not r or r[3] not in ("appellation", "subzone", "vineyard"):
            continue
        p = prod["p"][pi]
        if p[3] < MIN_RANGE:
            continue
        label = plain(p[0] + " " + name)
        # the answer must not be in the name: "Barolo Cannubi" says Barolo, "Chambertin Grand Cru" says Chambertin
        words = [w for w in plain(r[0]).split() if len(w) > 3 and w not in ("cote", "cotes", "vino", "vin", "wine", "valley", "grand", "premier", "village", "villages")]
        if plain(r[0]) in label or any(w in label.split() for w in words):
            continue
        if r[7] and any(plain(c) in label for c in r[7].split(", ") if len(c) > 3):
            continue
        by_place[pid].append((p[3], p[0], name, kind, lwin))
    out = []
    for pid, lst in by_place.items():
        lst.sort(key=lambda x: -x[0])
        seen = set()
        for n, producer, name, kind, lwin in lst:
            if producer in seen:
                continue
            seen.add(producer)
            out.append([producer, name, pid, kind, lwin, n])
            if len(seen) >= PER_PLACE:
                break
    out.sort(key=lambda x: -x[5])
    out = [x[:5] for x in out[:LIMIT]]
    doc = {"source": prod["source"], "about": "Wines for the Where is it from? game, chosen by pipeline/game_wines.py.",
           "w": out}
    json.dump(doc, open(os.path.join(WEB, "game-wines.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    cc = collections.Counter(idx[x[2]][2] for x in out)
    print(len(out), "wines,", len({x[2] for x in out}), "places,", dict(cc.most_common(12)))


if __name__ == "__main__":
    main()
