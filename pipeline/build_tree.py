"""Explorer tree: country > region > sub-region > appellation > cru, for the sidebar of the map.

Reads the published web/data (search.json and details-<cc>.json), so it runs after build_details.py or
build_world_web.py, and writes web/data/tree.json.

Where the hierarchy comes from:
  France      pipeline/lists/fr_regions.json (wine regions and sub-regions, editorial), Burgundy grands crus
              attached to their village by commune, premier cru climats under "<village> premier cru"
  Germany     Anbaugebiet > Bereich > Großlage > Einzellage (LWK Rheinland-Pfalz attributes)
  USA         state > AVA > nested AVAs (UC Davis AVA project: states, "within")
  Australia   state > zone > region > subregion (Wine Australia)
  Italy, Spain, Austria, Greece
              administrative region of the place centre (geoBoundaries, raw/geoboundaries/*-ADM*.geojson,
              downloaded by this script when missing). Without those files the country stays flat.
  everywhere  the "parent" of each place; a parent that is not a mapped place becomes a group

tree.json
  {"version": 1,
   "roots": [[continent, [country keys]]],
   "nodes": {key: [name, kind, bbox, [child keys], place count]}}
Keys are place ids for places and "g:..." for groups. A child key that is not in "nodes" is a place
without children: its name and outline box are in search.json. Group kinds: country, region, subregion,
state, group. A place can sit under two parents (Bonnes-Mares is in Chambolle-Musigny and in
Morey-Saint-Denis); the first one in tree order is its home for breadcrumbs.
"""
import json
import os
import re
import sys
import unicodedata
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web", "data")
RAW = os.path.join(ROOT, "raw", "geoboundaries")
LISTS = os.path.join(ROOT, "pipeline", "lists")

GB = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/{iso}/{adm}/geoBoundaries-{iso}-{adm}_simplified.geojson"
ADMIN = {"IT": ("ITA", "ADM2"), "ES": ("ESP", "ADM1"), "AT": ("AUT", "ADM1"), "GR": ("GRC", "ADM2")}
ADMIN_NAMES = {
    "País Vasco/Euskadi": "País Vasco", "Cataluña/Catalunya": "Catalunya", "Comunidad Foral de Navarra": "Navarra",
    "Región de Murcia": "Murcia", "Comunidad de Madrid": "Madrid", "Principado de Asturias": "Asturias",
    "Anatolikis Makedonias kai Thr*": "Eastern Macedonia and Thrace", "Kentrikis Makedonias": "Central Macedonia",
    "Dytikis Makedonias": "Western Macedonia", "Ipeiroy": "Epirus", "Thessalias": "Thessaly", "Stereas Elladas": "Central Greece",
    "Ionion Nison": "Ionian Islands", "Dytikis Elladas": "Western Greece", "Peloponnisoy": "Peloponnese", "Attikis": "Attica",
    "Voreioy Aigaioy": "North Aegean", "Notioy Aigaioy": "South Aegean", "Kritis": "Crete", "Agion Oros": "Mount Athos",
}
COUNTRY_EN = {
    "FR": "France", "IT": "Italy", "ES": "Spain", "DE": "Germany", "CH": "Switzerland", "AT": "Austria", "PT": "Portugal",
    "GR": "Greece", "HU": "Hungary", "RO": "Romania", "BG": "Bulgaria", "HR": "Croatia", "SI": "Slovenia", "CZ": "Czechia",
    "SK": "Slovakia", "BE": "Belgium", "CY": "Cyprus", "NL": "Netherlands", "GB": "United Kingdom", "MT": "Malta",
    "DK": "Denmark", "LU": "Luxembourg", "US": "United States", "AU": "Australia", "NZ": "New Zealand", "ZA": "South Africa",
    "CL": "Chile", "AR": "Argentina", "BR": "Brazil", "UY": "Uruguay", "CA": "Canada", "MX": "Mexico", "GE": "Georgia",
    "MD": "Moldova", "UA": "Ukraine", "AM": "Armenia", "TR": "Türkiye", "IL": "Israel", "LB": "Lebanon", "RS": "Serbia",
    "MK": "North Macedonia", "ME": "Montenegro", "BA": "Bosnia and Herzegovina", "JP": "Japan", "CN": "China", "IN": "India",
}
CONTINENTS = [
    ("Europe", ["FR", "IT", "ES", "DE", "PT", "AT", "CH", "GR", "HU", "RO", "BG", "HR", "SI", "CZ", "SK", "GE", "MD", "UA", "AM",
                "RS", "MK", "ME", "BA", "CY", "MT", "BE", "NL", "LU", "DK", "GB", "TR"]),
    ("Americas", ["US", "CA", "MX", "AR", "CL", "BR", "UY"]),
    ("Africa and Middle East", ["ZA", "IL", "LB"]),
    ("Asia and Oceania", ["AU", "NZ", "JP", "CN", "IN"]),
]
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
    "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}
TOP = {"grand_cru", "docg", "doca", "pago"}
LEVEL_ORDER = {"region": 0, "appellation": 1, "subzone": 2, "vineyard": 3, "vineyard_area": 4}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def slug(s):
    return norm(s).replace(" ", "-") or "x"


class Tree:
    def __init__(self, rows):
        self.rows = {r[1]: r for r in rows}
        self.nodes = {}   # key -> {"name", "kind", "kids": []}

    def group(self, key, name, kind):
        if key not in self.nodes:
            self.nodes[key] = {"name": name, "kind": kind, "kids": []}
        return key

    def link(self, parent, child):
        """Add child under parent once. Places get a node entry when they receive children."""
        if parent in self.rows and parent not in self.nodes:
            self.nodes[parent] = {"name": None, "kind": "place", "kids": []}
        kids = self.nodes[parent]["kids"]
        if child not in kids and child != parent:
            kids.append(child)


def rank_key(r):
    rk = 0 if r[4] in TOP else 1 if r[4] == "premier_cru" else 2
    return (rk, LEVEL_ORDER.get(r[3], 9), norm(r[0]))


def admin_lookup(cc):
    """Return f(lon, lat) -> admin region name, or None when the boundaries are not available."""
    if cc not in ADMIN:
        return None
    try:
        from shapely.geometry import shape, Point
        from shapely.strtree import STRtree
    except ImportError:
        print("  shapely missing, " + cc + " stays flat", file=sys.stderr)
        return None
    iso, adm = ADMIN[cc]
    path = os.path.join(RAW, f"{iso}-{adm}.geojson")
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        try:
            print("  downloading", iso, adm)
            urllib.request.urlretrieve(GB.format(iso=iso, adm=adm), path)
        except Exception as e:  # offline: keep the country flat
            print("  could not download", iso, adm, e, file=sys.stderr)
            return None
    feats = json.load(open(path, encoding="utf-8"))["features"]
    geoms = [shape(f["geometry"]) for f in feats]
    names = [ADMIN_NAMES.get(f["properties"]["shapeName"], f["properties"]["shapeName"]) for f in feats]
    tree = STRtree(geoms)

    def find(lon, lat):
        pt = Point(lon, lat)
        hits = [i for i in tree.query(pt) if geoms[i].contains(pt)]
        if hits:
            return names[hits[0]]
        i = tree.nearest(pt)  # a centre just off the coast or across a border
        return names[i] if i is not None and geoms[i].distance(pt) < 0.3 else None
    return find


def centre(r, d):
    if d.get("lat") is not None and d.get("lon") is not None:
        return d["lon"], d["lat"]
    b = r[6]
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2


def build():
    rows = json.load(open(os.path.join(WEB, "search.json"), encoding="utf-8"))
    by_cc = {}
    for r in rows:
        by_cc.setdefault(r[2], []).append(r)
    T = Tree(rows)
    details = {}

    def det(cc):
        if cc not in details:
            p = os.path.join(WEB, "details-" + cc.lower() + ".json")
            details[cc] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        return details[cc]

    for cc, crow in by_cc.items():
        ck = T.group("g:" + cc, COUNTRY_EN.get(cc, cc), "country")
        D = det(cc)
        names = {}
        for r in sorted(crow, key=lambda r: LEVEL_ORDER.get(r[3], 9)):
            names.setdefault(norm(r[0]), r)  # the highest level wins a shared name
        placed = set()

        def parent_of(r):
            if not r[5]:
                return None
            p = names.get(norm(r[5]))
            if p is None:  # "La Rioja" is mapped as "La Rioja Argentina", "Córdoba" as "Córdoba Argentina"
                p = names.get(norm(r[5] + " " + COUNTRY_EN.get(cc, "")))
            return p[1] if p and p[1] != r[1] else None

        if cc == "FR":
            spec = json.load(open(os.path.join(LISTS, "fr_regions.json"), encoding="utf-8"))
            apps = {norm(r[0]): r for r in crow if r[3] == "appellation"}
            village_of = {norm(k): v for k, v in spec["grand_cru_village"].items()}
            listed = set()
            for reg in spec["regions"]:
                rk = T.group("g:FR/" + slug(reg["name"]), reg["name"], "region")
                T.link(ck, rk)
                for sub in reg["subregions"]:
                    if sub["name"]:
                        sk = T.group(rk + "/" + slug(sub["name"]), sub["name"], "subregion")
                        T.link(rk, sk)
                    else:
                        sk = rk
                    if "match" in sub:
                        hits = sorted((r for r in crow if r[3] == "appellation" and re.match(sub["match"], r[0])), key=lambda r: norm(r[0]))
                    else:
                        hits = []
                        for a in sub["aocs"]:
                            r = apps.get(norm(a))
                            if r is None:
                                print("  FR list: no AOC", a, file=sys.stderr)
                                continue
                            hits.append(r)
                    for r in hits:
                        T.link(sk, r[1])
                        listed.add(r[1])
            # Burgundy grands crus under their villages, by commune
            for r in crow:
                if r[3] != "appellation" or r[4] != "grand_cru" or r[1] in listed:
                    continue
                for com in D.get(r[1], {}).get("communes", []):
                    v = village_of.get(norm(com), com)
                    va = apps.get(norm(v))
                    if va and va[1] != r[1]:
                        T.link(va[1], r[1])
                        listed.add(r[1])
            missing = [r[0] for r in crow if r[3] == "appellation" and r[1] not in listed]
            if missing:
                print("  FR appellations without a region:", missing, file=sys.stderr)
                ok = T.group("g:FR/other", "Other appellations", "region")
                T.link(ck, ok)
                for r in sorted((r for r in crow if r[3] == "appellation" and r[1] not in listed), key=rank_key):
                    T.link(ok, r[1])
                    listed.add(r[1])
            placed |= listed
            # dénominations: premier cru climats under "<village> premier cru" when it exists
            for r in sorted(crow, key=rank_key):
                if r[3] == "appellation":
                    continue
                p = parent_of(r)
                if not p:
                    continue
                if r[3] == "vineyard" and r[4] == "premier_cru":
                    pc = names.get(norm(r[5] + " premier cru"))
                    if pc and pc[3] == "subzone":
                        p = pc[1]
                T.link(p, r[1])
                placed.add(r[1])

        elif cc == "DE":
            regions = {norm(r[0]): r for r in crow if r[3] == "region"}
            gross = {}
            for r in crow:
                if r[3] == "subzone":
                    gross[(norm(r[5]), norm(r[0]))] = r
            for r in sorted(regions.values(), key=lambda r: norm(r[0])):
                T.link(ck, r[1])
                placed.add(r[1])
            for r in sorted(crow, key=rank_key):
                if r[3] == "region":
                    continue
                d = D.get(r[1], {})
                reg = regions.get(norm(d.get("region") or r[5]))
                if not reg:
                    T.link(ck, r[1]); placed.add(r[1]); continue
                bereich = (d.get("bereich") or "").replace("Bereich ", "").strip()
                parent = reg[1]
                if bereich:
                    parent = T.group("g:DE/" + reg[1] + "/" + slug(bereich), "Bereich " + bereich, "subregion")
                    T.link(reg[1], parent)
                if r[3] == "vineyard" and d.get("grosslage"):
                    g = gross.get((norm(reg[0]), norm(d["grosslage"])))
                    if g:
                        T.link(parent, g[1])
                        parent = g[1]
                if r[3] == "subzone" and r[0].strip("- ") == "":
                    T.nodes.setdefault(r[1], {"name": "Großlagenfrei", "kind": "place", "kids": []})["name"] = "Großlagenfrei"
                T.link(parent, r[1])
                placed.add(r[1])

        elif cc == "US":
            for r in sorted(crow, key=rank_key):
                p = parent_of(r)
                if p:
                    T.link(p, r[1])
                else:
                    for st in D.get(r[1], {}).get("states") or ["??"]:
                        sk = T.group("g:US/" + st, US_STATES.get(st, st), "state")
                        T.link(ck, sk)
                        T.link(sk, r[1])
                placed.add(r[1])

        elif cc == "AU":
            for r in sorted(crow, key=rank_key):
                p = parent_of(r)
                if p:
                    T.link(p, r[1])
                elif r[7]:
                    sk = T.group("g:AU/" + slug(r[7]), r[7], "state")
                    T.link(ck, sk)
                    T.link(sk, r[1])
                else:  # Tasmania: a state-wide GI
                    T.link(ck, r[1])
                placed.add(r[1])

        else:
            find = admin_lookup(cc)
            for r in sorted(crow, key=rank_key):
                p = parent_of(r)
                if p:
                    T.link(p, r[1])
                elif r[5]:  # a parent that is not a mapped place: a group (Swiss wine regions, Argentine provinces)
                    gk = T.group("g:" + cc + "/" + slug(r[5]), r[5], "region")
                    T.link(ck, gk)
                    T.link(gk, r[1])
                elif find:
                    reg = find(*centre(r, D.get(r[1], {}))) or "Other"
                    gk = T.group("g:" + cc + "/" + slug(reg), reg, "region")
                    T.link(ck, gk)
                    T.link(gk, r[1])
                else:
                    T.link(ck, r[1])
                placed.add(r[1])

        # anything not reached hangs from the country, never lost
        for r in sorted(crow, key=rank_key):
            if r[1] not in placed:
                T.link(ck, r[1])

    # order: groups as built (curated order for France, alphabetical elsewhere), places by rank then name
    def sort_kids(key):
        n = T.nodes[key]
        if n["kind"] in ("country",) and not key.startswith("g:FR"):
            groups = sorted([k for k in n["kids"] if k in T.nodes and T.nodes[k]["kind"] != "place"], key=lambda k: norm(T.nodes[k]["name"]))
            places = sorted([k for k in n["kids"] if k not in groups], key=lambda k: rank_key(T.rows[k]))
            n["kids"] = groups + places
        elif n["kind"] in ("state", "region", "subregion") and not key.startswith("g:FR"):
            groups = [k for k in n["kids"] if k in T.nodes and T.nodes[k]["kind"] != "place"]
            groups.sort(key=lambda k: norm(T.nodes[k]["name"]))
            places = sorted([k for k in n["kids"] if k not in groups], key=lambda k: rank_key(T.rows[k]))
            n["kids"] = groups + places
        elif n["kind"] == "place":
            groups = [k for k in n["kids"] if k not in T.rows]
            places = sorted([k for k in n["kids"] if k in T.rows], key=lambda k: rank_key(T.rows[k]))
            n["kids"] = sorted(groups, key=lambda k: norm(T.nodes[k]["name"])) + places
    for k in list(T.nodes):
        sort_kids(k)

    # boxes and counts, without looping on a place listed twice
    memo = {}

    def walk(key, stack=()):
        if key in memo:
            return memo[key]
        if key in stack:
            return set(), None
        ids, box = set(), None
        if key in T.rows:
            ids.add(key)
            box = list(T.rows[key][6])
        for k in T.nodes.get(key, {}).get("kids", []):
            kid_ids, kb = walk(k, stack + (key,))
            ids |= kid_ids
            if kb and key not in T.rows:
                box = kb[:] if box is None else [min(box[0], kb[0]), min(box[1], kb[1]), max(box[2], kb[2]), max(box[3], kb[3])]
        memo[key] = (ids, box)
        return memo[key]

    out_nodes = {}
    for k, n in T.nodes.items():
        ids, box = walk(k)
        out_nodes[k] = [n["name"], n["kind"], [round(v, 4) for v in box] if (box and k not in T.rows) else None, n["kids"],
                        len(ids) - (1 if k in T.rows else 0)]
    roots = []
    seen = set()
    for cont, ccs in CONTINENTS:
        keys = ["g:" + c for c in ccs if "g:" + c in T.nodes]
        seen.update(keys)
        if keys:
            roots.append([cont, keys])
    rest = sorted(k for k in T.nodes if k.startswith("g:") and k.count("/") == 0 and k not in seen)
    if rest:
        roots.append(["More", rest])
    # each continent: countries with most places first
    for r in roots:
        r[1].sort(key=lambda k: -out_nodes[k][4])

    reached = set()

    def mark(key):
        if key in reached:
            return
        reached.add(key)
        for k in T.nodes.get(key, {}).get("kids", []):
            mark(k)
    for _, keys in roots:
        for k in keys:
            mark(k)
    lost = [r[1] for r in rows if r[1] not in reached]
    print("tree:", len(out_nodes), "nodes,", len(rows) - len(lost), "of", len(rows), "places reached")
    if lost:
        print("  not reached:", lost[:20], file=sys.stderr)

    path = os.path.join(WEB, "tree.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "roots": roots, "nodes": out_nodes}, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    build()
