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
| France, Italy | Per-wine rules: colour, category, main and secondary grapes, yields, density | EU specifications compiled by Candiago et al. 2022 (via pdo-wine-data) | CC BY 4.0 |
| All | Regional bedrock per place | GLiM, Hartmann & Moosdorf 2012 | CC BY 3.0 |
| All | 151 editorial notes | Open Wine Atlas contributors | CC BY 4.0 |
| All | Relief, 3D terrain, and per place elevation, slope and aspect (measured live in the browser) | Mapterhorn terrain tiles: IGN RGE ALTI, German DGM1, swissALTI3D, IGN MDT, Copernicus GLO-30 | Open licences, see mapterhorn.com/attribution |

## How it works

```
raw/            downloaded source files (not committed, see sources.json)
pipeline/       one Python script per source, all writing the same schema
  inao.py         France
  basemap.py      world countries, lakes, rivers (Natural Earth)
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
