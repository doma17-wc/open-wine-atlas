"""Build the two pages of the atlas from index.src.html.

  web/index.html     static hosting with HTTP range requests (Vercel, any CDN): terrain, 3D, deep links
  web/artifact.html  the claude.ai artifact host (text files only, no outside requests): no terrain

Both inline the MapLibre stylesheet.
"""
import os
import sys

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
<meta property="og:title" content="Open Wine Atlas">
<meta property="og:description" content="Wine appellations, geographical indications, crus and single vineyards of 45 countries from open data, with terrain, climate, vintages and soil for each place.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230b0b0d'/%3E%3Cpath d='M7 22l6-9 4 5 3-4 5 8z' fill='none' stroke='%23e7c06a' stroke-width='2' stroke-linejoin='round'/%3E%3C/svg%3E">
"""

web = src.replace('const MODE = "artifact";', 'const MODE = "web";', 1)
assert web != src, "MODE marker not found"
web = HEAD + web.replace('<div id="map"', '</head>\n<body>\n<div id="map"', 1) + "\n</body>\n</html>\n"
open(os.path.join(here, "index.html"), "w", encoding="utf-8").write(web)
open(os.path.join(here, "artifact.html"), "w", encoding="utf-8").write(src)
for f in ("index.html", "artifact.html"):
    print(f, os.path.getsize(os.path.join(here, f)))
