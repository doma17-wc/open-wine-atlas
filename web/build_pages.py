"""Static pages for search engines and sharing: one page per wine place, region and country, plus the sitemap.

  web/places/index.html                         every country
  web/places/<country>/index.html               one country, by region
  web/places/<country>/area/<group>.html        a region of the country tree (Bordeaux, Mosel, Napa...)
  web/places/<country>/<place>.html             one appellation, sub-zone, cru or vineyard site
  web/sitemap.xml, web/robots.txt

Everything comes from web/data (search.json, tree.json, details-*.json, vintages.json), the same files the map
reads, so the pages always match the map. Each page links to the map with the place selected (/#<id>).
Run by build_web.py; can also run alone: python3 web/build_pages.py
"""
import html
import json
import math
import os
import re
import shutil
import unicodedata
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "places")
SITE = "https://openwineatlas.com"

esc = lambda s: html.escape(str(s), quote=True)


def slugify(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "place"


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def fmt_n(v, d=0):
    try:
        n = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return esc(v)
    return f"{n:,.{d}f}".rstrip("0").rstrip(".") if d else f"{n:,.0f}"


def fmt_list(a):
    a = [str(x) for x in a]
    return a[0] if len(a) == 1 else ", ".join(a[:-1]) + " and " + a[-1] if a else ""


def country_names():
    src = open(os.path.join(HERE, "index.src.html"), encoding="utf-8").read()
    m = re.search(r"const COUNTRY_EN = \{(.*?)\};", src, re.S)
    names = dict(re.findall(r'(\w\w): "([^"]+)"', m.group(1)))
    return names


RANK = {"grand_cru": "Grand cru", "premier_cru": "Premier cru", "docg": "DOCG", "doca": "DOCa", "pago": "Vino de Pago"}
LEVEL = {"region": "Wine region", "appellation": "Appellation", "subzone": "Sub-zone", "vineyard": "Vineyard site"}
WHAT = {"region": "a wine region", "appellation": "an appellation", "subzone": "a named sub-zone", "vineyard": "a climat",
        "vineyard_DE": "a registered vineyard site (Einzellage)",
        "grand_cru appellation": "a grand cru appellation", "grand_cru subzone": "a grand cru sub-zone", "grand_cru vineyard": "a grand cru climat",
        "premier_cru appellation": "a premier cru appellation", "premier_cru subzone": "a premier cru sub-zone", "premier_cru vineyard": "a premier cru climat",
        "docg appellation": "a DOCG appellation", "doca appellation": "a DOCa appellation", "pago appellation": "a Vino de Pago appellation",
        "docg subzone": "a DOCG sub-zone", "doca subzone": "a DOCa sub-zone"}
COLOUR = {"Red": "#8e3040", "White": "#d9c88a", "Rosé": "#d39aa0", "Rose": "#d39aa0"}
SCORE_BG = {1: "#4a3e2c", 2: "#75603a", 3: "#a2803f", 4: "#cfa04a", 5: "#f2c665"}
SCORE_FG = {1: "#e6dccb", 2: "#f3ead9", 3: "#0b0b0d", 4: "#0b0b0d", 5: "#0b0b0d"}
GRAPE_RE = re.compile(r"^(.*?)\s+(N|B|G|Rs|Rg)$")


def grape_name(g):
    m = GRAPE_RE.match(str(g).strip())
    return m.group(1) if m else str(g).strip()


CSS = """
:root{--night:#0b0b0d;--panel:#141417;--line:#2a2a31;--parchment:#e6dccb;--muted:#8d877c;--gold:#e7c06a;--copper:#cf8f5f;
--f-display:"Cormorant Garamond","Iowan Old Style","Palatino Linotype",Georgia,serif;--f-body:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
--f-mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--night);color:var(--parchment);font:16px/1.6 var(--f-body)}
a{color:var(--parchment);text-decoration-color:#57534a;text-underline-offset:3px}a:hover{text-decoration-color:var(--gold)}
.wrap{max-width:860px;margin:0 auto;padding:20px 16px 64px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.top .brand{font:600 22px/1.1 var(--f-display);text-decoration:none}
.top nav{display:flex;gap:14px;font-size:14px}
.crumbs{margin:22px 0 6px;font-size:13px;color:var(--muted)}.crumbs a{color:var(--muted)}
.eyebrow{font:500 12px var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
h1{font:600 clamp(34px,6vw,52px)/1.05 var(--f-display);margin:6px 0 12px;text-wrap:balance}
h2{font:600 26px/1.2 var(--f-display);margin:36px 0 10px}
.lead{font-size:18px;max-width:68ch}
.note{color:var(--muted);font-size:14px}
.badge{display:inline-block;padding:2px 9px;border:1px solid var(--line);border-radius:999px;font:500 12px var(--f-mono);margin-right:6px}
.badge.top{border-color:var(--gold);color:var(--gold)}.badge.pc{border-color:var(--copper);color:var(--copper)}
.cta{display:inline-flex;align-items:center;gap:8px;margin:18px 0 6px;padding:11px 18px;border-radius:999px;background:var(--parchment);color:var(--night);
font-weight:600;text-decoration:none}.cta:hover{background:#fff8ea}
.atlas-note{border-left:2px solid var(--gold);padding:2px 0 2px 14px;margin:18px 0}
dl.facts{display:grid;grid-template-columns:minmax(120px,190px) 1fr;gap:8px 18px;margin:0}
dl.facts dt{color:var(--muted);font-size:14px}dl.facts dd{margin:0;font-variant-numeric:tabular-nums}
.wine{padding:12px 0;border-top:1px solid var(--line)}.wine:first-of-type{border-top:0}
.wine b{font-weight:600}.chip{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;vertical-align:middle}
.grapes{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}.grapes span{padding:1px 8px;border:1px solid var(--line);border-radius:5px;font-size:14px}
ul.cols{columns:2 240px;column-gap:28px;padding:0;margin:0;list-style:none}ul.cols li{break-inside:avoid;padding:3px 0}
ul.cols li .k{color:var(--muted);font-size:13px;margin-left:6px}
.vgrid{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));gap:6px;max-width:520px}
.vgrid div{text-align:center;font:500 12px var(--f-mono);color:var(--muted)}
.vgrid .s{display:block;border-radius:5px;padding:4px 0;font-size:13px;margin-bottom:2px}
details{margin:8px 0}summary{cursor:pointer;color:var(--muted)}
.legal{white-space:pre-wrap;font-size:14px;color:#cfc6b6;max-height:none}
footer{margin-top:56px;padding-top:16px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}footer a{color:var(--muted)}
.reels{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:24px 0}
.reel{display:grid;gap:8px;align-content:start;padding:14px 16px;border:1px solid var(--line);border-radius:12px;background:var(--panel);text-decoration:none}
.reel:hover,.reel:focus-visible{border-color:var(--gold)}.reel[hidden]{display:none}
.reel b{font:600 22px/1.12 var(--f-display);text-wrap:balance}.reel .eyebrow{font-size:11px}
.reel ul{margin:0;padding:0;list-style:none;font-size:14px;columns:2 110px;column-gap:14px}.reel li{break-inside:avoid}.reel li .k{color:var(--muted);font:500 12px var(--f-mono)}
.reel .go{color:var(--gold);font-size:14px;font-weight:600}
.reel.vs b::after{content:"";display:block;width:34px;height:2px;margin-top:8px;background:var(--gold)}
@media (max-width:600px){dl.facts{grid-template-columns:1fr;gap:2px}dl.facts dd{margin-bottom:10px}.vgrid{grid-template-columns:repeat(5,minmax(0,1fr))}.top nav{gap:10px;font-size:13px}}
"""



def page(title, desc, path, body, jsonld=None):
    url = SITE + path
    ld = "".join('<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False).replace("</", "<\\/") + "</script>" for j in (jsonld or []))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0b0b0d">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Open Wine Atlas">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/places/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/places/style.css">
<script>window.va = window.va || function () {{ (window.vaq = window.vaq || []).push(arguments); }};</script>
<script defer src="/_vercel/insights/script.js"></script>
{ld}
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="/">Open Wine Atlas</a><nav><a href="/">Map</a><a href="/places/">All places</a><a href="/records/">Records</a></nav></header>
{body}
<footer>Open Wine Atlas is built only from open official registers and open data. Outlines, rules and facts come from the sources
named on each page. <a href="/places/">All wine places</a> · <a href="/">Open the map</a> · <a href="/privacy">Privacy</a> · <a href="/terms">Terms of Use</a> · <a href="/legal">Legal notice</a></footer>
</div>
</body>
</html>
"""


def main():
    idx = json.load(open(os.path.join(DATA, "search.json"), encoding="utf-8"))
    tree = json.load(open(os.path.join(DATA, "tree.json"), encoding="utf-8"))
    vint = json.load(open(os.path.join(DATA, "vintages.json"), encoding="utf-8"))
    CN = country_names()
    cname = lambda cc: re.sub(r"^the ", "", CN.get(cc, cc))
    cname_run = lambda cc: CN.get(cc, cc)
    details = {}
    for f in os.listdir(DATA):
        m = re.match(r"details-(\w\w)\.json$", f)
        if m:
            details.update(json.load(open(os.path.join(DATA, f), encoding="utf-8")))
    by_id = {r[1]: r for r in idx}
    by_name = {}
    for r in idx:
        k = norm(r[0] + (" " + r[7] if len(r) > 7 and r[7] else ""))
        if k not in by_name or r[3] == "appellation":
            by_name[k] = r
    children_by_name = {}
    for r in idx:
        if r[5]:
            children_by_name.setdefault(norm(r[5]), []).append(r)

    nodes = tree["nodes"]
    parent_of = {}
    for k, v in nodes.items():
        for c in v[3] or []:
            parent_of.setdefault(c, k)
    for root_name, kids in tree["roots"]:
        for c in kids:
            parent_of.setdefault(c, None)

    # ---------- urls: unique per country
    cslug = {cc: slugify(cname(cc)) for cc in {r[2] for r in idx}}
    url_of, used = {}, {}
    for r in sorted(idx, key=lambda r: ({"region": 0, "appellation": 1, "subzone": 2, "vineyard": 3}.get(r[3], 9), r[1])):
        cc = r[2]
        base = slugify(r[0])
        cand = [base] + ([base + "-" + slugify(r[5])] if r[5] else []) + [base + "-" + slugify(r[1])]
        s = next(c for c in cand if c not in used.setdefault(cc, set()))
        used[cc].add(s)
        url_of[r[1]] = f"/places/{cslug[cc]}/{s}"
    for k in nodes:
        if k.startswith("g:") and "/" in k:
            cc, rest = k[2:].split("/", 1)
            url_of[k] = f"/places/{cslug.get(cc, slugify(cc))}/area/{slugify(rest)}"
        elif k.startswith("g:"):
            url_of[k] = f"/places/{cslug.get(k[2:], slugify(k[2:]))}/"

    def node_name(k):
        if k in by_id:
            return by_id[k][0]
        return nodes[k][0] if k in nodes and nodes[k][0] else k

    def trail(k):
        out, seen = [], set()
        p = parent_of.get(k)
        while p and p not in seen:
            seen.add(p)
            out.append(p)
            p = parent_of.get(p)
        return list(reversed(out))

    def link(k, label=None):
        return f'<a href="{url_of[k]}">{esc(label or node_name(k))}</a>' if k in url_of else esc(label or node_name(k))

    def crumbs_html(k):
        t = [p for p in trail(k) if p in url_of]
        return '<div class="crumbs"><a href="/places/">All places</a>' + "".join(" › " + link(p) for p in t) + "</div>"

    def crumbs_ld(k, name, path):
        items = [("All places", "/places/")] + [(node_name(p), url_of[p]) for p in trail(k) if p in url_of] + [(name, path)]
        return {"@context": "https://schema.org", "@type": "BreadcrumbList",
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}

    def vintage_regions(r, d, pd):
        office = (d.get("inao_office") or pd.get("inao_office") or "").lower()
        n, par, reg = norm(r[0]), norm(r[5] or ""), (d.get("region") or "").lower()
        out = []
        for v in vint["regions"]:
            m = v.get("match", {})
            ok = (m.get("office") and office and office in m["office"]) or \
                 (m.get("names") and any(n == norm(x) or n.startswith(norm(x) + " ") or par == norm(x) for x in m["names"])) or \
                 (m.get("de_region") and r[2] == "DE" and (reg in m["de_region"] or n in m["de_region"] or par in m["de_region"])) or \
                 (m.get("ava_within") and r[2] == "US" and (r[0] in m["ava_within"] or any(w in m["ava_within"] for w in d.get("within", []))))
            if ok:
                out.append(v)
        return out

    def world_type(r, d):
        return re.sub(r"\s*\(.*\)\s*$", "", d.get("type", "")) if "-world-" in r[1] and d.get("type") else ""

    def summary(r, d, pd):
        name, cc, level, rank, parent = r[0], r[2], r[3], r[4], r[5]
        wt = world_type(r, d)
        lvl = "vineyard_DE" if level == "vineyard" and cc == "DE" else level
        what = ("a " + wt) if wt else WHAT.get(f"{rank} {level}") or WHAT.get(lvl) or "a place"
        area = d.get("area_ha")
        towns = d.get("gemarkungen") or d.get("communes") or []
        t = f"{name} is {what}{' of ' + parent if parent else ''} in {cname_run(cc)}"
        if area:
            t += f", covering {fmt_n(area, 1)} ha"
        if towns:
            t += f" in {fmt_list(towns)}" if len(towns) <= 3 else f" across {len(towns)} communes"
        t += "."
        if d.get("share_of_parent"):
            t += f" That is {d['share_of_parent']}% of the {parent} appellation area."
        if d.get("share_of_grosslage"):
            t += f" It makes up {d['share_of_grosslage']}% of the Großlage {d.get('grosslage')}."
        wines = d.get("wines") or pd.get("wines") or []
        if wines:
            cols = list(dict.fromkeys(w["colour"].lower() for w in wines if w.get("colour")))
            mains = list(dict.fromkeys(grape_name(g) for w in wines for g in w.get("main") or []))
            if cols and mains and len(mains) <= 4:
                t += f" The rules allow {fmt_list(cols)} wine, based on {fmt_list(mains)}."
            elif cols:
                t += f" The rules allow {fmt_list(cols)} wine."
        if d.get("bedrock"):
            t += " Regional bedrock: " + re.sub(r" \(.*\)", "", d["bedrock"][0][0]).lower() + "."
        at = where_sentence(r, d)
        if at:
            t += " " + at
        return t

    SECT16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    SECT8 = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]

    def km_txt(km):
        return fmt_n(round(km, 1) if km < 10 else round(km), 1 if km < 10 else 0)

    def from_town(name, t, direction=True):
        town, km, dr = t[0], t[1], t[2]
        if km < 6 and norm(town) in norm(name):
            return f"around the town of {town}"
        if km < 1.5:
            return f"next to {town}"
        return f"{km_txt(km)} km {SECT8[int(SECT16.index(dr) / 2 + 0.5) % 8]} of {town}"  # half up, as in the map

    def small_place(r):
        b = r[6]
        kx = 111.32 * math.cos(math.radians((b[1] + b[3]) / 2))
        return math.hypot((b[2] - b[0]) * kx, (b[3] - b[1]) * 110.57) < 25

    def where_sentence(r, d):
        if not d.get("near_town") or not small_place(r):
            return ""
        a = from_town(r[0], d["near_town"])
        c = d.get("near_city")
        if c and c[1] < 120:
            return f"It lies {a} and {from_town('', c)}."
        return f"It lies {a}."

    def short_type(r, d):
        if r[4] in RANK:
            return RANK[r[4]]
        t = d.get("type") or ""
        m = re.match(r"^([A-Z][A-Za-z.]*(?:/[A-Z][A-Za-z.]*)?)\b", t)
        return m.group(1) if m and len(m.group(1)) <= 8 else LEVEL.get(r[3], "")

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    # one shared stylesheet and icon, cached by the browser across pages
    open(os.path.join(OUT, "style.css"), "w", encoding="utf-8").write(CSS.strip() + "\n")
    open(os.path.join(OUT, "icon.svg"), "w", encoding="utf-8").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0b0b0d"/>'
        '<path d="M7 22l6-9 4 5 3-4 5 8z" fill="none" stroke="#e7c06a" stroke-width="2" stroke-linejoin="round"/></svg>\n')
    urls = [("/", "weekly", "1.0"), ("/places/", "weekly", "0.9")]

    def write(path, text):
        fp = os.path.join(HERE, path.lstrip("/"))
        if path.endswith("/"):
            fp = os.path.join(fp, "index.html")
        else:
            fp += ".html"
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(text)

    # ---------- one page per place
    for r in idx:
        pid, name, cc, level, rank, parent = r[1], r[0], r[2], r[3], r[4], r[5]
        d = details.get(pid, {})
        prec = by_name.get(norm(parent)) if parent else None
        pd = details.get(prec[1], {}) if prec else {}
        path = url_of[pid]
        typ = d.get("type") or LEVEL.get(level, "")
        st = short_type(r, d)
        summ = summary(r, d, pd)
        title = f"{name}{' ' + st if st and st not in name and st not in ('Appellation', 'Sub-zone', 'Vineyard site', 'Wine region') else ''}: wine map, rules and terrain | Open Wine Atlas"
        desc = summ if len(summ) <= 158 else summ[:155].rsplit(" ", 1)[0] + "…"

        badges = ""
        if rank in RANK:
            badges += f'<span class="badge {"top" if rank in ("grand_cru", "docg", "doca", "pago") else "pc"}">{RANK[rank]}</span>'
        badges += f'<span class="badge">{esc(LEVEL.get(level, level))}</span>'

        b = [crumbs_html(pid), f'<div class="eyebrow">{esc(cname(cc))} · {esc(typ)}</div>', f"<h1>{esc(name)}</h1>", f"<div>{badges}</div>",
             f'<p class="lead">{esc(summ)}</p>']
        if d.get("atlas_note"):
            b.append(f'<div class="atlas-note">{esc(d["atlas_note"])}</div>')
        b.append(f'<a class="cta" href="/#{esc(pid)}">Open {esc(name)} on the map →</a>'
                 '<p class="note">The map shows the official outline with relief, 3D terrain, slope and exposure, climate and soil.</p>')

        facts = []
        add = lambda k, v: v not in (None, "", "na", []) and facts.append((k, v))
        add("Official name", esc(d.get("official_name", "")) if d.get("official_name") and d.get("official_name") != name else "")
        add("Type", esc(typ))
        add("Within", link(prec[1]) if prec else "")
        add("Category", esc(d.get("category", "")))
        add("Protected since", esc(d.get("registered", "")))
        outline_kind = ("outline of the administrative units" if d.get("admin_units") else
                        "registered outline" if d.get("outline_quality") else "outline of listed communes")
        add("Area", (f"{fmt_n(d['area_ha'], 1)} ha" if d.get("area_ha") else
                     (f"{fmt_n(d['outline_area_ha'])} ha {outline_kind}" if d.get("outline_area_ha") else ""))
            + (f' <span class="note">{esc(d["area_note"])}</span>' if d.get("area_note") else ""))
        add("Vineyard area", (f"{fmt_n(d['vine_area_ha'], 2 if d['vine_area_ha'] < 10 else 1)} ha" +
                              (f' <span class="note">{esc(d["vine_area_src"])}</span>' if d.get("vine_area_src") else "") +
                              (f' <span class="note">{esc(d["vine_area_note"])}</span>' if d.get("vine_area_note") else "")) if d.get("vine_area_ha") else "")
        add("Growers", fmt_n(d["growers"]) if d.get("growers") else "")
        add("On the label", esc(d.get("label_rule", "")))
        add("Premier grand cru", esc(d.get("pgc_rule", "")))
        add("Grapes planted", esc(", ".join(f"{g} {fmt_n(pc, 1)}%" for g, pc in d["grape_share"])) +
            (f' <span class="note">{esc(d["grape_share_note"])}</span>' if d.get("grape_share_note") else "") if d.get("grape_share") else "")
        add("Premiers crus", esc(", ".join(f"{n} ({fmt_n(ha, 1)} ha)" for n, ha, *_ in d["premiers_crus"])) if d.get("premiers_crus") else "")
        add("Known producers", esc(d.get("producers_note", "")))
        add("Separate plots", fmt_n(d["plots"]) if d.get("plots") and d["plots"] > 1 else "")
        add("Extent N–S × E–W", f"{d['extent_km'][0]} × {d['extent_km'][1]} km" if d.get("extent_km") else "")
        if d.get("lat") is not None:
            add("Centre", f"{abs(d['lat']):.4f}° {'N' if d['lat'] >= 0 else 'S'}, {abs(d['lon']):.4f}° {'E' if d['lon'] >= 0 else 'W'}")
        add("Region", esc(d.get("region", "")) if cc == "DE" else "")
        add("Bereich", esc(d.get("bereich", "")))
        add("Großlage", esc(d.get("grosslage", "")))
        add("State", esc(d.get("state", "")) or (esc(", ".join(d["states"])) if d.get("states") else ""))
        add("Wine region", esc(d.get("wine_region", "")))
        add("Grapes", esc(", ".join(grape_name(g) for g in re.split(r"\s*[,/]\s*", d["grapes"]))) if d.get("grapes") and d["grapes"] != "na" else "")
        add("Other grapes", esc(", ".join(grape_name(g) for g in re.split(r"\s*[,/]\s*", d["grapes_other"]))) if d.get("grapes_other") and d["grapes_other"] != "na" else "")
        add("Max yield", f"{esc(d['max_yield_hl_ha'])} hl/ha" if d.get("max_yield_hl_ha") not in (None, "na") else "")
        add("Min planting density", f"{fmt_n(d['min_planting_density'])} vines/ha" if d.get("min_planting_density") not in (None, "na") else "")
        add("Irrigation", esc(d.get("irrigation", "")))
        add("INAO office", esc(d.get("inao_office", "")))
        add("Also known as", esc(d.get("aka", "")))
        add("Also registered as", esc(", ".join(d["also_registered"])) if d.get("also_registered") else "")
        add("Legal basis", esc(d.get("basis", "") or d.get("register_ref", "")))
        add("Federal rule", f'<a href="{esc(d["cfr_url"])}" rel="nofollow noopener">{esc(d.get("cfr", "27 CFR part 9"))}</a>' if d.get("cfr_url") else "")
        add("Petitioner", esc(d.get("petitioner", "")))
        b.append("<h2>Key facts</h2><dl class=\"facts\">" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts) + "</dl>")
        if d.get("outline"):
            b.append(f'<p class="note">Outline: {esc(d["outline"])}</p>')

        wf = []
        if d.get("near_town"):
            wf.append(("Nearest town", esc(from_town(name, d["near_town"]))))
        if d.get("near_city"):
            wf.append(("Nearest city", esc(from_town("", d["near_city"])) + f' <span class="note">{fmt_n(d["near_city"][3])} people</span>'))
        if d.get("sea_km") is not None:
            wf.append(("To the sea", f"{km_txt(d['sea_km'])} km"))
        if d.get("rivers"):
            wf.append(("Rivers nearby", " · ".join(f"{esc(n)} ({km_txt(k)} km)" for n, k in d["rivers"])))
        if d.get("lakes"):
            wf.append(("Lakes nearby", " · ".join(f"{esc(n)} ({km_txt(k)} km)" for n, k in d["lakes"])))
        twins = [t for t in d.get("lat_twins", []) if t in by_id]
        if twins:
            wf.append(("Same latitude", ", ".join(f"{link(t)} ({esc(cname(by_id[t][2]))})" for t in twins)))
        if wf:
            b.append("<h2>Where it is</h2><dl class=\"facts\">" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in wf) + "</dl>"
                     '<p class="note">Distances from the centre of the place. Towns: GeoNames (CC BY 4.0). Sea, rivers and lakes: Natural Earth.</p>')
        tr = d.get("terrain")
        if tr and tr.get("e"):
            mn, mean, mx, p10, p90 = tr["e"]
            tf = [("Elevation", f"{fmt_n(mn)}–{fmt_n(mx)} m"), ("Mean elevation", f"{fmt_n(mean)} m")]
            if tr.get("s"):
                tf.append(("Mean slope", f"{tr['s'][0]}° ({round(math.tan(math.radians(tr['s'][0])) * 100)} %)"))
                tf.append(("Steepest tenth", f"above {round(tr['s'][1])}°"))
            if tr.get("asp") is not None:
                tf.append(("Faces", SECT8[int(tr["asp"] / 45 + 0.5) % 8]))
            elif tr.get("dom") and tr.get("s"):
                tf.append(("Faces", "several directions, mostly " + SECT8[["N", "NE", "E", "SE", "S", "SW", "W", "NW"].index(tr["dom"])]))
            b.append("<h2>Terrain</h2><dl class=\"facts\">" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in tf) + "</dl>"
                     f'<p class="note">Measured over the whole outline on {fmt_n(tr["n"])} elevation cells of about {fmt_n(tr["res"])} m '
                     '(Mapterhorn terrain tiles).' + (" The outline is made of whole communes or districts, so it includes land that is not vineyard."
                                                       if "-eupdo-" in pid or "-world-" in pid else "") + "</p>")

        wines = d.get("wines") or []
        if wines:
            rows = []
            for w in wines:
                mains = "".join(f"<span>{esc(grape_name(g))}</span>" for g in w.get("main") or [])
                nn = " · ".join(x for x in [f"max {fmt_n(w['yield_hl'], 1)} hl/ha" if w.get("yield_hl") not in (None, "na", "") else "",
                                            f"min {fmt_n(w['density'])} vines/ha" if w.get("density") not in (None, "na", "") else ""] if x)
                kind = " · ".join(x for x in [w.get("colour", ""), w.get("category", "") if w.get("category") not in ("Wine", None) else ""] if x)
                rows.append(f'<div class="wine"><b><i class="chip" style="background:{COLOUR.get(w.get("colour"), "#8d877c")}"></i>{esc(w["wine"])}</b>'
                            f' <span class="note">{esc(kind)}</span>' + (f'<div class="grapes">{mains}</div>' if mains else "") +
                            (f'<div class="note">{nn}</div>' if nn else "") + "</div>")
            b.append(f"<h2>Wines and grape rules</h2>" + "".join(rows))

        vr = vintage_regions(r, d, pd)
        if vr:
            yrs = vint["years"][-20:]
            for v in vr:
                cells = "".join(f'<div><span class="s" style="background:{SCORE_BG[v["scores"][str(y)]]};color:{SCORE_FG[v["scores"][str(y)]]}">{v["scores"][str(y)]}</span>{str(y)[2:]}</div>'
                                if v["scores"].get(str(y)) else f'<div><span class="s">–</span>{str(y)[2:]}</div>' for y in yrs)
                b.append(f'<h2>Vintages: {esc(v["name"])}</h2><div class="vgrid">{cells}</div>')
            b.append(f'<p class="note">{esc(vint.get("note", ""))} Scale 1 to 5.</p>')

        if d.get("bedrock"):
            b.append("<h2>Bedrock</h2><ul class=\"cols\">" + "".join(f"<li>{esc(x[0])}<span class=\"k\">{x[1]}%</span></li>" for x in d["bedrock"]) + "</ul>"
                     '<p class="note">Regional bedrock from the GLiM global lithological map (Hartmann and Moosdorf 2012), not a soil survey.</p>')

        towns = d.get("gemarkungen") or d.get("communes") or d.get("counties") or []
        if towns:
            label = "Gemarkungen" if d.get("gemarkungen") else "Counties" if d.get("counties") and not d.get("communes") else "Communes"
            lst = "<ul class=\"cols\">" + "".join(f"<li>{esc(t)}</li>" for t in towns) + "</ul>"
            b.append(f"<h2>{label} · {len(towns)}</h2>" + (lst if len(towns) <= 40 else f"<details><summary>Show all {len(towns)}</summary>{lst}</details>"))

        kids = children_by_name.get(norm(name), [])
        kids = [k for k in kids if k[2] == cc and k[1] != pid]
        tkids = [c for c in (nodes.get(pid, [None, None, None, []])[3] or []) if c in by_id and c not in {k[1] for k in kids}]
        kids += [by_id[c] for c in tkids]
        if kids:
            kids.sort(key=lambda k: (0 if k[4] in ("grand_cru", "docg", "doca", "pago") else 1 if k[4] == "premier_cru" else 2, k[0]))
            b.append(f"<h2>Inside {esc(name)} · {len(kids)}</h2><ul class=\"cols\">" +
                     "".join(f"<li>{link(k[1])}<span class=\"k\">{esc(RANK.get(k[4]) or LEVEL.get(k[3], ''))}</span></li>" for k in kids) + "</ul>")
        for key, label in (("within", "Within"), ("contains", "Contains")):
            if d.get(key):
                items = [by_name.get(norm(x)) for x in d[key]]
                b.append(f"<h2>{label}</h2><ul class=\"cols\">" + "".join(f"<li>{link(it[1]) if it else esc(x)}</li>" for x, it in zip(d[key], items)) + "</ul>")
        nb = [n for n in d.get("neighbours", []) if n in by_id]
        if nb:
            b.append("<h2>Neighbours</h2><ul class=\"cols\">" + "".join(f"<li>{link(n)}</li>" for n in nb) + "</ul>")

        if d.get("wineries"):
            b.append(f"<h2>Wineries · {d.get('wineries_count', len(d['wineries']))}</h2><ul class=\"cols\">" +
                     "".join(f'<li><a href="{esc(u)}" rel="nofollow noopener ugc">{esc(n)}</a></li>' if u else f"<li>{esc(n)}</li>" for n, u in d["wineries"]) +
                     '</ul><p class="note">From OpenStreetMap. Missing a winery? Add it to OpenStreetMap and it appears here.</p>')

        if d.get("boundary_text"):
            b.append(f'<h2>Legal boundary</h2><details><summary>Read the boundary description</summary><p class="legal">{esc(d["boundary_text"])}</p></details>')

        src = []
        if d.get("eu_register"):
            src.append(f'<a href="{esc(d["eu_register"])}" rel="nofollow noopener">EU register of geographical indications</a>')
        if d.get("gi_url"):
            src.append(f'<a href="{esc(d["gi_url"])}" rel="nofollow noopener">Wine Australia GI register</a>')
        if d.get("outline_source"):
            os_ = d["outline_source"]
            src.append(esc(f'{os_.get("name", "")} ({os_.get("licence", "")})'))
        if pid.startswith("fr-inao"):
            src.append("INAO, Délimitation parcellaire des AOC viticoles (Licence Ouverte 2.0)")
        if pid.startswith("de-rlp"):
            src.append("Landwirtschaftskammer Rheinland-Pfalz, Weinbergslagen (dl-de/by-2-0)")
        if pid.startswith("us-ava"):
            src.append("UC Davis Library AVA project (CC0)")
        for t, u in d.get("refs", []):
            src.append(f'<a href="{esc(u)}" rel="nofollow noopener">{esc(t)}</a>')
        if src:
            b.append("<h2>Sources</h2><p class=\"note\">" + " · ".join(src) + "</p>")
        b.append(f'<a class="cta" href="/#{esc(pid)}">Open {esc(name)} on the map →</a>')

        ld = [{"@context": "https://schema.org", "@type": "Place", "name": name, "description": summ, "url": SITE + path,
               "containedInPlace": {"@type": "Country", "name": cname(cc)}}, crumbs_ld(pid, name, path)]
        if d.get("lat") is not None:
            ld[0]["geo"] = {"@type": "GeoCoordinates", "latitude": d["lat"], "longitude": d["lon"]}
        write(path, page(title, desc, path, "\n".join(b), ld))
        urls.append((path, "monthly", "0.6" if level == "vineyard" else "0.7"))

    # ---------- region pages from the country tree
    def list_node_children(k):
        out = []
        for c in nodes[k][3] or []:
            if c in by_id:
                r = by_id[c]
                out.append(f"<li>{link(c)}<span class=\"k\">{esc(RANK.get(r[4]) or LEVEL.get(r[3], ''))}</span></li>")
            elif c in nodes:
                out.append(f"<li>{link(c)}<span class=\"k\">{nodes[c][4] if len(nodes[c]) > 4 else ''} places</span></li>")
        return "<ul class=\"cols\">" + "".join(out) + "</ul>"

    for k, v in nodes.items():
        if not (k.startswith("g:") and "/" in k):
            continue
        cc = k[2:].split("/")[0]
        name, path, count = v[0], url_of[k], v[4] if len(v) > 4 else len(v[3] or [])
        lead = f"{name} is a wine region of {cname_run(cc)} with {count} wine places in the atlas: appellations, sub-zones, crus and vineyard sites from the official registers."
        body = (crumbs_html(k) + f'<div class="eyebrow">{esc(cname(cc))} · Wine region</div><h1>{esc(name)}</h1><p class="lead">{esc(lead)}</p>'
                f'<a class="cta" href="/">Explore {esc(name)} on the map →</a><h2>Places in {esc(name)}</h2>' + list_node_children(k))
        write(path, page(f"{name} wine region: appellations map | Open Wine Atlas", lead[:158], path, body, [crumbs_ld(k, name, path)]))
        urls.append((path, "monthly", "0.8"))

    # ---------- country pages
    countries = []
    for root_name, kids in tree["roots"]:
        for g in kids:
            if g not in nodes:
                continue
            cc = g[2:]
            v = nodes[g]
            path = url_of[g]
            count = v[4] if len(v) > 4 else 0
            lead = (f"Every wine appellation, protected origin and named vineyard of {cname_run(cc)} in the Open Wine Atlas: {count} places "
                    f"from the official registers, with outlines, rules, grapes, terrain and climate on the map.")
            body = (crumbs_html(g) + f'<div class="eyebrow">{esc(root_name)}</div><h1>Wine map of {esc(cname(cc))}</h1><p class="lead">{esc(lead)}</p>'
                    f'<a class="cta" href="/">Open the map →</a><h2>Regions and places</h2>' + list_node_children(g))
            write(path, page(f"{cname(cc)} wine map: {count} appellations and wine regions | Open Wine Atlas", lead[:158], path, body, [crumbs_ld(g, cname(cc), path)]))
            urls.append((path, "monthly", "0.9"))
            countries.append((root_name, cc, count))

    # ---------- all places
    groups = {}
    for root_name, cc, count in countries:
        groups.setdefault(root_name, []).append((cc, count))
    body = ('<h1>All wine places</h1><p class="lead">' + f"{len(idx):,}" + " appellations, protected origins, crus and vineyard sites in "
            f"{len(countries)} countries, built from official open registers. Pick a country.</p>"
            '<a class="cta" href="/">Open the map →</a>' +
            "".join(f"<h2>{esc(g)}</h2><ul class=\"cols\">" + "".join(f"<li>{link('g:' + cc, cname(cc))}<span class=\"k\">{c}</span></li>" for cc, c in sorted(v, key=lambda x: cname(x[0])))
                    + "</ul>" for g, v in groups.items()))
    write("/places/", page("All wine places: appellations of the world by country | Open Wine Atlas",
                           f"{len(idx):,} wine appellations, protected origins, crus and vineyard sites in {len(countries)} countries, from official open registers, on one map.",
                           "/places/", body))

    # ---------- records (pipeline/records.py)
    rec_path = os.path.join(DATA, "records.json")
    if os.path.exists(rec_path):
        rec = json.load(open(rec_path, encoding="utf-8"))
        titles = {"highest": "Highest", "lowest": "Lowest", "steepest": "Steepest", "largest": "Largest", "smallest": "Smallest",
                  "wineries": "Most wineries mapped", "inland": "Farthest from the sea", "north": "Farthest north", "south": "Farthest south"}
        hints = {"highest": "mean elevation, outlines drawn on the wine area only", "lowest": "mean elevation, outlines drawn on the wine area only",
                 "steepest": "mean slope, outlines drawn on the wine area only", "largest": "area of the outline", "smallest": "measured area",
                 "wineries": "OpenStreetMap wineries inside the outline", "inland": "from the centre to the nearest sea coast",
                 "north": "latitude of the centre", "south": "latitude of the centre"}

        def rec_val(c, v):
            if c["key"] in ("north", "south"):
                return f"{abs(v):.2f}° {'S' if v < 0 else 'N'}"
            if c["unit"] == "ha":
                return f"{fmt_n(round(v / 100))} km²" if v >= 100000 else f"{fmt_n(v, 2 if v < 10 else 0)} ha"
            if c["unit"] == "°":
                return f"{v}°"
            return f"{fmt_n(v)} {c['unit']}".strip()

        def rec_block(scope, heading):
            sc = rec["scopes"].get(scope, {})
            out = []
            for c in rec["cats"]:
                rows = [x for x in sc.get(c["key"], []) if x[0] in by_id]
                if not rows:
                    continue
                out.append(f'<h3>{titles[c["key"]]}</h3><p class="note">{hints[c["key"]]}</p><ol>' + "".join(
                    f'<li>{link(pid)} <span class="k">{esc(cname(by_id[pid][2])) + " · " if scope == "ALL" else ""}{rec_val(c, v)}</span></li>' for pid, v in rows) + "</ol>")
            return f"<h2>{esc(heading)}</h2>" + "".join(out) if out else ""

        lead = ("The extremes of the wine world: the highest, steepest, largest and smallest appellations and vineyard sites, the ones "
                "farthest from the sea and farthest north and south, measured on the same open data for every place in the atlas.")
        body = ('<h1>Wine records</h1><p class="lead">' + esc(lead) + '</p><a class="cta" href="/">Open the map →</a>' + rec_block("ALL", "The whole world") +
                "".join(rec_block(cc, cname(cc)) for cc in sorted((k for k in rec["scopes"] if k != "ALL"), key=cname)) +
                '<p class="note">Regions are left out, and so are places drawn from the districts that contain them. Outlines made of whole '
                "communes include land that is not vineyard. Elevation and slope records use only outlines drawn on the wine area itself: French parcels, "
                "German vineyard sites, US AVAs and Australian subregions. Terrain: Mapterhorn. Towns: GeoNames. Coast: Natural Earth.</p>")
        write("/records/", page("Wine records: the highest, steepest and largest vineyards and appellations | Open Wine Atlas", lead[:158], "/records/", body))
        urls.append(("/records/", "weekly", "0.9"))

    # ---------- reels (pipeline/reels.py): /reels/ lists them, /r/<slug> is the short link a video points to
    reels_path = os.path.join(DATA, "reels.json")
    if os.path.exists(reels_path):
        reels = json.load(open(reels_path, encoding="utf-8"))["reels"]
        shutil.rmtree(os.path.join(HERE, "r"), ignore_errors=True)
        kind_word = {"set": "Places together", "vs": "Side by side", "place": "One place"}

        def map_link(r, source):
            return f"/?utm_source={source}&utm_medium=social&utm_campaign={r['slug']}#r:{r['slug']}"

        for r in reels:
            to = map_link(r, "reel")
            desc = ", ".join(p["name"] for p in r["places"])[:150]
            write(f"/r/{r['slug']}", f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(r['title'])} | Open Wine Atlas</title>
<meta name="robots" content="noindex">
<meta name="description" content="{esc(desc)}">
<meta property="og:site_name" content="Open Wine Atlas">
<meta property="og:title" content="{esc(r['title'])}">
<meta property="og:description" content="{esc(desc)} · on the open map of the world's wine places">
<meta name="theme-color" content="#0b0b0d">
<meta http-equiv="refresh" content="0;url={esc(to)}">
<script>location.replace({json.dumps(to)});</script>
<style>body{{margin:0;background:#0b0b0d;color:#e6dccb;font:16px/1.5 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}}a{{color:#e7c06a}}</style>
</head>
<body><p>Opening <a href="{esc(to)}">{esc(r['title'])}</a> on the map…</p></body>
</html>
""")

        def card(r):
            places = r["places"]
            def ha(p):
                return f' <span class="k">{fmt_n(p["ha"], 1 if p["ha"] < 100 else 0)} ha</span>' if p.get("ha") is not None else ""
            lst = "".join(f"<li>{esc(p['name'])}{ha(p)}</li>" for p in places) if r["kind"] != "place" else ""
            day = r["at"][:10]
            return (f'<a class="reel {r["kind"]}" href="{esc(map_link(r, "reels-page"))}" data-at="{esc(r["at"])}">'
                    f'<span class="eyebrow">{kind_word[r["kind"]]} · <time datetime="{esc(r["at"])}">{esc(day)}</time></span>'
                    f'<b>{esc(r["title"])}</b>' + (f'<ul>{lst}</ul>' if lst else "") + '<span class="go">Open on the map →</span></a>')

        lead = ("Every place from our videos, one tap from the map. Each outline comes from the official register, "
                "and the map shows it with its terrain, climate and neighbours.")
        body = ('<p class="eyebrow">From the reels</p><h1>Seen it in a video? Find it here.</h1><p class="lead">' + esc(lead) + "</p>" +
                '<div class="reels">' + "".join(card(r) for r in reels) + "</div>" +
                '<p class="note">New videos every day on Instagram, TikTok and YouTube: @openwineatlas. '
                'Areas are the delimited areas of the registers, not the vineyard planted.</p>'
                # a reel scheduled for later is already in the build: it shows from its time on
                "<script>(function(){var now=Date.now();document.querySelectorAll('.reel[data-at]').forEach(function(a){"
                "var t=Date.parse(a.dataset.at);if(t>now)a.hidden=true;else{var d=new Date(t);a.querySelector('time').textContent="
                "d.toLocaleDateString(undefined,{weekday:'short',day:'numeric',month:'short'})}})})();</script>")
        write("/reels/", page("From the reels: every place from our wine map videos | Open Wine Atlas", lead[:158], "/reels/", body))
        urls.append(("/reels/", "daily", "0.8"))

    # ---------- id -> page, for the map and the social cards
    json.dump({k: v for k, v in url_of.items() if not k.startswith("g:")}, open(os.path.join(OUT, "ids.json"), "w", encoding="utf-8"),
              separators=(",", ":"), ensure_ascii=False)

    # ---------- sitemap, robots
    today = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{SITE}{esc(u)}</loc><lastmod>{today}</lastmod><changefreq>{f}</changefreq><priority>{p}</priority></url>" for u, f, p in urls]
    sm.append("</urlset>")
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
    open(os.path.join(HERE, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"pages: {len(urls)} urls, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
