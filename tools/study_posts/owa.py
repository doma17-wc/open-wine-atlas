"""Shared helpers for the study post tools: a local server for the atlas, a headless Chromium with the map
libraries served from a local folder, map renders of a place, and HTML to JPEG for the cards.

Nothing here is tied to one machine: the atlas checkout (--repo), the library folder (--libs) and Chromium
(OWA_CHROME, else Playwright's own) are all passed in.
"""
import base64
import functools
import glob
import http.server
import json
import os
import re
import subprocess
import sys
import threading

DEFAULT_CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
NPM = ["maplibre-gl@5.24.0", "pmtiles@4.5.0"]
NIGHT, PARCH, GOLD, MUTED, LINE = "#0b0b0d", "#e6dccb", "#e7c06a", "#a39b8e", "#2a2a31"


# ---------- data
class Atlas:
    def __init__(self, repo):
        self.repo = os.path.abspath(repo)
        self.web = os.path.join(self.repo, "web")
        d = os.path.join(self.web, "data")
        self.study = json.load(open(os.path.join(d, "study.json"), encoding="utf-8"))
        self.index = {r[1]: r for r in json.load(open(os.path.join(d, "search.json"), encoding="utf-8"))}
        self.questions = {}  # "<lesson id>#<question id>" -> (path, lesson, question)
        for p in self.study["paths"]:
            for l in p["lessons"]:
                for q in l["questions"]:
                    self.questions[l["id"] + "#" + q["id"]] = (p, l, q)

    def q(self, key):
        if key not in self.questions:
            raise SystemExit(f"unknown question {key}: use <lesson id>#<question id>, e.g. bourgogne-overview#q1")
        return self.questions[key]

    def path(self, pid):
        for p in self.study["paths"]:
            if p["id"] == pid:
                return p
        raise SystemExit(f"unknown path {pid}")

    def fonts_css(self, libs=None):
        """The atlas fonts as inline @font-face rules: @fontsource packages in --libs (installed with npm if missing;
        they position accents correctly), else the TTF files in api/fonts."""
        css = fontsource_css(libs) if libs else ""
        if css:
            return css
        f = os.path.join(self.repo, "api", "fonts")
        face = lambda fam, w, st, fn: ("@font-face{font-family:'%s';font-weight:%s;font-style:%s;src:url(data:font/ttf;base64,%s) format('truetype')}"
                                       % (fam, w, st, base64.b64encode(open(os.path.join(f, fn), "rb").read()).decode()))
        return (face("Cormorant Garamond", 500, "normal", "CormorantGaramond-Medium.ttf") +
                face("Cormorant Garamond", 500, "italic", "CormorantGaramond-MediumItalic.ttf") +
                face("IBM Plex Sans", 400, "normal", "IBMPlexSans-Regular.ttf") +
                face("IBM Plex Mono", 400, "normal", "IBMPlexMono-Regular.ttf") +
                face("IBM Plex Mono", 500, "normal", "IBMPlexMono-Medium.ttf"))


FONTS = [("cormorant-garamond", ["500", "500-italic"]), ("ibm-plex-sans", ["400"]), ("ibm-plex-mono", ["400", "500"])]


def fontsource_css(libs):
    base = os.path.join(libs, "node_modules", "@fontsource")
    if not all(os.path.isdir(os.path.join(base, p)) for p, _ in FONTS):
        try:
            os.makedirs(libs, exist_ok=True)
            subprocess.run(["npm", "i", "--silent", "--no-audit", "--no-fund", "--prefix", libs] + [f"@fontsource/{p}@5" for p, _ in FONTS], check=True)
        except Exception as e:  # no npm or no network: fall back to api/fonts
            print("fontsource not available:", e, file=sys.stderr)
            return ""
    out = []
    for pkg, files in FONTS:
        for w in files:
            css = open(os.path.join(base, pkg, w + ".css"), encoding="utf-8").read()
            for block in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S):
                name, rule = block
                if not re.search(r"-latin(-ext)?-", name):
                    continue
                woff2 = re.search(r"url\(\./files/([^)]+\.woff2)\)", rule).group(1)
                data = base64.b64encode(open(os.path.join(base, pkg, "files", woff2), "rb").read()).decode()
                rule = re.sub(r"src:[^;]+;", f"src:url(data:font/woff2;base64,{data}) format('woff2');", rule)
                out.append(rule.replace("font-display: swap;", ""))
    return "".join(out)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def data_uri(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


# ---------- libraries
def lib_file(libs, pkg, rel):
    """maplibre-gl / pmtiles from --libs: node_modules/<pkg>/... or <pkg>-<version>/... (unpacked npm tarball)."""
    for c in [os.path.join(libs, "node_modules", pkg, rel)] + sorted(glob.glob(os.path.join(libs, pkg + "-*", rel))) + \
             sorted(glob.glob(os.path.join(libs, pkg + "-*", "package", rel))):
        if os.path.isfile(c):
            return c
    os.makedirs(libs, exist_ok=True)
    subprocess.run(["npm", "i", "--silent", "--no-audit", "--no-fund", "--prefix", libs, *NPM], check=True)
    return os.path.join(libs, "node_modules", pkg, rel)


# ---------- local server with HTTP range requests (PMTiles needs them)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):  # the browser dropped a tile request it no longer needs
            pass

    def do_GET(self):
        # /api/pair (the "Drawn at the same scale" picture) is a serverless function on the live site: run it with node
        if self.path.startswith("/api/pair") and getattr(self, "pair", None):
            try:
                svg = self.pair(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
                self.send_header("Content-Length", str(len(svg)))
                self.end_headers()
                self.wfile.write(svg)
            except Exception as e:
                print("api/pair failed:", e, file=sys.stderr)
                self.send_error(500)
            return
        return super().do_GET()

    def send_head(self):
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


PAIR_RUNNER = """import handler from "./pair.mjs";
const res = { statusCode: 200, setHeader() {}, end(b) { process.stdout.write(b); process.exitCode = this.statusCode === 200 ? 0 : 1; } };
await handler({ url: process.argv[2] }, res);
"""


def pair_runner(repo, libs):
    """api/pair.mjs run with node from --libs (its packages pmtiles, @mapbox/vector-tile and pbf are installed there)."""
    if not all(os.path.isdir(os.path.join(libs, "node_modules", p)) for p in ["pmtiles", "@mapbox/vector-tile", "pbf"]):
        subprocess.run(["npm", "i", "--silent", "--no-audit", "--no-fund", "--prefix", libs, "pmtiles@4.5.0", "@mapbox/vector-tile@2", "pbf@4"], check=True)
    import shutil
    shutil.copy(os.path.join(repo, "api", "pair.mjs"), os.path.join(libs, "pair.mjs"))
    open(os.path.join(libs, "pair-run.mjs"), "w").write(PAIR_RUNNER)

    def run(url):
        out = subprocess.run(["node", os.path.join(libs, "pair-run.mjs"), url], cwd=repo, capture_output=True, timeout=120)
        if out.returncode:
            raise RuntimeError(out.stderr.decode()[-400:])
        return out.stdout
    return run


def serve(web, pair=None):
    handler = type("Handler", (Quiet,), {"pair": staticmethod(pair)} if pair else {})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(handler, directory=web))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


async def launch(p):
    exe = os.environ.get("OWA_CHROME") or (DEFAULT_CHROME if os.path.exists(DEFAULT_CHROME) else None)
    return await p.chromium.launch(executable_path=exe, args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])


async def atlas_page(br, base, libs, width, height, scale=1, mobile=False, storage=None, supabase_stub=None):
    """A page of the atlas with the CDN libraries served from --libs and every other outside request blocked.
    storage: localStorage entries set before the atlas starts (keys without the 'owa.' prefix)."""
    kw = dict(viewport={"width": width, "height": height}, device_scale_factor=scale)
    if mobile:
        kw.update(is_mobile=True, has_touch=True)
    pg = await br.new_page(**kw)
    ml, pm = lib_file(libs, "maplibre-gl", "dist/maplibre-gl.js"), lib_file(libs, "pmtiles", "dist/pmtiles.js")

    async def route(rt):
        u = rt.request.url
        if u.startswith(base):
            return await rt.continue_()
        if "jsdelivr" in u and "maplibre-gl" in u and u.endswith(".js"):
            return await rt.fulfill(path=ml, content_type="text/javascript")
        if "jsdelivr" in u and "pmtiles" in u:
            return await rt.fulfill(path=pm, content_type="text/javascript")
        if supabase_stub and "supabase" in u and u.endswith(".js"):
            return await rt.fulfill(path=supabase_stub, content_type="text/javascript")
        return await rt.abort()

    await pg.route("**/*", route)
    st = {"proj": "flat", "base": "dark", "lang": "en"}
    st.update(storage or {})
    js = ";".join("localStorage.setItem(%s,%s)" % (json.dumps("owa." + k), json.dumps(v if isinstance(v, str) else json.dumps(v))) for k, v in st.items())
    await pg.add_init_script("try{" + js + "}catch(e){}")
    return pg


async def wait_atlas(pg, extra=2000):
    await pg.wait_for_function("window.__map && window.__map.loaded() && document.getElementById('loading').hidden", timeout=120000)
    await pg.wait_for_timeout(extra)


IDLE = "() => new Promise((res) => { const m = window.__map; const t = setTimeout(res, 20000); m.once('idle', () => { clearTimeout(t); res(); }); m.triggerRepaint(); })"
HIDE_UI = (".rail,.sheet,.viewbar,.attrib,.mcrumbs,.showpanels,.maplibregl-control-container,.loading,.tag,.readout,#dash,.modal,.quiz,"
           ".relief-btn,.mapsel,.toast{display:none!important}")


async def map_png(br, base, libs, atlas, place_id, out_png, width, height, pad=80):
    """The real atlas map at a place, interface hidden, the place outlined in gold."""
    r = atlas.index[place_id]
    pg = await atlas_page(br, base, libs, width, height)
    await pg.goto(f"{base}/index.html#{place_id}")
    await wait_atlas(pg, 2500)
    await pg.add_style_tag(content=HIDE_UI)
    await pg.evaluate("""([b, p]) => { const m = window.__map; m.setPadding({top:0,bottom:0,left:0,right:0});
        m.fitBounds([[b[0],b[1]],[b[2],b[3]]], {padding:p, maxZoom:13.5, duration:0}); }""", [r[6], pad])
    await pg.evaluate("(id) => { try { window.OWA && window.OWA.markSelected(id); } catch (e) {} }", place_id)
    await pg.evaluate(IDLE)
    await pg.wait_for_timeout(3000)
    await pg.wait_for_function("document.getElementById('loading').hidden", timeout=60000)
    await pg.evaluate("() => { const m = window.__map; ['wineries', 'winery-labels'].forEach((l) => m.getLayer(l) && m.setLayoutProperty(l, 'visibility', 'none')); }")
    await pg.evaluate(IDLE)
    await pg.wait_for_timeout(1200)
    await pg.screenshot(path=out_png)
    await pg.close()


async def html_jpg(br, html, out_jpg, width, height, quality=90):
    pg = await br.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
    await pg.route("**/*", lambda rt: rt.abort() if not rt.request.url.startswith("data:") else rt.continue_())
    await pg.set_content(html)
    await pg.evaluate("document.fonts.ready")
    await pg.wait_for_timeout(300)
    # report text that runs out of its box, so a bad card is caught before it is posted
    over = await pg.evaluate("""() => [...document.querySelectorAll('[data-fit]')].filter(e => e.scrollHeight > e.clientHeight + (e.dataset.strict ? 2 : 20) || e.scrollWidth > e.clientWidth + 2).map(e => e.dataset.fit + ' ' + e.scrollWidth + 'x' + e.scrollHeight + ' in ' + e.clientWidth + 'x' + e.clientHeight)""")
    await pg.screenshot(path=out_jpg, type="jpeg", quality=quality)
    await pg.close()
    if os.path.getsize(out_jpg) > 1_450_000 and quality > 70:
        return await html_jpg(br, html, out_jpg, width, height, quality - 8)
    return over


def page_css(atlas, w, h, libs=None):
    return atlas.fonts_css(libs) + f"""
*{{box-sizing:border-box}}html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden;font-variant-numeric:lining-nums;background:{NIGHT};color:{PARCH};font-family:'IBM Plex Sans',sans-serif}}
.eb{{font:500 26px 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:{MUTED}}}
.gold{{color:{GOLD}}}
.foot{{position:absolute;left:80px;right:80px;bottom:56px;display:flex;justify-content:space-between;align-items:baseline;padding-top:22px;border-top:1px solid {LINE}}}
.foot b{{font:500 38px 'Cormorant Garamond',serif}}.foot span{{font:400 24px 'IBM Plex Mono',monospace;color:{MUTED};letter-spacing:.06em}}
"""


def foot(left="Open Wine Atlas", right="openwineatlas.com"):
    return f'<div class="foot"><b>{esc(left)}</b><span>{esc(right)}</span></div>'
