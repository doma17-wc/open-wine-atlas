"""Build the two pages of the atlas from index.src.html.

  web/index.html     static hosting with HTTP range requests (Vercel, any CDN): terrain, 3D, deep links
  web/artifact.html  the claude.ai artifact host (text files only, no outside requests): no terrain

Both inline the MapLibre stylesheet.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

here = os.path.dirname(os.path.abspath(__file__))
css_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "maplibre-gl.css")
css = open(css_path, encoding="utf-8").read()
src = open(os.path.join(here, "index.src.html"), encoding="utf-8").read().replace("/*MAPLIBRE_CSS*/", css)

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b0b0d">
<title>Open Wine Atlas: map of the world's wine appellations</title>
<meta name="description" content="Open map of the world's wine appellations, crus and vineyards: {N_PLACES} places in {N_COUNTRIES} countries with official outlines, grape rules, terrain and vintages.">
<link rel="canonical" href="https://www.openwineatlas.com/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Open Wine Atlas">
<meta property="og:url" content="https://www.openwineatlas.com/">
<meta property="og:title" content="Open Wine Atlas: map of the world's wine appellations">
<meta property="og:description" content="Wine appellations, geographical indications, crus and single vineyards of {N_COUNTRIES} countries from official registers, with terrain, climate, vintages and soil for each place.">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">{LD}</script>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230b0b0d'/%3E%3Cpath d='M7 22l6-9 4 5 3-4 5 8z' fill='none' stroke='%23e7c06a' stroke-width='2' stroke-linejoin='round'/%3E%3C/svg%3E">
<!-- Vercel Web Analytics -->
<script>window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };</script>
<script defer src="/_vercel/insights/script.js"></script>
"""

# the web page takes its title and description from HEAD; the artifact keeps the ones in index.src.html
import json  # noqa: E402
import re  # noqa: E402
_idx = json.load(open(os.path.join(here, "data", "search.json"), encoding="utf-8"))
HEAD = (HEAD.replace("{N_PLACES}", f"{len(_idx):,}").replace("{N_COUNTRIES}", str(len({r[2] for r in _idx})))
        .replace("{LD}", json.dumps({"@context": "https://schema.org", "@graph": [
            {"@type": "WebSite", "@id": "https://www.openwineatlas.com/#website", "url": "https://www.openwineatlas.com/",
             "name": "Open Wine Atlas", "inLanguage": "en", "publisher": {"@id": "https://www.openwineatlas.com/#org"}},
            {"@type": "Organization", "@id": "https://www.openwineatlas.com/#org", "name": "Open Wine Atlas",
             "url": "https://www.openwineatlas.com/", "email": "hello@openwineatlas.com",
             "sameAs": ["https://www.instagram.com/openwineatlas/", "https://www.pinterest.com/openwineatlas/"]}]}, ensure_ascii=False)))
web_src, n_head = re.subn(r"\A<title>.*?</title>\n<meta name=\"description\"[^>]*>\n", "", src, count=1)
assert n_head == 1, "title and description at the top of index.src.html not found"
web = web_src.replace('const MODE = "artifact";', 'const MODE = "web";', 1)
assert web != web_src, "MODE marker not found"
# data version: a short hash of every file in web/data, so a release with new data gets new addresses and
# browsers that cached the old tiles or place files for hours load the new ones at once
import hashlib  # noqa: E402
h = hashlib.sha256()
data_dir = os.path.join(here, "data")
for name in sorted(os.listdir(data_dir)):
    fp = os.path.join(data_dir, name)
    if os.path.isfile(fp):
        h.update(name.encode())
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
data_v = h.hexdigest()[:10]
web2 = web.replace('const DATA_V = "dev";', 'const DATA_V = "' + data_v + '";', 1)
assert web2 != web, "DATA_V marker not found"
web = web2
print("data version", data_v)
web = HEAD + web.replace('<div id="map"', '</head>\n<body>\n<div id="map"', 1) + "\n</body>\n</html>\n"
open(os.path.join(here, "index.html"), "w", encoding="utf-8").write(web)
open(os.path.join(here, "artifact.html"), "w", encoding="utf-8").write(src)
for f in ("index.html", "artifact.html"):
    print(f, os.path.getsize(os.path.join(here, f)))

# static pages for search engines and sharing (one per place, region and country) and the sitemap
import build_pages  # noqa: E402
build_pages.main()
