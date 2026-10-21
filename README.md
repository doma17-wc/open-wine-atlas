# Open Wine Atlas

An open, interactive atlas of wine places: appellations, geographical indications, crus, climats and
single vineyards. It covers 45 countries on six continents: all 21 EU wine countries, Switzerland, the United
States, and since October 2026 Australia, New Zealand, South Africa, South America, Canada, Mexico, the Caucasus,
the Balkans, the Middle East and Asia. It is built only from data published under open licences, so anyone can
check it, reuse it and extend it.

Live: https://open-wine-atlas.vercel.app

## What is in it (v0.2, October 2026)

| Country | Detail | Source | Licence |
|---|---|---|---|
| France | Every AOC at parcel level, plus premiers crus, grand cru climats and other complementary names (356 appellations, 916 dénominations) | INAO, Délimitation parcellaire des AOC viticoles, 2026-08-31 | Licence Ouverte 2.0 |
| Italy | 408 DOC/DOCG outlines (by commune), 73 flagged DOCG | Candiago et al. 2022, EU wine PDO inventory | CC BY 4.0 |
| Spain | 99 DO/DOCa/Vino de Pago outlines (by commune) | Candiago et al. 2022 | CC BY 4.0 |
| Germany | 13 Anbaugebiete and 6 single-site PDOs; 1,586 Einzellagen and 84 Großlagen for Mosel, Rheinhessen, Pfalz, Nahe, Mittelrhein and Ahr | Candiago et al. 2022; Landwirtschaftskammer Rheinland-Pfalz | CC BY 4.0; dl-de/by-2-0 |
| 17 more EU countries | 337 PDO outlines: Austria, Portugal, Greece, Hungary, Romania, Bulgaria, Croatia, Slovenia, Czechia, Slovakia, Belgium, Cyprus, the Netherlands, UK, Malta, Denmark, Luxembourg | Candiago et al. 2022 | CC BY 4.0 |
| United States | 276 AVAs with legal text, hierarchy, states and counties | UC Davis Library AVA project (27 CFR part 9) | CC0 1.0 |
| Switzerland | 13 cantonal AOC outlines (canton boundary), OSM vineyard areas | BFS GEOSTAT / swisstopo; OpenStreetMap | Open use with attribution; ODbL |
| Australia | 100 GIs: zones, regions, subregions; the 14 subregions from the official Wine Australia layer, the rest via adynak/WineRegions; Tasmania from the state outline | Wine Australia; geoBoundaries | CC BY 4.0 (Wine Australia) |
| Chile | 117 DOs: 6 regions, 18 subregions, 8 zones, areas, by comuna | Decreto 464/1994 (consolidated 2026) + geoBoundaries CHL ADM3 | CC BY 3.0 IGO |
| Argentina | 100 IGs and both DOCs, by department; 14 parajes as markers | INV resolutions (list of 18 April 2024 plus 2025) + geoBoundaries ARG ADM2 | CC BY 3.0 IGO |
| South Africa | 56 Wine of Origin units: geographical units, regions, districts, wards | Wine of Origin Scheme + geoBoundaries ZAF ADM1/ADM3 | CC BY 3.0 IGO |
| New Zealand, Brazil, Uruguay, Canada, Mexico | 75 GIs, IPs, DOs, VQA areas and regions | IPONZ, INPI, INAVI, VQA Ontario, BC VQA + geoBoundaries | per country, see DATA_LICENSE.md |
| Georgia, Moldova, Ukraine, Armenia, Türkiye, Israel, Lebanon, Serbia, North Macedonia, Montenegro, Bosnia and Herzegovina | 98 PDOs, IGPs and regions | Sakpatenti, AGEPI, Ukrainepatent, national wine laws + geoBoundaries | per country |
| Japan, China, India | 12 GIs and regions | National Tax Agency (JP), EU-China GI agreement, Indian GI registry + geoBoundaries | per country |
| All | About 9,600 wineries in 44 countries | OpenStreetMap via openwinemap | ODbL |
| All | Vineyards on the map (zoom 9 and more) and the planted area of each place, measured live inside its outline | OpenStreetMap `landuse=vineyard` via OpenFreeMap vector tiles (OpenMapTiles landcover) | ODbL; CC BY 4.0 |
| France, Italy | Per-wine rules: colour, category, main and secondary grapes, yields, density | EU specifications compiled by Candiago et al. 2022 (via pdo-wine-data) | CC BY 4.0 |
| All | Regional bedrock per place | GLiM, Hartmann & Moosdorf 2012 | CC BY 3.0 |
| All | About 33,000 producers and 185,000 wines, each placed on the site, appellation or region its record names | LWIN database, Liv-ex | CC BY 4.0 |
| All | 151 editorial notes | Open Wine Atlas contributors | CC BY 4.0 |
| All | Nearest town and city with distance and direction, distance to the sea, rivers and lakes nearby, latitude twins on other continents | GeoNames cities5000; Natural Earth 1:10m coastline, rivers, lakes | CC BY 4.0; public domain |
| All | Named rivers, lakes, mountain ranges and peaks on the map, each one can be highlighted | Natural Earth 1:10m rivers, lakes and physical regions | Public domain |
| All | Towns of 5,000 people or more on the map | GeoNames cities5000 | CC BY 4.0 |
| All | Close up (zoom 9 and more): small rivers, streams, lakes, villages and peaks, read live | OpenStreetMap via OpenFreeMap vector tiles (OpenMapTiles schema) | ODbL; CC BY 4.0 |
| All | Elevation, slope and aspect of every outline, measured ahead of time (for records, pages and when the live measurement cannot run) | Mapterhorn terrain tiles | Open licences, see mapterhorn.com/attribution |
| All | Relief, 3D terrain, and per place elevation, slope and aspect (measured live in the browser) | Mapterhorn terrain tiles: IGN RGE ALTI, German DGM1, swissALTI3D, IGN MDT, Copernicus GLO-30 | Open licences, see mapterhorn.com/attribution |

## Where it is, terrain and records

`pipeline/context.py` adds to every place the nearest town (5,000 people or more) and city (30,000 or more) with
distance and compass direction, the distance from its centre to the sea, the named rivers and lakes nearby and up to
five wine places on other continents at the same latitude (±0.35°). The sheet shows them under *Where it is*, and
the opening sentence of a small place says where it lies ("It lies 2.7 km north of Nuits-Saint-Georges and 18 km
south-south-west of Dijon").

`pipeline/terrain_stats.py` measures elevation, slope and aspect for every outline ahead of time, the same way the
map does live (Mapterhorn tiles, Sobel slope, aspect as the direction the ground faces). The sheet uses these figures
when the live measurement covers only part of the place or cannot run; the static pages print them.

`pipeline/records.py` turns both into `web/data/records.json`: the ten highest, lowest, steepest, largest and smallest
places, the ones with the most wineries, farthest from the sea and farthest north and south, for the world and for
each country. My atlas › Records shows them, and so does the static page `/records/`.

```bash
python pipeline/context.py && python pipeline/terrain_stats.py && python pipeline/records.py && python web/build_web.py
```

## Vineyard area

An outline is the legal or administrative area of a place. In Italy, Spain and most countries it is built from whole
communes or districts, so it also takes in woods, villages and fields. The sheet therefore shows the **vineyard area**:
the land inside the outline that OpenStreetMap maps as vineyard. The web page measures it in the browser, like the
terrain: it reads the OpenFreeMap tiles over the outline (landcover, subclass `vineyard`), draws the outline and the
vineyards on two canvases and adds up the pixels both cover, each weighted by its true area at that latitude. It uses
zoom 14, where every vineyard is in the tiles, as long as the outline touches at most 96 tiles, then zoom 13 and 12
(96 tiles each). Below zoom 14 OpenFreeMap (Planetiler, OpenMapTiles profile) leaves out polygons smaller than a
square of 8 px of a 256 px tile, about 1 ha at zoom 13 and 4 ha at zoom 12 in Burgundy, so the sheet then says the
figure is a minimum and from what plot size. Coarser than zoom 12 the figure would mean little: places that large
(Bordeaux, Bourgogne, a whole region) keep the area of their outline and ask the reader to open one of their
appellations. The area of the outline stays in the sheet as a note ("24% of the 51 ha outline"). Australia keeps the
planted area published by Wine Australia. The same tiles draw the vineyards on the map from zoom 9 in every country;
the Swiss layer from `poi.pmtiles` covers the zooms below and the claude.ai artifact page.

## Rivers, lakes, mountains and towns

`pipeline/geo.py` writes `web/data/geo.pmtiles` (zoom 2 to 8, drawn deeper by overzoom) and the search index
`web/data/geo.json`: named rivers with one smooth label line each, lakes, mountain ranges, plateaus and valleys, peaks with
their elevation (Natural Earth) and towns of 5,000 people or more (GeoNames). Rivers that Natural Earth names in two
languages along the way are joined under one name (Rhein and Rhine), and each keeps its other names for search and for
matching OpenStreetMap (Mosel and Moselle, Duero and Douro).

Every river, lake, peak and range has a stable id such as `river:rhone`, `lake:lake-geneva`, `peak:mont-blanc` or
`range:alps`. A click on it, a search or a link to `/#river:rhone` lights it up and shows its name above the map; the
rivers and lakes listed under *Where it is* on a place sheet do the same. From zoom 9 the web page also reads
OpenStreetMap from OpenFreeMap: small rivers, streams, villages and peaks, and the highlight follows the river there
(OSM writes La Saône, Río Duero: the article or the word river is allowed for). If OpenFreeMap cannot be reached the
Natural Earth rivers stay drawn close up. The layers switch on and off under Map and layers.

```bash
python pipeline/geo.py && python web/build_web.py
```

## Producers and wines

`pipeline/lwin.py` reads the LWIN database (Liv-ex Wine Identification Number, CC BY 4.0, free to download from
https://www.liv-ex.com/lwin-database-download/ into `raw/lwin/`) and places every live wine on the most precise atlas
place its record names: the site (Vosne-Romanée › Les Suchots, or the Einzellage in a German label such as Wehlener
Sonnenuhr), then the sub-region (Pauillac, Barolo), then the region (Champagne, Mosel). English names are translated by
`pipeline/lists/lwin_aliases.json`; two vineyards of the same name are never guessed. `build/lwin_unplaced.tsv` lists the
regions it could not place.

It writes `web/data/producers.json` (1.5 MB, for the search and the *Producers* list of every place and region) and
`web/data/wines.json` (9 MB, loaded when a producer opens or a search looks for a wine). A search for *Louis Roederer*
or *Cristal* opens the producer: its places light up on the map, and the sheet lists its wines under the place each
comes from, with the LWIN code. `#producer:<name>-<country>` links to one (`/#producer:louis-roederer-fr`).

```bash
python3 pipeline/lwin.py && python3 web/build_web.py
```

## Share images

`/api/story?id=<place id>` (or `?q=<name>`, or the short form `/story/<place id>`) returns a PNG of one place for
social media and slides: its real outline, the key facts from its details record and the atlas note. Formats:
`format=story` (1080 × 1920, default), `post` (1080 × 1350) and `square` (1080 × 1080).

Close up in France, Spain and Switzerland the background is the national orthophoto (IGN France, PNOA © IGN España,
SWISSIMAGE © swisstopo), whose licences allow reuse with the credit printed on the image. Everywhere else it is the
atlas' own dark land. Sentinel-2 cloudless is not used here because its licence excludes commercial reuse.
The function reads `web/data` from its own bundle, so previews and production behave the same.
Fonts: `api/fonts` (SIL OFL 1.1).

## Reels, short links and selections

Every video posted on the atlas' accounts is listed in `pipeline/lists/reels.json` with the places it shows, by
name. `pipeline/reels.py` resolves the names to atlas ids (it stops on a name it cannot pin down, so a reel never
links to the wrong vineyard) and writes `web/data/reels.json`; `web/build_pages.py` then writes:

* `/r/<slug>`: the short link for the caption or the link sticker of one reel. It opens the map at `/#r:<slug>`.
* `/reels/`: every reel, newest first, one tap from the map (the link in the profile bio). A reel scheduled for later
  is in the build already and shows from its publication time on.

On the map, `#r:<slug>`, `#set:<id>,<id>,…` and `#vs:<id>,<id>` light up a group of places together in gold, with
their names and areas on the map. The sheet lists them by area, offers the next step (the largest against the
smallest, the region around them, the other reels) and, for a pair, draws both at the same scale. A place opened
from the list keeps the group lit and a link back to it.

`/api/pair?ids=<id>,<id>[,…]` returns that same-scale drawing as an SVG, for two to eight places anywhere in the
world (`&theme=light` for a light background). It reads the outlines from the same PMTiles archives as the map.

```bash
# after each new reel: add it to pipeline/lists/reels.json, then
python3 pipeline/reels.py && python3 web/build_web.py
```

The analytics count each place, region, river or reel the visitor opens as a page view (`/map/place/<id>`,
`/map/region/<key>`, `/map/geo/<gid>`, `/map/reel/<slug>`), from their first click or key press on. A deep link opened
on arrival belongs to the landing page view, so a visit that only looks at what it came for still counts as a bounce.

## How it works

```
raw/            downloaded source files (not committed, see sources.json)
pipeline/       one Python script per source, all writing the same schema
  inao.py         France
  basemap.py      world countries, lakes, rivers (Natural Earth)
  geo.py          named rivers, lakes, ranges, peaks and towns for the map and the search (Natural Earth, GeoNames)
  eu_pdo.py       all EU PDO outlines outside the INAO file
  us_ava.py       United States AVAs
  fetch_world.py  downloads geoBoundaries, the Australian GI copy and OSM wine POIs for 44 countries
  world_specs.py  wine places outside the EU and US, each defined by the administrative units its law names
  world/          Chilean DO and Argentine IG tables compiled from the law texts
  world.py        builds those places (outlines, markers) and the Australian GIs
  build_world_web.py  merges the world layer into an existing web/data build (no need to rerun EU sources)
  rlp.py          Germany, Rheinland-Pfalz Einzellagen
  ch.py           Switzerland
  osm.py          wineries, Swiss vineyard areas
  fr_overview.py  generalised French outlines for small zoom levels
  build_index.py  search index
  enrich.py       computed facts per place: bedrock, neighbours, wineries inside, share of parent, wine rules
  build_details.py  merges source facts, computed facts and editorial notes per country
  build_tree.py   the explorer tree of the sidebar (web/data/tree.json)
  i18n_extract.py the translatable texts (web/i18n/_keys.json) and what each language still misses
  notes/          editorial notes (CC BY 4.0)
  build_tiles.py  vector tiles (PMTiles), search index, place details
  lists/          classification lists (DOCG, Vinos de Pago, Anbaugebiete)
contrib/        community additions in GeoJSON, reviewed by pull request
web/            the map (MapLibre GL, static files, no server code)
  index.src.html  the app; build_web.py turns it into index.html (web hosting) and artifact.html (claude.ai)
build/          intermediate files
```

Run it:

```bash
pip install geopandas pyogrio shapely pyproj
# install tippecanoe: https://github.com/felt/tippecanoe
python pipeline/basemap.py && python pipeline/inao.py && python pipeline/eu_pdo.py && python pipeline/us_ava.py && python pipeline/rlp.py \
  && python pipeline/ch.py && python pipeline/osm.py && python pipeline/fr_overview.py \
  && python pipeline/fetch_world.py && python pipeline/world.py \
  && python pipeline/build_tiles.py && python pipeline/enrich.py && python pipeline/build_details.py && python pipeline/build_tree.py
# or, to refresh only the world layer and the wineries on top of the published web/data:
python pipeline/fetch_world.py && python pipeline/world.py && python pipeline/osm.py && python pipeline/build_world_web.py && python pipeline/build_tree.py
python web/build_web.py                   # writes web/index.html and web/artifact.html
python web/encode_bin.py                  # only for the claude.ai artifact host, which serves text files
```

## Hosting

`web/` is a static site. Any host that answers HTTP range requests works, because the map reads
PMTiles archives in small pieces. Vercel deploys it as is (`vercel.json`). Locally:

```bash
npx serve web        # serve answers range requests; python -m http.server does not
```

## Map types

Base maps: Atlas (dark), Paper (light), Satellite (Sentinel-2 cloudless by EOX, with IGN France, swisstopo and
IGN España orthophotos from zoom 12) and Topo (OpenTopoMap). Terrain overlays: shaded relief, altitude tint,
slope and exposure. Slope and exposure tiles are computed in the browser from the elevation tiles. French
cadastral parcels (IGN) can be switched on from zoom 14.

## Per place, live in the browser

* Terrain: elevation, slope, aspect rose, slope classes and clear-sky sun on the ground relative to flat land.
* Climate 1991 to 2025 (Open-Meteo, ERA5-Land): growing season temperature, Winkler degree days, Huglin index,
  rain, harvest rain, sunshine, heat days, spring frost, cool nights, warming since the 1990s. In the southern
  hemisphere the season runs October to April and each vintage is named after its harvest year.
* Climate twins: the last five seasons of the place compared with 63 benchmark wine regions on every continent
  (same ERA5-Land data, fetched once and cached in the browser), with the closest matches and the warmth rank.
* Vintages: the measured climate of every vintage at that place, ranked, plus the editorial vintage chart of
  its region (`web/data/vintages.json`, 13 regions, 2005 to 2024).
* Soil: texture, pH, stones and organic carbon from SoilGrids 2.0 (250 m model).
* Wikipedia summary when an article clearly matches the place.

## Languages

The interface is in English by default and in Français, Italiano, Deutsch, Español, Português, Nederlands, 日本語,
中文 and 한국어 (button with the globe in the title box; `?lang=it` in a link opens a language directly; the choice is
remembered). Everything the interface writes is translated: menus, sheets, region pages, terrain, climate, soil,
vintages, My atlas, the guide and the glossary, plus the editorial atlas notes and the place types that come with the
data. Place names, grape names and the legal classifications (Grand cru, DOCG, AVA, Einzellage…) stay as the registers
write them. Country names come from the browser in the chosen language; Wikipedia summaries are fetched in the chosen
language first.

Texts live in `web/i18n/<code>.json`, keyed by the English text. `python pipeline/i18n_extract.py` lists every
translatable text in `web/i18n/_keys.json` and reports what each language is missing; see `web/i18n/README.md` for
the rules and how to add a language.

## Explore regions (sidebar)

The sidebar lists every place as a tree, so a region is two clicks away without knowing where it is on the map:
France › Bourgogne › Côte de Nuits › Morey-Saint-Denis › Premier cru › Les Ruchots.

* A name opens its sheet and flies the map there; the arrow only unfolds it. Arrow keys move through the list.
* Countries, regions and sub-regions open a region sheet: places, appellations, top crus and premiers crus counted, every
  place inside with its size, the top classified sites, and a Wikipedia summary when one matches.
* Hovering a name, in the sidebar or in a sheet list, draws it in gold on the map.
* A trail at the top of the map shows where you are; any step of it, or Esc, goes back up. Regions have their own
  links (`#g:FR/bourgogne/cote-de-nuits`).
* Wineries show their names from zoom 10.5 (the map drops names that would collide), and any dot shows its name on
  hover; a click opens a small sheet with its website and the appellations it sits in.

* Room for the map: the arrow beside the tabs (or `[`) slims the sidebar to a column of icons; the buttons on top of
  every sheet switch it between a small window (title only, a click opens it again), the normal panel and a large one;
  Map only (top right, or `F`) hides every panel and leaves a small title card for whatever you click. Esc brings the
  panels back. The slim sidebar and the large sheet are remembered in the browser.

The hierarchy is built by `pipeline/build_tree.py` into `web/data/tree.json`:

| Country | Levels | From |
|---|---|---|
| France | region › sub-region › appellation › premier cru › climat; grands crus under their village | `pipeline/lists/fr_regions.json` (editorial), INAO communes |
| Germany | Anbaugebiet › Bereich › Großlage › Einzellage | LWK Rheinland-Pfalz |
| United States | state › AVA › nested AVAs | UC Davis AVA project |
| Australia | state › zone › region › subregion | Wine Australia |
| Italy, Spain, Austria, Greece | administrative region › appellation | geoBoundaries ADM1/ADM2, by the centre of each place |
| Everywhere else | the parent named in each register | the source of each country |

## My atlas (personal dashboard)

Press **My atlas** (or the M key) for a dashboard that stays on the visitor's device:

* Overview: counts, recently viewed places, random discovery (grand cru, DOCG, Einzellage, AVA), the best recent vintages, places per country.
* Saved: places saved from any sheet, with the terrain and climate measured when they were opened, sortable by warmth, height or slope.
* Journal: tasting notes pinned to a vineyard (wine, vintage, score, notes), export to CSV or JSON, import JSON.
* Compare: up to four places side by side, with the growing season temperature of every vintage on one chart.
* Explore: every place in the atlas, filtered by name, country, level and classification, sortable.

Saved places show as gold rings on the map, tastings as copper rings. With a terrain overlay on, the cursor shows
elevation, slope and exposure under it.

## Pages for search engines and the weekly post

`web/build_pages.py` (run by `build_web.py`) writes one static page per place, region and country under
`web/places/`, plus `web/sitemap.xml` and `web/robots.txt`. The pages are made from the same files as the map, link
to it (`/#<place id>`) and use `https://openwineatlas.com` as their address.

`pipeline/social_card.py` picks the next place with an editorial note (countries in turn), renders a 1080x1350 card
of it from the atlas and drafts an English caption. The weekly post keeps its images and the list of posted places
on the `social` branch.

## Globe

The atlas opens on a globe and flies in to Europe. Globe / Flat (top right, or the G key) switches between the
globe and the flat map; the choice is remembered in the browser. The globe turns into the flat map by itself
close in (MapLibre does this around zoom 11 to 12), so parcels look the same in both. World view shows the whole
earth, the countries in Explore regions fly across it, and a click on a place seen from far out flies in to it. The base
map cuts Russia and Fiji at the date line (`pipeline/basemap.py`) so no outline runs round the earth.

## Terrain

The web build adds a hillshade, a 2D/3D switch and a Terrain section on every sheet. When you open a
place the browser downloads the elevation tiles under its outline (Mapterhorn, terrarium encoding, up to
zoom 14, about 3 m cells), rasterises the outline and computes:

* elevation range, 10th to 90th percentile and mean
* slope per cell (Horn method), mean, steepest tenth, share of five slope classes
* aspect per cell where the slope is 2° or more, an eight sector rose and the mean direction

Large appellations are measured on coarser cells, so slope and aspect are shown only when cells are
35 m or finer. Add `?dem=<url template>` to the address to test another terrarium tile source.

## Open system

* Data schema: see [SCHEMA.md](SCHEMA.md). One schema for every country.
* Adding a region: write one script that converts an official dataset into the schema. See [CONTRIBUTING.md](CONTRIBUTING.md).
* Fixing a place: open an issue or send a suggestion from the map ("Suggest a correction").
* Code: MIT. Data: each layer keeps the licence of its source, see [DATA_LICENSE.md](DATA_LICENSE.md).

## How outlines are drawn outside the EU and the US

Few countries publish their wine boundaries as open data. The atlas uses three levels of precision, shown on
every sheet and on the map:

* **legal**: the outline is the union of the administrative units that the law names (Chilean comunas in
  Decreto 464, Argentine departments, Japanese prefectures, Moldovan raions), or the official GI outline (Australia).
* **approx** (dashed on the map): the law draws the line along roads, rivers, farms or altitude, so the
  administrative units that contain the area stand in for it. The real area is smaller.
* **point**: places far smaller than any unit (South African wards, Mendoza parajes, Georgian village PDOs, the
  Niagara benches) are a marker at the town they are named after, never a misleadingly large polygon.

Political choices: Crimea, the Golan Heights and the West Bank are not drawn. Admin units come from
geoBoundaries gbOpen (Runfola et al. 2020); each place shows the licence of its unit layer.

## Next datasets to add

* Switzerland: cantonal vineyard cadastres (Rebbaukataster) and Geneva's AOC cadastre.
* Germany: Einzellagen for Baden, Württemberg, Franken, Rheingau, Hessische Bergstraße, Saale-Unstrut, Sachsen.
* Italy: Barolo and Barbaresco MGA, Etna contrade, Chianti Classico UGA where open data exists.
* Spain: MAPA "Zonas de calidad diferenciada: vinos" layer, Priorat vi de vila and paratges.
* Australia: the official Wine Australia GI layer (CC BY 4.0, ArcGIS FeatureServer
  `services6.arcgis.com/s8j6JbJJCqmhNgh7/arcgis/rest/services/Wine_Geographical_Indications_Australia/FeatureServer`,
  layers 0 subregions, 1 regions, 2 zones) to replace the adynak copy. Subregions are in
  `pipeline/world/au_official_subregions.geojson`; save the regions and zones layers next to it as
  `au_official_regions.geojson` and `au_official_zones.geojson` and `world.py` uses them automatically.
* New Zealand (IPONZ GI boundary files), South Africa (SAWIS demarcations), British Columbia (sub-GI schedule maps),
  Ontario (O. Reg. 359/24 areas): official boundaries exist only as PDFs or behind restrictive terms.
* Russia, Albania, Kosovo, Peru, Bolivia, Morocco, Tunisia: wine regions not yet mapped.
* Precomputed terrain for every place in the search index, so places can be sorted by slope or aspect.
* Climate: growing degree days and rainfall per place from E-OBS or ERA5-Land.
