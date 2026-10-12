"""Weekly social card: pick the next wine place, render a 1080x1350 image of it from the atlas, draft the caption.

    python3 pipeline/social_card.py --out DIR [--posted posted.json] [--id PLACE_ID] [--libs DIR]

Writes DIR/<id>.png and DIR/<id>.json (facts and a caption draft) and prints the json path.

The map is the real atlas (web/index.html) served from this checkout, with the interface hidden and a title and
facts laid over it. Only the atlas' own data files are used, so it renders without internet access apart from
npm (MapLibre, PMTiles and the atlas fonts are installed into --libs on first use). Outside tiles (terrain,
satellite) are skipped, which gives the dark Atlas look.

Places come from those with an editorial note (atlas_note), countries taken in turn, skipping ids in --posted.
"""
import argparse
import asyncio
import functools
import http.server
import json
import os
import re
import subprocess
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
NPM = ["maplibre-gl@5.24.0", "pmtiles@4.5.0", "@fontsource/cormorant-garamond@5", "@fontsource/ibm-plex-sans@5", "@fontsource/ibm-plex-mono@5"]
RANK = {"grand_cru": "Grand cru", "premier_cru": "Premier cru", "docg": "DOCG", "doca": "DOCa", "pago": "Vino de Pago"}
W, H = 1080, 1350


def load():
    idx = json.load(open(os.path.join(WEB, "data", "search.json"), encoding="utf-8"))
    det = {}
    for f in os.listdir(os.path.join(WEB, "data")):
        if re.match(r"details-\w\w\.json$", f):
            det.update(json.load(open(os.path.join(WEB, "data", f), encoding="utf-8")))
    src = open(os.path.join(WEB, "index.src.html"), encoding="utf-8").read()
    cn = dict(re.findall(r'(\w\w): "([^"]+)"', re.search(r"const COUNTRY_EN = \{(.*?)\};", src, re.S).group(1)))
    pages = json.load(open(os.path.join(WEB, "places", "ids.json"), encoding="utf-8"))
    return idx, det, cn, pages


def pick(idx, det, posted):
    cands = [r for r in idx if det.get(r[1], {}).get("atlas_note") and r[1] not in posted]
    if not cands:
        return None
    # countries in turn, starting with the one posted least; famous ranks first within a country
    done = {}
    for p in posted:
        cc = p.split("-")[0].upper()
        done[cc] = done.get(cc, 0) + 1
    by_cc = {}
    for r in cands:
        by_cc.setdefault(r[2], []).append(r)
    cc = min(by_cc, key=lambda c: (done.get(c, 0), -len(by_cc[c]), c))
    top = lambda r: (0 if r[4] in ("grand_cru", "docg", "doca", "pago") else 1 if r[4] == "premier_cru" else 2, r[0])
    return sorted(by_cc[cc], key=top)[0]


def grape_name(g):
    m = re.match(r"^(.*?)\s+(N|B|G|Rs|Rg)$", str(g).strip())
    return m.group(1) if m else str(g).strip()


def facts_for(r, d):
    out = []
    area = d.get("area_ha") or d.get("outline_area_ha")
    if area:
        out.append(("Area", f"{float(area):,.0f} ha"))
    mains = list(dict.fromkeys(grape_name(g) for w in d.get("wines") or [] for g in w.get("main") or []))
    if not mains and d.get("grapes") and d["grapes"] != "na":
        mains = [grape_name(g) for g in re.split(r"\s*[,/]\s*", d["grapes"])]
    if mains:
        out.append(("Grapes", ", ".join(mains[:4]) + (" and more" if len(mains) > 4 else "")))
    if d.get("registered"):
        out.append(("Protected since", d["registered"][:4]))
    elif d.get("max_yield_hl_ha") not in (None, "na"):
        out.append(("Max yield", f"{d['max_yield_hl_ha']} hl/ha"))
    if d.get("bedrock") and len(out) < 3:
        out.append(("Bedrock", re.sub(r" \(.*\)", "", d["bedrock"][0][0])))
    if d.get("communes") and len(out) < 3:
        out.append(("Communes", str(len(d["communes"]))))
    return out[:3]


def caption(r, d, cname, page):
    name, cc = r[0], r[2]
    typ = RANK.get(r[4]) or re.sub(r"\s*\(.*\)\s*$", "", d.get("type", "")) or "wine region"
    lines = [f"{name} · {cname}", "", d.get("atlas_note", "").strip(), ""]
    f = facts_for(r, d)
    if f:
        lines += [f"{k}: {v}" for k, v in f] + [""]
    lines += ["Explore the official outline, terrain, climate and vintages on the Open Wine Atlas. Link in bio.",
              f"openwineatlas.com{page}", ""]
    tag = lambda s: "#" + re.sub(r"[^A-Za-z0-9]", "", s if s.isupper() else s.title())
    tags = ["#wine", "#winemap", "#terroir", "#wset", "#sommelier", tag(name), tag(cname)] + ([tag(typ)] if len(typ) <= 12 else [])
    lines.append(" ".join(dict.fromkeys(t for t in tags if len(t) > 2)))
    return "\n".join(lines)


def ensure_libs(libs):
    need = not all(os.path.isdir(os.path.join(libs, "node_modules", p.rsplit("@", 1)[0])) for p in NPM)
    if need:
        os.makedirs(libs, exist_ok=True)
        subprocess.run(["npm", "i", "--silent", "--no-audit", "--no-fund", "--prefix", libs, *NPM], check=True)
    return os.path.join(libs, "node_modules")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_head(self):
        # HTTP range requests, which PMTiles needs
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        a, b = re.match(r"bytes=(\d+)-(\d*)", rng).groups()
        a, b = int(a), min(int(b) if b else size - 1, size - 1)
        f = open(path, "rb")
        f.seek(a)
        self.send_response(206)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
        self.send_header("Content-Length", str(b - a + 1))
        self.end_headers()
        self._left = b - a + 1
        return f

    def copyfile(self, src, dst):
        left = getattr(self, "_left", None)
        if left is None:
            return super().copyfile(src, dst)
        while left > 0:
            buf = src.read(min(65536, left))
            if not buf:
                break
            dst.write(buf)
            left -= len(buf)


def overlay_html(r, d, cname, fonts):
    esc = lambda s: (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    typ = RANK.get(r[4]) or re.sub(r"\s*\(.*\)\s*$", "", d.get("type", "")) or ""
    face = lambda fam, w, f: f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('/__fonts/{f}') format('woff2')}}"
    css = (face("Cormorant Garamond", 600, "cormorant-garamond/files/cormorant-garamond-latin-600-normal.woff2") +
           face("IBM Plex Sans", 400, "ibm-plex-sans/files/ibm-plex-sans-latin-400-normal.woff2") +
           face("IBM Plex Sans", 500, "ibm-plex-sans/files/ibm-plex-sans-latin-500-normal.woff2") +
           face("IBM Plex Mono", 500, "ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2") + """
      .rail,.sheet,.viewbar,.attrib,.mcrumbs,.showpanels,.maplibregl-control-container,.loading,.tag,.readout,#dash,.modal{display:none!important}
      #card{position:fixed;inset:0;pointer-events:none;z-index:50;font-family:'IBM Plex Sans';color:#e6dccb}
      #card .top{position:absolute;left:0;right:0;top:0;padding:72px 80px 140px;background:linear-gradient(#0b0b0d 0%,rgba(11,11,13,.92) 55%,rgba(11,11,13,0))}
      #card .eb{font:500 24px 'IBM Plex Mono';letter-spacing:.16em;text-transform:uppercase;color:#a39b8e}
      #card h1{font:600 112px/0.98 'Cormorant Garamond';margin:18px 0 0;letter-spacing:.005em;text-wrap:balance}
      #card .rk{display:inline-block;margin-top:22px;padding:6px 16px;border:1.5px solid #e7c06a;color:#e7c06a;border-radius:999px;font:500 22px 'IBM Plex Mono'}
      #card .bot{position:absolute;left:0;right:0;bottom:0;padding:170px 80px 70px;background:linear-gradient(rgba(11,11,13,0),rgba(11,11,13,.94) 40%,#0b0b0d)}
      #card .f{display:grid;grid-template-columns:250px 1fr;gap:14px 24px;font-size:30px;line-height:1.3}
      #card .f dt{color:#8d877c;font-size:24px;padding-top:4px}#card .f dd{margin:0}
      #card .ft{display:flex;justify-content:space-between;align-items:baseline;margin-top:44px;padding-top:24px;border-top:1px solid #2a2a31}
      #card .ft b{font:600 40px 'Cormorant Garamond'}#card .ft span{font:500 22px 'IBM Plex Mono';color:#a39b8e;letter-spacing:.06em}
    """)
    rank = f'<div class="rk">{esc(RANK[r[4]])}</div>' if r[4] in RANK else ""
    facts = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in facts_for(r, d))
    return css, (f'<div class="top"><div class="eb">{esc(cname)}{" · " + esc(typ) if typ else ""}</div><h1>{esc(r[0])}</h1>{rank}</div>'
                 f'<div class="bot"><dl class="f">{facts}</dl><div class="ft"><b>Open Wine Atlas</b><span>openwineatlas.com</span></div></div>')


async def render(r, d, cname, out_png, libs):
    from playwright.async_api import async_playwright
    nm = ensure_libs(libs)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=WEB))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    css, body = overlay_html(r, d, cname, nm)
    b = r[6]
    try:
        async with async_playwright() as p:
            exe = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
            br = await p.chromium.launch(executable_path=exe if os.path.exists(exe) else None,
                                         args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
            pg = await br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)

            async def cdn(route):
                u = route.request.url
                f = os.path.join(nm, "maplibre-gl/dist/maplibre-gl.js") if "maplibre-gl" in u else os.path.join(nm, "pmtiles/dist/pmtiles.js")
                await route.fulfill(path=f, content_type="text/javascript")

            async def fonts(route):
                await route.fulfill(path=os.path.join(nm, "@fontsource", route.request.url.split("/__fonts/", 1)[1]), content_type="font/woff2")

            await pg.route("https://cdn.jsdelivr.net/**", cdn)
            await pg.route("**/__fonts/**", fonts)
            await pg.route(lambda u: not u.startswith(f"http://127.0.0.1:{port}") and "jsdelivr" not in u, lambda rt: rt.abort())
            # flat map, Atlas look, English, no intro flight
            await pg.add_init_script("try{localStorage.setItem('owa.proj','flat');localStorage.setItem('owa.base','dark');localStorage.setItem('owa.lang','en')}catch(e){}")
            await pg.goto(f"http://127.0.0.1:{port}/index.html#{r[1]}")
            await pg.wait_for_function("window.__map && window.__map.loaded() && document.getElementById('loading').hidden", timeout=90000)
            await pg.wait_for_timeout(2500)
            await pg.add_style_tag(content=css)
            await pg.evaluate("(h) => { const c = document.createElement('div'); c.id = 'card'; c.innerHTML = h; document.body.appendChild(c); }", body)
            await pg.evaluate("""(b) => { const m = window.__map; m.setPadding({top:0,bottom:0,left:0,right:0});
                m.fitBounds([[b[0],b[1]],[b[2],b[3]]], {padding:{top:380,bottom:430,left:110,right:110}, maxZoom:13.5, duration:0}); }""", b)
            idle = "() => new Promise((res) => { const m = window.__map; const t = setTimeout(res, 20000); m.once('idle', () => { clearTimeout(t); res(); }); m.triggerRepaint(); })"
            await pg.evaluate(idle)
            # parcel-level files load after the move: give them time, then hide winery dots and names for a clean card
            await pg.wait_for_timeout(3000)
            await pg.wait_for_function("document.getElementById('loading').hidden", timeout=60000)
            await pg.evaluate("() => { const m = window.__map; ['wineries', 'winery-labels'].forEach((l) => m.getLayer(l) && m.setLayoutProperty(l, 'visibility', 'none')); }")
            await pg.evaluate(idle)
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(1200)
            await pg.screenshot(path=out_png)
            await br.close()
    finally:
        srv.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--posted", default="")
    ap.add_argument("--id", default="")
    ap.add_argument("--libs", default=os.path.join(ROOT, "build", "social-libs"))
    a = ap.parse_args()
    idx, det, cn, pages = load()
    posted = json.load(open(a.posted)) if a.posted and os.path.exists(a.posted) else []
    posted_ids = [p["id"] if isinstance(p, dict) else p for p in posted]
    r = next((x for x in idx if x[1] == a.id), None) if a.id else pick(idx, det, posted_ids)
    if not r:
        raise SystemExit("no place left to post")
    d = det.get(r[1], {})
    cname = re.sub(r"^the ", "", cn.get(r[2], r[2]))
    os.makedirs(a.out, exist_ok=True)
    png = os.path.join(a.out, r[1] + ".png")
    asyncio.run(render(r, d, cname, png, a.libs))
    page = pages.get(r[1], "/")
    info = {"id": r[1], "name": r[0], "country": cname, "level": r[3], "rank": r[4], "parent": r[5], "image": png,
            "page": "https://openwineatlas.com" + page, "map": f"https://openwineatlas.com/#{r[1]}",
            "atlas_note": d.get("atlas_note", ""), "facts": facts_for(r, d), "caption_draft": caption(r, d, cname, page)}
    jp = os.path.join(a.out, r[1] + ".json")
    json.dump(info, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(jp)


if __name__ == "__main__":
    main()
