# Open Wine Atlas

An open, interactive atlas of wine places: appellations, crus, climats and single vineyards.
It starts with France, Italy, Spain, Germany and Switzerland and is built only from data
published under open licences, so anyone can check it, reuse it and extend it.

## What is in it (v0.1, October 2026)

| Country | Detail | Source | Licence |
|---|---|---|---|
| France | Every AOC at parcel level, plus premiers crus, grand cru climats and other complementary names (356 appellations, 916 dénominations) | INAO, Délimitation parcellaire des AOC viticoles, 2026-08-31 | Licence Ouverte 2.0 |
| Italy | 408 DOC/DOCG outlines (by commune), 73 flagged DOCG | Candiago et al. 2022, EU wine PDO inventory | CC BY 4.0 |
| Spain | 99 DO/DOCa/Vino de Pago outlines (by commune) | Candiago et al. 2022 | CC BY 4.0 |
| Germany | 13 Anbaugebiete and 6 single-site PDOs; 1,586 Einzellagen and 84 Großlagen for Mosel, Rheinhessen, Pfalz, Nahe, Mittelrhein and Ahr | Candiago et al. 2022; Landwirtschaftskammer Rheinland-Pfalz | CC BY 4.0; dl-de/by-2-0 |
| Switzerland | 13 cantonal AOC outlines (canton boundary), OSM vineyard areas | BFS GEOSTAT / swisstopo; OpenStreetMap | Open use with attribution; ODbL |
| All | About 5,800 wineries | OpenStreetMap | ODbL |
| France, Italy | Per-wine rules: colour, category, main and secondary grapes, yields, density | EU specifications compiled by Candiago et al. 2022 (via pdo-wine-data) | CC BY 4.0 |
| All | Regional bedrock per place | GLiM, Hartmann & Moosdorf 2012 | CC BY 3.0 |
| All | 151 editorial notes | Open Wine Atlas contributors | CC BY 4.0 |
| All | Relief, 3D terrain, and per place elevation, slope and aspect (measured live in the browser) | Mapterhorn terrain tiles: IGN RGE ALTI, German DGM1, swissALTI3D, IGN MDT, Copernicus GLO-30 | Open licences, see mapterhorn.com/attribution |

## How it works

```
raw/            downloaded source files (not committed, see sources.json)
pipeline/       one Python script per source, all writing the same schema
  inao.py         France
  eu_pdo.py       Italy, Spain, Germany (appellation outlines)
  rlp.py          Germany, Rheinland-Pfalz Einzellagen
  ch.py           Switzerland
  osm.py          wineries, Swiss vineyard areas
  fr_overview.py  generalised French outlines for small zoom levels
  build_index.py  search index
  enrich.py       computed facts per place: bedrock, neighbours, wineries inside, share of parent, wine rules
  build_details.py  merges source facts, computed facts and editorial notes per country
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
python pipeline/inao.py && python pipeline/eu_pdo.py && python pipeline/rlp.py \
  && python pipeline/ch.py && python pipeline/osm.py && python pipeline/fr_overview.py \
  && python pipeline/build_tiles.py && python pipeline/enrich.py && python pipeline/build_details.py
python web/build_web.py                   # writes web/index.html and web/artifact.html
python web/encode_bin.py                  # only for the claude.ai artifact host, which serves text files
```

## Hosting

`web/` is a static site. Any host that answers HTTP range requests works, because the map reads
PMTiles archives in small pieces. Vercel deploys it as is (`vercel.json`). Locally:

```bash
npx serve web        # serve answers range requests; python -m http.server does not
```

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

## Next datasets to add

* Switzerland: cantonal vineyard cadastres (Rebbaukataster) and Geneva's AOC cadastre.
* Germany: Einzellagen for Baden, Württemberg, Franken, Rheingau, Hessische Bergstraße, Saale-Unstrut, Sachsen.
* Italy: Barolo and Barbaresco MGA, Etna contrade, Chianti Classico UGA where open data exists.
* Spain: MAPA "Zonas de calidad diferenciada: vinos" layer, Priorat vi de vila and paratges.
* Precomputed terrain for every place in the search index, so places can be sorted by slope or aspect.
* Climate: growing degree days and rainfall per place from E-OBS or ERA5-Land.
