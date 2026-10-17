"""The reels posted on the atlas' social accounts, resolved to atlas places.

Reads  pipeline/lists/reels.json (names as the reels write them)
Writes web/data/reels.json       (atlas ids, display names, areas)

The map opens a reel at /#r:<slug>; web/build_pages.py writes the short link /r/<slug> and the page /reels.
A name must match exactly one place of the atlas (accents and case do not matter). When two places share a name,
"in" picks the one whose commune list or parent contains it. The script stops on any name it cannot pin down, so
a reel never links to the wrong vineyard.

    python3 pipeline/reels.py && python3 web/build_web.py
"""
import glob
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pipeline", "lists", "reels.json")
DATA = os.path.join(ROOT, "web", "data")
OUT = os.path.join(DATA, "reels.json")
KINDS = {"set", "vs", "place"}
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower().replace("ß", "ss")).strip()


def short_name(name, parent, cc):
    """Les Clos for Chablis Grand Cru Les Clos, as the map labels it (French climats only: Barossa Valley stays whole)."""
    if cc == "FR" and parent and name.startswith(parent + " ") and len(name) > len(parent) + 1:
        return re.sub(r"^(premier|grand) cru ", "", name[len(parent) + 1:])
    return name


def main():
    rows = json.load(open(os.path.join(DATA, "search.json"), encoding="utf-8"))
    by_name = {}
    for r in rows:
        by_name.setdefault(norm(r[0]), []).append(r)
    details = {}
    for f in glob.glob(os.path.join(DATA, "details-*.json")):
        details.update(json.load(open(f, encoding="utf-8")))

    by_id = {r[1]: r for r in rows}

    def resolve(item, where):
        spec = {"name": item} if isinstance(item, str) else dict(item)
        if spec.get("id"):
            # an explicit atlas id wins (the name is kept for whoever reads the list)
            if spec["id"] not in by_id:
                sys.exit(f"{where}: unknown atlas id {spec['id']}")
            return by_id[spec["id"]], spec.get("label")
        cands = by_name.get(norm(spec["name"]), [])
        if spec.get("in"):
            w = norm(spec["in"])
            cands = [r for r in cands if w in norm(r[7] or "") or w in norm(r[5] or "")]
        if len(cands) > 1:
            # one name, several levels (Napa Valley the AVA and a district of the same name): the larger unit wins
            order = {"region": 0, "appellation": 1, "subzone": 2, "vineyard": 3}
            best = min(order.get(r[3], 9) for r in cands)
            top = [r for r in cands if order.get(r[3], 9) == best]
            if len(top) == 1:
                cands = top
        if len(cands) != 1:
            found = ", ".join(f"{r[0]} ({r[1]}, {r[7][:40] or r[5]})" for r in cands[:8]) or "nothing"
            sys.exit(f"{where}: '{spec['name']}' matches {found}. Add \"in\" or write the name as the atlas does.")
        return cands[0], spec.get("label")

    src = json.load(open(SRC, encoding="utf-8"))["reels"]
    seen, out = set(), []
    for reel in src:
        slug, kind = reel["slug"], reel["kind"]
        where = f"reel {slug}"
        if not SLUG.match(slug):
            sys.exit(f"{where}: the slug must be lower case words joined by hyphens")
        if slug in seen:
            sys.exit(f"{where}: the slug is used twice")
        seen.add(slug)
        if kind not in KINDS:
            sys.exit(f"{where}: kind must be one of {sorted(KINDS)}")
        n = len(reel["places"])
        if (kind == "vs" and n != 2) or (kind == "place" and n != 1) or (kind == "set" and n < 2):
            sys.exit(f"{where}: a {kind} reel cannot have {n} places")
        places = []
        for item in reel["places"]:
            r, label = resolve(item, where)
            d = details.get(r[1], {})
            p = {"id": r[1], "name": label or short_name(r[0], r[5], r[2]), "cc": r[2]}
            # a delimited area is a vineyard figure; an outline made of whole communes is not, so it is kept apart
            if d.get("area_ha") is not None:
                p["ha"] = d["area_ha"]
            elif d.get("outline_area_ha") is not None:
                p["outline_ha"] = d["outline_area_ha"]
            places.append(p)
        # the publication time with its offset, so the page can show a reel from that moment on wherever it is read
        at = datetime.fromisoformat(reel["at"]).replace(tzinfo=ZoneInfo("Europe/Zurich")).isoformat(timespec="minutes")
        out.append({"slug": slug, "at": at, "kind": kind, "title": reel["title"], "places": places})
    out.sort(key=lambda x: x["at"], reverse=True)
    json.dump({"reels": out}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} reels, {sum(len(x['places']) for x in out)} places -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
