"""Producers and wines from the LWIN database (Liv-ex Wine Identification Number), placed on the atlas.

Source: the LWIN database, free to download from https://www.liv-ex.com/lwin-database-download/ and published by
Liv-ex under Creative Commons Attribution 4.0 (CC BY 4.0). Put the downloaded file (.xlsx or .csv) in raw/lwin/.

Every live wine of the database is matched to the most precise atlas place its LWIN record names: the site first
(Clos de Vougeot, Cannubi), then the sub-region (Pauillac, Barolo), then the region (Champagne, Mosel). A name is
matched in the wine's own country only, against the places of web/data/search.json and the regions of
web/data/tree.json, with English names translated by pipeline/lists/lwin_aliases.json (Burgundy: Bourgogne).
A wine that matches nothing keeps its country only.

Writes two files to web/data (both carry "source", "date" and "file"):
  producers.json  {"places": [place id or explorer region key, ...],
                   "p": [[producer, country, [[place index, wines there], ...], wines], ...]}
                  small: the search, and the producers listed on a place sheet
  wines.json      {"w": [[wine, producer index, place index or -1, kind, LWIN-7], ...]}
                  loaded when a producer is opened or a search looks for a wine name
kind: r red, w white, p rosé, s sparkling, f fortified, d sweet, "" other. Reads the published web/data, so it runs
after build_tree.py. build/lwin_unplaced.tsv lists the regions it could not place, for pipeline/lists/lwin_aliases.json.

  python3 pipeline/lwin.py [path to the LWIN file]
"""
import collections
import csv
import datetime
import glob
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web", "data")
RAW = os.path.join(ROOT, "raw", "lwin")
LISTS = os.path.join(ROOT, "pipeline", "lists")

SOURCE = {"name": "LWIN, the Liv-ex Wine Identification Number", "licence": "CC BY 4.0",
          "licence_url": "https://creativecommons.org/licenses/by/4.0/", "attribution": "LWIN by Liv-ex",
          "url": "https://www.liv-ex.com/lwin/",
          "changes": "Wine names kept as published; each wine placed on an atlas appellation or region by its region, "
                     "sub-region and site; spirits, beer and retired codes left out."}
WINE_TYPES = {"wine", "fortified wine", "fortified", "sparkling wine", "sparkling", "still"}
NOT_A_WINE = re.compile(r"assortment|mixed case|presentation box|gift (box|set)|\bcase\b|tasting set|collection box", re.I)
LEVEL_PREF = {"appellation": 0, "region": 1, "subzone": 2, "vineyard": 3}


def norm(s):
    """Lowercase key without accents. Greek, Cyrillic and Georgian letters are kept, so that an alias can name a place
    written in its own script (Σαντορίνη)."""
    s = unicodedata.normalize("NFKD", str(s or "").replace("ß", "ss").replace("’", "'")).lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^\w]+|_", " ", s).strip()


def clean(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "null", "n/a", "na", "-") else s


def read_rows(path):
    """Rows as dicts with upper-case keys, from the .xlsx or .csv the Liv-ex site gives out."""
    if path.lower().endswith((".xlsx", ".xlsm", ".xls")):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        head = None
        for row in it:
            cells = [clean(c).upper() for c in row]
            if "LWIN" in cells or "LWIN7" in cells:
                head = cells
                break
        if head is None:
            sys.exit(f"no LWIN header row in {path}")
        for row in it:
            yield {h: clean(c) for h, c in zip(head, row) if h}
        return
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    lines = text.splitlines()
    k = next(i for i, l in enumerate(lines) if re.search(r"(^|[,;\t])\"?LWIN7?\"?([,;\t]|$)", l, re.I))
    dialect = csv.Sniffer().sniff(lines[k])
    rd = csv.reader(lines[k:], dialect)
    head = [clean(h).upper() for h in next(rd)]
    for row in rd:
        yield {h: clean(c) for h, c in zip(head, row) if h}


def kind_of(r):
    col, typ, sub = norm(r.get("COLOUR")), norm(r.get("TYPE")), norm(r.get("SUB_TYPE"))
    if "fortified" in typ or "fortified" in sub or sub in ("port", "sherry", "madeira"):
        return "f"
    if "sparkling" in typ or "sparkling" in sub or "champagne" in sub:
        return "s"
    if "sweet" in sub or "dessert" in sub:
        return "d"
    return {"red": "r", "white": "w", "rose": "p"}.get(col, "")


def country_codes():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build_tree import COUNTRY_EN
    cc = {norm(v): k for k, v in COUNTRY_EN.items()}
    cc.update({norm(k): v for k, v in json.load(open(os.path.join(LISTS, "lwin_aliases.json"), encoding="utf-8"))["countries"].items()})
    return cc


PREFIX = ("aoc ", "aop ", "doc ", "docg ", "do ", "doca ", "ava ", "bereich ", "grosslage ")
CRU = re.compile(r"\b(premier cru|1er cru|grand cru|grande? reserve)\b")


class Places:
    """Atlas places and explorer regions by country and normalised name.

    by    (cc, name)            -> [(preference, key)]   every place and region
    sites (cc, parent, short)   -> key                   a climat inside its village (Vosne-Romanée › Les Suchots),
                                                          an Einzellage inside its village (Wehlen › Sonnenuhr)
    """

    def __init__(self):
        self.by = collections.defaultdict(list)
        self.sites = {}
        for r in json.load(open(os.path.join(WEB, "search.json"), encoding="utf-8")):
            name, pid, cc, level, parent, alt = r[0], r[1], r[2], r[3], r[5], r[7]
            for key in self.keys(name):
                self.by[(cc, key)].append((LEVEL_PREF.get(level, 4), pid))
            if level == "vineyard":
                for full in self.keys(name):
                    p = norm(parent)
                    short = full[len(p) + 1:] if p and full.startswith(p + " ") else full
                    short = CRU.sub(" ", short).strip()
                    for par in [parent] + [a for a in (alt or "").split(", ") if a]:
                        self.sites.setdefault((cc, norm(par), short), pid)
        tree = json.load(open(os.path.join(WEB, "tree.json"), encoding="utf-8"))["nodes"]
        for k, v in tree.items():
            if not k.startswith("g:") or v[1] == "country":
                continue
            for key in self.keys(v[0]):
                self.by[(k[2:4], key)].append((5, k))
        for lst in self.by.values():
            lst.sort()
        al = json.load(open(os.path.join(LISTS, "lwin_aliases.json"), encoding="utf-8"))["places"]
        self.alias = {(cc, norm(k)): [norm(x) for x in (v if isinstance(v, list) else [v])]
                      for cc, d in al.items() for k, v in d.items()}

    @staticmethod
    def keys(name):
        """Every form a place can be looked up by: the name, each alternative of "A ou B" or "A / B" (INAO writes
        "Les Feusselottes ou Les Feusselotes"), and the name without a leading AOC, DOC or Bereich."""
        forms = [name] + [x for x in re.split(r" ou | / ", name) if x != name]
        head = re.split(r" ou | / ", name)[0]
        # "Chambolle-Musigny premier cru Les Feusselottes ou Les Feusselotes": the second form leaves out the village
        lead = re.match(r"^(.* (?:premier|grand) cru) ", head, re.I)
        if lead:
            forms += [lead.group(1) + " " + x for x in re.split(r" ou | / ", name)[1:]]
        out = set()
        for f in forms:
            k = norm(f)
            out.add(k)
            for pre in PREFIX:
                if k.startswith(pre):
                    out.add(k[len(pre):])
        return out

    def find(self, cc, name, region=False, unique=False):
        """The place of that name in that country. A region name prefers the explorer region (Bourgogne the
        region, not the regional AOC); a site name must be unambiguous."""
        k = norm(name)
        if not k:
            return None
        for key in self.alias.get((cc, k), []) + [k, CRU.sub(" ", k).strip()]:
            hit = self.by.get((cc, key))
            if not hit:
                continue
            # two vineyards of one name (there are four Altenbergs on the Mosel) cannot be told apart by name alone
            same = [x for x in hit if x[0] == hit[0][0]]
            if len({x[1] for x in same}) > 1 and (unique or hit[0][0] >= LEVEL_PREF["vineyard"]):
                return None
            if region:
                grp = [x for x in hit if x[0] == 5]
                if grp:
                    return grp[0][1]
            return hit[0][1]
        return None

    def site(self, cc, site, sub):
        """A site named inside its sub-region or village, as LWIN writes them: "Les Suchots" in Vosne-Romanée,
        "Wehlener Sonnenuhr" (the village as an adjective) in the Mosel."""
        s = CRU.sub(" ", norm(site)).strip()
        if not s:
            return None
        hit = self.sites.get((cc, norm(sub), s))
        if hit:
            return hit
        w = s.split(" ")
        if len(w) > 1 and w[0].endswith("er") and len(w[0]) > 4:
            for village in (w[0][:-2], w[0][:-1]):
                hit = self.sites.get((cc, village, " ".join(w[1:])))
                if hit:
                    return hit
        return self.find(cc, site, unique=True)


VILLAGE_SITE = re.compile(r"\b([A-ZÄÖÜ][a-zäöüß-]+er) ([A-ZÄÖÜ][\wäöüß-]+(?: [A-ZÄÖÜ][\wäöüß-]+)?)")


def place_of(places, cc, r):
    """The most precise atlas place an LWIN record names, and the column it came from."""
    site, sub, reg = r.get("SITE"), r.get("SUB_REGION"), r.get("REGION")
    if site:
        hit = places.site(cc, site, sub)
        if hit:
            return hit, "site"
        # the site written after its appellation: "Chablis" + "Les Clos" is Chablis Grand Cru Les Clos,
        # "Bourgogne" + "Hautes Cotes de Nuits" is Bourgogne Hautes Côtes de Nuits, "Macon" + "Fuisse" is Mâcon Fuissé
        for base in (sub, reg):
            for mid in (" ", " grand cru ", " premier cru "):
                hit = base and places.find(cc, base + mid + site, unique=True)
                if hit:
                    return hit, "site"
    if cc == "DE":
        # German labels name the Einzellage after the village: "Wiltinger Braune Kupp", "Wehlener Sonnenuhr"
        for m in VILLAGE_SITE.finditer(r.get("WINE") or ""):
            v, rest = m.group(1), m.group(2)
            for cand in (rest, rest.split(" ")[0]):
                for village in (v[:-2], v[:-1]):
                    hit = places.sites.get((cc, norm(village), norm(cand)))
                    if hit:
                        return hit, "site in wine name"
    if sub:
        hit = places.find(cc, sub)
        if hit:
            return hit, "sub_region"
    if reg:
        hit = places.find(cc, reg)
        if hit:
            return hit, "region"
    return None, None


def main(path=None):
    if path is None:
        files = sorted(glob.glob(os.path.join(RAW, "*.xlsx")) + glob.glob(os.path.join(RAW, "*.csv")))
        if not files:
            sys.exit("put the LWIN database (.xlsx or .csv) in raw/lwin/ first, see the top of this file")
        path = files[-1]
    ccs, places = country_codes(), Places()
    prods = collections.OrderedDict()
    seen = set()
    stats = collections.Counter()
    unknown = collections.Counter()
    for r in read_rows(path):
        lwin = re.sub(r"\D", "", r.get("LWIN") or r.get("LWIN7") or "")[:7]
        if len(lwin) != 7 or lwin in seen:
            continue
        status = norm(r.get("STATUS"))
        if status and status not in ("live", "active"):
            stats["not live"] += 1
            continue
        typ = norm(r.get("TYPE"))
        if typ and typ not in WINE_TYPES:
            stats["not wine"] += 1
            continue
        seen.add(lwin)
        cc = ccs.get(norm(r.get("COUNTRY")))
        if not cc:
            stats["country not in atlas"] += 1
            continue
        producer = " ".join(x for x in (r.get("PRODUCER_TITLE"), r.get("PRODUCER_NAME")) if x).strip()
        wine = r.get("WINE") or ""
        if not producer:
            producer, _, rest = (r.get("DISPLAY_NAME") or "").partition(",")
            wine = wine or rest.split(",")[0].strip()
        producer = re.sub(r"\s+", " ", producer).strip()
        if not producer:
            continue
        # the label as Liv-ex writes it, without the producer: "Echezeaux Grand Cru", "Blagny Premier Cru, Sous le Dos d'Ane"
        parts = [x.strip() for x in (r.get("DISPLAY_NAME") or "").split(", ") if x.strip()]
        parts = [x for x in parts if norm(x) != norm(producer)]
        # a last part that only repeats the region ("…, Mosel", "…, Toscana") is shown by the map already
        while len(parts) > 1 and norm(parts[-1]) in (norm(r.get("REGION")), norm(r.get("SUB_REGION")), norm(r.get("COUNTRY"))):
            parts.pop()
        label = ", ".join(parts) or wine
        if NOT_A_WINE.search(label) or norm(r.get("COLOUR")) == "mixed":
            stats["case or box"] += 1
            continue
        where, col = place_of(places, cc, r)
        stats["placed by " + col if col else "country only"] += 1
        if not where:
            unknown[(cc, r.get("REGION", ""), r.get("SUB_REGION", ""))] += 1
        prods.setdefault((producer, cc), []).append((label, where, kind_of(r), lwin))
    write(prods, path, stats, unknown)


def write(prods, path, stats, unknown):
    """producers.json, small, for the search and the place sheets; wines.json, the wines of every producer."""
    keys = sorted(prods, key=lambda k: (norm(k[0]), k[1]))
    ids = {}
    plist, wlist = [], []
    for i, (producer, cc) in enumerate(keys):
        wines = sorted(prods[(producer, cc)], key=lambda w: norm(w[0]))
        at = collections.Counter(ids.setdefault(w[1], len(ids)) for w in wines if w[1])
        plist.append([producer, cc, [[p, n] for p, n in at.most_common()], len(wines)])
        for w, p, k, l in wines:
            wlist.append([w, i, ids[p] if p else -1, k, l])
    meta = {"source": SOURCE, "date": datetime.date.today().isoformat(), "file": os.path.basename(path)}
    for name, doc in (("producers.json", {**meta, "places": list(ids), "p": plist}),
                      ("wines.json", {**meta, "w": wlist})):
        dst = os.path.join(WEB, name)
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  {name}: {os.path.getsize(dst) / 1e6:.1f} MB")
    print(f"  {len(plist)} producers, {len(wlist)} wines, {len(ids)} places")
    for k, v in sorted(stats.items()):
        print(f"    {k}: {v}")
    rep = os.path.join(ROOT, "build", "lwin_unplaced.tsv")
    os.makedirs(os.path.dirname(rep), exist_ok=True)
    with open(rep, "w", encoding="utf-8") as f:
        f.write("wines\tcountry\tregion\tsub_region\n")
        for (cc, reg, sub), c in unknown.most_common():
            f.write(f"{c}\t{cc}\t{reg}\t{sub}\n")
    print(f"    regions not placed: build/lwin_unplaced.tsv ({len(unknown)})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
